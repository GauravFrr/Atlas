"""
Atlas Telegram bot — owner panel + Approve / Recreate / Skip on email drafts.

  python scripts/run_telegram_approvals.py

Requires in .env:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  SMTP_* (for Approve and send)

Commands: /start /menu /status /health /leads /export /help
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.venv_guard import check_telegram_import, ensure_project_venv

ensure_project_venv()
check_telegram_import()

from config import get_settings
from database.connection import init_db
from utils.telegram_approval import build_application
from utils.telegram_bot.runner import run_bot


def main() -> None:
    settings = get_settings()
    if not settings.has_telegram:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        sys.exit(1)

    import asyncio

    asyncio.run(init_db())
    app = build_application(settings)
    name = getattr(settings, "telegram_bot_display_name", None) or "Atlas"
    print(f"{name} bot listening — owner panel + email approvals")
    print(f"Owner chat id: {settings.telegram_chat_id}")
    if settings.telegram_webhook_enabled:
        url = settings.resolved_telegram_webhook_url()
        print(f"Webhook mode → {url or '(set RAILWAY_PUBLIC_DOMAIN or TELEGRAM_WEBHOOK_URL)'}")
    else:
        print("Polling mode (local)")
    print("Send /start in Telegram to open the menu")
    run_bot(app, settings)


if __name__ == "__main__":
    main()
