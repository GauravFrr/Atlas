"""
Razorpay payment links — blueprint §22 (7-day expiry, UPI/cards/wallets).
"""

from __future__ import annotations

import asyncio
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger

from config import Settings


class RazorpayClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Any = None

    @property
    def is_configured(self) -> bool:
        return self.settings.has_razorpay

    def _get_client(self) -> Any:
        if self._client is None:
            import razorpay

            self._client = razorpay.Client(
                auth=(
                    self.settings.razorpay_key_id,
                    self.settings.razorpay_key_secret,
                )
            )
        return self._client

    async def create_payment_link(
        self,
        *,
        amount_inr: int,
        description: str,
        customer_name: str,
        customer_email: str,
        reference_id: str,
        notes: dict[str, str] | None = None,
        expire_days: int | None = None,
    ) -> dict[str, Any]:
        """Create Razorpay payment link; amount_inr is in rupees (not paise)."""
        if not self.is_configured:
            raise RuntimeError("Razorpay not configured")

        days = expire_days or int(
            getattr(self.settings, "razorpay_payment_link_expire_days", 7) or 7
        )
        expire_by = int(
            (datetime.now(timezone.utc) + timedelta(days=days)).timestamp()
        )
        amount_paise = max(100, int(amount_inr) * 100)

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": description[:255],
            "customer": {
                "name": (customer_name or "Client")[:120],
                "email": customer_email,
            },
            "notify": {"sms": False, "email": False},
            "reminder_enable": True,
            "expire_by": expire_by,
            "reference_id": reference_id[:40],
            "notes": notes or {},
        }

        def _create() -> dict[str, Any]:
            return self._get_client().payment_link.create(payload)

        data = await asyncio.to_thread(_create)
        logger.success(
            f"[Razorpay] Payment link {data.get('id')} → {data.get('short_url', '')[:60]}"
        )
        return data

    @staticmethod
    def verify_webhook_signature(
        body: bytes, signature: str, secret: str
    ) -> bool:
        if not secret or not signature:
            return False
        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
