"""
Generate sample Mikey-strategy emails in outputs/emails/demo_mail.txt

  python scripts/create_demo_mail.py --with-link
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings

_spec = importlib.util.spec_from_file_location(
    "mikey_sequence",
    ROOT / "modules" / "outreach" / "mikey_sequence.py",
)
_ms = importlib.util.module_from_spec(_spec)
assert _spec.loader
_spec.loader.exec_module(_ms)

_spec2 = importlib.util.spec_from_file_location(
    "icebreaker",
    ROOT / "modules" / "outreach" / "icebreaker.py",
)
_ib = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_ib)


def main() -> None:
    parser = argparse.ArgumentParser(description="Write outputs/emails/demo_mail.txt")
    parser.add_argument("--with-link", action="store_true")
    parser.add_argument("--niche", default="plumber", help="plumber or real_estate")
    args = parser.parse_args()
    settings = get_settings()

    from types import SimpleNamespace

    lead = SimpleNamespace(
        business_name="Austin Precision Plumbing",
        niche=args.niche,
        city="Austin TX",
        email="owner@austinprecisionplumbing.com",
        has_website=False,
        website_url=None,
    )

    demo_url = None
    if args.with_link:
        base = (settings.demo_site_base_url or "https://demos.example.com").rstrip("/")
        demo_url = f"{base}/austin-precision-plumbing/index.html"

    ib = _ib.fallback_icebreaker(lead, demo_url)
    sender = settings.your_name.strip() or "Gaurav"
    seq = _ms.build_sequence(lead, sender, demo_url=demo_url, steps=4, icebreaker=ib)
    e1 = seq[0]

    path = ROOT / "outputs" / "emails" / "demo_mail.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Mikey email strategy sample\n"
        f"TO: {lead.email}\n"
        f"SUBJECT A: {e1['subject']}\n"
        f"SUBJECT B: {e1.get('subject_b', '')}\n\n"
        f"--- EMAIL 1 (day 1) ---\n\n{e1['body']}\n\n"
        f"{_ms.format_sequence_export(seq[1:])}\n",
        encoding="utf-8",
    )
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
