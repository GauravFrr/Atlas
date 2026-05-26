"""
Add a manual test lead + draft cold email (no demo site).

  python scripts/seed_test_lead_draft.py --email itzmi3xel@gmail.com
  python scripts/seed_test_lead_draft.py --email you@gmail.com --business "Test Plumbing"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_settings
from constants import LeadStatus
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from llm.router import LLMRouter
from modules.lead_finder.scanners.google_maps import MapsScanResult
from modules.outreach.cold_email import ColdEmailEngine


def _place_id_for_email(email: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in email.lower())
    return f"test_{safe}"[:120]


async def main() -> None:
    p = argparse.ArgumentParser(description="Seed test lead + draft email (no website)")
    p.add_argument("--email", required=True)
    p.add_argument("--business", default="Mickael Test Plumbing")
    p.add_argument("--contact-name", default="Mickael", help="First name in greeting")
    p.add_argument("--niche", default="plumber")
    p.add_argument("--city", default="Austin TX")
    args = p.parse_args()

    email = args.email.strip().lower()
    settings = get_settings()
    await init_db()

    place_id = _place_id_for_email(email)
    maps_lead = MapsScanResult(
        place_id=place_id,
        business_name=args.business,
        niche=args.niche,
        city=args.city,
        country="US",
        address=f"123 Test St, {args.city}",
        phone="(512) 555-0100",
        email=email,
        has_website=False,
        website_url=None,
        rating=4.5,
        review_count=42,
        demo_site_path=None,
        raw={
            "test_lead": True,
            "contact_first_name": args.contact_name.strip(),
            "hunt_mode": "manual_test",
        },
    )

    llm = LLMRouter(settings)
    engine = ColdEmailEngine(settings, llm_router=llm)
    draft = await engine.draft_pitch(
        lead=maps_lead,
        your_name=settings.your_name,
        your_business=settings.your_business_name or "Digital Agency",
        demo_url=None,
    )

    repo = LeadRepository()
    campaign_run_id = str(uuid.uuid4())
    factory = get_session_factory()
    async with factory() as session:
        db_lead = await repo.create_from_maps(session, maps_lead, campaign_run_id)
        db_lead.demo_site_path = None
        await repo.update_after_draft(
            session,
            db_lead,
            draft["subject"],
            draft["body"],
            email=email,
        )
        data = dict(db_lead.enrichment_data or {})
        data["test_lead"] = True
        data["no_demo"] = True
        data["contact_first_name"] = args.contact_name.strip()
        db_lead.enrichment_data = data
        await session.commit()
        lead_id = db_lead.id

    engine.send_email(
        to_email=email,
        subject=draft["subject"],
        body=draft["body"],
        dry_run=True,
    )
    safe = "".join(c if c.isalnum() else "_" for c in email.split("@")[0]).lower()
    draft_path = ROOT / "outputs" / "emails" / f"draft_{safe}.txt"

    print(f"Lead id:     {lead_id}")
    print(f"Email:       {email}")
    print(f"Status:      {LeadStatus.DRAFT_READY}")
    print(f"Demo:        (none)")
    print(f"Subject:     {draft['subject']}")
    print(f"Draft file:  {draft_path}")
    print("\n--- body preview ---\n")
    print(draft["body"][:1200])
    if len(draft["body"]) > 1200:
        print("\n... (truncated; see draft file)")


if __name__ == "__main__":
    asyncio.run(main())
