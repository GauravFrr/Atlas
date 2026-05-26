"""
Run a full outreach campaign — one command, hands-free.

Examples:
  python scripts/run_campaign.py --niche plumber --city "Austin TX" --leads 10
  python scripts/run_campaign.py --niche dentist --city "Dallas TX" --leads 5 --send
  python scripts/run_campaign.py --niche plumber --city "Austin TX" --leads 3 --live
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from config import get_settings
from core.campaign_orchestrator import run_campaign
from utils.domain_pool import DomainPool
from utils.send_router import (
    can_use_instantly,
    can_use_smtp,
    describe_mode,
    resolve_send_mode,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Agent-Earns: Run a full Maps -> Demo -> Cold Email campaign",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_campaign.py --mock --niche plumber --city "Austin TX" --leads 3
  python scripts/run_campaign.py --niche plumber --city "Austin TX" --leads 10
  python scripts/run_campaign.py --niche dentist --city "Houston TX" --leads 5 --instantly
  python scripts/run_campaign.py --csv data/leads.csv --niche real_estate --city "London" --leads 5 --instantly
        """,
    )
    parser.add_argument(
        "--csv",
        metavar="PATH",
        default=None,
        help="Import leads from CSV (Email required). No Google API.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use fake leads (no Google Places API / billing required)",
    )
    parser.add_argument(
        "--niche",
        default="local_service",
        help='Business niche (default: local_service). Used for CSV rows without Niche column.',
    )
    parser.add_argument(
        "--city",
        default="US",
        help='Target city (default: US). Used for CSV rows without City column.',
    )
    parser.add_argument(
        "--leads",
        type=int,
        default=10,
        help="Number of NEW businesses to process (default: 10)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send via SMTP (Hostinger mailbox in .env or outreach_domains.json)",
    )
    parser.add_argument(
        "--instantly",
        action="store_true",
        help="Push leads to Instantly.ai (Instantly sends, not the agent)",
    )
    parser.add_argument(
        "--send-mode",
        choices=("draft", "smtp", "instantly", "auto", "hybrid"),
        default=None,
        help="draft | smtp | instantly | auto | hybrid (random + fallback)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Alias for --send (disables dry-run email saving only)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="DEBUG logging",
    )
    parser.add_argument(
        "--safe-demo",
        action="store_true",
        help="Use premium shell only (skip unique AI HTML)",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="With --mock: reset mock leads in memory bank so campaign processes leads again",
    )
    parser.add_argument(
        "--test-to",
        metavar="EMAIL",
        default=None,
        help="With --mock: route all leads to this inbox (Gmail +tags) for one full E2E test",
    )
    parser.add_argument(
        "--strict-spam",
        action="store_true",
        help="Block Instantly push if spam_words.txt phrases are found in email copy",
    )
    parser.add_argument(
        "--hunt-mode",
        default=None,
        metavar="MODE",
        help=(
            "Lead source: m02_outdated (best free/OSM), m10_no_website, m17_apollo, "
            "m03_reddit, etc. Default: m02_outdated without Google Places key"
        ),
    )
    return parser.parse_args()


