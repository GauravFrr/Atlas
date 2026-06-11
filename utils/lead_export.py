"""
Export sellable leads by package tier with optional geo/niche filters.
Used by scripts/export_lead_packages.py and Telegram /export.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import LeadStatus
from database.models.lead import Lead
from database.repositories.lead_repository import LeadRepository
from utils.lead_package_tier import LeadPackageTier

TIERS = [t.value for t in LeadPackageTier]
PRICING_PATH = Path(__file__).resolve().parents[1] / "data" / "lead_package_tiers.json"

_TIER_ALIASES = {
    "basic": "basic",
    "standard": "standard",
    "enriched": "enriched",
    "exclusive": "exclusive",
    "fresh": "exclusive",
}


def load_pricing() -> dict[str, Any]:
    if PRICING_PATH.is_file():
        return json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    return {}


def row_from_lead(lead: Lead) -> dict[str, str]:
    data = lead.enrichment_data or {}
    return {
        "id": lead.id,
        "package_tier": lead.package_tier or "",
        "business_name": lead.business_name or "",
        "email": lead.email or "",
        "phone": lead.phone or "",
        "website": lead.website or "",
        "location": lead.location or "",
        "country": str(data.get("country") or ""),
        "niche": lead.niche or "",
        "status": lead.status,
        "score": str(lead.score or 0),
        "problem_detected": lead.problem_detected or "",
        "hunt_mode": str(data.get("hunt_mode") or ""),
        "service_to_pitch": str(data.get("service_to_pitch") or ""),
        "has_website": str(data.get("has_website", "")),
        "demo_url": str(data.get("demo_url") or lead.demo_site_path or ""),
        "created_at": lead.created_at.isoformat() if lead.created_at else "",
        "sold": str(bool(data.get("lead_package_sold"))),
    }


def leads_to_csv_bytes(leads: list[Lead]) -> bytes:
    if not leads:
        return b""
    buf = io.StringIO()
    fieldnames = list(row_from_lead(leads[0]).keys())
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for lead in leads:
        writer.writerow(row_from_lead(lead))
    return buf.getvalue().encode("utf-8")


@dataclass
class LeadExportFilters:
    tier: str | None = None
    country: str | None = None
    city: str | None = None
    niche: str | None = None
    limit: int = 500
    unsold_only: bool = False
    exclude_contacted: bool = False
    mark_sold: bool = False
    buyer: str = ""

    def label_parts(self) -> list[str]:
        parts: list[str] = []
        if self.tier:
            parts.append(self.tier)
        if self.country:
            parts.append(f"country={self.country}")
        if self.city:
            parts.append(f"city={self.city}")
        if self.niche:
            parts.append(f"niche={self.niche}")
        if self.unsold_only:
            parts.append("unsold")
        if self.exclude_contacted:
            parts.append("fresh")
        return parts or ["all"]


@dataclass
class ExportFile:
    filename: str
    content: bytes
    row_count: int
    tier: str | None = None


@dataclass
class ExportResult:
    files: list[ExportFile] = field(default_factory=list)
    tier_counts: dict[str, int] = field(default_factory=dict)
    filters: LeadExportFilters | None = None
    committed: bool = False


def _filter_unsold(leads: list[Lead]) -> list[Lead]:
    out: list[Lead] = []
    for lead in leads:
        data = lead.enrichment_data or {}
        if data.get("lead_package_sold"):
            continue
        out.append(lead)
    return out


def _apply_country_city_niche(
    leads: list[Lead],
    *,
    country: str | None,
    city: str | None,
    niche: str | None,
) -> list[Lead]:
    """Post-filter for country (enrichment) when SQL JSON ops differ by dialect."""
    if not (country or city or niche):
        return leads
    out: list[Lead] = []
    country_q = (country or "").strip().lower()
    city_q = (city or "").strip().lower()
    niche_q = (niche or "").strip().lower()
    for lead in leads:
        data = lead.enrichment_data or {}
        loc = (lead.location or "").lower()
        ctry = str(data.get("country") or "").lower()
        if country_q and country_q not in ctry and country_q not in loc:
            continue
        if city_q and city_q not in loc:
            continue
        if niche_q and niche_q not in (lead.niche or "").lower():
            continue
        out.append(lead)
    return out


async def query_leads_for_export(
    session: AsyncSession,
    filters: LeadExportFilters,
) -> list[Lead]:
    q = select(Lead).where(Lead.is_deleted.is_(False), Lead.email.is_not(None))
    if filters.tier:
        q = q.where(Lead.package_tier == filters.tier)
    if filters.niche:
        q = q.where(func.lower(Lead.niche).like(f"%{filters.niche.strip().lower()}%"))
    if filters.city:
        q = q.where(func.lower(Lead.location).like(f"%{filters.city.strip().lower()}%"))
    if filters.exclude_contacted:
        q = q.where(
            Lead.status.not_in(
                (
                    LeadStatus.CONTACTED,
                    LeadStatus.REPLIED,
                    LeadStatus.CLIENT,
                )
            )
        )
    q = q.order_by(Lead.created_at.desc()).limit(max(1, min(filters.limit, 2000)))
    result = await session.execute(q)
    leads = list(result.scalars().all())
    if filters.unsold_only:
        leads = _filter_unsold(leads)
    leads = _apply_country_city_niche(
        leads,
        country=filters.country,
        city=filters.city,
        niche=filters.niche,
    )
    return leads[: filters.limit]


async def run_export(
    session: AsyncSession,
    repo: LeadRepository,
    filters: LeadExportFilters,
    *,
    split_by_tier: bool = False,
) -> ExportResult:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    result = ExportResult(filters=filters)
    result.tier_counts = await repo.count_by_package_tier(session)

    tiers_to_run = [filters.tier] if filters.tier else (TIERS if split_by_tier else [None])

    for tier in tiers_to_run:
        tier_filters = LeadExportFilters(
            tier=tier,
            country=filters.country,
            city=filters.city,
            niche=filters.niche,
            limit=filters.limit,
            unsold_only=filters.unsold_only,
            exclude_contacted=filters.exclude_contacted,
            mark_sold=False,
            buyer=filters.buyer,
        )
        leads = await query_leads_for_export(session, tier_filters)
        if not leads:
            continue

        if filters.mark_sold:
            for lead in leads:
                await repo.mark_package_sold(session, lead, buyer=filters.buyer)

        label = "_".join(tier_filters.label_parts())
        safe_label = re.sub(r"[^\w\-]+", "_", label)[:80]
        fname = f"leads_{safe_label}_{stamp}.csv"
        content = leads_to_csv_bytes(leads)
        result.files.append(
            ExportFile(filename=fname, content=content, row_count=len(leads), tier=tier)
        )

        if not split_by_tier:
            break

    if filters.mark_sold and result.files:
        await session.commit()
        result.committed = True

    return result


def parse_export_args(tokens: list[str]) -> LeadExportFilters | str:
    """
    Parse Telegram /export args. Returns filters or help hint string on error.
    """
    if not tokens or tokens[0].lower() in ("help", "?"):
        return "help"

    f = LeadExportFilters()
    for raw in tokens:
        tok = raw.strip().strip('"').strip("'")
        low = tok.lower()
        if low in _TIER_ALIASES:
            f.tier = _TIER_ALIASES[low]
            continue
        if low in ("unsold", "unsold-only", "unsold_only"):
            f.unsold_only = True
            continue
        if low in ("fresh", "exclude-contacted", "exclude_contacted"):
            f.exclude_contacted = True
            continue
        if low in ("mark_sold", "mark-sold", "sold"):
            f.mark_sold = True
            continue
        if "=" in tok:
            key, _, val = tok.partition("=")
            key = key.strip().lower()
            val = val.strip().strip('"').strip("'")
            if key in ("tier", "package", "package_tier"):
                if val.lower() in _TIER_ALIASES:
                    f.tier = _TIER_ALIASES[val.lower()]
            elif key in ("country", "ctry"):
                f.country = val
            elif key in ("city", "location", "loc"):
                f.city = val
            elif key == "niche":
                f.niche = val
            elif key == "limit":
                try:
                    f.limit = max(1, min(int(val), 2000))
                except ValueError:
                    return f"Bad limit: {val}"
            elif key == "buyer":
                f.buyer = val
            continue
        if low.isdigit():
            f.limit = max(1, min(int(low), 2000))
            continue
        return f"Unknown token: {tok}"

    return f


def export_help_text() -> str:
    pricing = load_pricing()
    lines = [
        "<b>📤 Export leads (CSV in chat)</b>",
        "",
        "<b>Quick</b>",
        "<code>/export inventory</code> — counts by tier",
        "<code>/export enriched</code> — one tier",
        "<code>/export exclusive unsold fresh</code>",
        "",
        "<b>Filters</b> (combine any)",
        "<code>country=IN</code> · <code>city=Mumbai</code>",
        "<code>niche=plumber</code> · <code>limit=100</code>",
        "",
        "<b>Examples</b>",
        "<code>/export standard country=US limit=50</code>",
        "<code>/export enriched city=Delhi niche=dentist</code>",
        "<code>/export tier=exclusive country=IN unsold</code>",
        "",
        "<b>Tiers</b> basic · standard · enriched · exclusive",
    ]
    if pricing.get("tiers"):
        lines.append("")
        lines.append("<b>Pricing (INR/lead)</b>")
        for t in TIERS:
            info = pricing["tiers"].get(t, {})
            lines.append(
                f"  {esc_html(info.get('label', t))}: ₹{info.get('price_inr', '?')}"
            )
    return "\n".join(lines)


def esc_html(text: object) -> str:
    from html import escape

    return escape(str(text or ""))


def inventory_summary_text(tier_counts: dict[str, int]) -> str:
    lines = ["<b>📦 Lead inventory (with email)</b>", ""]
    total = 0
    for t in TIERS:
        n = tier_counts.get(t, 0)
        total += n
        lines.append(f"  • <b>{t}</b> — {n}")
    unsorted = tier_counts.get("unsorted", 0)
    if unsorted:
        lines.append(f"  • <i>unsorted</i> — {unsorted}")
        total += unsorted
    lines.extend(["", f"<b>Total sellable rows:</b> {total}"])
    lines.append("")
    lines.append("Export: <code>/export enriched</code> or <code>/export help</code>")
    return "\n".join(lines)
