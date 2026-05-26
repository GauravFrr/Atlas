# Deploy webhooks on Railway (24/7)

Use Railway so Razorpay and Instantly always reach your app — no Cloudflare tunnel on your PC.

## 1. Create project

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub (or CLI).
2. Root directory: repo root (`Agent-Earns`).
3. Railway reads `railway.toml` → `python scripts/railway_start.py` (role from env).
4. Port: Railway sets `PORT` automatically on the webhook service.

### Two services, same repo (`railway.toml` locks the start command)

| Service | Variable | What runs |
|---------|----------|-----------|
| **Service 1 (webhooks)** | *(none)* or `RAILWAY_SERVICE_ROLE=webhook` | Webhooks + `/health` |
| **Service 2 (Telegram)** | `RAILWAY_SERVICE_ROLE=telegram` | `run_telegram_approvals.py` |

You **cannot** edit the start command in the Railway UI while `railway.toml` sets it — use the variable above on Service 2 instead.

**Service 1 only:** Settings → Deploy → Healthcheck Path = `/health`
**Service 2:** leave healthcheck **off** (no HTTP server).

## 2. Environment variables

Copy from `.env` into Railway → Variables:

| Variable | Required |
|----------|----------|
| `RAZORPAY_KEY_ID` | Yes |
| `RAZORPAY_KEY_SECRET` | Yes |
| `RAZORPAY_WEBHOOK_SECRET` | Yes |
| `TELEGRAM_BOT_TOKEN` | Yes (approvals on your phone) |
| `TELEGRAM_CHAT_ID` | Yes |
| `INSTANTLY_API_KEY` | If using Instantly |
| `INSTANTLY_CAMPAIGN_ID` | If using Instantly |
| `INSTANTLY_WEBHOOK_SECRET` | Optional header check |
| `SMTP_*` | For Approve → send (same as local) |
| `DATABASE_URL` | Optional; default SQLite on volume — prefer Railway volume mount at `/data` |

For SQLite persistence, add a **Volume** mounted at `F:\Agent-Earns` path in container as `/app/data` and set:

```bash
DATABASE_URL=sqlite+aiosqlite:////app/data/agent.db
```

## 3. Public URL

Railway → Settings → Networking → **Generate domain**

Example: `https://agent-earns-production.up.railway.app`

## 4. Register webhooks

**Razorpay** → Webhooks:

```text
https://YOUR-RAILWAY-DOMAIN/webhooks/razorpay
```

Events: `payment_link.paid`, `payment.captured`  
Secret = `RAZORPAY_WEBHOOK_SECRET`

**Instantly** → Webhooks:

```text
https://YOUR-RAILWAY-DOMAIN/webhooks/instantly
```

Event: `reply_received`  
Header `X-Webhook-Secret` = `INSTANTLY_WEBHOOK_SECRET` (if set)

## 5. Health check

```text
GET https://YOUR-RAILWAY-DOMAIN/health
```

## 6. Telegram approval bot (still local or second service)

Inline buttons need long polling. Options:

| Option | How |
|--------|-----|
| **A (simple)** | Keep on your PC: `python scripts/run_telegram_approvals.py` |
| **B** | Second Railway service: set variable `RAILWAY_SERVICE_ROLE=telegram` |

Webhook server and Telegram bot can be separate services (same `railway.toml` start command).

## 7. Verify

```bash
curl https://YOUR-RAILWAY-DOMAIN/health
curl https://YOUR-RAILWAY-DOMAIN/webhooks/razorpay
```

Local dev unchanged:

```bash
python scripts/run_instantly_webhook.py --port 8787
```
