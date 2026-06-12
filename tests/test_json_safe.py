"""JSON-safe enrichment serialization."""

from modules.lead_finder.scanners.outdated_site import OutdatedSiteResult
from utils.json_safe import to_jsonable
from utils.lead_package_tier import sync_maps_enrichment


def test_outdated_audit_serializes_for_postgres() -> None:
    audit = OutdatedSiteResult(
        domain="example.com",
        business_name="Test Biz",
        location="LA",
        niche="nail",
        has_ssl=False,
        is_mobile_friendly=False,
        design_score=3.5,
        page_speed_score=0.0,
        contact_email=None,
    )
    payload = to_jsonable(audit)
    assert payload["domain"] == "example.com"
    assert isinstance(payload["design_score"], float)

    class Lead:
        enrichment_data = {}

    class Maps:
        raw = {"outdated_audit": audit, "hunt_mode": "m01_broken_link"}
        has_website = True
        website_url = "https://example.com"

    lead = Lead()
    sync_maps_enrichment(lead, Maps())
    assert isinstance(lead.enrichment_data["website_audit"], dict)
