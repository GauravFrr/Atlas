# Production deploy — Railway / local

# Service 1 (webhooks): Razorpay + Instantly reply → Telegram draft
web: python scripts/run_instantly_webhook.py --host 0.0.0.0

# Service 2 (Telegram): Approve / Recreate / Skip + payment draft
# Railway: create second service with start command below
# telegram: python scripts/run_telegram_approvals.py

# Service 3 (optional): Atlas 24/7 loop
# worker: python start_agent.py
