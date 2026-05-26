"""
Method 17 — Apollo.io B2B lead sourcing (same outreach pipeline as Maps).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from loguru import logger

from integrations.platforms.apollo import ApolloClient
from modules.lead_finder.scanners.google_maps import MapsScanResult


class ApolloLeadScanner:
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        key = getattr(settings, "apollo_api_key", "") or ""
        self.client = ApolloClient(key) if key else None

    async def scan(self, niche: str, city: str, limit: int = 25) -> list[MapsScanResult]:
        if not self.client:
            logger.warning("[Apollo] APOLLO_API_KEY missing — skip")
            return []

        people = await self.client.search_people(niche=niche, location=city, limit=limit)
        leads: list[MapsScanResult] = []
        for p in people:
            email = (p.get("email") or "").strip()
            if not email or "@" not in email:
                continue
            org = p.get("organization") or {}
            name = org.get("name") or p.get("name") or "Business"
            website = org.get("website_url") or org.get("primary_domain")
            if website and not str(website).startswith("http"):
                website = f"https://{website}"
            domain = org.get("primary_domain") or ""
            place_id = f"apollo/{p.get('id') or email}"

            leads.append(
                MapsScanResult(
                    place_id=place_id,
                    business_name=name,
                    niche=niche,
                    city=city,
                    country="",
                    address=org.get("formatted_address") or city,
                    phone=org.get("phone") or p.get("phone"),
                    email=email,
                    has_website=bool(website),
                    website_url=website,
                    rating=None,
                    review_count=0,
                    raw={"apollo": p, "person_title": p.get("title")},
                )
            )
            if len(leads) >= limit:
                break

        logger.info(f"[Apollo] {len(leads)} leads with email for {niche} @ {city}")
        return leads
