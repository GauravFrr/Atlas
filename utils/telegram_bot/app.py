"""Build full Atlas Telegram application (panel + approvals)."""

from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler

from config import Settings
from utils.telegram_bot.handlers import register_handlers, _post_init


def build_application(settings: Settings) -> Application:
    if not settings.has_telegram:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(_post_init)
        .build()
    )
    app.bot_data["settings"] = settings
    register_handlers(app)
    from utils.telegram_approval import _on_callback

    app.add_handler(CallbackQueryHandler(_on_callback, pattern=r"^close:"))
    return app
