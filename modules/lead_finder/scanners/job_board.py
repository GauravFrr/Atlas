"""
Method 05 — Job Board Scraper
Method 11 — LinkedIn Job Monitor
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult

AUTOMATABLE_JOB_TITLES = [
    "social media manager",
    "marketing assistant",
    "data entry",
    "email marketer",
    "virtual assistant",
    "administrative assistant",
    "lead generation",
    "cold email",
    "appointment scheduler",
    "receptionist",
    "customer support",
    "order processor",
    "booking coordinator",
]

LINKEDIN_JOB_QUERIES = [
    "social media manager",
    "marketing coordinator",
    "automation specialist",
    "operations assistant",
    "virtual assistant",
    "customer support representative",
    "appointment setter",
]

# Posts hiring humans for work AI/automation can replace → pitch custom automation
AUTOMATION_REPLACEMENT_KEYWORDS = (
    "chatbot",
    "ai developer",
    "automation",
    "full stack",
    "software developer",
    "web developer",
    "mvp",
    "saas",
    "booking system",
    "scheduling",
)


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


def _parse_indeed_rss(xml_text: str, location: str, platform: str) -> list[JobPostLead]:
    leads: list[JobPostLead] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return leads
    for item in root.findall(".//item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        if title_el is None or title_el.text is None:
            continue
        title = title_el.text.strip()
        company = title.split(" - ")[0].strip() if " - " in title else title
        leads.append(
            JobPostLead(
                job_id=link_el.text if link_el is not None and link_el.text else title,
                company_name=company[:80],
                job_title=title,
                location=location,
                platform=platform,
                annual_salary_usd=None,
                posting_url=link_el.text if link_el is not None and link_el.text else "",
                automatable_role=title,
                contact_email=None,
                raw={"description": (desc_el.text or "")[:300] if desc_el is not None else ""},
            )
        )
    return leads


def _automation_primary_for_job(title: str) -> str:
    low = title.lower()
    if any(k in low for k in ("receptionist", "appointment", "scheduler", "booking")):
        return "booking"
    if any(k in low for k in ("order", "fulfillment", "processor")):
        return "ordering"
    if any(k in low for k in ("support", "customer service")):
        return "ai_chat"
    return "ai_chat"


def _jobs_to_maps(leads: list[JobPostLead], niche: str, source: str) -> list[MapsScanResult]:
    out: list[MapsScanResult] = []
    hunt_mode = "m05_job_board" if source == "m05" else "m11_linkedin_jobs"
    for j in leads:
        safe_id = re.sub(r"[^a-zA-Z0-9]", "_", j.job_id)[:40]
        primary = _automation_primary_for_job(j.job_title)
        out.append(
            maps_lead(
                source,
                safe_id,
                j.company_name,
                niche,
                j.location,
                website=j.posting_url,
                raw={
                    "hunt_mode": hunt_mode,
                    "job_title": j.job_title,
                    "platform": j.platform,
                    "method": source,
                    "automation_primary": primary,
                    "problem_detected": (
                        f"hiring for {j.job_title} — likely cheaper as AI + automation"
                    ),
                },
            )
        )
    return out


class JobBoardScraper:
    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, city: str, limit: int = 20) -> list[MapsScanResult]:
        all_jobs: list[JobPostLead] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for title in AUTOMATABLE_JOB_TITLES[:4]:
                q = quote_plus(title)
                loc = quote_plus(city)
                url = f"https://rss.indeed.com/rss?q={q}&l={loc}"
                try:
                    resp = await client.get(url, headers={"User-Agent": "Agent-Earns/1.0"})
                    if resp.status_code == 200:
                        all_jobs.extend(_parse_indeed_rss(resp.text, city, "indeed"))
                except Exception as e:
                    logger.debug(f"[M05] Indeed RSS: {e}")
                if len(all_jobs) >= limit * 2:
                    break

        logger.info(f"[M05] {len(all_jobs)} job posts from Indeed RSS")
        return _jobs_to_maps(all_jobs[:limit], "automation", "m05")[:limit]

    async def scan(
        self,
        platforms: list[str] | None = None,
        job_titles: list[str] | None = None,
        limit: int = 100,
    ) -> list[JobPostLead]:
        return []


class LinkedInJobMonitor:
    """Method 11 — Indeed RSS with LinkedIn-oriented role titles."""

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, city: str, limit: int = 20) -> list[MapsScanResult]:
        all_jobs: list[JobPostLead] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            for title in LINKEDIN_JOB_QUERIES:
                q = quote_plus(title)
                loc = quote_plus(city)
                url = f"https://rss.indeed.com/rss?q={q}&l={loc}"
                try:
                    resp = await client.get(url, headers={"User-Agent": "Agent-Earns/1.0"})
                    if resp.status_code == 200:
                        all_jobs.extend(_parse_indeed_rss(resp.text, city, "indeed_linkedin"))
                except Exception:
                    pass
                if len(all_jobs) >= limit * 2:
                    break
        logger.info(f"[M11] {len(all_jobs)} automatable job leads")
        return _jobs_to_maps(all_jobs[:limit], "automation", "m11")[:limit]
