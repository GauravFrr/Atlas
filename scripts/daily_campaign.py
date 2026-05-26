"""
Daily outreach runner — CSV or mock from .env, then reply sync.

.env (optional):
  DAILY_CAMPAIGN_CSV=d:\leads.csv
  DAILY_CAMPAIGN_NICHE=real_estate
  DAILY_CAMPAIGN_CITY=London
  DAILY_CAMPAIGN_LEADS=5

  python scripts/daily_campaign.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger

from config import get_settings
from core.campaign_orchestrator import run_campaign
from database.connection import init_db
from modules.outreach.reply_sync import sync_instantly_replies
from utils.send_router import resolve_send_mode


async def main() -> None:
    settings = get_settings()
    await init_db()

    csv_path = os.getenv("DAILY_CAMPAIGN_CSV", "").strip()
    niche = os.getenv("DAILY_CAMPAIGN_NICHE", "real_estate")
    city = os.getenv("DAILY_CAMPAIGN_CITY", "London")
    leads = int(os.getenv("DAILY_CAMPAIGN_LEADS", "5"))
    mode = resolve_send_mode(settings, os.getenv("EMAIL_SEND_MODE", "instantly"))

    if csv_path:
        if not Path(csv_path).is_file():
            logger.error(f"DAILY_CAMPAIGN_CSV not found: {csv_path}")
            sys.exit(1)
        result = await run_campaign(
            niche=niche,
            city=city,
            leads=leads,
            send_mode=mode,
            csv_path=csv_path,
            settings=settings,
        )
    else:
        logger.warning("DAILY_CAMPAIGN_CSV not set — skipping send, reply sync only")
        result = None

    if settings.has_instantly:
        reply = await sync_instantly_replies(settings)
        logger.info(f"Reply sync: {reply.new_replies} new")

    if result:
        print(result.summary_text())


if __name__ == "__main__":
    asyncio.run(main())
