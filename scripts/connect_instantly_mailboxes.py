"""
Connect Hostinger mailboxes from data/outreach_domains.json to Instantly (API v2)
and enable warmup.

Prerequisites:
  - New Instantly workspace on Growth (or higher) — API v2 key with accounts:create
  - Hostinger email passwords in .env (SMTP_PASSWORD or per-mailbox below)

  python scripts/connect_instantly_mailboxes.py --dry-run
  python scripts/connect_instantly_mailboxes.py
  python scripts/connect_instantly_mailboxes.py --only gaurav@gauravxd.dev

Do NOT paste API keys or passwords in chat — only in .env locally.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.platforms.instantly import InstantlyClient
from utils.domain_pool import DomainPool

HOSTINGER_IMAP = ("imap.hostinger.com", 993)
HOSTINGER_SMTP = ("smtp.hostinger.com", 587)


def _password_for_domain(domain, settings) -> str:
    pwd = (domain.smtp_password or "").strip()
    if not pwd:
        pwd = (settings.smtp_password or "").strip()
    return pwd


async def main() -> None:
    parser = argparse.ArgumentParser(description="Connect Hostinger mailboxes to Instantly")
    parser.add_argument("--dry-run", action="store_true", help="Print actions only")
    parser.add_argument(
        "--api-key",
        default="",
        help="Override INSTANTLY_API_KEY (else from .env)",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Connect single address only (e.g. gaurav@gauravxd.dev)",
    )
    parser.add_argument("--no-warmup", action="store_true", help="Skip warmup enable step")
    args = parser.parse_args()

    settings = get_settings()
    api_key = (args.api_key or settings.instantly_api_key or "").strip()
    if not api_key:
        print("Set INSTANTLY_API_KEY in .env (API v2 key from new workspace)")
        sys.exit(1)

    pool = DomainPool(settings)
    if not pool.domains:
        print("No domains in outreach_domains.json")
        sys.exit(1)

    client = InstantlyClient(api_key=api_key, campaign_id="")
    connected: list[str] = []

    for domain in pool.domains:
        email = (domain.smtp_from_email or domain.smtp_user or "").strip().lower()
        if not email:
            continue
        if args.only and email != args.only.strip().lower():
            continue

        pwd = _password_for_domain(domain, settings)
        if not pwd:
            print(f"SKIP {email}: no password (set SMTP_PASSWORD in .env)")
            continue

        first = (domain.smtp_from_name or settings.your_name or "Gaurav").split()[0]
        print(f"\n{'[dry-run] ' if args.dry_run else ''}Connect {email} ({domain.name})")

        if args.dry_run:
            connected.append(email)
            continue

        existing = {
            (a.get("email") or "").lower()
            for a in await client.list_accounts(limit=100)
        }
        if email in existing:
            print(f"  Already in Instantly — skipping create")
            connected.append(email)
            continue

        result = await client.create_imap_account(
            email=email,
            first_name=first,
            last_name=".",
            imap_host=HOSTINGER_IMAP[0],
            imap_port=HOSTINGER_IMAP[1],
            smtp_host=HOSTINGER_SMTP[0],
            smtp_port=HOSTINGER_SMTP[1],
            username=email,
            password=pwd,
        )
        if result:
            connected.append(email)

    if not connected:
        print("\nNo accounts connected.")
        sys.exit(1)

    if args.dry_run:
        print(f"\nDry-run: would connect {len(connected)} account(s), then enable warmup.")
        return

    if not args.no_warmup:
        print(f"\nEnabling warmup for {len(connected)} account(s)...")
        await client.enable_warmup(connected)

    print("\nDone. Next steps:")
    print("  1. Instantly UI → Email Accounts → confirm all show Connected + Warmup ON")
    print("  2. Create a campaign → add these accounts as senders")
    print("  3. Copy campaign UUID → INSTANTLY_CAMPAIGN_ID in .env")
    print("  4. Set EMAIL_SEND_MODE=instantly (wait 2+ weeks before heavy cold volume)")


if __name__ == "__main__":
    asyncio.run(main())
