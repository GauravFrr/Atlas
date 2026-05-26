"""List leads in INSTANTLY_CAMPAIGN_ID via API (debug UI mismatch)."""

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
    client = InstantlyClient(
        settings.instantly_api_key, settings.instantly_campaign_id
    )
    items = await client.list_campaign_leads(limit=100)
    print(f"Campaign {settings.instantly_campaign_id[:8]}... — {len(items)} lead(s)\n")
    for x in items:
        print(
            f"{x.get('email')} | {x.get('first_name')} {x.get('last_name')} | "
            f"status={x.get('status')}"
        )


if __name__ == "__main__":
    asyncio.run(main())
