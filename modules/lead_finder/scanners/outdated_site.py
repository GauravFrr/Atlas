"""
Method 02 — Outdated Website Detector
Checks SSL + mobile viewport + legacy HTML signals on sites from Maps/OSM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

from modules.lead_finder.scanners.google_maps import MapsScanResult

LEGACY_HTML_PATTERNS = (
    r"<font\b",
    r"<center\b",
    r"tables?\s+width\s*=",
    r"visitor counter",
    r"under construction",
    r"best viewed in",
)


@dataclass
class OutdatedSiteResult:
    domain: str
    business_name: str
    location: str
    niche: str
    has_ssl: bool
    is_mobile_friendly: bool
    design_score: float
    page_speed_score: float
    contact_email: str | None
    mockup_html: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        return self.design_score < 6.0 or not self.has_ssl or not self.is_mobile_friendly


class OutdatedSiteScanner:
    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    def _normalize_url(self, url: str) -> str:
        u = url.strip()
        if not u.startswith("http"):
            u = f"https://{u}"
        return u

    async def check_ssl(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=15.0, follow_redirects=True, verify=True
            ) as client:
                resp = await client.get(self._normalize_url(url))
                return resp.status_code < 500
        except Exception:
            return False

    def _check_mobile_html(self, html: str) -> bool:
        low = html.lower()[:8000]
        return "viewport" in low and (
            "width=device-width" in low or "initial-scale" in low
        )

    def _legacy_score(self, html: str) -> float:
        """10 = modern, 1 = very outdated."""
        low = html.lower()
        hits = sum(1 for p in LEGACY_HTML_PATTERNS if re.search(p, low))
        if hits >= 3:
            return 2.0
        if hits >= 1:
            return 4.0
        if len(html) < 1500:
            return 5.0
        return 7.0

    async def audit_url(
        self,
        url: str,
        *,
        business_name: str = "",
        niche: str = "",
        location: str = "",
    ) -> OutdatedSiteResult | None:
        normalized = self._normalize_url(url)
        domain = urlparse(normalized).netloc or url

        html = ""
        has_ssl = await self.check_ssl(normalized)
        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                follow_redirects=True,
                headers={"User-Agent": "Agent-Earns/1.0"},
            ) as client:
                resp = await client.get(normalized)
                html = resp.text[:50000] if resp.status_code < 400 else ""
        except Exception as e:
            logger.debug(f"[M02] fetch {domain}: {e}")
            html = ""

        mobile = self._check_mobile_html(html) if html else False
        design = self._legacy_score(html) if html else 3.0
        if not has_ssl:
            design = min(design, 3.0)
        if html and not mobile:
            design = min(design, 4.5)

        return OutdatedSiteResult(
            domain=domain,
            business_name=business_name or domain,
            location=location,
            niche=niche,
            has_ssl=has_ssl,
            is_mobile_friendly=mobile,
            design_score=design,
            page_speed_score=0.0,
            contact_email=None,
            raw={"url": normalized, "html_len": len(html)},
        )

    async def filter_outdated_maps_leads(
        self,
        leads: list[MapsScanResult],
        *,
        limit: int = 20,
        sparse_fallback: bool = True,
    ) -> list[MapsScanResult]:
        """Keep businesses with outdated websites; optional fallback in thin OSM markets."""
        kept: list[MapsScanResult] = []
        audited: list[tuple[MapsScanResult, OutdatedSiteResult]] = []

        for lead in leads:
            if not lead.website_url:
                continue
            audit = await self.audit_url(
                lead.website_url,
                business_name=lead.business_name,
                niche=lead.niche,
                location=lead.city,
            )
            if not audit:
                continue
            audited.append((lead, audit))
            if audit.is_target:
                from utils.json_safe import to_jsonable

                lead.raw = {**lead.raw, "outdated_audit": to_jsonable(audit)}
                kept.append(lead)
            if len(kept) >= limit:
                break

        if not kept and audited and sparse_fallback:
            audited.sort(key=lambda pair: pair[1].design_score)
            for lead, audit in audited[:limit]:
                from utils.json_safe import to_jsonable

                lead.raw = {
                    **lead.raw,
                    "outdated_audit": to_jsonable(audit),
                    "m02_sparse_fallback": True,
                }
                kept.append(lead)
            logger.warning(
                f"[M02] No sites passed outdated rules — using {len(kept)} lowest design-score "
                f"lead(s) in this market (thin OSM data)"
            )

        logger.info(f"[M02] {len(kept)} outdated sites from {len(leads)} checked")
        return kept

    async def scan(
        self,
        niche: str,
        location: str,
        limit: int = 30,
    ) -> list[OutdatedSiteResult]:
        """Standalone scan: pull businesses with sites from Maps/OSM then audit."""
        from config import get_settings
        from modules.lead_finder.scanners.osm_maps import OSMMapsScanner
        from modules.lead_finder.scanners.google_maps import GoogleMapsScanner

        settings = self.settings or get_settings()
        raw: list[MapsScanResult] = []
        if settings.google_places_api_key:
            raw = await GoogleMapsScanner(settings).scan(
                niche, location, limit=limit * 4, no_website_only=False
            )
        if len(raw) < limit:
            extra = await OSMMapsScanner(settings).scan(
                niche, location, limit=limit * 4, no_website_only=False
            )
            seen = {x.place_id for x in raw}
            raw.extend(x for x in extra if x.place_id not in seen)

        maps_kept = await self.filter_outdated_maps_leads(raw, limit=limit)
        results: list[OutdatedSiteResult] = []
        for m in maps_kept:
            audit = m.raw.get("outdated_audit")
            if isinstance(audit, OutdatedSiteResult):
                results.append(audit)
        return results

    def build_pitch_context(self, result: OutdatedSiteResult) -> dict[str, Any]:
        return {
            "method": "outdated_site",
            "domain": result.domain,
            "business_name": result.business_name,
            "has_ssl": result.has_ssl,
            "is_mobile_friendly": result.is_mobile_friendly,
            "design_score": result.design_score,
            "has_mockup": result.mockup_html is not None,
        }