def _default_hunt_mode(settings) -> str:
    if settings.google_places_api_key:
        return "m10_no_website"
    return "m02_outdated"


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    if args.safe_demo:
        settings.demo_generation_mode = "safe"

    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    requested_mode = args.send_mode
    if args.instantly:
        requested_mode = "instantly"
    elif args.send or args.live:
        requested_mode = "smtp"

    mode = resolve_send_mode(settings, requested_mode)

    pool = DomainPool(settings)
    pool_smtp = pool.enabled and any(d.has_smtp() for d in pool.domains)
    if mode == "hybrid":
        if not can_use_instantly(settings) and not (can_use_smtp(settings)):
            logger.error(
                "Hybrid needs at least Instantly OR Hostinger SMTP configured."
            )
            sys.exit(1)
        if not can_use_instantly(settings) or not can_use_smtp(settings):
            logger.warning(
                "Hybrid: only one channel fully configured — fallback may be limited."
            )

    if mode == "smtp" and not settings.has_smtp and not pool_smtp:
        logger.error(
            "SMTP mode but no mailbox configured.\n"
            "  Option A: SMTP_USER + SMTP_PASSWORD in .env (Hostinger: smtp.hostinger.com)\n"
            "  Option B: data/outreach_domains.json with smtp_* per domain\n"
            "  See docs/BUSINESS_EMAIL_SETUP.md"
        )
        sys.exit(1)

    if mode == "instantly" and not settings.has_instantly:
        logger.error(
            "Instantly mode but INSTANTLY_API_KEY / INSTANTLY_CAMPAIGN_ID missing.\n"
            "See docs/INSTANTLY_SETUP.md"
        )
        sys.exit(1)

    if mode == "auto" and not can_use_instantly(settings) and not can_use_smtp(settings):
        logger.warning(
            "AUTO mode: neither Instantly nor SMTP configured — drafts only."
        )

    if args.csv and not Path(args.csv).is_file():
        logger.error(f"CSV not found: {args.csv}")
        sys.exit(1)

    if args.csv and args.mock:
        logger.error("Use either --csv or --mock, not both")
        sys.exit(1)

    scan_src = (settings.lead_scan_source or "auto").lower()
    if not args.csv and not args.mock and not settings.google_places_api_key:
        if scan_src == "google":
            logger.error("LEAD_SCAN_SOURCE=google requires GOOGLE_PLACES_API_KEY in .env")
            sys.exit(1)
        if scan_src not in ("auto", "osm"):
            logger.error(
                "GOOGLE_PLACES_API_KEY is not set.\n"
                "  Option A: Add the key to .env (Maps + low-review hunts)\n"
                "  Option B: LEAD_SCAN_SOURCE=osm or auto (free OpenStreetMap)\n"
                "  Option C: --mock or --csv data/leads.csv\n"
                '    python scripts/run_campaign.py --niche plumber --city "Austin TX" --leads 2 --instantly'
            )
            sys.exit(1)
        logger.info("No Google Places key — using free OpenStreetMap scan (LEAD_SCAN_SOURCE=auto)")

    if not settings.has_gemini and not settings.has_groq:
        logger.error("Set GEMINI_API_KEY or GROQ_API_KEY in .env")
        sys.exit(1)

    if args.test_to and not args.mock:
        logger.error("--test-to only works with --mock")
        sys.exit(1)

    if args.strict_spam:
        settings.strict_spam_check = True

    print("\n" + "=" * 50)
    print("  AGENT-EARNS | CAMPAIGN ORCHESTRATOR")
    print("=" * 50)
    print(f"  Niche:  {args.niche}")
    print(f"  City:   {args.city}")
    print(f"  Leads:  {args.leads}")
    if args.csv:
        source = f"CSV ({args.csv})"
    elif args.mock:
        source = "MOCK (no Google API)"
    elif (settings.lead_scan_source or "auto").lower() in ("auto", "osm") and not settings.google_places_api_key:
        source = "OpenStreetMap (free)"
    else:
        source = "Google Maps / auto"
    print(f"  Source: {source}")
    print(f"  Send:   {describe_mode(mode)}")
    if args.test_to:
        print(f"  Test:   all mock leads -> {args.test_to}")
    print(f"  Demo:   {settings.demo_generation_mode}")
    hunt_mode = args.hunt_mode or _default_hunt_mode(settings)
    if not args.csv and not args.mock:
        from core.lead_sources import hunt_mode_label

        print(f"  Hunt:   {hunt_mode_label(hunt_mode)}")
    print("=" * 50 + "\n")

    try:
        result = await run_campaign(
            niche=args.niche,
            city=args.city,
            leads=args.leads,
            send_mode=mode,
            use_mock=args.mock,
            fresh_mock=args.fresh and args.mock,
            test_to=args.test_to,
            csv_path=args.csv,
            settings=settings,
            hunt_mode=hunt_mode if not args.csv and not args.mock else "m10_no_website",
        )
    except Exception as e:
        logger.exception(f"Campaign failed: {e}")
        sys.exit(1)

    print("\n" + result.summary_text())
    print("\nOutputs:")
    print("  Demos:  outputs/demos/")
    print("  Emails: outputs/emails/")
    if mode in ("instantly", "hybrid"):
        print("  Instantly CSV: outputs/instantly/")
    print(f"  Memory: agent.db (campaign {result.campaign_id[:8]}...)")


if __name__ == "__main__":
    asyncio.run(main())
