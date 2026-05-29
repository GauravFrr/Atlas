"""
Simulate Razorpay payment_link.paid webhook (test mode E2E without card UI).

Requires a pending payment row (from create_payment_link.py).

  python scripts/simulate_razorpay_paid.py --email itzmi3xel@gmail.com
  python scripts/simulate_razorpay_paid.py --email itzmi3xel@gmail.com --url http://127.0.0.1:8787
  python scripts/simulate_razorpay_paid.py --email itzmi3xel@gmail.com --url https://service-1-webhooks-production.up.railway.app
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from config import get_settings
from constants import PaymentStatus
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from database.repositories.payment_repository import PaymentRepository


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _payload_for_payment(link_id: str, lead_id: str) -> dict:
    return {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": link_id,
                    "status": "paid",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_simulated",
                    "status": "captured",
                    "notes": {"lead_id": lead_id},
                }
            },
        },
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8787",
        help="Webhook base URL (no trailing path)",
    )
    args = parser.parse_args()

    settings = get_settings()
    await init_db()
    factory = get_session_factory()
    pay_repo = PaymentRepository()
    lead_repo = LeadRepository()

    async with factory() as session:
        lead = await lead_repo.get_by_email(session, args.email.strip().lower())
        if not lead:
            print("Lead not found")
            sys.exit(1)
        payment = await pay_repo.get_by_lead(session, lead.id, pending_only=True)
        if not payment:
            payment = await pay_repo.get_by_lead(session, lead.id, pending_only=False)
        if not payment:
            print("No payment row — run: python scripts/create_payment_link.py --email", args.email)
            sys.exit(1)
        if payment.status == PaymentStatus.CONFIRMED:
            print(f"Payment already confirmed ({payment.id}). Use a new link or another lead.")
            sys.exit(0)
        link_id = payment.razorpay_payment_link_id or ""
        if not link_id:
            print("Payment row missing razorpay_payment_link_id")
            sys.exit(1)

    body_dict = _payload_for_payment(link_id, lead.id)
    body = json.dumps(body_dict).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    secret = (settings.razorpay_webhook_secret or "").strip()
    if secret:
        headers["X-Razorpay-Signature"] = _sign(body, secret)
    else:
        print("Warning: RAZORPAY_WEBHOOK_SECRET empty — webhook may reject if server requires it")

    target = args.url.rstrip("/") + "/webhooks/razorpay"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(target, content=body, headers=headers)
    print(f"POST {target} → {resp.status_code}")
    print(resp.text)
    if resp.status_code >= 400:
        sys.exit(1)
    print("Check Telegram for PAID — START DELIVERY checklist.")


if __name__ == "__main__":
    asyncio.run(main())
