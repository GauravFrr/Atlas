"""
Resolve email greeting: owner first name from site/Hunter, else Hi there (never biz words).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

from utils.platform_domains import is_platform_url
from utils.youtube_channel import is_youtube_lead

# Words that are never a person's first name (niche, city, service terms)
_NOT_NAMES = frozenset({
    "austin", "dallas", "houston", "plumber", "plumbing", "bathroom", "remodeling",
    "remodel", "kitchen", "heating", "cooling", "hvac", "electric", "electrical",
    "roofing", "landscaping", "cleaning", "dental", "dentist", "legal", "law",
    "auto", "repair", "service", "services", "company", "co", "inc", "llc",
    "the", "and", "tx", "usa", "home", "pro", "best", "local", "metro",
    "precision", "economy", "capitol", "nomi", "team", "group", "solutions",
    "mr", "mrs", "ms", "dr", "sir", "dear",
    "youtube", "google", "channel", "video", "subscribe", "copyright",
    "privacy", "terms", "creators", "advertise", "developers", "press",
})

_OWNER_PATTERNS = (
    re.compile(
        r"(?:owner|founder|president|ceo|managed\s+by|meet)\s*[:\-]?\s*"
        r"([A-Z][a-z]{2,20})(?:\s+[A-Z][a-z]{2,25})?",
        re.I,
    ),
    re.compile(r"I'm\s+([A-Z][a-z]{2,20})\s*,?\s*(?:owner|founder)", re.I),
    re.compile(r"([A-Z][a-z]{2,20})\s+[A-Z][a-z]{2,25}\s*,\s*(?:owner|founder)", re.I),
)


def _domain(url: str | None) -> str:
    if not url:
        return ""
    return (
        urlparse(url if "://" in url else f"https://{url}")
        .netloc.replace("www.", "")
        .lower()
    )


def _looks_like_garbage_name(name: str) -> bool:
    """YouTube page noise (minified JS fragments), not real names."""
    clean = name.strip()
    if len(clean) < 3 or len(clean) > 24:
        return True
    low = clean.lower()
    vowels = sum(1 for c in low if c in "aeiou")
    if vowels == 0:
        return True
    if vowels / max(len(low), 1) < 0.15 and len(low) > 5:
        return True
    if re.search(r"[^a-zA-Z\-']", clean):
        return True
    low = clean.lower()
    if "q" in low and "qu" not in low:
        return True
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{4,}", low):
        return True
    # Random mixed case blobs from YouTube DOM (Qfuciqp, Dnsquqi)
    if clean != clean.title() and clean != clean.lower() and not clean.isupper():
        if not re.match(r"^[A-Z][a-z]+([\-'][A-Z][a-z]+)?$", clean):
            return True
    return False


def looks_like_first_name(name: str) -> bool:
    clean = name.strip().split()[0] if name else ""
    if len(clean) < 2 or len(clean) > 20:
        return False
    if not clean[0].isalpha():
        return False
    if clean.lower() in _NOT_NAMES:
        return False
    if clean.isupper() and len(clean) > 3:
        return False
    if _looks_like_garbage_name(clean):
        return False
    return True


def normalize_first_name(name: str) -> str:
    part = name.strip().split()[0]
    return part[:1].upper() + part[1:].lower() if part else ""


def _from_raw(lead: Any) -> str | None:
    raw = getattr(lead, "raw", None) or {}
    for key in (
        "contact_first_name",
        "first_name",
        "owner_first_name",
        "contact_name",
    ):
        val = str(raw.get(key) or "").strip()
        if not val:
            continue
        first = val.split()[0]
        if looks_like_first_name(first):
            return normalize_first_name(first)
        if is_youtube_lead(lead):
            raw.pop(key, None)
            lead.raw = raw
    return None


def scrape_first_name_from_html(html: str) -> str | None:
    chunk = html[:80000]
    for pat in _OWNER_PATTERNS:
        m = pat.search(chunk)
        if m:
            candidate = m.group(1)
            if looks_like_first_name(candidate):
                return normalize_first_name(candidate)
    return None


async def scrape_owner_from_website(website_url: str) -> str | None:
    if not website_url or is_platform_url(website_url):
        return None
    url = website_url if website_url.startswith("http") else f"https://{website_url}"
    try:
        async with httpx.AsyncClient(
            timeout=18.0,
            follow_redirects=True,
            headers={"User-Agent": "Agent-Earns/1.0"},
        ) as client:
            for path in ("", "/about", "/about-us", "/team"):
                try:
                    resp = await client.get(url.rstrip("/") + path)
                    if resp.status_code >= 400:
                        continue
                    name = scrape_first_name_from_html(resp.text)
                    if name:
                        logger.info(f"[Greeting] Owner name from site: {name}")
                        return name
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"[Greeting] Site scrape failed: {e}")
    return None


async def hunter_first_name(settings: Any, website_url: str | None) -> str | None:
    key = getattr(settings, "hunter_api_key", "") or ""
    domain = _domain(website_url)
    if not key or not domain or is_platform_url(website_url):
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": key, "limit": 5},
            )
            if resp.status_code != 200:
                return None
            for row in resp.json().get("data", {}).get("emails", []):
                fn = str(row.get("first_name") or "").strip()
                if looks_like_first_name(fn):
                    logger.info(f"[Greeting] Hunter contact: {fn}")
                    return normalize_first_name(fn)
    except Exception as e:
        logger.debug(f"[Greeting] Hunter name lookup failed: {e}")
    return None


async def ensure_contact_name(lead: Any, settings: Any) -> None:
    """Cache contact_first_name on lead.raw before drafting email."""
    if _from_raw(lead):
        return
    if is_youtube_lead(lead):
        # Never scrape youtube.com — use Hi there unless a real name is in raw
        return
    url = getattr(lead, "website_url", None)
    raw = getattr(lead, "raw", None) or {}
    ext = str(raw.get("external_website") or "").strip()
    if ext and not is_platform_url(ext):
        url = ext
    name = await scrape_owner_from_website(url) if url else None
    if not name:
        name = await hunter_first_name(settings, url)
    if name and looks_like_first_name(name):
        lead.raw = {**(lead.raw or {}), "contact_first_name": name}


def first_name_from_lead(lead: Any) -> str:
    """Real first name or 'there' for Hi there — never a business word."""
    found = _from_raw(lead)
    return found if found else "there"


def email_greeting_line(lead: Any, *, formal: bool = False) -> str:
    """
    Opening line for email body.
    - Named contact: Hey {Name},
    - No name: Hi there,  (or Hello, / Dear Sir/Ma'am, if formal)
    """
    first = first_name_from_lead(lead)
    if first != "there":
        return f"Hey {first},"
    if formal:
        return "Dear Sir/Ma'am,"
    return "Hi there,"


def subject_name_hint(lead: Any) -> str:
    """Subject slug — real name or neutral 'there'."""
    first = first_name_from_lead(lead)
    return first.lower() if first != "there" else "there"
