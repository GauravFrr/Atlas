# Deploy webhooks on Railway (24/7)

Use Railway so Razorpay and Instantly always reach your app — no Cloudflare tunnel on your PC.

## 1. Create project

1. [railway.app](https://railway.app) → New Project → Deploy from GitHub (or CLI).
2. Root directory: repo root (`Agent-Earns`).
3. Railway reads `railway.toml` → `python scripts/railway_start.py` (role from env).
4. Port: Railway sets `PORT` automatically on the webhook service.

### Three services, same repo (`railway.toml` locks the start command)

| Service | Variable | What runs |
|---------|----------|-----------|
| **Service 1 (webhooks)** | *(none)* or `RAILWAY_SERVICE_ROLE=webhook` | Webhooks + `/health` |
| **Service 2 (Telegram)** | `RAILWAY_SERVICE_ROLE=telegram` | `run_telegram_approvals.py` |
| **Service 3 (Atlas)** | `RAILWAY_SERVICE_ROLE=agent` | `start_agent.py` (30-min loop) |

You **cannot** edit the start command in the Railway UI while `railway.toml` sets it — use the variable above per service.

**Service 1 only:** Settings → Deploy → Healthcheck Path = `/health`  
**Services 2 & 3:** leave healthcheck **off** (no HTTP server).

### Shared database (required for reply sync + approvals)

Without this, each service has its own empty `agent.db` → `not in memory bank` on Instantly replies.

**Recommended — Supabase Postgres (free, survives Railway outages):** see `docs/DATABASE.md`

```bash
DATABASE_URL=postgresql://postgres.xxxx:pass@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```

Set in **Shared Variables** on all 3 services. No volume needed.

**Alternative — SQLite on Railway volume** (data tied to Railway):

1. New Volume → attach to all 3 services at **`/app/data`**
2. `DATABASE_URL=sqlite+aiosqlite:////app/data/agent.db`

Redeploy all three services after changing DB config.

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
| `DATABASE_URL` | **Yes on Railway** — `sqlite+aiosqlite:////app/data/agent.db` + volume at `/app/data` |

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

## 6. Telegram approval bot (second Railway service)

| Option | How |
|--------|-----|
| **Local** | `python scripts/run_telegram_approvals.py` (long polling) |
| **Railway** | Service 2: `RAILWAY_SERVICE_ROLE=telegram` + **Generate domain** |

On Railway the bot uses **webhooks** (not long polling) so connections don’t drop with `httpx.ReadError`.

1. Telegram service → **Settings → Networking → Generate domain** (e.g. `atlas-telegram-production.up.railway.app`).
2. Railway sets `RAILWAY_PUBLIC_DOMAIN` automatically → webhook URL becomes `https://YOUR-DOMAIN/telegram/webhook`.
3. On **Service 2 (Telegram)** add (recommended — explicit):

| Variable | Value |
|----------|--------|
| `PORT` | `8080` |
| `TELEGRAM_WEBHOOK_URL` | `https://YOUR-TELEGRAM-DOMAIN.up.railway.app/telegram/webhook` |

Example: `https://service-2-telegram-production.up.railway.app/telegram/webhook`

4. Networking → domain port = **`8080`** (must match `PORT`).
5. Healthcheck path: `/health` on the **Telegram** service (not the webhook service).

Verify after deploy:

```bash
curl https://YOUR-TELEGRAM-DOMAIN/health
```

Logs should show: `Telegram webhook registered → https://...`

## 7. Verify

```bash
curl https://YOUR-RAILWAY-DOMAIN/health
curl https://YOUR-RAILWAY-DOMAIN/webhooks/razorpay
```

Local dev unchanged:

```bash
python scripts/run_instantly_webhook.py --port 8787
```
