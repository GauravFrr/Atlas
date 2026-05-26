"""M22 — GitHub Monetization Service for Mikey

TARGET:  Open-source maintainers with 50–1,000 stars
EARN:    Indirect — authority + inbound leads for Mikey's freelance services
LOGIC:   Find popular repos → add sponsorship → write announcement tweet
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from loguru import logger


@dataclass
class GitHubRepo:
    owner: str
    repo: str
    stars: int
    language: str | None
    description: str | None
    topics: list[str] = field(default_factory=list)
    sponsorship_url: str | None = None
    announcement_tweet: str | None = None


class GitHubMonetizer:
    """
    Method 22 — Helps open-source maintainers monetize their projects.

    This is a service for Mikey to build authority and generate leads through:
      - Adding sponsorship links to popular repos
      - Writing announcement tweets
      - Showcasing sponsored projects in his portfolio

    Usage:
        monetizer = GitHubMonetizer(settings, llm_router)
        repos = await monetizer.scan_for_sponsorships(language="Python")
        for repo in repos[:3]:
            await monetizer.add_sponsorship(repo, sponsorship_url="...")
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router
        self.scanned_repos: list[GitHubRepo] = []
        logger.debug("GitHubMonetizer initialized")

    async def scan_for_sponsorships(
        self,
        language: str | None = None,
        min_stars: int = 50,
        max_stars: int = 1000,
        limit: int = 20,
    ) -> list[GitHubRepo]:
        """
        Find GitHub repositories that are good candidates for sponsorship.

        Args:
            language: Programming language to filter by
            min_stars: Minimum stars threshold (default: 50)
            max_stars: Maximum stars threshold (default: 1000)
            limit: Maximum number of repos to return

        Returns:
            List of GitHubRepo objects with sponsorship info
        """
        logger.info(
            f"[M22] Scanning GitHub for sponsorships | language={language} | "
            f"stars={min_stars}-{max_stars} | limit={limit}"
        )

        # TODO: Implement actual GitHub API scraping using:
        #   - GitHub GraphQL API
        #   - Search by language, stars, topics
        #   - Check for existing sponsorship settings

        # Mock implementation for now
        self.scanned_repos = [
            GitHubRepo(
                owner="author_a",
                repo="tool_alpha",
                stars=234,
                language="Python",
                description="A useful utility for developers.",
                topics=["developer-tools", "utility"],
            ),
            GitHubRepo(
                owner="author_b",
                repo="framework_beta",
                stars=451,
                language="TypeScript",
                description="Modern web framework.",
                topics=["web-development", "framework"],
            ),
            GitHubRepo(
                owner="author_c",
                repo="library_gamma",
                stars=89,
                language="Rust",
                description="High-performance library.",
                topics=["performance", "library"],
            ),
        ]

        # Filter by stars
        filtered_repos = [r for r in self.scanned_repos if min_stars <= r.stars <= max_stars]

        logger.info(f"Found {len(filtered_repos)} candidate repositories")
        return filtered_repos[:limit]

    async def add_sponsorship(
        self, repo: GitHubRepo, sponsorship_url: str | None = None
    ) -> GitHubRepo:
        """
        Add sponsorship information to a GitHub repository.

        Args:
            repo: The repository to update
            sponsorship_url: URL for sponsorship (GitHub Sponsors, Open Collective, etc.)

        Returns:
            Updated repository with sponsorship info
        """
        if not sponsorship_url:
            sponsorship_url = f"https://github.com/sponsors/{repo.owner}"

        logger.info(
            f"Adding sponsorship to {repo.owner}/{repo.repo} | "
            f"sponsorship_url={sponsorship_url}"
        )

        # TODO: Implement GitHub API call to add sponsorship
        #   - Would require authentication and specific API endpoints

        # Update the repo object
        repo.sponsorship_url = sponsorship_url

        return repo

    async def generate_announcement_tweet(
        self, repo: GitHubRepo, personalized_context: str | None = None
    ) -> str:
        """
        Generate a tweet announcing sponsorship of a repository.

        Args:
            repo: The repository that's now sponsored
            personalized_context: Additional context or reason for sponsoring

        Returns:
            Tweet draft ready to post
        """
        # Context about why we're sponsoring
        context = (
            f"This repository is '{repo.owner}/{repo.repo}', a {repo.language} project "
            f"with {repo.stars} stars. It's useful for [specific purpose]."
            if personalized_context
            else f"This is a {repo.language} project with {repo.stars} stars that I find valuable."
        )

        # Use LLM to generate tweet
        if self.llm:
            prompt = f"""
            You are Mikey, an expert in AI automation and open-source. 
            Write a short, professional tweet announcing that you're sponsoring this project:
            
            Context: {context}
            Repository: {repo.owner}/{repo.repo}
            Sponsorship URL: {repo.sponsorship_url}
            
            Tweet should:
            1. Express genuine appreciation for the project
            2. Mention why it's valuable
            3. Include a link to sponsor the project
            4. Tag the owner if possible (use {repo.owner})
            5. Use relevant hashtags (#OpenSource, #GitHub, #Sponsorship)
            6. Keep it under 280 characters
            
            Do NOT sound salesy. Focus on supporting the open-source community.
            
            Generate the tweet body only:
            """
            
            tweet = await self.llm.generate(
                prompt=prompt,
                max_tokens=150,
            )
            
            # Add hashtags
            hashtags = " #OpenSource #GitHub #Sponsorship #AI"
            return f"{tweet.strip()}{hashtags}"
        
        # Fallback to template
        return f"""
        Excited to sponsor {repo.owner}/{repo.repo}! This is a great {repo.language} project that helps developers with [purpose]. Check them out and consider sponsoring too! 👇
        {repo.sponsorship_url}
        #OpenSource #GitHub #Sponsorship #AI
        """
