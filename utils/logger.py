"""
Loguru Structured Logging — Configured for both dev and production.
JSON format in production, human-readable in dev.
Auto-rotation, compression, retention policies.
"""

import sys
from loguru import logger
from config import Settings


def setup_logger(settings: Settings, verbose: bool = False) -> None:
    """Configure Loguru with environment-appropriate settings."""
    logger.remove()

    level = "DEBUG" if verbose else settings.agent_log_level

    if settings.is_production:
        # Production: JSON logs with rotation
        logger.add(
            "logs/agent.log",
            level=level,
            rotation="100 MB",
            compression="zip",
            retention="30 days",
            serialize=True,  # JSON format
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
        )
        logger.add(
            "logs/errors.log",
            level="ERROR",
            rotation="50 MB",
            compression="zip",
            retention="90 days",
        )
    else:
        # Development: Colored human-readable console output
        logger.add(
            sys.stdout,
            level=level,
            colorize=True,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
        )
        logger.add(
            "logs/agent.log",
            level="DEBUG",
            rotation="50 MB",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        )

    # Dedicated logs for key operations
    logger.add(
        "logs/emails.log",
        filter=lambda r: "email" in r["name"].lower() or "outreach" in r["name"].lower(),
        rotation="50 MB",
        retention="30 days",
    )
    logger.add(
        "logs/payments.log",
        filter=lambda r: "payment" in r["name"].lower() or "razorpay" in r["name"].lower(),
        rotation="50 MB",
        retention="90 days",  # Keep payment logs longer
    )
    logger.add(
        "logs/leads.log",
        filter=lambda r: "lead" in r["name"].lower(),
        rotation="50 MB",
        retention="30 days",
    )
    logger.add(
        "logs/performance.log",
        filter=lambda r: "performance" in r["name"].lower() or "self_improvement" in r["name"].lower(),
        rotation="10 MB",
        retention="90 days",
    )
