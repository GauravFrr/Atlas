"""
Railway entrypoint — one start command for all services; role from env.

Service 1 (webhooks):  RAILWAY_SERVICE_ROLE=webhook   (default)
Service 2 (Telegram):  RAILWAY_SERVICE_ROLE=telegram

  python scripts/railway_start.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    role = (os.environ.get("RAILWAY_SERVICE_ROLE") or "webhook").strip().lower()
    py = sys.executable

    if role == "telegram":
        cmd = [py, str(ROOT / "scripts" / "run_telegram_approvals.py")]
    elif role == "agent":
        cmd = [py, str(ROOT / "start_agent.py")]
    else:
        port = os.environ.get("PORT", "8787")
        cmd = [
            py,
            str(ROOT / "scripts" / "run_instantly_webhook.py"),
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ]

    print(f"[railway_start] role={role} cmd={' '.join(cmd)}", flush=True)
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
