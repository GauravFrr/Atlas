"""
Method 12 — ProductHunt Launch Monitor
TARGET:  Founders launching on ProductHunt daily
EARN:    $100–300 per press release
VOLUME:  50+ launches per day
LOGIC:   Monitor PH launches → score traction → pitch press release within 2 hours

Timing is critical — pitch within 2 hours of launch while founder excitement is highest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import xml.etree.ElementTree as ET

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


@dataclass
class ProductHuntLaunch:
    ph_id: str
    product_name: str
    tagline: str
    description: str
    upvotes: int
    comments: int
    maker_name: str
    maker_twitter: str | None
    maker_email: str | None
    launch_url: str
    launched_at: datetime
    traction_score: float   # composite: upvotes + comments + growth velocity
    press_release_draft: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        """Target launches with good traction but not already huge."""
        return 50 <= self.upvotes <= 500 and self.traction_score >= 5.0

    @property
    def hours_since_launch(self) -> float:
        return (datetime.now(timezone.utc) - self.launched_at).total_seconds() / 3600


class ProductHuntMonitor:
    """
    Method 12 — Monitors ProductHunt for new launches and pitches press releases.
    Must act within 2 hours of launch for best conversion.

    Usage:
        monitor = ProductHuntMonitor(settings, llm_router)
        launches = await monitor.scan(min_upvotes=50)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, limit: int = 20) -> list[MapsScanResult]:
        leads: list[MapsScanResult] = []
        token = getattr(self.settings, "producthunt_api_token", "") or ""
        headers = {"User-Agent": "Agent-Earns/1.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with httpx.AsyncClient(timeout=25.0, headers=headers) as client:
                resp = await client.get("https://www.producthunt.com/feed", follow_redirects=True)
                if resp.status_code == 200 and "<item>" in resp.text:
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    entries = root.findall("atom:entry", ns) or root.findall(".//item")
                    for i, entry in enumerate(entries[:limit]):
                        title = (
                            entry.findtext("atom:title", default="", namespaces=ns)
                            or entry.findtext("title")
                            or f"Product {i}"
                        )
                        link = entry.find("atom:link", ns)
                        href = link.get("href") if link is not None else entry.findtext("link") or ""
                        leads.append(
                            maps_lead(
                                "m12",
                                str(i),
                                title[:100],
                                "saas",
                                "global",
                                website=href,
                                raw={"method": "producthunt", "launch_url": href},
                            )
                        )
        except Exception as e:
            logger.debug(f"[M12] ProductHunt feed: {e}")
        logger.info(f"[M12] {len(leads)} PH launches")
        return leads

    async def scan(
        self,
        min_upvotes: int = 50,
        max_hours_old: float = 6.0,
    ) -> list[ProductHuntLaunch]:
        """
        Fetch today's ProductHunt launches, filter by traction.

        TODO: Implement using:
          - ProductHunt GraphQL API
          - Filter by upvotes + time since launch
          - Gemini to score traction and draft press release
        """
        logger.info(f"[M12] ProductHunt Monitor: min_upvotes={min_upvotes}, max_hours={max_hours_old}")
        return []

    async def draft_press_release(self, launch: ProductHuntLaunch) -> str:
        """Draft a press release pitch email for the founder."""
        # TODO: Gemini prompt — write a 3-paragraph press release sample
        # that positions us as PR experts and teases coverage on TechCrunch/Mashable
        raise NotImplementedError
