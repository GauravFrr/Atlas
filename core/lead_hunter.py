"""
Autonomous lead hunting — agent finds prospects itself (no CSV required).

Rotates hunt modes each run:
  - no_website: Google Maps / OSM (free)
  - outdated: businesses with old websites (SSL/mobile checks)
  - low_reviews: ≤3.5 stars (Google Places API)
  - apollo: B2B emails (APOLLO_API_KEY)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config import Settings
from core.campaign_orchestrator import CampaignResult, run_campaign
from core.lead_sources import (
    PRODUCTION_HUNT_MODES,
    available_hunt_modes,
    hunt_mode_label,
    normalize_mode,
    pick_hunt_mode,
)


_TARGETS_CACHE: list[dict[str, str]] | None = None


def _extra_list(raw: str) -> list[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


def all_hunt_targets() -> list[dict[str, str]]:
    """
    Every niche × city combo, in a stable interleaved order so consecutive
    cycles hit different cities and niches (not 100 niches of NYC in a row).
    Extend via HUNT_EXTRA_NICHES / HUNT_EXTRA_CITIES env vars.
    """
    global _TARGETS_CACHE
    if _TARGETS_CACHE is not None:
        return _TARGETS_CACHE

    from modules.lead_finder.scanners.google_maps import PRIORITY_NICHES, TARGET_CITIES

    niches = list(PRIORITY_NICHES)
    cities = list(TARGET_CITIES)
    try:
        from config import get_settings

        settings = get_settings()
        niches += [n for n in _extra_list(getattr(settings, "hunt_extra_niches", "")) if n not in niches]
        cities += [c for c in _extra_list(getattr(settings, "hunt_extra_cities", "")) if c not in cities]
    except Exception:
        pass

    pairs: list[dict[str, str]] = []
    for city in cities:
        for niche in niches:
            pairs.append({"niche": niche, "city": city})

    # Deterministic shuffle: stable across restarts (rotation_index stays valid)
    # but consecutive indexes vary both market and niche.
    import random

    random.Random(42).shuffle(pairs)
    _TARGETS_CACHE = pairs
    return pairs


def pick_next_target(rotation_index: int) -> tuple[dict[str, str], int]:
    targets = all_hunt_targets()
    if not targets:
        return {"niche": "plumber", "city": "Austin TX"}, 0
    idx = rotation_index % len(targets)
    return targets[idx], idx


async def hunt_and_outreach(
    settings: Settings,
    *,
    leads: int,
    send_mode: str,
    rotation_index: int,
    source_index: int = 0,
    max_attempts: int = 8,
) -> tuple[CampaignResult | None, dict[str, Any]]:
    meta: dict[str, Any] = {"attempts": []}
    targets = all_hunt_targets()
    idx = rotation_index

    modes = available_hunt_modes(settings)
    meta["available_modes"] = modes

    scan = (settings.lead_scan_source or "auto").lower()
    has_google = bool(settings.google_places_api_key)
    logger.info(
        f"[Hunter] scan_source={scan} google_places={'yes' if has_google else 'no'} "
        f"→ {len(targets)} markets, {len(modes)} hunt modes, target={leads} leads/run"
    )
    if len(modes) == 1:
        prod = ",".join(PRODUCTION_HUNT_MODES)
        logger.warning(
            f"[Hunter] Only 1 hunt mode active ({modes[0]}). "
            f"Delete AUTOPILOT_HUNT_MODES on Railway to use all {len(PRODUCTION_HUNT_MODES)} "
            f"production modes, or set: {prod}"
        )
    if scan == "google" and not settings.google_places_api_key:
        target, _ = pick_next_target(idx)
        meta["blocked"] = "google_places_api_key"
        meta["would_hunt"] = f"{target['niche']} @ {target['city']}"
        return None, meta

    settings.demo_generation_mode = settings.demo_generation_mode or "safe"

    for attempt in range(max_attempts):
        hunt_mode, _ = pick_hunt_mode(source_index + attempt, settings)
        meta["hunt_mode"] = hunt_mode
        meta["hunt_mode_label"] = hunt_mode_label(hunt_mode)
        target, idx = pick_next_target(idx)
        niche = target["niche"]
        city = target["city"]
        logger.info(
            f"[Hunter] {hunt_mode_label(hunt_mode)} → {niche} @ {city} (up to {leads} leads)"
        )

        try:
            result = await run_campaign(
                niche=niche,
                city=city,
                leads=leads,
                send_mode=send_mode,
                settings=settings,
                hunt_mode=hunt_mode,
            )
            # M10 (no website) often returns 0 in US/UK — same market, outdated sites.
            if (
                hunt_mode == "m10_no_website"
                and result.leads_processed == 0
                and result.emails_sent == 0
            ):
                logger.info(
                    f"[Hunter] M10 empty for {niche} @ {city} — retry with M02 outdated"
                )
                result = await run_campaign(
                    niche=niche,
                    city=city,
                    leads=leads,
                    send_mode=send_mode,
                    settings=settings,
                    hunt_mode="m02_outdated",
                )
                meta["hunt_mode"] = "m02_outdated"
                meta["hunt_mode_label"] = hunt_mode_label("m02_outdated")
        except Exception as e:
            logger.error(f"[Hunter] Campaign failed {niche}@{city}: {e}")
            meta["attempts"].append(
                {"niche": niche, "city": city, "hunt_mode": hunt_mode, "error": str(e)}
            )
            idx = (idx + 1) % len(targets)
            continue

        meta["attempts"].append(
            {
                "niche": niche,
                "city": city,
                "hunt_mode": hunt_mode,
                "scan_source": result.scan_source,
                "processed": result.leads_processed,
                "sent": result.emails_sent,
            }
        )
        meta["rotation_index"] = (idx + 1) % len(targets)
        meta["source_index"] = (source_index + 1) % max(len(modes), 1)
        meta["niche"] = niche
        meta["city"] = city

        if result.leads_processed > 0 or result.emails_sent > 0:
            return result, meta

        logger.info(f"[Hunter] No new leads — next market (mode={hunt_mode})")
        idx = (idx + 1) % len(targets)

    meta["rotation_index"] = idx % len(targets)
    meta["source_index"] = (source_index + 1) % max(len(modes), 1)
    return None, meta
