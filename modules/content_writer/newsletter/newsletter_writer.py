"""M19 — Newsletter Monetization for Mikey

TARGET:  Niche communities with 1k–10k subscribers
EARN:    $200–2,000 per sponsor slot at 2k+ subs
VOLUME:  Weekly newsletter with 51 editions per year
LOGIC:   Write high-quality niche newsletter → grow subscribers → sell sponsor slots
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from loguru import logger


@dataclass
class NewsletterEdition:
    """Represents one edition of the newsletter."""
    edition_number: int
    title: str
    slug: str
    published_at: datetime
    subscriber_count: int
    sponsor_slot_price_usd: float
    content_type: str     # "curated" | "original_insight"
    content_summary: str  # 1-2 sentence summary
    raw: dict[str, Any] = field(default_factory=dict)


class NewsletterWriter:
    """
    Method 19 — Writes and monetizes niche newsletters.

    This module enables Mikey to:
      - Write high-quality weekly newsletters (curated + original)
      - Grow subscriber base via Twitter/LinkedIn
      - Sell sponsor slots to relevant companies
      - Track monetization metrics

    Usage:
        writer = NewsletterWriter(settings, llm_router)
        edition = await writer.write_edition("AI automation for agencies", 42)
        await writer.promote_edition(edition, platforms=["twitter", "linkedin"])
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router
        self.published_editions: list[NewsletterEdition] = []
        logger.debug("NewsletterWriter initialized")

    async def write_edition(
        self,
        niche: str,
        edition_number: int,
        content_type: str = "curated",
    ) -> NewsletterEdition:
        """
        Write and structure a new newsletter edition.

        Args:
            niche: The niche topic (e.g., "AI automation for agencies")
            edition_number: The edition number (for tracking consistency)
            content_type: "curated" (best content this week) or "original_insight" (deep dive)

        Returns:
            NewsletterEdition with full content structure
        """
        logger.info(
            f"[M19] Writing newsletter edition #{edition_number} | "
            f"niche={niche} | type={content_type}"
        )

        # Base metadata
        published_at = datetime.now()
        title = f"{niche.title()} Digest - Edition #{edition_number} ({published_at.strftime('%b %d, %Y')})"
        slug = f"{niche.replace(' ', '-')}-{edition_number}-{int(published_at.timestamp())}"

        # Placeholder subscriber count (would come from Beehiiv)
        subscriber_count = 342 if edition_number < 10 else 1284

        # Placeholder sponsor slot price (scales with subscribers)
        if subscriber_count >= 2000:
            slot_price_usd = 450.0
        elif subscriber_count >= 1000:
            slot_price_usd = 225.0
        else:
            slot_price_usd = 100.0

        # Generate content with LLM
        if self.llm:
            content, summary = await self._generate_content(niche, content_type, edition_number)
        else:
            content = f"Placeholder content for {niche}"
            summary = f"This is a placeholder newsletter edition for {niche}"

        # Create edition object
        edition = NewsletterEdition(
            edition_number=edition_number,
            title=title,
            slug=slug,
            published_at=published_at,
            subscriber_count=subscriber_count,
            sponsor_slot_price_usd=slot_price_usd,
            content_type=content_type,
            content_summary=summary,
            raw={"content": content},
        )

        self.published_editions.append(edition)
        logger.info(
            f"Generated newsletter edition: {title} | "
            f"subs={subscriber_count} | price=${slot_price_usd}"
        )

        return edition

    async def _generate_content(
        self,
        niche: str,
        content_type: str,
        edition_number: int,
    ) -> tuple[str, str]:
        """Use LLM to generate newsletter content."""
        if content_type == "curated":
            content, summary = await self._generate_curated_content(niche, edition_number)
        else:
            content, summary = await self._generate_original_insight(niche, edition_number)

        return content, summary

    async def _generate_curated_content(
        self,
        niche: str,
        edition_number: int,
    ) -> tuple[str, str]:
        """Generate curated content with LLM."""
        prompt = f"""
        You are writing a weekly curated newsletter for {niche}.
        Edition number: {edition_number}
        Today's date: {datetime.now().strftime('%Y-%m-%d')}
        
        Task:
        1. Find 3-5 high-quality articles/resources published this week related to {niche}
        2. Write a short, insightful summary for each (2-3 sentences)
        3. Write a brief introduction (2-3 sentences) about what makes this week's curation special
        
        Format:
        <h1>[Newsletter Title]</h1>
        <p>[Intro Paragraph]</p>
        <section>
            <h2>Article 1</h2>
            <p>[Summary 1]</p>
            <a href="[Original URL]">Read More</a>
        </section>
        ...
        <footer>
            <p>Published: {datetime.now().strftime('%b %d, %Y')}</p>
            <p>Sponsored by: [Your Brand Name] (placeholder)</p>
            <p>If you want to sponsor, reply to this email!</p>
        </footer>
        
        IMPORTANT:
        - Keep summaries insightful and add value beyond just repeating the title
        - Maintain a professional, intelligent tone
        - Use HTML for formatting
        - Do NOT actually scrape the web - generate realistic placeholder content
        """

        assert self.llm is not None, "LLM Router is required to generate content"
        content = await self.llm.generate(
            prompt=prompt,
            max_tokens=2000,
        )

        # Extract summary from content
        summary = f"Curated collection of {niche} resources from this week"

        return content, summary

    async def _generate_original_insight(
        self,
        niche: str,
        edition_number: int,
    ) -> tuple[str, str]:
        """Generate original insight-driven content with LLM."""
        prompt = f"""
        You are writing a weekly newsletter for {niche}.
        Edition number: {edition_number}
        Today's date: {datetime.now().strftime('%Y-%m-%d')}
        
        Topic: An original insight about [key trend in {niche}]
        
        Task:
        1. Write a deep, insightful analysis of a current trend in {niche}
        2. Provide actionable advice that readers can implement immediately
        3. Support your points with realistic examples (you can invent them)
        4. Keep it professional, data-driven (even if data is illustrative)
        5. Use HTML formatting with headings and paragraphs
        
        Structure:
        <h1>[Newsletter Title]</h1>
        <p>[Insightful Introduction]</p>
        
        <section>
            <h2>The Insight</h2>
            <p>[Detailed Breakdown]</p>
        </section>
        
        <section>
            <h2>Actionable Takeaway</h2>
            <p>[Step-by-step advice]</p>
        </section>
        
        <footer>
            <p>Published: {datetime.now().strftime('%b %d, %Y')}</p>
            <p>Sponsored by: [Your Brand Name] (placeholder)</p>
        </footer>
        """

        assert self.llm is not None, "LLM Router is required to generate content"
        content = await self.llm.generate(
            prompt=prompt,
            max_tokens=2500,
        )
        
        summary = f"Original insight on {niche} trends for edition {edition_number}"
        return content, summary

