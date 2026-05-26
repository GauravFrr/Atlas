"""Convert any scanner output into MapsScanResult for the outreach pipeline."""

from __future__ import annotations

from typing import Any

from modules.lead_finder.scanners.google_maps import MapsScanResult


def maps_lead(
    source: str,
    source_id: str,
    business_name: str,
    niche: str,
    city: str,
    *,
    email: str | None = None,
    website: str | None = None,
    phone: str | None = None,
    address: str = "",
    has_website: bool | None = None,
    rating: float | None = None,
    review_count: int = 0,
    raw: dict[str, Any] | None = None,
) -> MapsScanResult:
    hw = has_website if has_website is not None else bool(website)
    return MapsScanResult(
        place_id=f"{source}/{source_id}",
        business_name=business_name[:200],
        niche=niche,
        city=city,
        country="",
        address=address or city,
        phone=phone,
        email=email,
        has_website=hw,
        website_url=website,
        rating=rating,
        review_count=review_count,
        raw={"source": source, **(raw or {})},
    )
