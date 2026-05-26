"""
Razorpay webhook — payment_link.paid → confirm payment + Telegram.

Register in Razorpay Dashboard → Webhooks:
  URL: https://YOUR-PUBLIC-URL/webhooks/razorpay
  Secret: same as RAZORPAY_WEBHOOK_SECRET in .env
  Events: payment_link.paid, payment.captured
"""

from __future__ import annotations

from fastapi import Header, HTTPException, Request
from loguru import logger

from config import get_settings
from database.connection import init_db
from modules.payment_handler.manager import Manager

_init_done = False


async def _ensure_db() -> None:
    global _init_done
    if not _init_done:
        await init_db()
        _init_done = True


async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None, alias="X-Razorpay-Signature"),
) -> dict[str, str]:
    settings = get_settings()
    secret = (settings.razorpay_webhook_secret or "").strip()
    body = await request.body()

    if secret:
        from modules.payment_handler.providers.razorpay_client import RazorpayClient

        if not x_razorpay_signature or not RazorpayClient.verify_webhook_signature(
            body, x_razorpay_signature, secret
        ):
            logger.warning("[Razorpay] Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

    import json

    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    await _ensure_db()
    mgr = Manager(settings)
    result = await mgr.handle_webhook_payload(payload)
    logger.info(f"[Razorpay] Webhook result: {result}")
    return {k: str(v) for k, v in result.items()}
