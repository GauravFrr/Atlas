"""
Send one real test email to yourself — SMTP or Instantly.

  python scripts/send_test_email.py
  python scripts/send_test_email.py --to itzmi3xel@gmail.com
  python scripts/send_test_email.py --method smtp
  python scripts/send_test_email.py --method instantly
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from modules.lead_finder.scanners.google_maps import MapsScanResult
from modules.outreach.cold_email import ColdEmailEngine
from modules.outreach.icebreaker import generate_icebreaker
from modules.outreach.mikey_sequence import build_email_1
from modules.outreach.instantly_push import InstantlyPush


DEFAULT_TO = "itzmi3xel@gmail.com"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send Agent-Earns test email to you")
    parser.add_argument("--to", default=DEFAULT_TO, help="Your inbox")
    parser.add_argument(
        "--method",
        choices=("auto", "smtp", "instantly", "draft"),
        default="auto",
        help="auto = smtp if configured, else instantly, else save draft only",
    )
    args = parser.parse_args()
    settings = get_settings()
    to = args.to.strip()

    demo_url = None
    demos = sorted((ROOT / "outputs" / "demos").glob("*.html"))
    if demos and settings.demo_site_base_url:
        slug = demos[-1].stem
        demo_url = f"{settings.demo_site_base_url.rstrip('/')}/{slug}/index.html"

    lead = MapsScanResult(
        place_id="ChIJtest_send_me",
        business_name="Test Plumbing Co",
        niche="plumber",
        city="Austin TX",
        country="US",
        address="123 Test St",
        phone="(512) 555-0199",
        email=to,
        has_website=False,
        website_url=None,
        rating=4.5,
        review_count=10,
    )
    sender = settings.your_name.strip() or "Gaurav"
    icebreaker = await generate_icebreaker(lead, demo_url, llm=None)
    draft = build_email_1(lead, icebreaker, demo_url=demo_url, sender_name=sender)
    subject = draft["subject"]
    body = draft["body"]

    out = ROOT / "outputs" / "emails" / "test_send_ready.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f"TO: {to}\nSUBJECT: {subject}\n\n{body}",
        encoding="utf-8",
    )
    print(f"Draft saved: {out}\n")

    method = args.method
    if method == "auto":
        if settings.has_smtp:
            method = "smtp"
        elif settings.has_instantly:
            method = "instantly"
        else:
            method = "draft"

    if method == "draft":
        print("No SMTP or Instantly in .env — email was NOT sent automatically.")
        print("\nTo automate sends, add ONE of these to .env:\n")
        print("  A) Instantly (you already use this):")
        print("     INSTANTLY_API_KEY=...")
        print("     INSTANTLY_CAMPAIGN_ID=...")
        print("     Then: python scripts/send_test_email.py --method instantly\n")
        print("  B) Business SMTP (Zoho / Workspace on your domain):")
        print("     See docs/BUSINESS_EMAIL_SETUP.md")
        print("     Then: python scripts/send_test_email.py --method smtp\n")
        print(f"  C) Manual: copy {out} into Instantly or Gmail and send to {to}")
        sys.exit(0)

    if method == "smtp":
        if not settings.has_smtp:
            print("SMTP not configured. See docs/BUSINESS_EMAIL_SETUP.md")
            sys.exit(1)
        cfg = settings.get_smtp_config()
        print(f"SMTP send → {to}")
        print(f"From: {cfg.get('from_name')} <{cfg.get('from_email')}>")
        ok = ColdEmailEngine(settings, None).send_email(
            to, subject, body, smtp_config=cfg, dry_run=False
        )
        sys.exit(0 if ok else 1)

    if method == "instantly":
        if not settings.has_instantly:
            print("Instantly not configured.")
            print("Add INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID to .env")
            print("See docs/INSTANTLY_SETUP.md")
            sys.exit(1)
        print(f"Instantly push → {to} (campaign sends per Instantly rules)")
        print("WARNING: If campaign is ACTIVE, Instantly may send the full 3-email sequence.")
        push = InstantlyPush(settings)
        ok = await push.push_lead(lead, demo_url=demo_url, your_name=settings.your_name)
        if ok:
            print("Lead added in Instantly. Check Instantly → Campaign → Leads.")
            print(f"Also check inbox {to} in a few minutes (depends on warmup/limits).")
        else:
            print("Instantly API failed. Use the draft file or CSV import instead.")
        sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
