"""
Website + automation focused hunt modes (core offers).

M25 social_only  — "website" is just a Facebook/Instagram/Linktree page → sell a real website.
M24 chatbot      — decent site but no chat / booking / follow-up tools → sell automation.
M26 new_business — almost no reviews yet (new business) → sell web presence early.

All reuse the Maps/OSM scan (scan_local_fn) so leads flow into the normal
demo → email → Instantly pipeline.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.scanners.google_maps import MapsScanResult
from utils.platform_domains import is_platform_url

# Signatures of chat / booking / automation tools already on a site.
# If NONE found → strong automation pitch (Method 24).
AUTOMATION_TOOL_SIGNATURES = (
    "calendly.com",
    "acuityscheduling",
    "squareup.com/appointments",
    "setmore.com",
    "simplybook",
    "booksy.com",
    "vagaro.com",
    "intercom",
    "drift.com",
    "tawk.to",
    "crisp.chat",
    "tidio",
    "livechat",
    "zendesk",
    "hubspot",
    "wa.me/",
    "api.whatsapp.com",
    "manychat",
    "chatbot",
    "podium.com",
    "birdeye.com",
)

NEW_BUSINESS_MAX_REVIEWS = 3


def _tag_mode(leads: list[MapsScanResult], mode: str) -> list[MapsScanResult]:
    for lead in leads:
        lead.raw = {**(lead.raw or {}), "hunt_mode": mode}
    return leads


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
            # Treat as "no real website" for demo + pitch copy
            lead.has_website = False
            lead.raw = {
                **(lead.raw or {}),
                "social_only_url": url,
                "problem_detected": "only a social media page — no real website",
            }
            lead.website_url = None
            kept.append(lead)
            if len(kept) >= limit:
                break
        logger.info(f"[M25] {len(kept)} social-only businesses (from {len(raw)} scanned)")
        return _tag_mode(kept, "m25_social_only")


class NoAutomationScanner:
    """M24 — has a website but no chat/booking/follow-up tools → automation pitch."""

    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        self.settings = settings

    @staticmethod
    def _has_automation_tools(html: str) -> bool:
        low = html.lower()
        return any(sig in low for sig in AUTOMATION_TOOL_SIGNATURES)

    async def _check_site(
        self, client: httpx.AsyncClient, lead: MapsScanResult
    ) -> MapsScanResult | None:
        url = (lead.website_url or "").strip()
        if not url or is_platform_url(url):
            return None
        if not url.startswith("http"):
            url = f"https://{url}"
        try:
            resp = await client.get(url)
            if resp.status_code >= 400:
                return None
            html = resp.text[:120_000]
        except Exception:
            return None
        if self._has_automation_tools(html):
            return None
        lead.raw = {
            **(lead.raw or {}),
            "no_automation_tools": True,
            "problem_detected": "no chat, booking, or follow-up automation on the site",
        }
        return lead

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
        with_site = [lead for lead in raw if lead.website_url]
        kept: list[MapsScanResult] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Agent-Earns/1.0"},
        ) as client:
            # Small batches — keep it polite and fast
            for i in range(0, len(with_site), 8):
                if len(kept) >= limit:
                    break
                batch = with_site[i : i + 8]
                results = await asyncio.gather(
                    *(self._check_site(client, lead) for lead in batch),
                    return_exceptions=True,
                )
                for res in results:
                    if isinstance(res, MapsScanResult):
                        kept.append(res)
                        if len(kept) >= limit:
                            break
        logger.info(
            f"[M24] {len(kept)} sites without automation tools "
            f"(checked {len(with_site)} sites)"
        )
        return _tag_mode(kept, "m24_chatbot")


class NewBusinessScanner:
    """M26 — almost no reviews = likely a new business → needs web presence now."""

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
                "problem_detected": (
                    "brand-new business with little online presence — "
                    "first website + reviews setup"
                ),
            }
            kept.append(lead)
            if len(kept) >= limit:
                break
        logger.info(f"[M26] {len(kept)} new businesses (from {len(raw)} scanned)")
        return _tag_mode(kept, "m26_new_business")
