"""
Website + AI automation focused hunt modes (core offers for Gaurav's stack).

M25 social_only   — only Facebook/Instagram/Linktree → sell website + AI setup.
M24 chatbot       — site missing AI chat / booking / ordering for their niche → automation.
M27 no_booking    — booking-heavy niches (salon, dentist, clinic) with no booking widget.
M28 no_ordering   — restaurants/cafes with no online ordering.
M26 new_business  — brand-new business (≤3 reviews) → website + automation bundle.

All reuse Maps/OSM scan (scan_local_fn) → demo → Instantly pipeline.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.scanners.google_maps import MapsScanResult
from utils.automation_gaps import (
    detect_automation_gaps,
    missing_category,
    niche_automation_needs,
    problem_line_for_gaps,
)
from utils.platform_domains import is_platform_url

NEW_BUSINESS_MAX_REVIEWS = 3

# Niches where online ordering is the #1 pitch
ORDERING_NICHES = frozenset({
    "restaurant", "cafe", "bakery", "pizza", "food truck", "catering",
    "bar", "brewery", "coffee shop",
})

# Niches where appointment booking is the #1 pitch
BOOKING_NICHES = frozenset({
    "hair salon", "nail salon", "barber", "spa", "massage", "beauty salon",
    "dentist", "chiropractor", "optometrist", "physical therapy", "veterinarian",
    "doctor", "clinic", "gym", "personal trainer", "yoga studio",
    "auto repair", "lawyer", "accountant",
})


def _tag_mode(leads: list[MapsScanResult], mode: str) -> list[MapsScanResult]:
    for lead in leads:
        lead.raw = {**(lead.raw or {}), "hunt_mode": mode}
    return leads


def _niche_matches(niche: str, keys: frozenset[str]) -> bool:
    n = (niche or "").lower().replace("_", " ")
    return any(k in n or n in k for k in keys)


class SocialOnlyScanner:
    """M25 — business lists a social page instead of a real website."""

    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        self.settings = settings

    async def scan_maps(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        raw, _src = await scan_local_fn(
            niche, city, max(limit * 4, 30), no_website_only=False
        )
        kept: list[MapsScanResult] = []
        for lead in raw:
            url = (lead.website_url or "").strip()
            if not url or not is_platform_url(url):
                continue
            lead.has_website = False
            lead.raw = {
                **(lead.raw or {}),
                "social_only_url": url,
                "problem_detected": (
                    "only a social media page — no real website or AI chatbot"
                ),
            }
            lead.website_url = None
            kept.append(lead)
            if len(kept) >= limit:
                break
        logger.info(f"[M25] {len(kept)} social-only businesses (from {len(raw)} scanned)")
        return _tag_mode(kept, "m25_social_only")


class _SiteAutomationScanner:
    """Shared HTML fetch + gap detection for M24/M27/M28."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings

    async def _fetch_html(
        self, client: httpx.AsyncClient, url: str
    ) -> str | None:
        if not url.startswith("http"):
            url = f"https://{url}"
        try:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None
            return resp.text[:120_000]
        except Exception:
            return None

    async def _scan_with_filter(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
        *,
        mode: str,
        keep_fn: Any,
        log_label: str,
    ) -> list[MapsScanResult]:
        raw, _src = await scan_local_fn(
            niche, city, max(limit * 4, 30), no_website_only=False
        )
        with_site = [
            lead for lead in raw
            if lead.website_url and not is_platform_url(lead.website_url or "")
        ]
        kept: list[MapsScanResult] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Agent-Earns/1.0"},
        ) as client:
            for i in range(0, len(with_site), 8):
                if len(kept) >= limit:
                    break
                batch = with_site[i : i + 8]
                htmls = await asyncio.gather(
                    *(self._fetch_html(client, lead.website_url or "") for lead in batch),
                    return_exceptions=True,
                )
                for lead, html in zip(batch, htmls):
                    if not isinstance(html, str):
                        continue
                    gaps = detect_automation_gaps(html, niche)
                    if not keep_fn(gaps, html):
                        continue
                    lead.raw = {
                        **(lead.raw or {}),
                        **gaps,
                        "problem_detected": problem_line_for_gaps(gaps, niche),
                    }
                    kept.append(lead)
                    if len(kept) >= limit:
                        break
        logger.info(f"[{log_label}] {len(kept)} leads (checked {len(with_site)} sites)")
        return _tag_mode(kept, mode)


class NoAutomationScanner(_SiteAutomationScanner):
    """
    M24 — website missing the automation this niche needs
    (AI chatbot, booking, ordering, scheduling).
    """

    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        super().__init__(settings)

    async def scan_maps(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        def keep(gaps: dict, _html: str) -> bool:
            return bool(gaps.get("automation_missing"))

        return await self._scan_with_filter(
            niche, city, limit, scan_local_fn,
            mode="m24_chatbot",
            keep_fn=keep,
            log_label="M24",
        )


class NoBookingScanner(_SiteAutomationScanner):
    """M27 — booking niches (salon, dentist, gym…) with no appointment widget."""

    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        super().__init__(settings)

    async def scan_maps(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        if not _niche_matches(niche, BOOKING_NICHES) and "booking" not in niche_automation_needs(niche):
            logger.debug(f"[M27] skip {niche} — not a booking niche")
            return []

        def keep(gaps: dict, html: str) -> bool:
            return missing_category(html, "booking") and "booking" in gaps.get("automation_missing", [])

        return await self._scan_with_filter(
            niche, city, limit, scan_local_fn,
            mode="m27_no_booking",
            keep_fn=keep,
            log_label="M27",
        )


class NoOrderingScanner(_SiteAutomationScanner):
    """M28 — restaurants/cafes with no online ordering on their site."""

    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        super().__init__(settings)

    async def scan_maps(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        if not _niche_matches(niche, ORDERING_NICHES):
            logger.debug(f"[M28] skip {niche} — not an ordering niche")
            return []

        def keep(gaps: dict, html: str) -> bool:
            return missing_category(html, "ordering") and "ordering" in gaps.get("automation_missing", [])

        return await self._scan_with_filter(
            niche, city, limit, scan_local_fn,
            mode="m28_no_ordering",
            keep_fn=keep,
            log_label="M28",
        )


class NewBusinessScanner:
    """M26 — almost no reviews = likely a new business → needs web + automation."""

    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        self.settings = settings

    async def scan_maps(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        raw, _src = await scan_local_fn(
            niche, city, max(limit * 4, 30), no_website_only=False
        )
        kept: list[MapsScanResult] = []
        for lead in raw:
            if (lead.review_count or 0) > NEW_BUSINESS_MAX_REVIEWS:
                continue
            lead.raw = {
                **(lead.raw or {}),
                "new_business_signal": True,
                "automation_primary": "ai_chat",
                "problem_detected": (
                    "brand-new business — needs website + AI chatbot + booking from day one"
                ),
            }
            kept.append(lead)
            if len(kept) >= limit:
                break
        logger.info(f"[M26] {len(kept)} new businesses (from {len(raw)} scanned)")
        return _tag_mode(kept, "m26_new_business")
