"""M21 — Medium/Substack Writer. M22 — GitHub Repo Monetizer. Stubs."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from loguru import logger


@dataclass
class LongFormArticle:
    platform: str           # "medium" | "substack"
    title: str
    body: str
    tags: list[str]
    published_url: str | None = None


class MediumSubstackWriter:
    """
    Method 21 — Writes articles on AI/automation/freelancing → earns via Medium Partner.
    EARN: $50–500/month passive. Timeline: Month 2+.
    """
    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def write_article(self, topic: str, platform: str = "medium") -> LongFormArticle:
        logger.info(f"[M21] Long Form Writer: topic={topic}, platform={platform}")
        raise NotImplementedError


@dataclass
class OpenSourceTool:
    repo_name: str
    description: str
    readme: str
    cli_script: str
    sponsors_url: str | None = None


class GitHubMonetizer:
    """
    Method 22 — Builds useful open source CLI tools → GitHub sponsors + job leads.
    EARN: $100–1,000/month long term. Timeline: Month 4+.
    """
    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def build_tool(self, problem: str) -> OpenSourceTool:
        logger.info(f"[M22] GitHub Monetizer: problem={problem}")
        raise NotImplementedError
