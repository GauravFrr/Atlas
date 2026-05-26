"""
Method 06 — YouTube Channel Auditor
TARGET:  US/UK YouTubers with 1k–100k subs and poor optimization
EARN:    $50 audit + $200–500 optimization package
LOGIC:   YouTube Data API → audit channel → generate branded PDF → email creator

Free Audit Report Includes:
  - Title SEO score (0–100)
  - Thumbnail quality rating via Gemini Vision
  - Description keyword analysis
  - Upload frequency consistency grade
  - Top 3 actionable improvements (teaser)
  - Full report locked behind paid upgrade
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


@dataclass
class ChannelAuditResult:
    channel_id: str
    channel_name: str
    subscriber_count: int
    video_count: int
    avg_views_per_video: float
    title_seo_score: float          # 0–100
    thumbnail_quality_score: float  # 0–10 from Gemini Vision
    upload_frequency_grade: str     # "A" | "B" | "C" | "D" | "F"
    description_keyword_score: float
    top_improvements: list[str]
    contact_email: str | None
    audit_pdf_path: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        return (
            self.title_seo_score * 0.3
            + self.thumbnail_quality_score * 10 * 0.3
            + self.description_keyword_score * 0.2
            + {"A": 100, "B": 75, "C": 50, "D": 25, "F": 0}.get(self.upload_frequency_grade, 50) * 0.2
        )

    @property
    def is_target(self) -> bool:
        """Channels that need help — not too big, not too small."""
        return 1_000 <= self.subscriber_count <= 100_000 and self.overall_score < 60


class YouTubeAuditor:
    """
    Method 06 — Audits YouTube channels and generates free PDF audit reports.

    Usage:
        auditor = YouTubeAuditor(settings, llm_router)
        results = await auditor.scan(niche="tech", limit=20)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, niche: str, city: str, limit: int) -> list[MapsScanResult]:
        api_key = getattr(self.settings, "youtube_api_key", "") or ""
        leads: list[MapsScanResult] = []
        query = f"{niche} {city}"

        if api_key:
            from utils.youtube_channel import apply_channel_metadata, fetch_channel_metadata

            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": query,
                "type": "channel",
                "maxResults": min(limit, 25),
                "key": api_key,
            }
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        for item in resp.json().get("items", []):
                            sn = item.get("snippet", {})
                            cid = item.get("id", {}).get("channelId", "")
                            lead = maps_lead(
                                "m06",
                                cid or sn.get("title", "")[:20],
                                sn.get("channelTitle", "YouTube Channel"),
                                niche,
                                city,
                                website=None,
                                has_website=False,
                                raw={
                                    "channel_id": cid,
                                    "method": "youtube",
                                    "channel_url": f"https://www.youtube.com/channel/{cid}",
                                },
                            )
                            if cid:
                                meta = await fetch_channel_metadata(cid, api_key)
                                if meta:
                                    apply_channel_metadata(lead, meta)
                            leads.append(lead)
            except Exception as e:
                logger.debug(f"[M06] YouTube API: {e}")

        if not leads and not api_key:
            logger.info("[M06] Set YOUTUBE_API_KEY for channel search; using search fallback row")
            leads.append(
                maps_lead(
                    "m06",
                    f"yt_{niche[:12]}",
                    f"YouTube: {niche} ({city})",
                    niche,
                    city,
                    website=f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
                    raw={"method": "youtube_search", "needs_youtube_api_key": True},
                )
            )

        logger.info(f"[M06] {len(leads)} YouTube targets")
        return leads[:limit]

    async def scan(self, niche: str, limit: int = 20) -> list[ChannelAuditResult]:
        """
        Find under-optimized channels in a niche.

        TODO: Implement using:
          - YouTube Data API v3 (search, channels, videos endpoints)
          - Gemini Vision for thumbnail scoring
          - NLP for title/description SEO scoring
        """
        logger.info(f"[M06] YouTube Auditor: niche={niche}, limit={limit}")
        return []

    async def audit_channel(self, channel_id: str) -> ChannelAuditResult:
        """Perform full audit on a single channel."""
        raise NotImplementedError

    async def generate_pdf_report(self, result: ChannelAuditResult) -> str:
        """Generate a branded PDF audit report. Returns file path."""
        # TODO: Use reportlab or weasyprint to render the audit as PDF
        raise NotImplementedError
