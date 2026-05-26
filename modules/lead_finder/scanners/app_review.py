"""
Method 07 — App Store Review Miner
TARGET:  US SaaS founders, app developers
EARN:    $500–3,000 per fix project
LOGIC:   Read 1-star reviews → cluster pain points → pitch the founder

Pitch: "47 users complained about your onboarding in the last 30 days — I can fix it"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


@dataclass
class AppPainPoint:
    category: str           # "onboarding" | "performance" | "ui" | "missing_feature" | etc.
    complaint_count: int
    sample_reviews: list[str]
    severity: str           # "critical" | "major" | "minor"


@dataclass
class AppReviewLead:
    app_id: str
    app_name: str
    platform: str           # "ios" | "android"
    developer_name: str
    developer_email: str | None
    avg_rating: float
    review_count: int
    pain_points: list[AppPainPoint]
    top_fixable_issue: str
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        """Apps with 3-star or below and at least one fixable issue."""
        return self.avg_rating <= 3.5 and len(self.pain_points) > 0


class AppReviewMiner:
    """
    Method 07 — Mines App Store & Play Store reviews for recurring pain points.

    Usage:
        miner = AppReviewMiner(settings, llm_router)
        leads = await miner.scan(category="productivity", platform="ios", limit=20)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, niche: str, limit: int = 20) -> list[MapsScanResult]:
        leads: list[MapsScanResult] = []
        term = niche.replace("_", " ")
        url = "https://itunes.apple.com/search"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    url,
                    params={"term": term, "media": "software", "entity": "software", "limit": 50},
                )
                if resp.status_code != 200:
                    return leads
                for app in resp.json().get("results", []):
                    rating = float(app.get("averageUserRating") or 5.0)
                    count = int(app.get("userRatingCount") or 0)
                    if rating > 3.5 or count < 5:
                        continue
                    aid = str(app.get("trackId", ""))
                    leads.append(
                        maps_lead(
                            "m07",
                            aid,
                            app.get("trackName", "App"),
                            niche,
                            "US",
                            website=app.get("trackViewUrl"),
                            raw={
                                "rating": rating,
                                "reviews": count,
                                "seller": app.get("sellerName"),
                                "method": "app_store",
                            },
                        )
                    )
                    if len(leads) >= limit:
                        break
        except Exception as e:
            logger.debug(f"[M07] iTunes search: {e}")
        logger.info(f"[M07] {len(leads)} low-rated apps")
        return leads

    async def scan(
        self,
        category: str,
        platform: str = "ios",
        max_rating: float = 3.5,
        limit: int = 20,
    ) -> list[AppReviewLead]:
        """
        Find apps with recurring user complaints we can pitch fixes for.

        TODO: Implement using:
          - App Store scraper (iTunes RSS feed or app-store-scraper library)
          - Google Play scraper
          - Gemini to cluster reviews into pain point categories
          - Hunter.io to find developer contact email
        """
        logger.info(f"[M07] App Review Miner: category={category}, platform={platform}")
        return []

    async def cluster_reviews(self, reviews: list[str]) -> list[AppPainPoint]:
        """Use Gemini to group 1-star reviews into actionable pain point categories."""
        # TODO: Batch reviews → Gemini → categorized pain points
        raise NotImplementedError

    def build_pitch_context(self, lead: AppReviewLead) -> dict[str, Any]:
        pain = lead.pain_points[0] if lead.pain_points else None
        return {
            "method": "app_review",
            "app_name": lead.app_name,
            "complaint_count": pain.complaint_count if pain else 0,
            "top_issue": lead.top_fixable_issue,
            "avg_rating": lead.avg_rating,
        }
