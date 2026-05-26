"""
Method 14 — SaaS Churn Email Writer
TARGET:  US SaaS founders with free trial products
EARN:    $200–600 per email sequence (5–8 emails)
LOGIC:   Find SaaS with weak onboarding → pitch email sequence that fixes trial conversion
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.lead_adapter import maps_lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


@dataclass
class SaaSChurnLead:
    company_name: str
    product_url: str
    founder_email: str | None
    category: str           # from G2/Capterra
    has_trial: bool
    has_onboarding_emails: bool
    estimated_trial_rate: float | None
    pitch_draft: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_target(self) -> bool:
        return self.has_trial and not self.has_onboarding_emails


class SaaSChurnScanner:
    """
    Method 14 — Finds SaaS products with weak onboarding to pitch email sequences.

    Usage:
        scanner = SaaSChurnScanner(settings, llm_router)
        leads = await scanner.scan(category="project management", limit=30)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan_maps(self, niche: str, limit: int = 20) -> list[MapsScanResult]:
        leads: list[MapsScanResult] = []
        term = f"{niche} saas".replace("_", " ")
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.get(
                    "https://itunes.apple.com/search",
                    params={"term": term, "media": "software", "limit": 40},
                )
                if resp.status_code != 200:
                    return leads
                for app in resp.json().get("results", []):
                    price = float(app.get("price") or 0)
                    if price > 0:
                        continue
                    aid = str(app.get("trackId", ""))
                    leads.append(
                        maps_lead(
                            "m14",
                            aid,
                            app.get("trackName", "SaaS"),
                            niche,
                            "US",
                            website=app.get("trackViewUrl"),
                            raw={
                                "free_trial": True,
                                "seller": app.get("sellerName"),
                                "method": "saas_churn",
                            },
                        )
                    )
                    if len(leads) >= limit:
                        break
        except Exception as e:
            logger.debug(f"[M14] SaaS search: {e}")
        logger.info(f"[M14] {len(leads)} free SaaS apps")
        return leads

    async def scan(self, category: str = "", limit: int = 30) -> list[SaaSChurnLead]:
        logger.info(f"[M14] SaaS Churn Scanner: category={category}")
        return []
