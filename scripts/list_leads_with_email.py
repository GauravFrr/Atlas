"""List leads that have an email (for create_payment_link.py)."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.connection import get_session_factory, init_db
from database.models.lead import Lead
from sqlalchemy import select


async def main() -> None:
    await init_db()
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(Lead)
            .where(Lead.is_deleted.is_(False), Lead.email.is_not(None))
            .order_by(Lead.updated_at.desc())
            .limit(30)
        )
        rows = list(result.scalars())
        if not rows:
            print("No leads with email in agent.db")
            return
        for lead in rows:
            print(f"{lead.email}\t{lead.business_name}\t{lead.status}")


if __name__ == "__main__":
    asyncio.run(main())
