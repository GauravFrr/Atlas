"""
Create a Razorpay payment link for a lead (by email or lead id).

  python scripts/create_payment_link.py --email team@example.com
  python scripts/create_payment_link.py --lead-id <uuid>
  python scripts/create_payment_link.py --email you@gmail.com --name "Test" --standalone
  python scripts/create_payment_link.py --email x@y.com --amount 4999
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_settings
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from modules.payment_handler.manager import Manager


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--email", help="Lead email in agent.db (or customer email with --standalone)")
    p.add_argument("--lead-id", help="Lead UUID")
    p.add_argument("--name", default="Client", help="Customer name for --standalone")
    p.add_argument(
        "--standalone",
        action="store_true",
        help="Create link without a lead row (Razorpay test / your own email)",
    )
    p.add_argument("--amount", type=int, help="Amount in INR (default from config)")
    p.add_argument(
        "--force-new",
        action="store_true",
        help="Create a new link even if a pending link exists",
    )
    args = p.parse_args()

    if not args.email and not args.lead_id:
        p.error("Provide --email or --lead-id")

    settings = get_settings()
    if not settings.has_razorpay:
        print("Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env")
        sys.exit(1)

    await init_db()
    mgr = Manager(settings)
    lead_id = args.lead_id

    if args.standalone and args.email:
        email = args.email.strip()
        amount = args.amount or mgr.default_amount_inr()
        data = await mgr.razorpay.create_payment_link(
            amount_inr=amount,
            description=f"Agent-Earns — {args.name}",
            customer_name=args.name,
            customer_email=email,
            reference_id=f"std-{uuid.uuid4().hex[:24]}",
            notes={"standalone": "true"},
        )
        print(f"OK (standalone) — INR {amount} link:\n{data.get('short_url')}")
        print("Note: no lead in DB — webhook may not match a lead unless email exists in DB.")
        return

    if args.email and not lead_id:
        factory = get_session_factory()
        async with factory() as session:
            lead = await LeadRepository().get_by_email(session, args.email.strip())
            if not lead:
                print(f"No lead for {args.email}")
                print("Tip: use --standalone for your own test email, or pick a lead from DB:")
                print("  python scripts/list_leads_with_email.py")
                sys.exit(1)
            lead_id = lead.id

    if args.force_new and lead_id:
        from constants import PaymentStatus
        from database.repositories.payment_repository import PaymentRepository

        factory = get_session_factory()
        async with factory() as session:
            old = await PaymentRepository().get_by_lead(
                session, lead_id, pending_only=True
            )
            if old:
                old.status = PaymentStatus.CANCELLED
                await session.commit()
                print(f"Cancelled previous pending link {old.id}")

    rz_ref = None
    if args.force_new and lead_id:
        rz_ref = f"{lead_id}-{uuid.uuid4().hex[:8]}"

    result = await mgr.create_link_for_lead(
        lead_id, amount_inr=args.amount, reference_id=rz_ref
    )
    if result.get("ok"):
        print(f"OK — INR {result.get('amount_inr')} link:\n{result.get('short_url')}")
    else:
        print(f"Failed: {result}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
