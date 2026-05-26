"""
Verify Hostinger mailbox rotation is loaded from data/outreach_domains.json.

  python scripts/test_mailbox_rotation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from utils.domain_pool import DomainPool


def main() -> None:
    settings = get_settings()
    path = settings.outreach_domains_file or "(not set)"
    print(f"OUTREACH_DOMAINS_FILE = {path}")
    print(f"SMTP_PASSWORD set     = {bool(settings.smtp_password)}")

    pool = DomainPool(settings)
    if not pool.enabled:
        print("\nFAIL: Domain pool empty. Set OUTREACH_DOMAINS_FILE=data/outreach_domains.json in .env")
        sys.exit(1)

    print(f"\nLoaded {len(pool.domains)} mailbox(es):\n")
    ok = True
    for d in pool.domains:
        ready = d.has_smtp()
        mark = "OK" if ready else "MISSING PASSWORD"
        if not ready:
            ok = False
        print(f"  [{mark}] {d.name}")
        print(f"         From: {d.smtp_from_name} <{d.smtp_from_email or d.smtp_user}>")
        print(f"         SMTP: {d.smtp_user} @ {d.smtp_host}:{d.smtp_port}")
        print()

    # Show stable rotation example
    sample_ids = ["osm/node/1", "osm/node/2", "osm/node/3", "osm/node/4", "osm/node/5"]
    print("Sample rotation (same lead -> same mailbox every time):")
    for pid in sample_ids:
        chosen = pool.pick(pid)
        assert chosen
        print(f"  {pid[:16]:16} -> {chosen.smtp_user}")

    if not ok:
        print("Set SMTP_PASSWORD in .env (shared Hostinger password for all mailboxes).")
        sys.exit(1)

    print("\nAll mailboxes ready for rotation.")
    sys.exit(0)


if __name__ == "__main__":
    main()
