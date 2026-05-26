"""
Webhook server + public HTTPS tunnel (Python ngrok — no CLI install needed).

1. Sign up: https://dashboard.ngrok.com/get-started/your-authtoken
2. Add to .env:  NGROK_AUTHTOKEN=your_token_here
3. Run:

   python scripts/run_webhooks_tunnel.py

4. Copy the printed URL into Razorpay:
   https://xxxx.ngrok-free.app/webhooks/razorpay
"""

from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Load .env before ngrok
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _run_uvicorn(host: str, port: int) -> None:
    import uvicorn

    uvicorn.run(
        "api.instantly_webhook:app",
        host=host,
        port=port,
        log_level="info",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    token = (os.getenv("NGROK_AUTHTOKEN") or "").strip()
    if not token:
        print(
            "Missing NGROK_AUTHTOKEN in .env\n\n"
            "1. https://dashboard.ngrok.com/get-started/your-authtoken\n"
            "2. Add: NGROK_AUTHTOKEN=...\n"
            "3. Run this script again\n\n"
            "Or install ngrok CLI: https://ngrok.com/download"
        )
        sys.exit(1)

    server = threading.Thread(
        target=_run_uvicorn,
        args=(args.host, args.port),
        daemon=True,
    )
    server.start()
    time.sleep(1.5)

    import ngrok

    listener = ngrok.forward(
        args.port,
        authtoken=token,
        bind_tls=True,
    )
    public = listener.url()
    if callable(public):
        public = public()

    webhook_base = public.rstrip("/")
    print("\n" + "=" * 60)
    print("  Webhooks are live")
    print("=" * 60)
    print(f"  Public URL:     {webhook_base}")
    print(f"  Razorpay:       {webhook_base}/webhooks/razorpay")
    print(f"  Instantly:      {webhook_base}/webhooks/instantly")
    print(f"  Health:         {webhook_base}/health")
    print("=" * 60)
    print("\nPaste the Razorpay URL in Dashboard → Webhooks → Create")
    print("Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        try:
            ngrok.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()
