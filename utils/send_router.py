"""
How outbound email is sent — pick one method per campaign (or hybrid per lead).
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal

SendMode = Literal["draft", "smtp", "instantly", "auto", "hybrid"]
SendChannel = Literal["instantly", "smtp"]

VALID_MODES = ("draft", "smtp", "instantly", "auto", "hybrid")


def has_pool_smtp(settings: Any) -> bool:
    from utils.domain_pool import DomainPool

    pool = DomainPool(settings)
    return pool.enabled and any(d.has_smtp() for d in pool.domains)


def can_use_smtp(settings: Any) -> bool:
    return bool(getattr(settings, "has_smtp", False)) or has_pool_smtp(settings)


def can_use_instantly(settings: Any) -> bool:
    return bool(getattr(settings, "has_instantly", False))


def pick_hybrid_channel(place_id: str, settings: Any) -> SendChannel:
    """Stable random per lead: ~half Instantly, ~half SMTP."""
    if not can_use_instantly(settings):
        return "smtp"
    if not can_use_smtp(settings):
        return "instantly"
    digest = hashlib.sha256(place_id.encode("utf-8")).hexdigest()
    return "instantly" if int(digest[:8], 16) % 2 == 0 else "smtp"


def resolve_send_mode(settings: Any, requested: str | None = None) -> SendMode:
    mode = (
        requested or getattr(settings, "email_send_mode", "draft") or "draft"
    ).lower().strip()
    if mode not in VALID_MODES:
        mode = "draft"

    if mode == "auto":
        if can_use_instantly(settings):
            return "instantly"
        if can_use_smtp(settings):
            return "smtp"
        return "draft"

    if mode == "hybrid":
        if can_use_instantly(settings) or can_use_smtp(settings):
            return "hybrid"
        return "draft"

    if mode == "instantly" and not can_use_instantly(settings):
        return "draft"
    if mode == "smtp" and not can_use_smtp(settings):
        return "draft"

    return mode  # type: ignore[return-value]


def describe_mode(mode: SendMode) -> str:
    return {
        "draft": "DRY RUN (drafts only)",
        "smtp": "SMTP — Hostinger mailbox",
        "instantly": "INSTANTLY — warmed campaign",
        "auto": "AUTO (Instantly else SMTP)",
        "hybrid": "HYBRID — random Instantly/SMTP per lead + fallback",
    }.get(mode, str(mode))
