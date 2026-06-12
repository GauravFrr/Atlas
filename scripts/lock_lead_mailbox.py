"""
Backfill per-lead mailbox lock (when first email was sent outside the agent).

  python scripts/lock_lead_mailbox.py --email itzmi3xel@gmail.com --from gaurav@gauravxd.dev
  python scripts/lock_lead_mailbox.py --email lead@biz.com --from mike@urmikexd.dev --domain urmikexd-mike
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from utils.mailbox_lock import lock_mailbox_on_lead


async def main() -> None:
    parser = argparse.ArgumentParser(description="Lock outbound mailbox for a lead")
    parser.add_argument("--email", required=True, help="Lead email address")
    parser.add_argument("--from", dest="from_email", required=True, help="From address used first")
    parser.add_argument("--domain", default="", help="Optional outreach domain name from pool")
    parser.add_argument("--channel", default="smtp", choices=("smtp", "instantly"))
    args = parser.parse_args()

    await init_db()
    repo = LeadRepository()
    async with get_session_factory()() as session:
        lead = await repo.get_by_email(session, args.email.strip().lower())
        if not lead:
            print(f"No lead for {args.email}")
            return
        from config import get_settings
        from utils.domain_pool import DomainPool

        pool = DomainPool(get_settings())
        domain = pool.get_by_name(args.domain) if args.domain else None
        if not domain:
            domain = pool.get_by_from_email(args.from_email)
        lock_mailbox_on_lead(
            lead,
            smtp_cfg={"from_email": args.from_email},
            domain=domain,
            send_channel=args.channel,
        )
        await session.commit()
        print(f"Locked {lead.email} -> {args.from_email}")


if __name__ == "__main__":
    asyncio.run(main())
