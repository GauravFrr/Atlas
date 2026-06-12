"""Run Atlas Telegram bot — webhook on Railway, polling locally."""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from loguru import logger
from telegram import Update
from telegram.error import NetworkError, RetryAfter, TimedOut
from telegram.ext import Application

from config import Settings


async def _on_error(update: object, context) -> None:
    err = context.error
    if isinstance(err, RetryAfter):
        logger.warning(f"Telegram rate limit — retry after {err.retry_after}s")
        return
    if isinstance(err, (NetworkError, TimedOut)):
        logger.warning(f"Telegram network blip (will retry): {err}")
        return
    logger.exception("Telegram handler error: {}", err)


def register_error_handler(app: Application) -> None:
    app.add_error_handler(_on_error)


def _run_polling(app: Application) -> None:
    logger.info("Telegram mode: long polling (local / no public domain)")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        bootstrap_retries=-1,
        close_loop=False,
    )


def _run_webhook_server(
    app: Application, settings: Settings, webhook_url: str
) -> None:
    """Starlette ASGI app — avoids FastAPI 422 on Telegram POST body."""
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Route

    parsed = urlparse(webhook_url)
    hook_path = parsed.path or "/telegram/webhook"
    if not hook_path.startswith("/"):
        hook_path = f"/{hook_path}"

    @asynccontextmanager
    async def lifespan(_starlette_app: Starlette):
        await app.initialize()
        await app.start()
        await app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.success(f"Telegram webhook registered → {webhook_url}")
        yield
        await app.bot.delete_webhook(drop_pending_updates=False)
        await app.stop()
        await app.shutdown()

    async def health(_request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "telegram"})

    async def telegram_webhook(request) -> Response:
        # Always return 200 so Telegram does not retry-storm on parse errors.
        try:
            body = await request.body()
            if body:
                data = json.loads(body)
                update = Update.de_json(data, app.bot)
                if update:
                    await app.process_update(update)
        except Exception as exc:
            logger.exception("Telegram webhook handler failed: {}", exc)
        return Response(status_code=200)

    asgi_app = Starlette(
        routes=[
            Route("/health", health, methods=["GET"]),
            Route(hook_path, telegram_webhook, methods=["POST"]),
        ],
        lifespan=lifespan,
    )

    port = int(os.environ.get("PORT", "8080"))
    logger.info(f"Telegram mode: webhook on 0.0.0.0:{port}{hook_path}")
    uvicorn.run(asgi_app, host="0.0.0.0", port=port, log_level="info")


def run_bot(app: Application, settings: Settings) -> None:
    register_error_handler(app)

    if settings.telegram_webhook_enabled:
        webhook_url = settings.resolved_telegram_webhook_url()
        if not webhook_url:
            logger.warning(
                "TELEGRAM_USE_WEBHOOK set but no URL — "
                "assign a public domain on Railway or set TELEGRAM_WEBHOOK_URL"
            )
            _run_polling(app)
            return
        _run_webhook_server(app, settings, webhook_url)
        return

    _run_polling(app)
