"""
Method 03 — Reddit / Forum Lead Mining
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult

INTENT_KEYWORDS = [
    "looking for a developer",
    "need someone to build",
    "does anyone recommend",
    "anyone recommend",
    "recommend a",
    "tired of doing this manually",
    "how do i automate",
    "my website is terrible",
    "website is outdated",
    "need a chatbot",
    "need help with cold email",
    "hire a freelancer",
    "struggling with my website",
    "need a website",
    "need a web designer",
    "looking for a web",
    "no website",
    "without a website",
    "bad website",
    "redo my site",
    "need more leads",
    "need more customers",
    "book more appointments",
]

TARGET_SUBREDDITS = [
    "entrepreneur",
    "smallbusiness",
    "startups",
    "webdev",
    "forhire",
    "digital_marketing",
    "SEO",
    "ecommerce",
    "shopify",
]


@dataclass
class RedditLead:
    post_id: str
    subreddit: str
    title: str
    body: str
    author: str
    url: str
    matched_keyword: str
    intent_score: float
    raw: dict[str, Any] = field(default_factory=dict)


class RedditMiner:
    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    def _matches_intent(self, text: str, niche: str = "") -> str | None:
        low = text.lower()
        for kw in INTENT_KEYWORDS:
            if kw in low:
                return kw
        n = niche.lower().strip()
        if n and n not in ("general", "local_service"):
            for phrase in (
                f"need a {n}",
                f"looking for {n}",
                f"recommend a {n}",
                f"hire a {n}",
                f"{n} near me",
            ):
                if phrase in low:
                    return phrase
        return None

    async def scan_maps(self, niche: str, city: str, limit: int) -> list[MapsScanResult]:
        leads: list[MapsScanResult] = []
        headers = {"User-Agent": "Agent-Earns/1.0 (lead research)"}

        async with httpx.AsyncClient(timeout=25.0, headers=headers) as client:
            for sub in TARGET_SUBREDDITS:
                if len(leads) >= limit:
                    break
                url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    posts = resp.json().get("data", {}).get("children", [])
                except Exception as e:
                    logger.debug(f"[M03] reddit r/{sub}: {e}")
                    continue

                for child in posts:
                    data = child.get("data", {})
                    title = data.get("title", "")
                    body = data.get("selftext", "")[:500]
                    combined = f"{title} {body}"
                    kw = self._matches_intent(combined, niche=niche)
                    if not kw:
                        continue
                    pid = data.get("id", "")
                    leads.append(
                        maps_lead(
                            "m03",
                            pid,
                            title[:120],
                            niche,
                            city,
                            website=data.get("url"),
                            raw={
                                "subreddit": sub,
                                "author": data.get("author"),
                                "permalink": f"https://reddit.com{data.get('permalink', '')}",
                                "keyword": kw,
                                "outreach_channel": "reddit_reply",
                            },
                        )
                    )
                    if len(leads) >= limit:
                        break

        logger.info(f"[M03] {len(leads)} Reddit intent posts")
        return leads

    async def scan(
        self,
        subreddits: list[str] | None = None,
        keywords: list[str] | None = None,
        limit: int = 100,
        min_intent_score: float = 6.0,
    ) -> list[RedditLead]:
        maps = await self.scan_maps("general", "global", min(limit, 25))
        return [
            RedditLead(
                post_id=m.place_id.split("/")[-1],
                subreddit=m.raw.get("subreddit", ""),
                title=m.business_name,
                body="",
                author=m.raw.get("author", ""),
                url=m.raw.get("permalink", ""),
                matched_keyword=m.raw.get("keyword", ""),
                intent_score=7.0,
            )
            for m in maps
        ]
