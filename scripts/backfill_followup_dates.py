"""
One-off: schedule next_followup for CONTACTED leads missing it (SMTP channel only).
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from constants import LeadStatus
from database.connection import get_session_factory, init_db
from database.models.lead import Lead
from database.repositories.lead_repository import LeadRepository
from modules.outreach.sequence_schedule import schedule_next_followup
from sqlalchemy import select


async def main() -> None:
    await init_db()
    factory = get_session_factory()
    n = 0
    for attempt in range(1, 6):
        try:
            async with factory() as session:
                result = await session.execute(
                    select(Lead).where(
                        Lead.is_deleted.is_(False),
                        Lead.status == LeadStatus.CONTACTED,
                        Lead.next_followup.is_(None),
                    )
                )
                for lead in result.scalars():
                    ch = (lead.enrichment_data or {}).get("send_channel") or "smtp"
                    if ch == "instantly":
                        continue
                    schedule_next_followup(lead)
                    n += 1
                await session.commit()
            print(f"Scheduled follow-up for {n} SMTP lead(s).")
            return
        except Exception as e:
            if "locked" not in str(e).lower() and attempt < 5:
                raise
            if attempt >= 5:
                raise
            print(f"DB busy (agent running?) — retry {attempt}/5 in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
