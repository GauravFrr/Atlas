"""
Mock lead generator — test the full campaign pipeline without Google Places API.

Use when billing is disabled or for local development:
  python scripts/run_campaign.py --mock --niche plumber --city "Austin TX" --leads 3
"""

from __future__ import annotations

import re

from modules.lead_finder.scanners.google_maps import MapsScanResult


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())[:24]


# Realistic sample businesses per niche (no website, local service)
_MOCK_BUSINESSES: dict[str, list[tuple[str, str | None, str]]] = {
    # (business_name_suffix, email_or_none, phone)
    "plumber": [
        ("Precision Plumbing", "owner@precisionplumbing.local", "(512) 555-0101"),
        ("Lone Star Drain & Pipe", "hello@lonestardrain.local", "(512) 555-0102"),
        ("Capitol City Plumbing Co", None, "(512) 555-0103"),
        ("24/7 Emergency Plumbers", "dispatch@247plumbers.local", "(512) 555-0104"),
        ("Austin Pipe Masters", None, "(512) 555-0105"),
    ],
    "dentist": [
        ("Smile Studio Dental", "frontdesk@smilestudio.local", "(512) 555-0201"),
        ("Family Dental Care", None, "(512) 555-0202"),
        ("Downtown Dental Group", "info@downtowndental.local", "(512) 555-0203"),
    ],
    "electrician": [
        ("Bright Wire Electric", "jobs@brightwire.local", "(512) 555-0301"),
        ("Austin Power Pros", None, "(512) 555-0302"),
        ("Safe Volt Services", "contact@safevolt.local", "(512) 555-0303"),
    ],
    "default": [
        ("Local Pro Services", "contact@localpro.local", "(512) 555-0991"),
        ("City Business Solutions", None, "(512) 555-0992"),
        ("Main Street Experts", "hello@mainstreet.local", "(512) 555-0993"),
    ],
}


def mock_place_id_prefix(niche: str, city: str) -> str:
    """Stable prefix for mock place_ids (used for memory-bank reset)."""
    return f"ChIJmock_{_slug(niche)}_{_slug(city)}_"


def generate_mock_leads(
    niche: str,
    city: str,
    count: int,
) -> list[MapsScanResult]:
    """
    Build fake MapsScanResult rows — same shape as a real Google Maps scan.
    place_id values are stable so re-running tests memory-bank deduplication.
    """
    niche_key = niche.lower().strip()
    templates = _MOCK_BUSINESSES.get(niche_key, _MOCK_BUSINESSES["default"])

    leads: list[MapsScanResult] = []
    for i in range(count):
        name_suffix, base_email, phone = templates[i % len(templates)]
        business_name = f"{city.split()[0]} {name_suffix}"
        place_id = f"{mock_place_id_prefix(niche_key, city)}{i:03d}"

        # Unique email per lead (templates repeat when count > len(templates))
        email = _unique_mock_email(base_email, place_id)

        leads.append(
            MapsScanResult(
                place_id=place_id,
                business_name=business_name,
                niche=niche,
                city=city,
                country="US",
                address=f"{100 + i} Main St, {city}",
                phone=phone,
                email=email,
                has_website=False,
                website_url=None,
                rating=4.2 + (i % 3) * 0.2,
                review_count=12 + i * 7,
            )
        )

    return leads


def override_emails_for_test(leads: list[MapsScanResult], test_to: str) -> None:
    """Route all mock leads to one inbox (Gmail +tags) for end-to-end testing."""
    test_to = test_to.strip()
    if "@" not in test_to:
        raise ValueError(f"Invalid --test-to address: {test_to}")
    local, _, domain = test_to.partition("@")
    for lead in leads:
        tag = lead.place_id.replace("ChIJmock_", "").replace("_", "")[:20]
        lead.email = f"{local}+mock{tag}@{domain}"


def _unique_mock_email(base: str | None, place_id: str) -> str | None:
    """Derive a unique inbox per mock lead so DB email uniqueness never collides."""
    if not base:
        return None
    local, _, domain = base.partition("@")
    if not domain:
        return base
    tag = place_id.replace("ChIJmock_", "").replace("_", "")[:24]
    return f"{local}+{tag}@{domain}"
