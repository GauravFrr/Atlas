"""
Lead sell packages (for export / resale) — Basic → Standard → Enriched → Exclusive.

Matches pricing discussed for CSV resale (not Razorpay service tiers).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class LeadPackageTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ENRICHED = "enriched"
    EXCLUSIVE = "exclusive"


EXCLUSIVE_MAX_AGE_DAYS = 7


def _enrichment(lead: Any) -> dict:
    data = getattr(lead, "enrichment_data", None) or {}
    return data if isinstance(data, dict) else {}


def _has_email(lead: Any) -> bool:
    return bool((getattr(lead, "email", None) or "").strip())


def _is_enriched(lead: Any) -> bool:
    data = _enrichment(lead)
    if getattr(lead, "score_breakdown", None):
        return True
    if data.get("website_audit") or data.get("outdated_audit"):
        return True
    if data.get("website_pitch_tier") or data.get("service_to_pitch"):
        return True
    if str(data.get("hunt_mode") or "").startswith("m06"):
        return True
    if data.get("youtube_channel") or data.get("channel_id"):
        return True
    if int(getattr(lead, "score", 0) or 0) >= 6:
        return True
    return False


def _is_standard(lead: Any) -> bool:
    if not (getattr(lead, "business_name", None) or "").strip():
        return False
    if not (getattr(lead, "niche", None) or "").strip():
        return False
    if not (getattr(lead, "location", None) or "").strip():
        return False
    # Website status: column set (incl. empty = no site) or enrichment flag
    data = _enrichment(lead)
    if getattr(lead, "website", None) is not None:
        return True
    if "has_website" in data:
        return True
    if data.get("website_audit") is not None:
        return True
    return False


def _is_exclusive_eligible(lead: Any) -> bool:
    data = _enrichment(lead)
    if data.get("lead_package_sold"):
        return False
    created = getattr(lead, "created_at", None)
    if not created:
        return True
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - created
    return age <= timedelta(days=EXCLUSIVE_MAX_AGE_DAYS)


def classify_package_tier(lead: Any) -> str | None:
    """
    Return sell tier or None (no email — stored for inventory but not in sell CSV by default).
    Contacted / replied leads still get a tier (resale at lower trust — export can filter).
    """
    if not _has_email(lead):
        return None
    if not _is_standard(lead):
        return LeadPackageTier.BASIC.value
    if not _is_enriched(lead):
        return LeadPackageTier.STANDARD.value
    if _is_exclusive_eligible(lead):
        return LeadPackageTier.EXCLUSIVE.value
    return LeadPackageTier.ENRICHED.value


def sync_maps_enrichment(lead: Any, maps_lead: Any) -> None:
    """Copy hunt/audit/pitch context from MapsScanResult onto the DB row."""
    data = dict(_enrichment(lead))
    raw = getattr(maps_lead, "raw", None) or {}
    if raw.get("hunt_mode"):
        data["hunt_mode"] = raw["hunt_mode"]
    if raw.get("outdated_audit"):
        from utils.json_safe import to_jsonable

        data["website_audit"] = to_jsonable(raw["outdated_audit"])
    for key in (
        "website_pitch_tier",
        "service_to_pitch",
        "service_pitch_label",
        "problem_detected",
        "youtube_channel",
        "channel_id",
        "subscriber_count",
    ):
        if raw.get(key) is not None:
            data[key] = raw[key]
    data["has_website"] = bool(
        getattr(maps_lead, "has_website", False) or getattr(maps_lead, "website_url", "")
    )
    lead.enrichment_data = data

    breakdown = getattr(maps_lead, "raw", {}) or {}
    if breakdown.get("outdated_audit") and isinstance(breakdown["outdated_audit"], dict):
        lead.score_breakdown = breakdown["outdated_audit"]
