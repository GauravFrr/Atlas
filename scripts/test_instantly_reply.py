"""
Check Instantly reply context + optional dry-run send path.

  python scripts/test_instantly_reply.py --email lead@biz.com
  python scripts/test_instantly_reply.py --email lead@biz.com --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_settings
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from modules.outreach.instantly_reply_send import (
    resolve_instantly_reply_context,
    send_approved_reply_via_instantly,
)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test Instantly reply send context")
    parser.add_argument("--email", required=True, help="Lead email in DB")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print reply context; do not POST /emails/reply",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.has_instantly:
        print("Instantly not configured (INSTANTLY_API_KEY + INSTANTLY_CAMPAIGN_ID)")
        sys.exit(1)

    await init_db()
    repo = LeadRepository()
    async with get_session_factory()() as session:
        lead = await repo.get_by_email(session, args.email.strip().lower())
        if not lead:
            print(f"No lead for {args.email}")
            sys.exit(1)

    ctx = await resolve_instantly_reply_context(settings, lead)
    print("Reply context:")
    print(f"  eaccount:       {ctx.get('eaccount') or '(missing)'}")
    print(f"  reply_to_uuid:  {ctx.get('reply_to_uuid') or '(missing)'}")
    data = lead.enrichment_data or {}
    print(f"  locked mailbox: {data.get('outbound_mailbox') or '(none)'}")
    last = data.get("last_reply") or {}
    print(f"  last_reply id:  {last.get('instantly_email_id') or '(none)'}")

    if args.dry_run:
        if ctx.get("eaccount") and ctx.get("reply_to_uuid"):
            print("\nOK — ready for Instantly reply API on approve.")
        else:
            print("\nMissing context — run reply sync or lock mailbox.")
            sys.exit(2)
        return

    result = await send_approved_reply_via_instantly(
        settings,
        lead,
        subject="Test",
        body="(Atlas Instantly reply test — ignore)",
    )
    print(result)
    sys.exit(0 if result.get("ok") else 3)


if __name__ == "__main__":
    asyncio.run(main())
