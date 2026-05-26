"""Show recent Atlas task logs from agent_logs table."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database.connection import get_session_factory, init_db
from database.repositories.agent_log_repository import AgentLogRepository


async def main() -> None:
    limit = 20
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    await init_db()
    async with get_session_factory()() as session:
        rows = await AgentLogRepository().list_recent(session, limit=limit)
    if not rows:
        print("No agent logs yet. Run: python start_agent.py --once")
        return
    for r in rows:
        err = f" | {r.error_message[:60]}" if r.error_message else ""
        print(
            f"{r.created_at} | tick={r.tick_number} | {r.status:7} | "
            f"{r.task_name} ({r.elapsed_ms}ms){err}"
        )


if __name__ == "__main__":
    asyncio.run(main())
