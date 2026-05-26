"""Block platform / social hosts from Hunter, scrape, and website audits."""

from __future__ import annotations

from urllib.parse import urlparse

PLATFORM_DOMAINS = frozenset({
    "youtube.com",
    "youtu.be",
    "google.com",
    "googleusercontent.com",
    "facebook.com",
    "fb.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "linkedin.com",
    "pinterest.com",
    "reddit.com",
    "tumblr.com",
    "wikipedia.org",
    "amazon.com",
    "apple.com",
    "spotify.com",
    "linktr.ee",
    "linktree.com",
    "beacons.ai",
    "bio.link",
})

BLOCKED_EMAIL_DOMAINS = frozenset({
    "youtube.com",
    "google.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "linkedin.com",
    "example.com",
    "wix.com",
    "sentry.io",
    "domain.com",
})


def domain_from_url(url: str | None) -> str:
    if not url:
        return ""
    raw = url.strip()
    if not raw.startswith("http"):
        raw = f"https://{raw}"
    return urlparse(raw).netloc.replace("www.", "").lower()


def is_platform_domain(domain: str) -> bool:
    d = domain.replace("www.", "").lower().strip()
    if not d:
        return False
    if d in PLATFORM_DOMAINS:
        return True
    return any(d == p or d.endswith(f".{p}") for p in PLATFORM_DOMAINS)


def is_platform_url(url: str | None) -> bool:
    return is_platform_domain(domain_from_url(url))


def is_blocked_email(email: str) -> bool:
    e = email.strip().lower()
    if "@" not in e:
        return True
    domain = e.split("@")[-1]
    return any(skip in domain for skip in BLOCKED_EMAIL_DOMAINS)
