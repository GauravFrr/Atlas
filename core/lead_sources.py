"""
All Category A lead-hunting methods (01–17) from docs/AGENT_EARNING_METHODS.md.
Autopilot rotates through enabled modes each cycle.
"""

from __future__ import annotations

from config import Settings

# hunt_mode_id → dashboard label (matches doc methods)
HUNT_MODES: list[tuple[str, str]] = [
    ("m01_broken_link", "M01 Broken link outreach"),
    ("m02_outdated", "M02 Outdated website"),
    ("m03_reddit", "M03 Reddit / forum mining"),
    ("m04_low_reviews", "M04 Low Google reviews"),
    ("m05_job_board", "M05 Job board scraper"),
    ("m06_youtube", "M06 YouTube channel audit"),
    ("m07_app_review", "M07 App store reviews"),
    ("m08_etsy_amazon", "M08 Etsy / Amazon listings"),
    ("m09_social_dm", "M09 Social DM targets"),
    ("m10_no_website", "M10 Local directory (no website)"),
    ("m11_linkedin_jobs", "M11 LinkedIn job monitor"),
    ("m12_producthunt", "M12 ProductHunt launches"),
    ("m13_forum", "M13 Quora / forum answers"),
    ("m14_saas_churn", "M14 SaaS churn / onboarding"),
    ("m15_shopify", "M15 Shopify store audit"),
    ("m16_podcast", "M16 Podcast guest outreach"),
    ("m17_apollo", "M17 Apollo cold email"),
    ("m24_chatbot", "M24 Missing AI chat / automation for niche"),
    ("m25_social_only", "M25 Social-page-only business (website)"),
    ("m26_new_business", "M26 New business, no presence (website)"),
    ("m27_no_booking", "M27 No online booking (salon, clinic, gym…)"),
    ("m28_no_ordering", "M28 No online ordering (restaurant, cafe…)"),
]

# Production default — local businesses / sites where email enrichment works.
# Ordered website-first, automation second (core offers), volume modes interleaved.
PRODUCTION_HUNT_MODES: list[str] = [
    "m02_outdated",       # website rebuild
    "m24_chatbot",        # AI chatbot + niche automation gaps
    "m27_no_booking",     # appointment booking missing
    "m28_no_ordering",    # online ordering missing
    "m25_social_only",    # website: only FB/Insta page
    "m10_no_website",     # website: no site at all
    "m04_low_reviews",    # reputation + website
    "m26_new_business",   # website: brand-new business
    "m03_reddit",         # Reddit: need dev / chatbot / SaaS
    "m05_job_board",      # hiring → pitch automation instead
    "m01_broken_link",    # website fix → rebuild
    "m17_apollo",         # B2B cold email
    "m15_shopify",        # store audit
    "m06_youtube",        # channel audit
]

# Aliases for older state files
MODE_ALIASES: dict[str, str] = {
    "no_website": "m10_no_website",
    "outdated": "m02_outdated",
    "low_reviews": "m04_low_reviews",
    "apollo": "m17_apollo",
    "broken_link": "m01_broken_link",
    "reddit": "m03_reddit",
    "job_board": "m05_job_board",
    "youtube": "m06_youtube",
    "app_review": "m07_app_review",
    "etsy_amazon": "m08_etsy_amazon",
    "social_dm": "m09_social_dm",
    "linkedin_jobs": "m11_linkedin_jobs",
    "producthunt": "m12_producthunt",
    "forum": "m13_forum",
    "saas_churn": "m14_saas_churn",
    "shopify": "m15_shopify",
    "podcast": "m16_podcast",
    "chatbot": "m24_chatbot",
    "social_only": "m25_social_only",
    "new_business": "m26_new_business",
    "no_booking": "m27_no_booking",
    "no_ordering": "m28_no_ordering",
}


def normalize_mode(mode_id: str) -> str:
    m = (mode_id or "m10_no_website").lower().strip()
    return MODE_ALIASES.get(m, m)


def all_hunt_mode_ids() -> list[str]:
    return [mid for mid, _ in HUNT_MODES]


def _parse_mode_list(raw: str) -> list[str]:
    out: list[str] = []
    for part in (raw or "").split(","):
        mode = normalize_mode(part.strip())
        if mode and mode in all_hunt_mode_ids() and mode not in out:
            out.append(mode)
    return out


def available_hunt_modes(settings: Settings) -> list[str]:
    """
    Modes Atlas rotates through.
    Production default skips M07 (App Store apps) and other low-email hunters.
    Override with AUTOPILOT_HUNT_MODES=m10_no_website,m02_outdated,...
    """
    explicit = _parse_mode_list(getattr(settings, "autopilot_hunt_modes", "") or "")
    if explicit:
        return explicit
    if getattr(settings, "is_production", False):
        return list(PRODUCTION_HUNT_MODES)
    return all_hunt_mode_ids()


def pick_hunt_mode(source_index: int, settings: Settings) -> tuple[str, int]:
    modes = available_hunt_modes(settings)
    idx = source_index % len(modes)
    return modes[idx], idx


def hunt_mode_label(mode_id: str) -> str:
    mode_id = normalize_mode(mode_id)
    for mid, label in HUNT_MODES:
        if mid == mode_id:
            return label
    return mode_id
