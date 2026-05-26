"""
Method 09 — Cold DM on Instagram / Twitter
TARGET:  US/UK coaches, course creators, small business owners
EARN:    $200–800/month retainer
LOGIC:   Find accounts with poor engagement → send personalized DM → pitch social audit/automation

Method 13 — Quora / Forum Answer Marketing
TARGET:  English-speaking business owners searching for solutions
EARN:    Passive inbound leads 24/7 (indirect)
LOGIC:   Find relevant questions → post expert answers → soft funnel to Fiverr/website

Method 16 — Podcast Guest Outreach (For Mikey)
TARGET:  US/UK podcasts in AI, automation, freelancing, SaaS
EARN:    Indirect — generates high-quality inbound client inquiries
LOGIC:   Find podcast → check episode count + audience → write personalized pitch
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


# ─── Method 09 ────────────────────────────────────────────────────────────────

@dataclass
class SocialDMLead:
    platform: str               # "instagram" | "twitter"
    handle: str
    follower_count: int
    engagement_rate: float      # percentage
    niche: str
    has_automation_gap: bool    # True if posting irregularly / no auto-replies
    dm_draft: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        return self.engagement_rate < 2.0 or self.has_automation_gap


class SocialDMScanner:
    """
    Method 09 — Finds social media accounts with poor engagement to pitch DM services.

    Usage:
        scanner = SocialDMScanner(settings, llm_router)
        leads = await scanner.scan(platform="twitter", niche="coaches", limit=50)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(
        self,
        niche: str,
        city: str,
        limit: int,
        scan_local_fn: Any,
    ) -> list[MapsScanResult]:
        raw, _ = await scan_local_fn(niche, city, max(limit * 5, 30), no_website_only=False)
        leads: list[MapsScanResult] = []
        for biz in raw:
            tags = biz.raw.get("osm", {}).get("tags", {}) if isinstance(biz.raw, dict) else {}
            if not tags and isinstance(biz.raw, dict):
                tags = biz.raw
            ig = tags.get("contact:instagram") or tags.get("instagram")
            tw = tags.get("contact:twitter") or tags.get("twitter")
            if not ig and not tw:
                continue
            handle = ig or tw
            platform = "instagram" if ig else "twitter"
            leads.append(
                maps_lead(
                    "m09",
                    biz.place_id.replace("/", "_"),
                    biz.business_name,
                    niche,
                    city,
                    email=biz.email,
                    website=biz.website_url,
                    phone=biz.phone,
                    raw={
                        "platform": platform,
                        "handle": handle,
                        "outreach_channel": "social_dm",
                        "method": "m09",
                    },
                )
            )
            if len(leads) >= limit:
                break
        logger.info(f"[M09] {len(leads)} social handles from OSM/Maps")
        return leads

    async def scan(
        self,
        platform: str = "twitter",
        niche: str = "",
        limit: int = 50,
    ) -> list[SocialDMLead]:
        logger.info(f"[M09] Social DM Scanner: platform={platform}, niche={niche}")
        return []


# ─── Method 13 ────────────────────────────────────────────────────────────────

@dataclass
class ForumAnswerOpportunity:
    platform: str               # "quora" | "reddit" | "indiehackers"
    question_id: str
    question_text: str
    url: str
    relevance_score: float
    drafted_answer: str | None = None
    soft_cta: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class ForumAnswerMarketer:
    """
    Method 13 — Monitors Quora/Reddit/IndieHackers and posts expert answers
    that funnel readers to our Fiverr gigs or website.

    Usage:
        marketer = ForumAnswerMarketer(settings, llm_router)
        opportunities = await marketer.scan(topics=["cold email", "website builder"], limit=20)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, niche: str, limit: int = 20) -> list[MapsScanResult]:
        leads: list[MapsScanResult] = []
        tag = niche.replace(" ", "-").lower()[:40]
        url = "https://api.stackexchange.com/2.3/questions"
        params = {
            "order": "desc",
            "sort": "activity",
            "tagged": tag if len(tag) > 2 else "small-business",
            "site": "stackoverflow",
            "pagesize": min(limit, 30),
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    return leads
                for q in resp.json().get("items", []):
                    qid = str(q.get("question_id", ""))
                    title = q.get("title", "Question")
                    link = q.get("link", "")
                    leads.append(
                        maps_lead(
                            "m13",
                            qid,
                            title[:120],
                            niche,
                            "global",
                            website=link,
                            raw={
                                "platform": "stackoverflow",
                                "outreach_channel": "forum_answer",
                                "tags": q.get("tags", []),
                            },
                        )
                    )
                    if len(leads) >= limit:
                        break
        except Exception as e:
            logger.debug(f"[M13] StackExchange: {e}")
        logger.info(f"[M13] {len(leads)} forum questions")
        return leads

    async def scan(
        self,
        topics: list[str] | None = None,
        platforms: list[str] | None = None,
        limit: int = 20,
    ) -> list[ForumAnswerOpportunity]:
        logger.info(f"[M13] Forum Answer Marketer: topics={topics}, platforms={platforms}")
        return []


# ─── Method 16 ────────────────────────────────────────────────────────────────

@dataclass
class PodcastPitchLead:
    podcast_id: str
    podcast_name: str
    host_name: str
    episode_count: int
    niche: str
    audience_size: int | None
    contact_email: str | None
    pitch_draft: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        return self.episode_count >= 20 and (self.audience_size is None or self.audience_size < 50_000)


class PodcastOutreacher:
    """
    Method 16 — Pitches Mikey as a guest on relevant English-language podcasts.
    Indirect earning: podcast appearances → authority → inbound foreign clients.

    Usage:
        outreacher = PodcastOutreacher(settings, llm_router)
        leads = await outreacher.scan(niches=["AI", "automation", "freelancing"], limit=20)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan(
        self,
        niches: list[str] | None = None,
        limit: int = 20,
    ) -> list[PodcastPitchLead]:
        """
        TODO: Implement using Listen Notes API + Gemini pitch writer
        """
        niches = niches or ["AI", "automation", "freelancing", "SaaS"]
        logger.info(f"[M16] Podcast Outreacher: niches={niches}")
        return []
