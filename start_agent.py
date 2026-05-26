"""
Agent-Earns — single start command (matches ULTIMATE_AGENT_BLUEPRINT_V3).

  python start_agent.py          # Atlas runs 24/7 (blueprint loop)
  python start_agent.py --once   # one 30-min tick (test)

Blueprint flow (docs/ULTIMATE_AGENT_BLUEPRINT_V3.md):
  STARTUP → load .env → DB → health check
  MAIN LOOP (every 30 min):
    read state → decision engine (P1–P8) → execute task → sleep

Earning methods: docs/AGENT_EARNING_METHODS.md
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from loguru import logger

from config import get_settings


def setup_logging(verbose: bool = False) -> None:
    settings = get_settings()
    logger.remove()
    level = "DEBUG" if verbose else (settings.agent_log_level or "INFO")
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}</cyan> | <level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )
    (ROOT / "logs").mkdir(exist_ok=True)
    logger.add(ROOT / "logs" / "agent.log", rotation="50 MB", retention="14 days")
    for sub in ("demos", "emails", "instantly"):
        (ROOT / "outputs" / sub).mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "lead_queue" / "incoming").mkdir(parents=True, exist_ok=True)


async def main() -> None:
    args = parse_args()
    setup_logging(verbose=args.verbose)
    settings = get_settings()

    # Blueprint § STARTUP (same as main.py)
    from main import startup_sequence

    boot = argparse.Namespace(
        test=args.once,
        verbose=args.verbose,
        dry_run=False,
        module=None,
        no_dashboard=True,
    )
    await startup_sequence(boot)

    from core.agent import Agent

    agent = Agent(settings=settings)

    if args.once:
        logger.info("Blueprint: single tick (decision engine + one task)")
        await agent.startup()
        assert agent.loop is not None
        await agent.loop._run_tick()
        return

    logger.info(
        f"Blueprint: Atlas loop every {settings.agent_loop_interval_minutes} min "
        "(Ctrl+C to stop)"
    )
    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Agent stopped (Ctrl+C). State saved in agent.db.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Start Agent-Earns per ULTIMATE_AGENT_BLUEPRINT_V3",
    )
    p.add_argument("--once", action="store_true", help="One tick then exit")
    p.add_argument("--verbose", action="store_true", help="DEBUG logging")
    return p.parse_args()


if __name__ == "__main__":
    asyncio.run(main())
