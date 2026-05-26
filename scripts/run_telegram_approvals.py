"""
Listen for Telegram inline buttons (Approve / Recreate / Skip) on close-email drafts.

Keep this running while the agent is on (separate terminal):

  .\\venv\\Scripts\\python.exe scripts/run_telegram_approvals.py

Requires in .env:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
  SMTP_* (for Approve and send)
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


def main() -> None:
    settings = get_settings()
    if not settings.has_telegram:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        sys.exit(1)

    import asyncio

    asyncio.run(init_db())
    app = build_application(settings)
    print("Telegram approval bot listening (Approve / Recreate / Skip)...")
    print(f"Owner chat id: {settings.telegram_chat_id}")
    # run_polling owns the event loop — do not wrap in asyncio.run() (Windows error)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
