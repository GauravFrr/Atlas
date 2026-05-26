"""
Legacy entry — prefer start_agent.py at project root.

  python start_agent.py
  python scripts/run_autopilot.py --once
  python scripts/run_autopilot.py --loop
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from core.autopilot import run_forever, run_once, _print_cycle_summary


async def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-Earns autopilot (legacy)")
    parser.add_argument("--loop", action="store_true", help="Run every N minutes")
    parser.add_argument("--once", action="store_true", help="Single cycle")
    args = parser.parse_args()

    settings = get_settings()

    if args.once or not args.loop:
        from database.connection import init_db

        await init_db()
        result = await run_once(settings)
        _print_cycle_summary(result, cycle=1)
        return

    await run_forever(settings)


if __name__ == "__main__":
    asyncio.run(main())
