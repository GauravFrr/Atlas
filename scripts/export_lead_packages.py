"""
Export sellable leads by package tier (Basic / Standard / Enriched / Exclusive).

Usage:
  python scripts/export_lead_packages.py
  python scripts/export_lead_packages.py --tier enriched --limit 100
  python scripts/export_lead_packages.py --country IN --city Mumbai
  python scripts/export_lead_packages.py --all-tiers --unsold-only --mark-sold --buyer friend
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from utils.lead_export import (
    TIERS,
    LeadExportFilters,
    load_pricing,
    run_export,
)
async def main() -> None:
    parser = argparse.ArgumentParser(description="Export leads by sell package tier")
    parser.add_argument("--tier", choices=TIERS, help="Single tier to export")
    parser.add_argument("--all-tiers", action="store_true", help="One CSV per tier")
    parser.add_argument("--country", help="Filter by country code or name")
    parser.add_argument("--city", help="Filter by city (location column)")
    parser.add_argument("--niche", help="Filter by niche")
    parser.add_argument("--limit", type=int, default=500, help="Max rows")
    parser.add_argument("--unsold-only", action="store_true")
    parser.add_argument("--exclude-contacted", action="store_true")
    parser.add_argument("--mark-sold", action="store_true")
    parser.add_argument("--buyer", default="")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "lead_exports",
    )
    args = parser.parse_args()

    pricing = load_pricing()
    await init_db()
    repo = LeadRepository()
    factory = get_session_factory()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    filters = LeadExportFilters(
        tier=args.tier,
        country=args.country,
        city=args.city,
        niche=args.niche,
        limit=args.limit,
        unsold_only=args.unsold_only,
        exclude_contacted=args.exclude_contacted,
        mark_sold=args.mark_sold,
        buyer=args.buyer,
    )

    async with factory() as session:
        counts = await repo.count_by_package_tier(session)
        print("Package tier inventory (with email):")
        for t in TIERS + ["unsorted"]:
            print(f"  {t}: {counts.get(t, 0)}")
        if pricing.get("tiers"):
            print("\nPricing (INR per lead):")
            for t in TIERS:
                info = pricing["tiers"].get(t, {})
                print(
                    f"  {info.get('label', t)}: ₹{info.get('price_inr', '?')} "
                    f"— {info.get('description', '')}"
                )

        result = await run_export(
            session,
            repo,
            filters,
            split_by_tier=args.all_tiers and not args.tier,
        )

        exported_total = 0
        for ef in result.files:
            path = args.out_dir / ef.filename
            path.write_bytes(ef.content)
            exported_total += ef.row_count
            print(f"\nWrote {ef.row_count} → {path}")

        if not result.committed and not args.mark_sold:
            await session.rollback()

    print(f"\nDone. Exported {exported_total} lead(s).")


if __name__ == "__main__":
    asyncio.run(main())
