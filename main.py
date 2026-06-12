"""
Agent-Earns | Atlas — dashboard + decision-engine loop (advanced).

Start the agent (blueprint loop, no dashboard):

  python start_agent.py

This file: Atlas + optional dashboard:

  python main.py [--no-dashboard]
"""

import asyncio
import argparse
import sys
from loguru import logger

from config import get_settings
from constants import AgentState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent-Earns: Autonomous AI Earning System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start in production mode
  python main.py --test             # Run one test cycle and exit
  python main.py --verbose          # Verbose logging
  python main.py --module leads     # Run only lead finder
        """
    )
    parser.add_argument("--test", action="store_true", help="Run one test cycle and exit")
    parser.add_argument("--verbose", action="store_true", help="Set log level to DEBUG")
    parser.add_argument("--module", type=str, help="Run specific module only")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable the web dashboard")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without sending emails or payments")
    return parser.parse_args()


def setup_logging(verbose: bool = False, env: str = "development") -> None:
    """Configure Loguru structured logging."""
    logger.remove()  # Remove default handler

    log_level = "DEBUG" if verbose else get_settings().agent_log_level

    if env == "production":
        # JSON format for production (machine-readable)
        logger.add(
            "logs/agent.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation="100 MB",
            compression="zip",
            retention="30 days",
            serialize=True,  # JSON output
        )
        logger.add(
            "logs/errors.log",
            level="ERROR",
            rotation="50 MB",
            compression="zip",
            retention="90 days",
        )
    else:
        # Human-readable format for development
        logger.add(
            sys.stdout,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
            level=log_level,
            colorize=True,
        )
        logger.add(
            "logs/agent.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level="DEBUG",
            rotation="50 MB",
            retention="7 days",
        )

    # Separate logs for key operations
    logger.add("logs/emails.log", filter=lambda r: "email" in r["name"].lower(), rotation="50 MB")
    logger.add("logs/payments.log", filter=lambda r: "payment" in r["name"].lower(), rotation="50 MB")
    logger.add("logs/leads.log", filter=lambda r: "lead" in r["name"].lower(), rotation="50 MB")


async def startup_sequence(args: argparse.Namespace) -> None:
    """Full startup sequence with health checks and initialization."""
    settings = get_settings()

    logger.info("=" * 60)
    logger.info(f"  {settings.agent_name} | Agent-Earns v1.0.0")
    logger.info(f"  Environment: {settings.agent_env}")
    logger.info(f"  Dry Run: {args.dry_run}")
    logger.info("=" * 60)

    # Step 1: Validate configuration
    logger.info("Step 1/5: Validating configuration...")
    features = settings.get_enabled_features()
    enabled = [k for k, v in features.items() if v]
    disabled = [k for k, v in features.items() if not v]

    if not features["llm_gemini"] and not features["llm_groq"]:
        logger.error("FATAL: No LLM API keys configured. Set GEMINI_API_KEY or GROQ_API_KEY in .env")
        sys.exit(1)

    logger.info(f"Enabled features: {', '.join(enabled)}")
    if disabled:
        logger.warning(f"Disabled features (no API keys): {', '.join(disabled)}")

    from core.lead_sources import available_hunt_modes

    hunt_raw = (settings.autopilot_hunt_modes or "").strip()
    hunt_modes = available_hunt_modes(settings)
    if hunt_raw:
        logger.info(f"Hunt config: AUTOPILOT_HUNT_MODES={hunt_raw!r} → {len(hunt_modes)} active mode(s)")
    else:
        logger.info(f"Hunt config: default production rotation → {len(hunt_modes)} mode(s)")

    # Step 2: Initialize logging files
    logger.info("Step 2/5: Logging initialized...")
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("outputs/websites", exist_ok=True)
    os.makedirs("outputs/chatbots", exist_ok=True)
    os.makedirs("outputs/designs", exist_ok=True)
    os.makedirs("outputs/reports", exist_ok=True)
    os.makedirs("outputs/invoices", exist_ok=True)

    # Step 3: Initialize database
    logger.info("Step 3/5: Initializing database...")
    try:
        from database.connection import init_db
        await init_db()
        logger.success("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    # Step 4: Health check all APIs
    logger.info("Step 4/5: Running API health checks...")
    try:
        from utils.health_checker import HealthChecker
        checker = HealthChecker(settings)
        health_report = await checker.check_all()
        
        for service, status in health_report.items():
            if status["healthy"]:
                logger.info(f"  [OK] {service}")
            else:
                logger.warning(f"  [FAIL] {service}: {status.get('error', 'Unknown error')}")
    except Exception as e:
        logger.warning(f"Health check failed (non-fatal): {e}")

    # Step 5: Initialize agent
    logger.info("Step 5/5: Initializing agent core...")
    logger.success("Startup sequence complete. Atlas is ready.")


async def run_test_cycle(args: argparse.Namespace) -> None:
    """Run a single test cycle and exit."""
    logger.info("Running test cycle...")
    await startup_sequence(args)

    from core.agent import Agent
    agent = Agent(settings=get_settings())
    
    logger.info("Running single agent tick (test mode)...")
    await agent.tick(dry_run=True)
    
    logger.info("Test cycle complete. Exiting.")


async def run_single_module(module_name: str, args: argparse.Namespace) -> None:
    """Run a specific module for testing."""
    await startup_sequence(args)
    settings = get_settings()

    module_map = {
        "leads": "modules.lead_finder.manager",
        "outreach": "modules.outreach.manager",
        "payment": "modules.payment_handler.manager",
        "content": "modules.content_writer.manager",
        "website": "modules.website_builder.manager",
    }

    if module_name not in module_map:
        logger.error(f"Unknown module: {module_name}. Available: {list(module_map.keys())}")
        sys.exit(1)

    import importlib
    mod = importlib.import_module(module_map[module_name])
    logger.info(f"Running module: {module_name}")
    await mod.run(settings=settings, dry_run=args.dry_run)


async def main() -> None:
    """Main async entry point."""
    args = parse_args()
    settings = get_settings()

    # Setup logging first
    setup_logging(verbose=args.verbose, env=settings.agent_env)

    try:
        if args.test:
            await run_test_cycle(args)
            return

        if args.module:
            await run_single_module(args.module, args)
            return

        # Full production run
        await startup_sequence(args)

        # Start agent + dashboard concurrently
        tasks = []

        # Agent loop
        from core.agent import Agent
        agent = Agent(settings=settings, dry_run=args.dry_run)
        tasks.append(asyncio.create_task(agent.run(), name="agent_loop"))

        # Dashboard (unless disabled)
        if not args.no_dashboard:
            from dashboard.app import create_app
            import uvicorn
            app = create_app()
            config = uvicorn.Config(
                app=app,
                host="0.0.0.0",
                port=settings.dashboard_port,
                log_level="warning",  # Don't clutter agent logs with uvicorn noise
            )
            server = uvicorn.Server(config)
            tasks.append(asyncio.create_task(server.serve(), name="dashboard"))
            logger.info(f"Dashboard starting at http://localhost:{settings.dashboard_port}")

        # Run all tasks, cancel all if any fail
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user (Ctrl+C)")
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
