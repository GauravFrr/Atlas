"""
Method 10b — OpenStreetMap business scanner (FREE, no API key).

Same pipeline as Google Maps: find local businesses → demo → Instantly.
Uses Nominatim (geocode) + Overpass API. Respect OSM usage policy (low rate).
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
from loguru import logger

from modules.lead_finder.scanners.google_maps import MapsScanResult

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
PHOTON_URL = "https://photon.komoot.io/api/"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _user_agent(settings: Any = None) -> str:
    email = ""
    if settings:
        email = (
            getattr(settings, "your_email", "")
            or getattr(settings, "gmail_sender_address", "")
            or ""
        ).strip()
    if email:
        return f"Agent-Earns/1.0 (+mailto:{email})"
    return "Agent-Earns/1.0 (autonomous-local-outreach)"


# Approx bbox (south, west, north, east) when geocoders rate-limit
CITY_BBOX_FALLBACK: dict[str, tuple[float, float, float, float]] = {
    "austin tx": (30.05, -97.95, 30.45, -97.55),
    "dallas tx": (32.65, -97.05, 33.05, -96.55),
    "houston tx": (29.55, -95.65, 30.05, -95.05),
    "chicago il": (41.64, -87.95, 42.02, -87.52),
    "new york ny": (40.48, -74.26, 40.92, -73.70),
    "los angeles ca": (33.70, -118.65, 34.35, -118.05),
    "london uk": (51.28, -0.51, 51.69, 0.33),
    "denver co": (39.61, -105.11, 39.91, -104.71),
    "seattle wa": (47.49, -122.45, 47.73, -122.22),
    "miami fl": (25.70, -80.35, 25.95, -80.10),
}

# niche keyword → Overpass filter fragments (OR-combined in query)
NICHE_OSM_FILTERS: dict[str, list[str]] = {
    "plumber": ['craft="plumber"', 'shop="plumber"'],
    "electrician": ['craft="electrician"'],
    "hvac": ['craft="hvac"'],
    "roofer": ['craft="roofer"'],
    "landscaper": ['craft="gardener"', 'shop="garden_centre"'],
    "dentist": ['amenity="dentist"'],
    "chiropractor": ['healthcare="chiropractor"'],
    "optometrist": ['healthcare="optometrist"'],
    "physical therapy": ['healthcare="physiotherapist"'],
    "restaurant": ['amenity="restaurant"'],
    "cafe": ['amenity="cafe"'],
    "bakery": ['shop="bakery"'],
    "food truck": ['amenity="fast_food"'],
    "lawyer": ['office="lawyer"'],
    "accountant": ['office="accountant"'],
    "insurance agent": ['office="insurance"'],
    "hair salon": ['shop="hairdresser"'],
    "nail salon": ['shop="beauty"'],
    "barber": ['shop="barber"'],
    "gym": ['leisure="fitness_centre"'],
    "personal trainer": ['leisure="fitness_centre"'],
    "yoga studio": ['leisure="sports_centre"'],
    "real estate agent": ['office="estate_agent"'],
    "property management": ['office="estate_agent"'],
    "auto repair": ['shop="car_repair"'],
    "car wash": ['amenity="car_wash"'],
    "mechanic": ['shop="car_repair"'],
    "cleaning service": ['shop="cleaning"'],
    "pest control": ['craft="pest_control"'],
    "locksmith": ['craft="locksmith"'],
}


def _niche_filters(niche: str) -> list[str]:
    key = niche.lower().strip()
    if key in NICHE_OSM_FILTERS:
        return NICHE_OSM_FILTERS[key]
    safe = re.sub(r'[^a-z0-9 ]', '', key)
    if not safe:
        safe = "business"
    return [f'name~"{safe}",i']


def _fallback_bbox(city: str) -> tuple[float, float, float, float] | None:
    key = city.lower().strip()
    if key in CITY_BBOX_FALLBACK:
        return CITY_BBOX_FALLBACK[key]
    for name, bbox in CITY_BBOX_FALLBACK.items():
        if name in key or key in name:
            return bbox
    return None


async def _geocode_photon(
    client: httpx.AsyncClient, city: str, headers: dict[str, str]
) -> tuple[float, float, float, float] | None:
    resp = await client.get(
        PHOTON_URL,
        params={"q": city, "limit": 1},
        headers=headers,
    )
    if resp.status_code != 200:
        return None
    features = resp.json().get("features") or []
    if not features:
        return None
    coords = features[0].get("geometry", {}).get("coordinates") or []
    if len(coords) >= 2:
        lon, lat = float(coords[0]), float(coords[1])
        pad = 0.12
        return lat - pad, lon - pad, lat + pad, lon + pad
    extent = features[0].get("properties", {}).get("extent")
    if extent and len(extent) >= 4:
        west, south, east, north = map(float, extent[:4])
        return south, west, north, east
    return None


async def _geocode_bbox(
    client: httpx.AsyncClient, city: str, settings: Any = None
) -> tuple[float, float, float, float] | None:
    """Return south, west, north, east for Overpass."""
    headers = {"User-Agent": _user_agent(settings)}

    bbox = await _geocode_photon(client, city, headers)
    if bbox:
        return bbox

    await asyncio.sleep(1.1)
    try:
        resp = await client.get(
            NOMINATIM_URL,
            params={"q": city, "format": "json", "limit": 1},
            headers=headers,
        )
        if resp.status_code == 200:
            rows = resp.json()
            if rows:
                bb = rows[0].get("boundingbox")
                if bb and len(bb) >= 4:
                    south, north, west, east = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
                    return south, west, north, east
                lat = float(rows[0].get("lat", 0))
                lon = float(rows[0].get("lon", 0))
                pad = 0.08
                return lat - pad, lon - pad, lat + pad, lon + pad
    except Exception as e:
        logger.debug(f"[OSM] Nominatim skipped: {e}")

    fb = _fallback_bbox(city)
    if fb:
        logger.info(f"[OSM] Using built-in bbox for {city}")
        return fb

    logger.warning(f"[OSM] Could not geocode '{city}'")
    return None


def _tags(element: dict[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in (element.get("tags") or {}).items()}


def _element_to_lead(
    element: dict[str, Any],
    *,
    niche: str,
    city: str,
    no_website_only: bool,
) -> MapsScanResult | None:
    tags = _tags(element)
    name = tags.get("name") or tags.get("brand")
    if not name:
        return None

    website = tags.get("website") or tags.get("contact:website")
    has_website = bool(website and website.startswith("http"))
    if no_website_only and has_website:
        return None

    osm_type = element.get("type", "node")
    osm_id = element.get("id", 0)
    place_id = f"osm/{osm_type}/{osm_id}"

    lat = element.get("lat") or (element.get("center") or {}).get("lat")
    lon = element.get("lon") or (element.get("center") or {}).get("lon")
    addr_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city") or city,
        tags.get("addr:state"),
        tags.get("addr:postcode"),
    ]
    address = ", ".join(p for p in addr_parts if p) or city

    phone = tags.get("phone") or tags.get("contact:phone")
    email = tags.get("email") or tags.get("contact:email")

    return MapsScanResult(
        place_id=place_id,
        business_name=name,
        niche=niche,
        city=city,
        country=tags.get("addr:country", ""),
        address=address,
        phone=phone,
        email=email,
        has_website=has_website,
        website_url=website if has_website else None,
        rating=None,
        review_count=0,
        raw={"osm": element, "lat": lat, "lon": lon},
    )


class OSMMapsScanner:
    """
    Free local business discovery via OpenStreetMap (no Google billing).
    """

    def __init__(self, settings: Any = None) -> None:
        self.settings = settings

    async def scan(
        self,
        niche: str,
        city: str,
        limit: int = 50,
        no_website_only: bool = True,
    ) -> list[MapsScanResult]:
        logger.info(f"[OSM] Scanning {niche} @ {city} (limit={limit}, free)")
        filters = _niche_filters(niche)

        headers = {"User-Agent": _user_agent(self.settings)}

        async with httpx.AsyncClient(timeout=60.0) as client:
            bbox = await _geocode_bbox(client, city, self.settings)
            if not bbox:
                return []

            south, west, north, east = bbox
            filter_lines = "\n      ".join(
                f'node[{f}]({south},{west},{north},{east});' for f in filters
            )
            filter_lines += "\n      " + "\n      ".join(
                f'way[{f}]({south},{west},{north},{east});' for f in filters
            )

            query = f"""
            [out:json][timeout:45];
            (
              {filter_lines}
            );
            out center {min(limit * 3, 120)};
            """

            try:
                resp = await client.post(
                    OVERPASS_URL,
                    data={"data": query},
                    headers=headers,
                )
            except Exception as e:
                logger.error(f"[OSM] Overpass request failed: {e}")
                return []

            if resp.status_code != 200:
                logger.error(f"[OSM] Overpass HTTP {resp.status_code}: {resp.text[:300]}")
                return []

            data = resp.json()
            elements = data.get("elements", [])

        leads: list[MapsScanResult] = []
        seen: set[str] = set()
        skipped_website = 0
        skipped_unnamed = 0
        for el in elements:
            tags = _tags(el)
            name = tags.get("name") or tags.get("brand")
            if not name:
                skipped_unnamed += 1
                continue
            website = tags.get("website") or tags.get("contact:website")
            if no_website_only and website and str(website).startswith("http"):
                skipped_website += 1
                continue
            lead = _element_to_lead(el, niche=niche, city=city, no_website_only=no_website_only)
            if not lead or lead.place_id in seen:
                continue
            seen.add(lead.place_id)
            leads.append(lead)
            if len(leads) >= limit:
                break

        if no_website_only and elements and not leads:
            logger.warning(
                f"[OSM] {len(elements)} businesses in bbox but 0 without website "
                f"({skipped_website} have website). Try --hunt-mode m02_outdated"
            )
        logger.info(
            f"[OSM] Found {len(leads)} leads for {niche} @ {city} "
            f"(raw={len(elements)}, skipped_website={skipped_website})"
        )
        return leads
