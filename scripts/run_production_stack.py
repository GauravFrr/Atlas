"""
Local production stack — webhooks + Telegram approvals (+ optional Atlas loop).

  python scripts/run_production_stack.py
  python scripts/run_production_stack.py --agent-once
  python scripts/run_production_stack.py --webhook-only

Railway: deploy two services (see docs/PRODUCTION_RUN.md).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _check_env() -> list[str]:
    from config import get_settings

    s = get_settings()
    missing: list[str] = []
    if not s.telegram_bot_token or not s.telegram_chat_id:
        missing.append("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
    if not getattr(s, "instantly_api_key", ""):
        missing.append("INSTANTLY_API_KEY (recommended)")
    if not getattr(s, "razorpay_key_id", ""):
        missing.append("RAZORPAY_* (for payment webhooks)")
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Agent-Earns production services")
    parser.add_argument(
        "--webhook-only",
        action="store_true",
        help="Only start webhook server (port from PORT or 8787)",
    )
    parser.add_argument(
        "--agent-once",
        action="store_true",
        help="After starting services, run one Atlas cycle (start_agent.py --once)",
    )
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8787")))
    args = parser.parse_args()

    warn = _check_env()
    if warn:
        print("Warning — missing optional env:")
        for w in warn:
            print(f"  - {w}")

    port = args.port
    py = sys.executable

    if args.webhook_only:
        print(f"Starting webhook server on 0.0.0.0:{port} ...")
        subprocess.run(
            [py, str(ROOT / "scripts" / "run_instantly_webhook.py"), "--host", "0.0.0.0", "--port", str(port)],
            cwd=str(ROOT),
        )
        return

    print("Starting production stack:")
    print(f"  1) Webhooks http://0.0.0.0:{port}")
    print("  2) Telegram approvals (polling)")
    print("Press Ctrl+C to stop both.\n")

    webhook = subprocess.Popen(
        [py, str(ROOT / "scripts" / "run_instantly_webhook.py"), "--host", "0.0.0.0", "--port", str(port)],
        cwd=str(ROOT),
    )
    telegram = subprocess.Popen(
        [py, str(ROOT / "scripts" / "run_telegram_approvals.py")],
        cwd=str(ROOT),
    )

    if args.agent_once:
        subprocess.run(
            [py, str(ROOT / "start_agent.py"), "--once"],
            cwd=str(ROOT),
        )

    try:
        webhook.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for proc in (telegram, webhook):
            if proc.poll() is None:
                proc.terminate()
        for proc in (telegram, webhook):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    main()
