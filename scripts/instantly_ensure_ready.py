"""
Resume Instantly campaign, sending accounts, and warmup before outreach.

  python scripts/instantly_ensure_ready.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.platforms.instantly import InstantlyClient


async def main() -> None:
    settings = get_settings()
    if not settings.has_instantly:
        print("Set INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID in .env")
        sys.exit(1)

    client = InstantlyClient(
        settings.instantly_api_key, settings.instantly_campaign_id
    )
    camp = await client.get_campaign()
    if camp:
        print(f"Campaign: {camp.get('name')} (status={camp.get('status')})")
        print(f"Mailboxes: {', '.join(camp.get('email_list') or [])}")

    ok = await client.ensure_send_ready(force=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
