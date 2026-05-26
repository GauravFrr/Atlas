"""Convert DB Lead rows to MapsScanResult (no outreach imports)."""

from __future__ import annotations

from typing import Any

from database.models.lead import Lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


def _enrichment(lead: Lead) -> dict[str, Any]:
    return dict(lead.enrichment_data or {})


def lead_to_maps_scan(lead: Lead) -> MapsScanResult:
    """Rebuild MapsScanResult from a DB lead for the outreach pipeline."""
    data = _enrichment(lead)
    raw = dict(data.get("raw") or {})
    raw.setdefault("source", lead.source or "google_maps")
    hunt = data.get("hunt_mode") or raw.get("hunt_mode") or "m10_no_website"
    raw["hunt_mode"] = hunt

    pid = lead.place_id or lead.id
    if pid.startswith("m06/"):
        raw.setdefault("method", "youtube")
        raw.setdefault("channel_id", pid.split("/", 1)[-1])
        raw.setdefault(
            "channel_url",
            data.get("channel_url") or f"https://www.youtube.com/channel/{raw['channel_id']}",
        )

    if data.get("contact_first_name"):
        raw.setdefault("contact_first_name", data["contact_first_name"])
    if data.get("icebreaker"):
        raw["icebreaker"] = data["icebreaker"]

    return MapsScanResult(
        place_id=pid,
        business_name=lead.business_name,
        niche=lead.niche or "local_service",
        city=lead.location or "",
        country=str(data.get("country") or ""),
        address=str(data.get("address") or lead.location or ""),
        phone=lead.phone,
        email=lead.email,
        has_website=bool(lead.website),
        website_url=lead.website,
        rating=data.get("rating"),
        review_count=int(data.get("review_count") or 0),
        demo_site_path=lead.demo_site_path,
        raw=raw,
    )
