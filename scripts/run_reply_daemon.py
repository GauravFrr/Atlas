"""
Background reply poller — checks Instantly every N minutes.

  python scripts/run_reply_daemon.py
  python scripts/run_reply_daemon.py --interval 10
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger

from config import get_settings
from database.connection import init_db
from modules.outreach.reply_sync import sync_instantly_replies


async def main() -> None:
    parser = argparse.ArgumentParser(description="Poll Instantly replies on a loop")
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Minutes between polls (default: REPLY_SYNC_INTERVAL_MINUTES from .env)",
    )
    args = parser.parse_args()
    settings = get_settings()
    if not settings.has_instantly:
        logger.error("Instantly not configured in .env")
        sys.exit(1)

    minutes = args.interval or settings.reply_sync_interval_minutes
    seconds = max(60, minutes * 60)

    await init_db()
    logger.info(f"Reply daemon started — every {minutes} min")

    while True:
        try:
            await sync_instantly_replies(settings)
        except Exception as e:
            logger.exception(f"Reply sync error: {e}")
        await asyncio.sleep(seconds)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
