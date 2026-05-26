"""
Method 01 — Broken Link Outreach
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


@dataclass
class BrokenLinkResult:
    domain: str
    broken_urls: list[str]
    contact_email: str | None
    site_score: float
    niche: str
    location: str
    raw: dict[str, Any] = field(default_factory=dict)


class BrokenLinkScanner:
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    async def _find_broken_on_site(self, base_url: str, max_links: int = 12) -> list[str]:
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        broken: list[str] = []
        try:
            async with httpx.AsyncClient(
                timeout=12.0, follow_redirects=True, headers={"User-Agent": "Agent-Earns/1.0"}
            ) as client:
                resp = await client.get(base_url)
                if resp.status_code >= 400:
                    return [base_url]
                soup = BeautifulSoup(resp.text[:80000], "lxml")
                host = urlparse(base_url).netloc
                hrefs: list[str] = []
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.startswith("#") or href.startswith("mailto:"):
                        continue
                    full = urljoin(base_url, href)
                    if urlparse(full).netloc == host:
                        hrefs.append(full)
                    if len(hrefs) >= max_links:
                        break
                for link in hrefs:
                    try:
                        head = await client.head(link, timeout=8.0)
                        if head.status_code >= 400:
                            broken.append(link)
                    except Exception:
                        broken.append(link)
        except Exception as e:
            logger.debug(f"[M01] crawl {base_url}: {e}")
        return broken[:5]

    async def scan_maps(
        self,
        niche: str,
        location: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        raw, _ = await scan_local_fn(niche, location, max(limit * 5, 25), no_website_only=False)
        leads: list[MapsScanResult] = []
        for biz in raw:
            if not biz.website_url:
                continue
            broken = await self._find_broken_on_site(biz.website_url)
            if not broken:
                continue
            leads.append(
                maps_lead(
                    "m01",
                    biz.place_id.replace("/", "_"),
                    biz.business_name,
                    niche,
                    location,
                    email=biz.email,
                    website=biz.website_url,
                    phone=biz.phone,
                    raw={"broken_urls": broken, "method": "broken_link"},
                )
            )
            if len(leads) >= limit:
                break
        logger.info(f"[M01] {len(leads)} sites with broken links")
        return leads

    async def scan(self, niche: str, location: str, limit: int = 50) -> list[BrokenLinkResult]:
        logger.info(f"[M01] Broken Link Scanner: {niche} @ {location}")
        return []

    def build_pitch_context(self, result: BrokenLinkResult) -> dict[str, Any]:
        return {
            "method": "broken_link",
            "domain": result.domain,
            "broken_count": len(result.broken_urls),
            "broken_sample": result.broken_urls[:2],
        }
