"""
Clear demos/drafts on leads with no email; keep rows in DB for resale inventory.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from constants import LeadStatus
from core.lead_email_gate import remove_local_demo, valid_email
from database.connection import get_session_factory, init_db
from database.models.lead import Lead
from database.repositories.lead_repository import LeadRepository
from sqlalchemy import select


async def main() -> None:
    await init_db()
    repo = LeadRepository()
    factory = get_session_factory()
    n = 0
    async with factory() as session:
        result = await session.execute(
            select(Lead).where(
                Lead.is_deleted.is_(False),
                Lead.status.in_(
                    (
                        LeadStatus.NEW,
                        LeadStatus.PENDING_EMAIL,
                        LeadStatus.DRAFT_READY,
                    )
                ),
            )
        )
        for lead in result.scalars():
            if valid_email(lead.email):
                continue
            remove_local_demo(lead.demo_site_path)
            await repo.discard_no_email(session, lead, reason="no_email_cleanup")
            n += 1
        await session.commit()
    print(f"Cleaned {n} lead(s) with no email (demos removed, rows kept).")


if __name__ == "__main__":
    asyncio.run(main())
