"""Hunt modes M24/M25/M26 — website & automation lead scanners."""

from types import SimpleNamespace

import pytest

from modules.lead_finder.scanners.google_maps import MapsScanResult
from modules.lead_finder.scanners.website_automation import (
    NewBusinessScanner,
    NoAutomationScanner,
    SocialOnlyScanner,
)


def _maps(name: str, website: str | None, reviews: int = 10) -> MapsScanResult:
    return MapsScanResult(
        place_id=f"test/{name}",
        business_name=name,
        niche="plumber",
        city="Austin TX",
        country="US",
        address="Austin TX",
        phone=None,
        email=None,
        has_website=bool(website),
        website_url=website,
        rating=4.0,
        review_count=reviews,
    )


def _scan_fn(leads):
    async def fn(niche, city, limit, *, no_website_only=True):
        return list(leads), "google_maps"

    return fn


@pytest.mark.asyncio
async def test_social_only_keeps_platform_urls() -> None:
    leads = [
        _maps("FB Only Biz", "https://www.facebook.com/fbonlybiz"),
        _maps("Real Site Biz", "https://realsite.com"),
        _maps("Linktree Biz", "https://linktr.ee/somebiz"),
    ]
    out = await SocialOnlyScanner(SimpleNamespace()).scan_maps(
        "plumber", "Austin TX", 10, _scan_fn(leads)
    )
    names = [lead.business_name for lead in out]
    assert names == ["FB Only Biz", "Linktree Biz"]
    assert all(not lead.has_website for lead in out)
    assert all(lead.raw["hunt_mode"] == "m25_social_only" for lead in out)


@pytest.mark.asyncio
async def test_new_business_filters_by_reviews() -> None:
    leads = [
        _maps("Established", "https://old.com", reviews=120),
        _maps("Brand New", "https://new.com", reviews=1),
        _maps("No Reviews", None, reviews=0),
    ]
    out = await NewBusinessScanner(SimpleNamespace()).scan_maps(
        "plumber", "Austin TX", 10, _scan_fn(leads)
    )
    names = [lead.business_name for lead in out]
    assert names == ["Brand New", "No Reviews"]
    assert all(lead.raw["hunt_mode"] == "m26_new_business" for lead in out)


def test_automation_gap_detection() -> None:
    from utils.automation_gaps import detect_automation_gaps, has_any_automation

    has_tools = "<html><script src='https://widget.calendly.com/x.js'></script></html>"
    no_tools = "<html><body>Welcome to our plumbing site. Call us!</body></html>"
    assert has_any_automation(has_tools) is True
    gaps = detect_automation_gaps(no_tools, "plumber")
    assert gaps["automation_missing"]


def test_new_modes_registered() -> None:
    from core.lead_sources import PRODUCTION_HUNT_MODES, all_hunt_mode_ids, normalize_mode

    ids = all_hunt_mode_ids()
    for mode in (
        "m24_chatbot",
        "m25_social_only",
        "m26_new_business",
        "m27_no_booking",
        "m28_no_ordering",
        "m29_no_support",
        "m03_reddit",
        "m05_job_board",
    ):
        assert mode in ids
        assert mode in PRODUCTION_HUNT_MODES
    assert normalize_mode("social_only") == "m25_social_only"
    assert normalize_mode("chatbot") == "m24_chatbot"
    assert normalize_mode("no_booking") == "m27_no_booking"


def test_pitch_routing_for_new_modes() -> None:
    from modules.outreach.website_pitch import ServiceOffer, service_offer_for_lead

    social = _maps("FB Biz", None)
    social.raw = {"hunt_mode": "m25_social_only"}
    assert service_offer_for_lead(social) == ServiceOffer.WEBSITE

    chatbot = _maps("Modern Biz", "https://modern.com")
    chatbot.raw = {"hunt_mode": "m24_chatbot"}
    assert service_offer_for_lead(chatbot) == ServiceOffer.AUTOMATION

    newbiz = _maps("New Biz", None, reviews=0)
    newbiz.raw = {"hunt_mode": "m26_new_business"}
    assert service_offer_for_lead(newbiz) == ServiceOffer.WEBSITE

    booking = _maps("Salon", "https://salon.com")
    booking.raw = {"hunt_mode": "m27_no_booking", "automation_primary": "booking"}
    assert service_offer_for_lead(booking) == ServiceOffer.AUTOMATION

    ordering = _maps("Pizza", "https://pizza.com")
    ordering.raw = {"hunt_mode": "m28_no_ordering", "automation_primary": "ordering"}
    assert service_offer_for_lead(ordering) == ServiceOffer.AUTOMATION

    support = _maps("Shop", "https://shop.com")
    support.raw = {"hunt_mode": "m29_no_support", "automation_primary": "customer_support"}
    assert service_offer_for_lead(support) == ServiceOffer.AUTOMATION
