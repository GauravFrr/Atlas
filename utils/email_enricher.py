"""
Email Enricher — Hunter.io + mailto scrape when OSM has no email.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

_MAILTO_RE = re.compile(
    r"mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})",
    re.I,
)
from utils.platform_domains import domain_from_url, is_blocked_email, is_platform_domain


class EmailEnricher:
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.api_key = getattr(settings, "hunter_api_key", "") or ""

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _domain_from_url(website_url: str) -> str:
        raw = website_url.strip()
        if not raw.startswith("http"):
            raw = f"https://{raw}"
        return urlparse(raw).netloc.replace("www.", "").lower()

    def _valid_email(self, email: str) -> bool:
        return not is_blocked_email(email)

    async def find_email_for_domain(self, domain: str) -> str | None:
        if not domain:
            return None
        domain = self._domain_from_url(domain) if "/" in domain or domain.startswith("http") else domain.replace("www.", "")

        if self.is_available:
            email = await self._hunter_domain_search(domain)
            if email:
                return email
            logger.info(f"[Hunter] No emails in database for {domain}")

        return await self._scrape_mailto(domain)

    async def _hunter_domain_search(self, domain: str) -> str | None:
        url = "https://api.hunter.io/v2/domain-search"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    url,
                    params={"domain": domain, "api_key": self.api_key, "limit": 10},
                )
                if resp.status_code != 200:
                    logger.warning(f"[Hunter] API {resp.status_code}: {resp.text[:200]}")
                    return None
                emails = resp.json().get("data", {}).get("emails", [])
                if not emails:
                    return None
                preferred = ("info@", "contact@", "hello@", "office@", "service@")
                for prefix in preferred:
                    for row in emails:
                        val = str(row.get("value") or "").strip()
                        if val.lower().startswith(prefix) and self._valid_email(val):
                            logger.success(f"[Hunter] {domain} → {val}")
                            return val
                val = str(emails[0].get("value") or "").strip()
                if self._valid_email(val):
                    logger.success(f"[Hunter] {domain} → {val}")
                    return val
        except Exception as e:
            logger.warning(f"[Hunter] Lookup failed for {domain}: {e}")
        return None

    async def _scrape_mailto(self, domain: str) -> str | None:
        if not domain:
            return None
        base = f"https://{domain}"
        try:
            async with httpx.AsyncClient(
                timeout=18.0,
                follow_redirects=True,
                headers={"User-Agent": "Agent-Earns/1.0"},
            ) as client:
                for path in ("", "/contact", "/contact-us"):
                    try:
                        resp = await client.get(base.rstrip("/") + path)
                        if resp.status_code >= 400:
                            continue
                        for match in _MAILTO_RE.findall(resp.text[:100000]):
                            if self._valid_email(match) and domain in match.lower():
                                logger.success(f"[Enrich] mailto on {domain} → {match}")
                                return match.strip()
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"[Enrich] mailto scrape failed for {domain}: {e}")
        return None

    async def enrich_maps_lead(
        self, website_url: str | None, *, lead: Any = None
    ) -> str | None:
        raw = getattr(lead, "raw", None) or {} if lead else {}
        ext = str(raw.get("external_website") or "").strip()
        if ext and not is_platform_domain(domain_from_url(ext)):
            website_url = ext
        elif website_url and is_platform_domain(self._domain_from_url(website_url)):
            logger.info(
                f"[Enrich] Skipping platform domain {self._domain_from_url(website_url)}"
            )
            return None
        if not website_url:
            return None
        domain = self._domain_from_url(website_url)
        if is_platform_domain(domain):
            return None
        logger.info(f"[Enrich] Looking up email for {domain} (Hunter + site scrape)")
        return await self.find_email_for_domain(domain)
