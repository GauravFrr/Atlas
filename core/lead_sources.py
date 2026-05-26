"""
All Category A lead-hunting methods (01–17) from docs/AGENT_EARNING_METHODS.md.
Autopilot rotates through every mode each cycle.
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
}


def normalize_mode(mode_id: str) -> str:
    m = (mode_id or "m10_no_website").lower().strip()
    return MODE_ALIASES.get(m, m)


def all_hunt_mode_ids() -> list[str]:
    return [mid for mid, _ in HUNT_MODES]


def available_hunt_modes(settings: Settings) -> list[str]:
    """All 17 doc methods — always rotate (some may return 0 leads without API keys)."""
    _ = settings
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
