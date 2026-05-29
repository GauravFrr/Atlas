"""
Pull Instantly replies into Atlas + Telegram (when webhook missed).

  python scripts/pull_instantly_reply.py
  python scripts/pull_instantly_reply.py --email itzmi3xel+mocktest999@gmail.com
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
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from modules.outreach.reply_sync import sync_instantly_replies


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--email",
        default="",
        help="After sync, queue Telegram draft for this lead if in DB",
    )
    p.add_argument(
        "--queue",
        action="store_true",
        help="Force queue_close_approval for --email after sync",
    )
    args = p.parse_args()

    settings = get_settings()
    if not settings.has_instantly:
        print("Set INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID in .env")
        sys.exit(1)

    await init_db()
    print("Syncing Instantly inbox → agent.db ...")
    result = await sync_instantly_replies(settings)
    print(
        f"Scanned: {result.scanned} | New: {result.new_replies} | "
        f"Interested: {result.interested} | Errors: {result.errors}"
    )

    email = (args.email or "").strip().lower()
    if not email:
        return

    factory = get_session_factory()
    async with factory() as session:
        lead = await LeadRepository().get_by_email(session, email)
    if not lead:
        print(
            f"\nLead {email} not in agent.db — webhook/sync cannot draft.\n"
            "Fix: re-run campaign with that email, or:\n"
            f"  python scripts/queue_close_approval.py --email {email} --reply \"yes interested\"\n"
            "(only works if you seed/add the lead first)"
        )
        sys.exit(1)

    if args.queue or result.interested > 0:
        print(f"\nLead found: {lead.business_name}. Queueing Telegram draft ...")
        import subprocess

        py = sys.executable
        subprocess.check_call(
            [
                py,
                str(ROOT / "scripts" / "queue_close_approval.py"),
                "--email",
                email,
                "--reply",
                "how much does it cost",
            ]
        )


if __name__ == "__main__":
    asyncio.run(main())
