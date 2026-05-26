"""
Method 04 — Google Reviews Monitor (low-rated local businesses).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.scanners.google_maps import MapsScanResult

AUTOMATABLE_JOB_TITLES = [
    "social media manager",
    "marketing assistant",
    "data entry",
    "email marketer",
    "content coordinator",
    "lead generation specialist",
    "outreach coordinator",
    "cold email specialist",
    "virtual assistant",
    "administrative assistant",
]


@dataclass
class ReviewsLead:
    place_id: str
    business_name: str
    niche: str
    location: str
    rating: float
    review_count: int
    recent_negative: list[str]
    contact_email: str | None
    website_url: str | None = None
    phone: str | None = None
    address: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        return self.rating <= 3.5 and self.review_count >= 5


class GoogleReviewsMonitor:
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    def to_maps_result(self, lead: ReviewsLead) -> MapsScanResult:
        return MapsScanResult(
            place_id=lead.place_id,
            business_name=lead.business_name,
            niche=lead.niche,
            city=lead.location,
            country="",
            address=lead.address,
            phone=lead.phone,
            email=lead.contact_email,
            has_website=bool(lead.website_url),
            website_url=lead.website_url,
            rating=lead.rating,
            review_count=lead.review_count,
            raw={**lead.raw, "hunt_mode": "low_reviews", "rating": lead.rating},
        )

    async def scan(
        self,
        niche: str,
        location: str,
        max_rating: float = 3.5,
        min_reviews: int = 5,
        limit: int = 50,
    ) -> list[ReviewsLead]:
        api_key = getattr(self.settings, "google_places_api_key", None)
        if not api_key:
            logger.warning("[M04] Needs GOOGLE_PLACES_API_KEY")
            return []

        query = f"{niche} in {location}"
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        leads: list[ReviewsLead] = []

        logger.info(f"[M04] Low reviews scan: {query} (≤{max_rating} stars)")

        async with httpx.AsyncClient(timeout=45.0) as client:
            search_resp = await client.get(
                search_url, params={"query": query, "key": api_key}
            )
            if search_resp.status_code != 200:
                logger.error(f"[M04] Places error: {search_resp.text[:200]}")
                return []

            places = search_resp.json().get("results", [])
            for place in places:
                if len(leads) >= limit:
                    break
                rating = float(place.get("rating") or 5.0)
                review_count = int(place.get("user_ratings_total") or 0)
                if rating > max_rating or review_count < min_reviews:
                    continue

                place_id = place.get("place_id")
                if not place_id:
                    continue

                det_resp = await client.get(
                    details_url,
                    params={
                        "place_id": place_id,
                        "fields": "name,website,formatted_phone_number,formatted_address,rating,user_ratings_total",
                        "key": api_key,
                    },
                )
                if det_resp.status_code != 200:
                    continue
                det = det_resp.json().get("result", {})

                leads.append(
                    ReviewsLead(
                        place_id=place_id,
                        business_name=det.get("name", place.get("name", "Business")),
                        niche=niche,
                        location=location,
                        rating=float(det.get("rating") or rating),
                        review_count=int(det.get("user_ratings_total") or review_count),
                        recent_negative=[],
                        contact_email=None,
                        website_url=det.get("website"),
                        phone=det.get("formatted_phone_number"),
                        address=det.get("formatted_address", ""),
                        raw=det,
                    )
                )

        logger.info(f"[M04] Found {len(leads)} low-review targets")
        return leads


@dataclass
class JobPostLead:
    job_id: str
    company_name: str
    job_title: str
    location: str
    platform: str
    annual_salary_usd: float | None
    posting_url: str
    automatable_role: str
    contact_email: str | None
    roi_monthly_savings: float | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class JobBoardScraper:
    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan(
        self,
        platforms: list[str] | None = None,
        job_titles: list[str] | None = None,
        limit: int = 100,
    ) -> list[JobPostLead]:
        platforms = platforms or ["linkedin", "indeed"]
        titles = job_titles or AUTOMATABLE_JOB_TITLES
        logger.info(f"[M05/M11] Job Board Scraper: platforms={platforms}, tracking {len(titles)} roles")
        return []

    async def calculate_roi(
        self, annual_salary_usd: float, automation_monthly: float = 500.0
    ) -> dict[str, float]:
        annual_automation = automation_monthly * 12
        annual_savings = annual_salary_usd - annual_automation
        return {
            "annual_salary": annual_salary_usd,
            "annual_automation_cost": annual_automation,
            "annual_savings": annual_savings,
            "roi_multiplier": annual_salary_usd / max(annual_automation, 1),
        }
