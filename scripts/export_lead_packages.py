"""
Export sellable leads by package tier (Basic / Standard / Enriched / Exclusive).

Usage:
  python scripts/export_lead_packages.py
  python scripts/export_lead_packages.py --tier enriched --limit 100
  python scripts/export_lead_packages.py --all-tiers --unsold-only --mark-sold --buyer friend
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from utils.lead_package_tier import LeadPackageTier

TIERS = [t.value for t in LeadPackageTier]
PRICING_PATH = ROOT / "data" / "lead_package_tiers.json"


def _load_pricing() -> dict:
    if PRICING_PATH.is_file():
        return json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    return {}


def _row_from_lead(lead) -> dict[str, str]:
    data = lead.enrichment_data or {}
    return {
        "id": lead.id,
        "package_tier": lead.package_tier or "",
        "business_name": lead.business_name or "",
        "email": lead.email or "",
        "phone": lead.phone or "",
        "website": lead.website or "",
        "location": lead.location or "",
        "niche": lead.niche or "",
        "status": lead.status,
        "score": str(lead.score or 0),
        "problem_detected": lead.problem_detected or "",
        "hunt_mode": str(data.get("hunt_mode") or ""),
        "service_to_pitch": str(data.get("service_to_pitch") or ""),
        "has_website": str(data.get("has_website", "")),
        "demo_url": str(data.get("demo_url") or lead.demo_site_path or ""),
        "created_at": (
            lead.created_at.isoformat() if lead.created_at else ""
        ),
        "sold": str(bool(data.get("lead_package_sold"))),
    }


def _filter_leads(leads, *, unsold_only: bool, with_email_only: bool):
    out = []
    for lead in leads:
        if with_email_only and not (lead.email or "").strip():
            continue
        data = lead.enrichment_data or {}
        if unsold_only and data.get("lead_package_sold"):
            continue
        out.append(lead)
    return out


async def main() -> None:
    parser = argparse.ArgumentParser(description="Export leads by sell package tier")
    parser.add_argument(
        "--tier",
        choices=TIERS,
        help="Single tier to export (default: all tiers into separate files)",
    )
    parser.add_argument("--all-tiers", action="store_true", help="Export every tier")
    parser.add_argument("--limit", type=int, default=500, help="Max rows per tier")
    parser.add_argument(
        "--unsold-only",
        action="store_true",
        help="Skip leads already marked lead_package_sold",
    )
    parser.add_argument(
        "--exclude-contacted",
        action="store_true",
        help="Skip CONTACTED / REPLIED / CLIENT (fresh resale only)",
    )
    parser.add_argument(
        "--mark-sold",
        action="store_true",
        help="After export, flag exported leads as sold in enrichment_data",
    )
    parser.add_argument("--buyer", default="", help="Buyer name when --mark-sold")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "outputs" / "lead_exports",
        help="Output directory for CSV files",
    )
    args = parser.parse_args()

    tiers = [args.tier] if args.tier else TIERS
    if not args.tier and not args.all_tiers:
        args.all_tiers = True

    pricing = _load_pricing()
    await init_db()
    repo = LeadRepository()
    factory = get_session_factory()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

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

        exported_total = 0
        for tier in tiers:
            leads = await repo.list_by_package_tier(
                session,
                tier,
                limit=args.limit,
                exclude_contacted=args.exclude_contacted,
            )
            leads = _filter_leads(
                leads, unsold_only=args.unsold_only, with_email_only=True
            )
            if not leads:
                continue

            path = args.out_dir / f"leads_{tier}_{stamp}.csv"
            fieldnames = list(_row_from_lead(leads[0]).keys())
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for lead in leads:
                    writer.writerow(_row_from_lead(lead))
                    if args.mark_sold:
                        await repo.mark_package_sold(
                            session, lead, buyer=args.buyer
                        )
            exported_total += len(leads)
            print(f"\nWrote {len(leads)} → {path}")

        if args.mark_sold:
            await session.commit()
        else:
            await session.rollback()

    print(f"\nDone. Exported {exported_total} lead(s).")


if __name__ == "__main__":
    asyncio.run(main())
