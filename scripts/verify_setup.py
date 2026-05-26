"""
Quick health check for Agent-Earns hosting + core APIs.

  python scripts/verify_setup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from utils.hostinger_pool import HostingerDemoPool
from utils.netlify_pool import NetlifyAccountPool


def main() -> None:
    s = get_settings()
    issues: list[str] = []
    ok: list[str] = []

    if s.has_gemini or s.has_groq:
        ok.append("LLM (Gemini or Groq)")
    else:
        issues.append("Set GEMINI_API_KEY or GROQ_API_KEY")

    if s.has_telegram:
        ok.append("Telegram alerts")
    else:
        issues.append("TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID")

    if s.has_instantly:
        ok.append("Instantly")
    else:
        issues.append("INSTANTLY_API_KEY + INSTANTLY_CAMPAIGN_ID")

    if s.has_smtp:
        ok.append("SMTP (Hostinger)")
    else:
        issues.append("SMTP_USER + SMTP_PASSWORD")

    np = NetlifyAccountPool(s)
    if np.enabled:
        ok.append(f"Netlify pool ({len(np.accounts)} accounts)")
    else:
        issues.append("NETLIFY_AUTH_TOKEN + NETLIFY_SITE_ID")

    hp = HostingerDemoPool(s)
    if hp.enabled:
        ok.append(f"Hostinger FTP ({len(hp.sites)} sites)")
        for site in hp.sites:
            ok.append(f"  - {site.name}: {site.demo_base_url}")
    else:
        issues.append("FTP_* + HOSTINGER_SITES_FILE")

    if s.has_r2:
        ok.append("Cloudflare R2 (fallback)")
    else:
        ok.append("R2 off (OK — last fallback only)")

    strategy = (getattr(s, "demo_host_strategy", "random") or "random").lower()
    if s.demo_upload_mode == "auto" and not s.demo_prefer_r2:
        if strategy == "random":
            ok.append("Demo stack: random Hostinger/Netlify, R2 backup")
        else:
            ok.append("Demo stack: Netlify -> Hostinger -> R2")
    elif s.demo_prefer_r2:
        issues.append("DEMO_PREFER_R2=true puts R2 before Netlify — set false")

    if Path(s.outreach_domains_file or "").is_file() if s.outreach_domains_file else False:
        ok.append("Mailbox rotation (outreach_domains.json)")
    elif getattr(s, "outreach_domains_file", ""):
        issues.append(f"OUTREACH_DOMAINS_FILE missing: {s.outreach_domains_file}")

    print("=" * 50)
    print("  AGENT-EARNS SETUP CHECK")
    print("=" * 50)
    for line in ok:
        print(f"  OK   {line}")
    for line in issues:
        print(f"  FIX  {line}")
    print("=" * 50)
    print("\nTests to run:")
    print("  python scripts/test_netlify_accounts.py")
    print("  python scripts/test_ftp_demo.py")
    print("  python scripts/test_mailbox_rotation.py")
    print("  python start_agent.py")
    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
