"""
Apply Agent-Earns recommended Instantly campaign settings + activate.

  python scripts/instantly_configure_campaign.py
  python scripts/instantly_configure_campaign.py --daily-limit 15 --timezone America/New_York
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.platforms.instantly import CAMPAIGN_STATUS_ACTIVE, InstantlyClient


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily-limit", type=int, default=10)
    parser.add_argument("--timezone", default="America/Detroit")
    parser.add_argument("--no-activate", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    if not settings.has_instantly:
        print("Set INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID in .env")
        sys.exit(1)

    client = InstantlyClient(
        settings.instantly_api_key, settings.instantly_campaign_id
    )
    before = await client.get_campaign()
    if not before:
        print("Could not load campaign")
        sys.exit(1)

    print(f"Before: status={before.get('status')} daily_limit={before.get('daily_limit')}")

    ok = await client.apply_agent_earns_preset(
        timezone=args.timezone,
        daily_limit=args.daily_limit,
        activate=not args.no_activate,
    )
    after = await client.get_campaign()
    if not after:
        sys.exit(1)

    sched = (after.get("campaign_schedule") or {}).get("schedules") or [{}]
    s0 = sched[0] if sched else {}
    print("\nAfter:")
    print(f"  status:      {after.get('status')} ({'active' if after.get('status') == CAMPAIGN_STATUS_ACTIVE else 'paused'})")
    print(f"  daily_limit: {after.get('daily_limit')}")
    print(f"  email_gap:   {after.get('email_gap')} min")
    print(f"  stop_reply:  {after.get('stop_on_reply')}")
    print(f"  stop_ooo:    {after.get('stop_on_auto_reply')}")
    print(f"  schedule:    {s0.get('timing')} {s0.get('days')} tz={s0.get('timezone')}")
    steps = ((after.get("sequences") or [{}])[0].get("steps") or [])
    for i, st in enumerate(steps, 1):
        print(f"  step {i} wait: {st.get('delay')} {st.get('delay_unit')}")

    if not ok:
        sys.exit(1)
    print("\nDone — campaign configured for Agent-Earns.")


if __name__ == "__main__":
    asyncio.run(main())
