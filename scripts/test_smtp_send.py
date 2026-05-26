"""
Send one test email through your business SMTP (@gauravxd.dev).

  python scripts/test_smtp_send.py --to you@gmail.com
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from modules.outreach.cold_email import ColdEmailEngine


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Recipient for test email")
    parser.add_argument(
        "--mailbox",
        default="",
        help="Use a rotated mailbox email from outreach_domains.json (optional)",
    )
    args = parser.parse_args()
    settings = get_settings()

    cfg = settings.get_smtp_config()
    if args.mailbox:
        from utils.domain_pool import DomainPool

        pool = DomainPool(settings)
        match = next(
            (d for d in pool.domains if d.smtp_user.lower() == args.mailbox.lower()),
            None,
        )
        if not match:
            print(f"Mailbox not in outreach_domains.json: {args.mailbox}")
            sys.exit(1)
        cfg = match.get_smtp_config(settings.your_name, settings=settings)

    if not cfg.get("host") or not cfg.get("user") or not cfg.get("password"):
        print("SMTP not configured. See docs/BUSINESS_EMAIL_SETUP.md")
        print("Required: SMTP_PROVIDER (or SMTP_HOST), SMTP_USER, SMTP_PASSWORD")
        sys.exit(1)
    print(f"Host:     {cfg['host']}:{cfg['port']}")
    print(f"Login:    {cfg['user']}")
    print(f"From:     {cfg.get('from_name')} <{cfg.get('from_email')}>")
    print(f"BCC self:     {cfg.get('bcc_self', True)}")
    print(f"Save to Sent: {cfg.get('save_to_sent', True)}")
    print(f"Sending test to: {args.to}")
    print("After send: check Hostinger Inbox (BCC) and Sent folder.")

    engine = ColdEmailEngine(settings=settings, llm_router=None)
    body = (
        f"Hi,\n\n"
        f"This is a test from Agent-Earns using your business mailbox.\n\n"
        f"If you see From: {cfg.get('from_email')}, SMTP is set up correctly.\n"
        f"You should also see this in Hostinger Sent (IMAP copy) and Inbox (BCC).\n\n"
        f"— {settings.your_name}"
    )
    ok = engine.send_email(
        to_email=args.to,
        subject="Agent-Earns SMTP test (gauravxd.dev)",
        body=body,
        smtp_config=cfg,
        dry_run=False,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
