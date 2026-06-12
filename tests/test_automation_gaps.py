"""Niche-aware automation gap detection (AI chat, booking, ordering)."""

from utils.automation_gaps import (
    detect_automation_gaps,
    has_any_automation,
    missing_category,
    niche_automation_needs,
    problem_line_for_gaps,
)


def test_restaurant_needs_ordering() -> None:
    needs = niche_automation_needs("restaurant")
    assert "ordering" in needs
    assert "ai_chat" in needs


def test_salon_needs_booking() -> None:
    needs = niche_automation_needs("hair salon")
    assert "booking" in needs


def test_detect_gaps_on_plain_site() -> None:
    html = "<html><body>Welcome to Joe's Pizza. Call us!</body></html>"
    gaps = detect_automation_gaps(html, "restaurant")
    assert "ordering" in gaps["automation_missing"]
    assert gaps["automation_primary"] == "ordering"


def test_detect_calendly_present() -> None:
    html = '<script src="https://assets.calendly.com/assets/external/widget.js"></script>'
    assert not missing_category(html, "booking")
    assert has_any_automation(html)


def test_problem_line_for_booking() -> None:
    line = problem_line_for_gaps({"automation_primary": "booking"}, "dentist")
    assert "booking" in line.lower()


def test_ai_chatbot_detected() -> None:
    html = '<script src="https://embed.tawk.to/abc123/default"></script>'
    gaps = detect_automation_gaps(html, "plumber")
    assert "ai_chat" not in gaps["automation_missing"]


def test_customer_support_gap_on_plain_site() -> None:
    html = "<html><body>Contact us by phone only.</body></html>"
    gaps = detect_automation_gaps(html, "insurance agent")
    assert "customer_support" in gaps["automation_missing"]


def test_zendesk_counts_as_customer_support() -> None:
    html = '<script src="https://static.zdassets.com/ekr/snippet.js"></script>'
    assert not missing_category(html, "customer_support")
