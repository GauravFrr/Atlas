"""
Method 16 — Podcast Guest Outreach for Mikey

TARGET:  US/UK podcasts in AI, automation, freelancing, SaaS
EARN:    Indirect — generates high-quality inbound client inquiries for Mikey
LOGIC:   Find podcast → check episode count + audience → write personalized pitch
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from loguru import logger

import httpx

from integrations.platforms.listen_notes import ListenNotesClient
from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


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
        """Target podcasts with 20–500 episodes (established but not saturated)."""
        return 20 <= self.episode_count <= 500 and (
            self.audience_size is None or self.audience_size < 50_000
        )


class PodcastOutreacher:
    """
    Method 16 — Pitches Mikey as a guest on relevant English-language podcasts.

    This is a lead generation tool that produces:
      - Guest appearances on podcasts
      - Authority-building opportunities
      - High-quality inbound client inquiries

    Usage:
        outreacher = PodcastOutreacher(settings, llm_router)
        leads = await outreacher.scan(niches=["AI", "automation"], limit=20)
        for lead in leads:
            if lead.is_target:
                await outreacher.send_pitch(lead)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router
        self.scraped_podcasts: list[PodcastPitchLead] = []
        logger.debug("PodcastOutreacher initialized")

    async def _scan_itunes_podcasts(self, query: str, limit: int) -> list[MapsScanResult]:
        """Free Apple iTunes Search API — no key, fine for podcast discovery."""
        leads: list[MapsScanResult] = []
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    "https://itunes.apple.com/search",
                    params={
                        "term": query,
                        "media": "podcast",
                        "entity": "podcast",
                        "limit": min(limit * 2, 50),
                        "country": "US",
                    },
                )
                if resp.status_code != 200:
                    return leads
                for pod in resp.json().get("results", []):
                    eps = int(pod.get("trackCount") or 0)
                    if eps and not (10 <= eps <= 600):
                        continue
                    pid = str(pod.get("collectionId") or pod.get("trackId") or "")
                    title = pod.get("collectionName") or pod.get("trackName") or "Podcast"
                    leads.append(
                        maps_lead(
                            "m16",
                            pid or title[:16],
                            title[:100],
                            query,
                            "US",
                            website=pod.get("collectionViewUrl") or pod.get("trackViewUrl"),
                            raw={
                                "host": pod.get("artistName"),
                                "episodes": eps,
                                "method": "podcast_guest_pitch",
                                "source": "itunes",
                                "genre": pod.get("primaryGenreName"),
                            },
                        )
                    )
                    if len(leads) >= limit:
                        break
        except Exception as e:
            logger.debug(f"[M16] iTunes podcast search: {e}")
        return leads

    async def scan_maps(self, niche: str, limit: int = 20) -> list[MapsScanResult]:
        query = f"{niche} entrepreneur business"
        leads: list[MapsScanResult] = []

        key = getattr(self.settings, "listen_notes_api_key", "") or ""
        if key:
            client = ListenNotesClient(key)
            podcasts = await client.search_podcasts(
                f"{niche} business automation", limit=limit
            )
            for p in podcasts:
                pid = str(p.get("id", ""))
                title = p.get("title_original") or p.get("title", "Podcast")
                pub = p.get("publisher_original") or p.get("publisher", "")
                eps = int(p.get("total_episodes") or 0)
                if eps and not (20 <= eps <= 500):
                    continue
                leads.append(
                    maps_lead(
                        "m16",
                        pid or title[:20],
                        title[:100],
                        niche,
                        "US/UK",
                        website=p.get("listennotes_url") or p.get("link"),
                        raw={
                            "host": pub,
                            "episodes": eps,
                            "method": "podcast_guest_pitch",
                            "source": "listen_notes",
                        },
                    )
                )
                if len(leads) >= limit:
                    break

        if len(leads) < limit:
            extra = await self._scan_itunes_podcasts(query, limit - len(leads))
            seen = {x.place_id for x in leads}
            for x in extra:
                if x.place_id not in seen:
                    leads.append(x)

        logger.info(f"[M16] {len(leads)} podcast targets (iTunes/ListenNotes)")
        return leads[:limit]

    async def scan(
        self,
        niches: list[str] | None = None,
        limit: int = 20,
        language: Literal["en", "US", "UK", "global"] = "US",
    ) -> list[PodcastPitchLead]:
        """
        Scrape podcasts and return potential guest opportunities.

        Args:
            niches: Target podcast categories (e.g., ["AI", "automation", "SaaS"])
            limit: Maximum number of podcast opportunities to find
            language: Target audience language/region

        Returns:
            List of PodcastPitchLead objects
        """
        # Default to AI and automation if no niche specified
        niches = niches or ["AI", "automation", "SaaS", "freelancing"]

        logger.info(
            f"[M16] Starting podcast scan | niches={niches} | limit={limit} | language={language}"
        )

        # TODO: Implement actual podcast scraping using:
        #   - Listen Notes API (free tier available)
        #   - Spotify API
        #   - Apple Podcasts API
        #   - Manual scraping for specific platforms

        # Mock implementation for now
        self.scraped_podcasts = [
            PodcastPitchLead(
                podcast_id="podcast_123",
                podcast_name="AI for Entrepreneurs",
                host_name="Alex Martinez",
                episode_count=45,
                niche="AI for Business",
                audience_size=8_500,
                contact_email="[EMAIL_ADDRESS]",
            ),
            PodcastPitchLead(
                podcast_id="podcast_456",
                podcast_name="The Automation Insiders",
                host_name="Sarah Chen",
                episode_count=120,
                niche="Business Automation",
                audience_size=15_200,
                contact_email="[EMAIL_ADDRESS]",
            ),
            PodcastPitchLead(
                podcast_id="podcast_789",
                podcast_name="SaaS Growth Secrets",
                host_name="David Rodriguez",
                episode_count=15,
                niche="SaaS",
                audience_size=3_200,
                contact_email="[EMAIL_ADDRESS]",
            ),
            PodcastPitchLead(
                podcast_id="podcast_101",
                podcast_name="Freelance Freedom",
                host_name="Emily Carter",
                episode_count=88,
                niche="Freelancing",
                audience_size=6_800,
                contact_email="[EMAIL_ADDRESS]",
            ),
        ]

        # Filter for target podcasts
        target_podcasts = [p for p in self.scraped_podcasts if p.is_target][:limit]

        logger.info(f"Found {len(target_podcasts)} target podcasts out of {len(self.scraped_podcasts)}")
        return target_podcasts

    async def generate_pitch(
        self,
        podcast_id: str,
        personalized_context: str | None = None,
    ) -> str:
        """
        Generate a personalized pitch email for a podcast.

        Args:
            podcast_id: ID of the podcast to pitch
            personalized_context: Additional context about why this podcast

        Returns:
            Personalized pitch email draft
        """
        podcast = next((p for p in self.scraped_podcasts if p.podcast_id == podcast_id), None)
        if not podcast:
            raise ValueError(f"Podcast with ID {podcast_id} not found")

        # Default context
        context = (
            f"This podcast is in the '{podcast.niche}' niche, "
            f"has {podcast.episode_count} episodes, and an audience of approximately {podcast.audience_size}. "
            "The host, Alex Martinez, frequently interviews experts in business automation and AI."
            if personalized_context
            else f"This is a {podcast.niche} podcast with {podcast.episode_count} episodes."
        )

        # Use LLM to generate personalized pitch
        if self.llm:
            prompt = f"""
            You are Mikey, an expert in AI automation and business systems. 
            Write a short, professional, and personalized podcast guest pitch email.
            
            Context: {context}
            Podcast Name: {podcast.podcast_name}
            Host Name: {podcast.host_name}
            
            Mikey's Expertise:
            - AI automation for small businesses
            - Building custom business systems
            - Automating cold email outreach
            - AI sales agents
            - Integrating ChatGPT with business workflows
            
            Email Structure:
            1. Show genuine appreciation for the podcast
            2. Mention a specific episode you liked (if possible)
            3. Briefly introduce Mikey and his expertise
            4. Suggest 2-3 relevant topics you could discuss
            5. Mention your unique value proposition
            6. Keep it concise (under 200 words)
            7. End with a clear call to action (offer to send more info)
            
            Do NOT sound salesy or generic.
            Do NOT mention "Agent-Earns" unless contextually relevant.
            Focus on providing value to the podcast audience.
            
            Generate the email body only (no subject line yet):
            """
            
            email_body = await self.llm.generate(
                prompt=prompt,
                max_tokens=400,
            )
            
            # Add subject line
            subject = f"Podcast Guest Pitch: AI Automation Expert for {podcast.podcast_name}"
            return f"Subject: {subject}\n\n{email_body.strip()}"
        
        # Fallback to template if no LLM
        return f"""
        Subject: Podcast Guest Pitch: AI Automation Expert for {podcast.podcast_name}
        
        Hi {podcast.host_name},
        
        I'm a big fan of {podcast.podcast_name} and really enjoyed your recent episode on [specific topic].
        """