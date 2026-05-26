"""
Start webhook server — Instantly replies + Razorpay payments.

  python scripts/run_instantly_webhook.py --port 8787

Expose with ngrok: ngrok http 8787
  Instantly → /webhooks/instantly
  Razorpay  → /webhooks/razorpay
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8787")),
    )
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    uvicorn.run(
        "api.instantly_webhook:app",
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
