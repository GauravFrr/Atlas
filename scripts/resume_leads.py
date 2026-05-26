"""
Finish incomplete leads stored in agent.db (demo, email, publish, draft, send).

  python scripts/resume_leads.py              # dry-run report
  python scripts/resume_leads.py --apply      # run pipeline
  python scripts/resume_leads.py --apply -n 5 # max 5 leads
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from core.lead_resume import assess_lead, run_resume_queue
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository


def _safe(text: str) -> str:
    try:
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", errors="replace").decode("ascii")


async def report_only(limit: int) -> None:
    await init_db()
    repo = LeadRepository()
    factory = get_session_factory()
    async with factory() as session:
        leads = await repo.list_incomplete(session, limit)
    if not leads:
        print("No incomplete leads — memory bank is caught up.")
        return
    print(f"\n{len(leads)} incomplete lead(s):\n")
    print(f"{'Business':<32} {'Status':<14} {'Missing steps'}")
    print("-" * 72)
    for lead in leads:
        plan = assess_lead(lead)
        steps = ", ".join(plan.missing) if plan.missing else "—"
        line = f"{lead.business_name[:31]:<32} {lead.status:<14} {steps}"
        print(_safe(line))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Run missing steps (default is report only)",
    )
    parser.add_argument("-n", "--max", type=int, default=10, help="Max leads to resume")
    args = parser.parse_args()
    settings = get_settings()

    if not args.apply:
        await report_only(args.max)
        print("\nRun with --apply to finish these leads.\n")
        return

    await init_db()
    from utils.send_router import resolve_send_mode

    send_mode = resolve_send_mode(settings, settings.email_send_mode or "instantly")
    stats = await run_resume_queue(settings, max_leads=args.max, send_mode=send_mode)
    print("\nResume complete:")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
