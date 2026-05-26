"""
Email-first gate — no demo/draft/publish until a valid contact email exists.
Saves LLM quota by skipping (and removing) uncontactable leads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from modules.lead_finder.scanners.google_maps import MapsScanResult
from utils.platform_domains import is_blocked_email


def valid_email(email: str | None) -> str | None:
    """Return normalized email if contactable, else None."""
    e = (email or "").strip()
    if not e or is_blocked_email(e):
        return None
    return e


def maps_has_email(maps_lead: MapsScanResult) -> bool:
    return valid_email(maps_lead.email) is not None


async def resolve_email_for_maps(
    maps_lead: MapsScanResult,
    settings: Any,
    enricher: Any,
) -> str | None:
    """
    Find a business email (scan data, YouTube About, Hunter/scrape).
    Updates maps_lead.email when found.
    """
    existing = valid_email(maps_lead.email)
    if existing:
        maps_lead.email = existing
        return existing

    from utils.youtube_channel import enrich_youtube_lead, is_youtube_lead

    if is_youtube_lead(maps_lead):
        found = await enrich_youtube_lead(maps_lead, settings, enricher)
        if found:
            maps_lead.email = valid_email(found) or found
            return maps_lead.email
        return None

    if maps_lead.website_url:
        found = await enricher.enrich_maps_lead(
            maps_lead.website_url, lead=maps_lead
        )
        if found:
            maps_lead.email = valid_email(found) or found
            return maps_lead.email

    return None


def remove_local_demo(path: str | None) -> None:
    """Delete generated demo HTML so we do not keep orphan files."""
    if not path:
        return
    p = Path(path)
    if p.is_file():
        try:
            p.unlink()
            logger.info(f"[Email gate] Removed demo file {p}")
        except OSError as e:
            logger.warning(f"[Email gate] Could not remove {p}: {e}")
