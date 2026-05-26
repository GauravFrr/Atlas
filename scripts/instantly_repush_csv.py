"""
Re-push leads from a campaign Instantly export CSV into Agent-Earns campaign.

Use when API returned "success" but leads never appeared (old skip_if_in_workspace bug).

  python scripts/instantly_repush_csv.py outputs/instantly/leads_afeee9d0.csv
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.platforms.instantly import InstantlyClient
from loguru import logger


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


async def main() -> None:
    parser = argparse.ArgumentParser(description="Re-push Instantly export CSV to campaign")
    parser.add_argument("csv_path", help="Path to outputs/instantly/leads_*.csv")
    parser.add_argument("--dry-run", action="store_true", help="Print only, no API")
    args = parser.parse_args()

    path = Path(args.csv_path)
    if not path.is_file():
        logger.error(f"File not found: {path}")
        sys.exit(1)

    settings = get_settings()
    if not settings.has_instantly:
        logger.error("INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID required in .env")
        sys.exit(1)

    client = InstantlyClient(
        settings.instantly_api_key, settings.instantly_campaign_id
    )
    rows = load_rows(path)
    logger.info(f"Loaded {len(rows)} row(s) from {path}")

    ok_count = 0
    for row in rows:
        email = (row.get("email") or "").strip()
        if not email:
            continue
        payload = {
            "email": email,
            "first_name": (row.get("first_name") or row.get("firstName") or "").strip(),
            "last_name": (row.get("last_name") or "").strip(),
            "company_name": (row.get("company_name") or row.get("companyName") or "").strip(),
        }
        custom = {
            k: v
            for k, v in row.items()
            if k not in payload
            and k != "email"
            and v
            and not k.startswith("subject")
        }
        # Keep body_* and icebreaker etc.
        payload["custom_variables"] = {k: str(v) for k, v in custom.items() if v}

        if args.dry_run:
            print(f"Would push: {email} ({len(payload['custom_variables'])} vars)")
            continue

        result = await client.add_leads_bulk(
            [payload],
            skip_if_in_workspace=False,
            skip_if_in_campaign=False,
        )
        if result.ok:
            ok_count += 1
        else:
            logger.error(f"Failed {email}: {result.error}")

    if not args.dry_run:
        items = await client.list_campaign_leads(limit=50)
        logger.info(f"Campaign now has {len(items)} lead(s) in Instantly API")
        for x in items:
            print(f"  - {x.get('email')}")
        print(f"\nUploaded: {ok_count}/{len(rows)}")


if __name__ == "__main__":
    asyncio.run(main())
