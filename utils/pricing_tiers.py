"""
Load data/pricing_tiers.json and resolve Razorpay amounts from lead pitch type.

USD list prices → INR via settings.usd_to_inr_rate (default 85).
Phase key: intro | standard | premium (from JSON current_phase).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from loguru import logger

DEFAULT_TIERS_PATH = Path(__file__).resolve().parents[1] / "data" / "pricing_tiers.json"

# direct_outreach_usd service label → lead pitch
_SERVICE_MAP: dict[str, tuple[str, str]] = {
    "website": ("Landing Page (1 page + SEO)", "intro"),
    "website_full": ("Full Website (5 pages + blog + SEO)", "intro"),
    "automation": ("AI Chatbot (website widget)", "intro"),
    "youtube": ("Social Media Pack (30 posts)", "intro"),
}


@lru_cache(maxsize=4)
def _load_tiers_file(path_str: str) -> dict[str, Any]:
    path = Path(path_str)
    if not path.is_file():
        logger.warning(f"[Pricing] Missing {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error(f"[Pricing] Invalid JSON in {path}: {e}")
        return {}


def load_pricing_tiers(settings: Any | None = None) -> dict[str, Any]:
    path = DEFAULT_TIERS_PATH
    if settings is not None:
        custom = str(getattr(settings, "pricing_tiers_file", "") or "").strip()
        if custom:
            path = Path(custom)
    return _load_tiers_file(str(path.resolve()))


def current_phase(data: dict[str, Any]) -> str:
    phase = str(data.get("current_phase") or "intro").strip().lower()
    if phase in ("intro", "standard", "premium"):
        return phase
    return "intro"


def _lookup_direct_usd(data: dict[str, Any], service_label: str, phase: str) -> int | None:
    for row in data.get("direct_outreach_usd") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("service") or "").strip() == service_label:
            val = row.get(phase)
            if val is not None:
                return int(val)
    return None


def pitch_key_for_lead(lead: Any) -> str:
    """website | website_full | automation | youtube"""
    data = getattr(lead, "enrichment_data", None) or {}
    hunt = str(data.get("hunt_mode") or "").lower()
    if hunt in ("m10_no_website", "no_website"):
        return "website"
    if hunt in ("m02_outdated", "outdated"):
        return "website_full"

    try:
        from modules.outreach.universal_scripts import lead_pitch_service

        svc = lead_pitch_service(lead)
    except Exception:
        svc = "website"

    if svc == "website":
        tier = str(data.get("pitch_tier") or data.get("website_tier") or "").lower()
        if tier in ("outdated", "modern"):
            return "website_full"
        problem = str(getattr(lead, "problem_detected", "") or "").lower()
        if "outdated" in problem or "rebuild" in problem:
            return "website_full"
        return "website"
    if svc == "automation":
        return "automation"
    if svc == "youtube":
        return "youtube"
    return "website"


def amount_usd_for_lead(lead: Any, settings: Any | None = None) -> int | None:
    data = load_pricing_tiers(settings)
    if not data:
        return None
    phase = current_phase(data)
    key = pitch_key_for_lead(lead)
    label, _ = _SERVICE_MAP.get(key, _SERVICE_MAP["website"])
    usd = _lookup_direct_usd(data, label, phase)
    if usd is None and key == "website_full":
        usd = _lookup_direct_usd(
            data, "Basic Website (3 pages)", phase
        )
    return usd


def amount_inr_for_lead(lead: Any, settings: Any) -> int | None:
    """INR rupees for Razorpay from pricing_tiers.json + lead pitch."""
    usd = amount_usd_for_lead(lead, settings)
    if usd is None:
        return None
    rate = float(getattr(settings, "usd_to_inr_rate", 85) or 85)
    inr = int(round(usd * rate))
    return max(100, inr)


def payment_description_for_lead(lead: Any, settings: Any) -> str:
    key = pitch_key_for_lead(lead)
    labels = {
        "website": "Landing page + lead capture",
        "website_full": "Website rebuild package",
        "automation": "AI chatbot & automation setup",
        "youtube": "Channel / content package",
    }
    label = labels.get(key, "Digital package")
    name = (getattr(lead, "business_name", None) or "your business")[:80]
    return f"{label} — {name}"
