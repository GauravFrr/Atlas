"""
Who gets which offer — aligned with ULTIMATE_AGENT_BLUEPRINT_V3 §9 + AGENT_EARNING_METHODS.

WEBSITE pitch (Methods 10 / 02 / 25):
  - No website (M10)
  - Outdated site: pre-2018 feel, not mobile, no SSL, M02 design_score < 5

AUTOMATION pitch (Methods 24 / real estate / job-board style):
  - Already has a professional modern site (mobile + SSL + design_score >= 6)
  - Pitch: AI chatbot, instant lead reply, online booking — NOT a new website

Blueprint lead score: +3 no site or pre-2018 site | -2 already professional site + SEO
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from modules.lead_finder.scanners.google_maps import MapsScanResult
else:
    MapsScanResult = Any

# M02: score < 5 → outdated mockup (AGENT_EARNING_METHODS)
OUTDATED_DESIGN_MAX = 5.0
# Blueprint: "professional website" → automation, not rebuild
PROFESSIONAL_DESIGN_MIN = 6.0


class ServiceOffer(str, Enum):
    WEBSITE = "website"
    AUTOMATION = "automation"
    YOUTUBE = "youtube"


class WebsitePitchTier(str, Enum):
    NO_SITE = "no_site"
    OUTDATED = "outdated"
    MODERN = "modern"


@dataclass(frozen=True)
class PitchPlan:
    service: ServiceOffer
    tier: WebsitePitchTier
    problem_detected: str
    service_label: str  # for logs / Instantly {{service_to_pitch}}


def lead_has_website(lead: MapsScanResult) -> bool:
    return bool(getattr(lead, "has_website", False) or getattr(lead, "website_url", ""))


def _audit_from_lead(lead: MapsScanResult) -> Any | None:
    return (getattr(lead, "raw", None) or {}).get("outdated_audit")


def _audit_scores(audit: Any) -> tuple[float, bool, bool]:
    if isinstance(audit, dict):
        return (
            float(audit.get("design_score", 3.0)),
            bool(audit.get("is_mobile_friendly", False)),
            bool(audit.get("has_ssl", False)),
        )
    return (
        float(getattr(audit, "design_score", 3.0)),
        bool(getattr(audit, "is_mobile_friendly", False)),
        bool(getattr(audit, "has_ssl", False)),
    )


def _hunt_mode(lead: MapsScanResult) -> str:
    return str((getattr(lead, "raw", None) or {}).get("hunt_mode", "") or "").lower()


def _is_youtube_lead(lead: MapsScanResult) -> bool:
    from utils.youtube_channel import is_youtube_lead as _yt

    return _yt(lead)


def _is_real_estate(lead: MapsScanResult) -> bool:
    n = (lead.niche or "").lower()
    return n in ("real_estate", "realtor", "real estate", "property", "broker")


def website_pitch_tier(lead: MapsScanResult) -> WebsitePitchTier:
    if _is_youtube_lead(lead):
        return WebsitePitchTier.NO_SITE
    if not lead_has_website(lead):
        return WebsitePitchTier.NO_SITE

    audit = _audit_from_lead(lead)
    if not audit:
        return WebsitePitchTier.MODERN

    score, mobile, ssl = _audit_scores(audit)
    if score >= PROFESSIONAL_DESIGN_MIN and mobile and ssl:
        return WebsitePitchTier.MODERN
    if score < OUTDATED_DESIGN_MAX or not mobile or not ssl:
        return WebsitePitchTier.OUTDATED
    return WebsitePitchTier.OUTDATED


def service_offer_for_lead(lead: MapsScanResult) -> ServiceOffer:
    tier = website_pitch_tier(lead)
    mode = _hunt_mode(lead)

    if _is_youtube_lead(lead) or mode == "m06_youtube":
        return ServiceOffer.YOUTUBE

    if _is_real_estate(lead):
        return ServiceOffer.AUTOMATION

    if mode in ("m11_linkedin_jobs", "m05_job_board", "m24_chatbot"):
        return ServiceOffer.AUTOMATION

    if mode == "m10_no_website":
        return ServiceOffer.WEBSITE

    if mode == "m02_outdated":
        if tier == WebsitePitchTier.MODERN:
            return ServiceOffer.AUTOMATION
        return ServiceOffer.WEBSITE

    if tier == WebsitePitchTier.MODERN:
        return ServiceOffer.AUTOMATION
    return ServiceOffer.WEBSITE


def resolve_pitch_plan(lead: MapsScanResult) -> PitchPlan:
    tier = website_pitch_tier(lead)
    service = service_offer_for_lead(lead)

    if service == ServiceOffer.YOUTUBE:
        problem = "YouTube channel not fully optimized for search, thumbnails, and off-platform leads"
        label = "YouTube channel audit + optimization (Method 06)"
    elif service == ServiceOffer.WEBSITE:
        if tier == WebsitePitchTier.NO_SITE:
            problem = "no website — enquiries likely phone-only"
            label = "Modern website + lead capture (Method 10)"
        else:
            problem = "outdated or weak mobile site — losing visitors"
            label = "Website rebuild + mobile + lead capture (Method 02)"
    else:
        problem = "no AI chat, booking, or automated follow-up on a decent site"
        label = "AI chatbot + lead automation + online booking (Method 24)"

    return PitchPlan(
        service=service,
        tier=tier,
        problem_detected=problem,
        service_label=label,
    )


async def ensure_website_audit(lead: MapsScanResult, settings: Any) -> None:
    from utils.platform_domains import is_platform_url

    if _is_youtube_lead(lead):
        return
    if not lead_has_website(lead) or not lead.website_url:
        return
    if is_platform_url(lead.website_url):
        return
    if _audit_from_lead(lead):
        return

    from modules.lead_finder.scanners.outdated_site import OutdatedSiteScanner

    scanner = OutdatedSiteScanner(settings)
    audit = await scanner.audit_url(
        lead.website_url,
        business_name=lead.business_name,
        niche=lead.niche,
        location=lead.city,
    )
    if audit:
        from utils.json_safe import to_jsonable

        lead.raw = {
            **(lead.raw or {}),
            "outdated_audit": to_jsonable(audit),
        }


def cache_pitch_on_lead(lead: MapsScanResult) -> PitchPlan:
    plan = resolve_pitch_plan(lead)
    lead.raw = {
        **(lead.raw or {}),
        "website_pitch_tier": plan.tier.value,
        "service_to_pitch": plan.service.value,
        "service_pitch_label": plan.service_label,
        "problem_detected": plan.problem_detected,
    }
    return plan


# --- Email copy (professional, blueprint-aligned) ---

_AUTOMATION_OFFERS = (
    (
        "I set up an AI chat widget on your existing site so visitors get instant answers "
        "and qualified leads — 24/7, even when you're on a job."
    ),
    (
        "I add automated lead capture and follow-up on top of your current site so "
        "after-hours enquiries don't sit in voicemail."
    ),
    (
        "I wire online booking and appointment reminders into your site so customers "
        "can schedule without phone tag."
    ),
)

_OFFER_WEBSITE_NO_SITE = (
    "I build modern, mobile-friendly sites with built-in lead capture — so new customers "
    "can find you online and reach you after hours, not only by phone."
)

_OFFER_WEBSITE_OUTDATED = (
    "I rebuild dated local business sites — secure, mobile-first, and built to turn "
    "visitors into enquiries instead of bounce-offs."
)

_OFFER_AUTOMATION_SUFFIX = (
    "Your site already works — this is about not losing leads after they land on it."
)

_OFFER_YOUTUBE = (
    "I audit and optimize YouTube channels — titles, thumbnails, descriptions, and a "
    "simple landing page so viewers who want to hire or buy can reach you off-platform."
)

_REAL_ESTATE_OFFER = (
    "I build AI systems that instantly respond, qualify, and follow up with every inbound "
    "lead automatically — so no one slips through while your team is heads-down."
)


def offer_line(lead: MapsScanResult, plan: PitchPlan | None = None) -> str:
    p = plan or resolve_pitch_plan(lead)
    if _is_real_estate(lead):
        return _REAL_ESTATE_OFFER
    if p.service == ServiceOffer.YOUTUBE:
        return _OFFER_YOUTUBE
    if p.service == ServiceOffer.WEBSITE:
        if p.tier == WebsitePitchTier.NO_SITE:
            return _OFFER_WEBSITE_NO_SITE
        return _OFFER_WEBSITE_OUTDATED
    digest = hashlib.sha256(lead.place_id.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(_AUTOMATION_OFFERS)
    return f"{_AUTOMATION_OFFERS[idx]} {_OFFER_AUTOMATION_SUFFIX}"


def demo_intro_line(lead: MapsScanResult, plan: PitchPlan | None = None) -> str:
    p = plan or resolve_pitch_plan(lead)
    if p.service == ServiceOffer.YOUTUBE:
        return "I put together a quick brand landing page preview if you want a look:"
    if p.service == ServiceOffer.WEBSITE:
        return "I put together a quick site preview if you want a look:"
    return "I put together a quick preview of the chat / booking flow on your site:"


def cta_line(lead: MapsScanResult, company: str, plan: PitchPlan | None = None) -> str:
    p = plan or resolve_pitch_plan(lead)
    if p.service == ServiceOffer.YOUTUBE:
        return (
            f"Would a channel audit plus a simple landing page for {company} "
            f"be useful right now?"
        )
    if p.service == ServiceOffer.WEBSITE:
        if p.tier == WebsitePitchTier.NO_SITE:
            return f"Would getting {company} online with lead capture be useful right now?"
        return f"Would a refreshed, mobile-friendly site be useful for {company} right now?"
    return (
        f"Would adding chat, automated follow-up, or online booking be useful for "
        f"{company} right now?"
    )


def fallback_icebreaker_for_plan(lead: MapsScanResult, plan: PitchPlan) -> str:
    from modules.outreach.icebreaker import company_name, icebreaker_subject

    biz = company_name(lead)
    site = icebreaker_subject(lead)
    niche = lead.niche.lower().replace("_", " ")
    city = lead.city.split(",")[0].strip()

    if plan.service == ServiceOffer.YOUTUBE:
        return (
            f"Saw {biz} on YouTube in the {niche} space around {city} — strong content, "
            f"but the channel page and description likely aren't pulling in as many "
            f"off-platform enquiries as they could."
        )

    if plan.tier == WebsitePitchTier.NO_SITE:
        return (
            f"Saw {biz} doesn't have a website yet — common for busy {niche} shops in {city}. "
            f"But that usually means new enquiries still go straight to the phone with nothing "
            f"capturing after hours."
        )

    if plan.service == ServiceOffer.WEBSITE:
        audit = _audit_from_lead(lead)
        detail = "looks dated or weak on mobile"
        if audit:
            score, mobile, ssl = _audit_scores(audit)
            if not ssl:
                detail = "still isn't on secure HTTPS"
            elif not mobile:
                detail = "isn't really mobile-friendly"
            elif score < OUTDATED_DESIGN_MAX:
                detail = "looks like an older template"
        return (
            f"Saw {site} — {detail} for a {niche} business today. "
            f"You're likely losing visitors who never call or fill out a form."
        )

    return (
        f"Saw {biz} already has a solid site at {site}. "
        f"But there's no AI chat, online booking, or automated follow-up when someone reaches out."
    )


# Back-compat aliases
def website_pitch_tier_cached(lead: MapsScanResult) -> WebsitePitchTier:
    return website_pitch_tier(lead)


def cache_pitch_tier_on_lead(lead: MapsScanResult) -> WebsitePitchTier:
    return cache_pitch_on_lead(lead).tier


def fallback_icebreaker_for_tier(lead: MapsScanResult, tier: WebsitePitchTier) -> str:
    plan = resolve_pitch_plan(lead)
    return fallback_icebreaker_for_plan(lead, plan)
