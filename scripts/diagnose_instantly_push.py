"""
Debug Instantly lead push (why Sent: 0).

  python scripts/diagnose_instantly_push.py --email itzmi3xel@gmail.com
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.platforms.instantly import InstantlyClient


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    s = get_settings()
    if not s.instantly_api_key or not s.instantly_campaign_id:
        print("Set INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID in .env")
        sys.exit(1)

    client = InstantlyClient(s.instantly_api_key, s.instantly_campaign_id)
    try:
        campaign = await client.get_campaign()
    except Exception as e:
        print(f"Network error reaching api.instantly.ai: {e}")
        print("Check internet/DNS/VPN, then retry.")
        sys.exit(1)
    print("Campaign:", json.dumps(campaign or {}, indent=2)[:1200])

    accounts = await client.list_accounts(limit=100)
    print(f"\nAccounts ({len(accounts)}):")
    for a in accounts[:10]:
        print(
            f"  {a.get('email')} status={a.get('status')} "
            f"warmup={a.get('warmup_status')}"
        )

    result = await client.add_leads_bulk(
        [
            InstantlyClient._lead_payload(
                args.email,
                "Test",
                "Lead",
                "Diagnose Co",
                {"body_1": "Test body", "demo_url": "https://example.com"},
            )
        ],
        skip_if_in_workspace=False,
        skip_if_in_campaign=False,
    )
    print("\nAdd result:", json.dumps(result.raw or {"error": result.error}, indent=2))
    print("ok:", result.ok, "uploaded:", result.leads_uploaded)


if __name__ == "__main__":
    asyncio.run(main())
