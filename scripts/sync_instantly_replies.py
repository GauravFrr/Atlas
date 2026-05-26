"""
Poll Instantly for new lead replies → update DB → Telegram alerts.

  python scripts/sync_instantly_replies.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from database.connection import init_db
from modules.outreach.reply_sync import sync_instantly_replies


async def main() -> None:
    settings = get_settings()
    if not settings.has_instantly:
        print("Set INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID in .env")
        sys.exit(1)
    await init_db()
    result = await sync_instantly_replies(settings)
    print(
        f"Scanned: {result.scanned} | New: {result.new_replies} | "
        f"Hot: {result.interested} | Not now: {result.not_now} | "
        f"Unsub: {result.unsubscribe} | Unknown: {result.unknown}"
    )
    if result.errors:
        print("Errors:", result.errors)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
