"""
Dry-run post-payment delivery handoff (Telegram + DB) without Razorpay.

  python scripts/test_payment_handoff.py --email lead@example.com
  python scripts/test_payment_handoff.py --lead-id UUID
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from config import get_settings
from constants import LeadStatus
from database.connection import get_session_factory, init_db
from database.models.payment import Payment
from database.repositories.lead_repository import LeadRepository
from modules.service_delivery.payment_handoff import start_delivery_after_payment


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", default="")
    parser.add_argument("--lead-id", default="")
    parser.add_argument("--dry-run", action="store_true", help="Print only, no Telegram")
    args = parser.parse_args()

    settings = get_settings()
    await init_db()
    repo = LeadRepository()
    factory = get_session_factory()

    async with factory() as session:
        lead = None
        if args.lead_id:
            lead = await repo.get_by_id(session, args.lead_id.strip())
        elif args.email:
            lead = await repo.get_by_email(session, args.email.strip().lower())
        if not lead:
            print("Lead not found")
            sys.exit(1)

        payment = Payment(
            lead_id=lead.id,
            amount_paise=399900,
            description="Test handoff",
            customer_email=lead.email or "test@example.com",
            customer_name=lead.business_name,
            short_url="https://rzp.io/test",
        )
        payment.id = "test-handoff"
        lead.status = LeadStatus.CLIENT

        if args.dry_run:
            from modules.service_delivery.payment_handoff import (
                build_delivery_record,
                format_telegram_handoff,
            )

            delivery = build_delivery_record(lead, payment, settings)
            print(format_telegram_handoff(lead, delivery))
            return

        await start_delivery_after_payment(lead, payment, settings)
        await session.flush()
        await session.commit()
        print(f"Handoff sent for {lead.business_name} ({lead.id})")


if __name__ == "__main__":
    asyncio.run(main())
