"""
YouTube channel leads — never treat youtube.com as the business website.

Hydrate channel metadata (API + description parse) for real site/email.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

from utils.platform_domains import (
    domain_from_url,
    is_blocked_email,
    is_platform_domain,
    is_platform_url,
)

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.I,
)
_URL_RE = re.compile(r"https?://[^\s\]>\"']+", re.I)

_CHANNEL_ID_RE = re.compile(
    r"(?:youtube\.com/channel/|youtube\.com/@)([A-Za-z0-9_\-]+)",
    re.I,
)


def is_youtube_lead(lead: Any) -> bool:
    raw = getattr(lead, "raw", None) or {}
    if str(raw.get("method") or "") == "youtube":
        return True
    if str(raw.get("source") or "") == "m06":
        return True
    hunt = str(raw.get("hunt_mode") or "").lower()
    if hunt in ("m06_youtube", "m06_youtube_auditor"):
        return True
    return is_youtube_channel_url(getattr(lead, "website_url", None))


def is_youtube_channel_url(url: str | None) -> bool:
    if not url:
        return False
    low = url.lower()
    return "youtube.com/channel/" in low or "youtube.com/@" in low


def extract_channel_id(url: str | None) -> str | None:
    if not url:
        return None
    m = _CHANNEL_ID_RE.search(url)
    if m:
        return m.group(1)
    return None


def channel_id_from_lead(lead: Any) -> str | None:
    raw = getattr(lead, "raw", None) or {}
    cid = str(raw.get("channel_id") or "").strip()
    if cid:
        return cid
    return extract_channel_id(getattr(lead, "website_url", None))


def _pick_external_url(urls: list[str]) -> str | None:
    for u in urls:
        dom = domain_from_url(u)
        if dom and not is_platform_domain(dom):
            return u.split("?")[0].rstrip("/")
    return None


def parse_channel_description(description: str) -> tuple[str | None, str | None]:
    """Return (external_website, email) from channel About text."""
    if not description:
        return None, None
    email = None
    for match in _EMAIL_RE.findall(description):
        if not is_blocked_email(match):
            email = match.strip().lower()
            break
    urls = _URL_RE.findall(description)
    site = _pick_external_url(urls)
    return site, email


async def fetch_channel_metadata(
    channel_id: str,
    api_key: str,
) -> dict[str, Any] | None:
    if not channel_id or not api_key:
        return None
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet,statistics",
        "id": channel_id,
        "key": api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                logger.debug(f"[M06] channels.list {resp.status_code}: {resp.text[:200]}")
                return None
            items = resp.json().get("items", [])
            if not items:
                return None
            item = items[0]
            sn = item.get("snippet", {}) or {}
            stats = item.get("statistics", {}) or {}
            desc = str(sn.get("description") or "")
            ext_site, email = parse_channel_description(desc)
            return {
                "channel_id": channel_id,
                "channel_title": str(sn.get("title") or ""),
                "channel_description": desc[:2000],
                "channel_url": f"https://www.youtube.com/channel/{channel_id}",
                "external_website": ext_site,
                "contact_email": email,
                "subscriber_count": int(stats.get("subscriberCount") or 0),
            }
    except Exception as e:
        logger.debug(f"[M06] Channel metadata failed: {e}")
    return None


def apply_channel_metadata(lead: Any, meta: dict[str, Any]) -> None:
    """Merge API metadata onto lead; set business website only if external."""
    raw = dict(getattr(lead, "raw", None) or {})
    raw.update(
        {
            "method": "youtube",
            "channel_id": meta.get("channel_id") or raw.get("channel_id"),
            "channel_url": meta.get("channel_url") or raw.get("channel_url"),
            "channel_title": meta.get("channel_title") or raw.get("channel_title"),
        }
    )
    ext = meta.get("external_website")
    if ext:
        raw["external_website"] = ext
        lead.website_url = ext
        lead.has_website = True
    else:
        raw.pop("external_website", None)
        lead.website_url = None
        lead.has_website = False

    email = meta.get("contact_email")
    if email and not is_blocked_email(email):
        raw["contact_email"] = email
        if not (getattr(lead, "email", None) or "").strip():
            lead.email = email

    lead.raw = raw


async def hydrate_youtube_lead(lead: Any, settings: Any) -> None:
    """Fetch channel About + links; never leave website_url as youtube.com."""
    if not is_youtube_lead(lead):
        return

    raw = dict(getattr(lead, "raw", None) or {})
    raw["method"] = "youtube"
    cid = channel_id_from_lead(lead)
    if cid:
        raw["channel_id"] = cid
        raw["channel_url"] = f"https://www.youtube.com/channel/{cid}"

    # Clear platform URL from website column — store on channel_url only
    if is_platform_url(getattr(lead, "website_url", None)):
        lead.website_url = raw.get("external_website") or None
        lead.has_website = bool(lead.website_url)

    api_key = getattr(settings, "youtube_api_key", "") or ""
    if cid and api_key and not raw.get("channel_description"):
        meta = await fetch_channel_metadata(cid, api_key)
        if meta:
            apply_channel_metadata(lead, meta)
            raw = dict(lead.raw or {})
            logger.info(
                f"[M06] {meta.get('channel_title')}: "
                f"site={meta.get('external_website') or 'none'} "
                f"email={meta.get('contact_email') or 'none'}"
            )

    lead.raw = {**raw, "method": "youtube"}
    if is_platform_url(getattr(lead, "website_url", None)):
        lead.website_url = None
        lead.has_website = False


async def enrich_youtube_lead(lead: Any, settings: Any, enricher: Any) -> str | None:
    """
    Email for creators: channel description → external site (Hunter) — never youtube.com.
    """
    await hydrate_youtube_lead(lead, settings)
    raw = getattr(lead, "raw", None) or {}

    if (getattr(lead, "email", None) or "").strip():
        e = lead.email.strip()
        if not is_blocked_email(e):
            return e
        lead.email = None

    desc_email = str(raw.get("contact_email") or "").strip()
    if desc_email and not is_blocked_email(desc_email):
        lead.email = desc_email
        logger.success(f"[M06] Channel About email → {desc_email}")
        return desc_email

    ext = str(raw.get("external_website") or "").strip() or getattr(lead, "website_url", None)
    if ext and not is_platform_url(ext):
        found = await enricher.enrich_maps_lead(ext, lead=lead)
        if found:
            lead.email = found
            return found

    logger.warning(
        f"[M06] No business email for {getattr(lead, 'business_name', 'channel')} "
        f"(add link in channel About or skip)"
    )
    return None
