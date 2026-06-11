# Production run — 24/7 stack

Blueprint: **webhooks always on** → **Telegram approvals** → **Atlas loop** (optional third service).

---

## Local (Windows)

```powershell
cd F:\Agent-Earns
.\venv\Scripts\activate
python scripts/run_production_stack.py
```

Starts:
1. Webhook server (`PORT` or 8787) — Razorpay + Instantly
2. Telegram bot — Approve / Recreate / Skip / payment draft

One Atlas tick after startup:

```powershell
python scripts/run_production_stack.py --agent-once
```

Webhook only:

```powershell
python scripts/run_production_stack.py --webhook-only
```

Full Atlas 24/7 (separate terminal):

```powershell
python start_agent.py
```

---

## Railway (recommended)

### Service 1 — Webhooks
- Start: `python scripts/run_instantly_webhook.py --host 0.0.0.0`
- Health: `GET /health`
- See `docs/RAILWAY.md` for env vars + webhook URLs

### Service 2 — Telegram
- Start: `python scripts/run_telegram_approvals.py`
- Same env as local (`TELEGRAM_*`, `SMTP_*`, `INSTANTLY_*`, DB path)

### Service 3 — Atlas
- Variable: `RAILWAY_SERVICE_ROLE=agent`
- Start: `python start_agent.py`

### Shared SQLite volume (all 3 services)
- Mount **`/app/data`** on webhooks + Telegram + Atlas
- `DATABASE_URL=sqlite+aiosqlite:////app/data/agent.db` in **Shared Variables**
- Without this, reply sync shows `not in memory bank` (split DB per container)

---

## `.env` checklist

| Variable | Purpose |
|----------|---------|
| `INSTANTLY_API_KEY` | Push leads + warmup |
| `INSTANTLY_CAMPAIGN_ID` | Campaign UUID |
| `EMAIL_SEND_MODE=instantly` | No raw SMTP cold send |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | Approvals |
| `RAZORPAY_*` | Payment links + webhooks |
| `SMTP_PASSWORD` | Approve → send from locked mailbox |
| `USD_TO_INR_RATE=85` | Payment amount from `pricing_tiers.json` |

---

## After Instantly DNS is green

1. Test one lead:
   ```powershell
   python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 1 --instantly --test-to YOUR@gmail.com
   ```
2. Run production stack locally or deploy Railway services 1 + 2.
3. Start Atlas: `python start_agent.py` or `--once` for a single cycle.

---

## Post-payment delivery (blueprint §22)

When Razorpay webhook confirms payment:

1. Lead → `client`
2. `enrichment_data.delivery` = checklist (website / rebuild / automation)
3. **Telegram** — paid + demo URL + numbered checklist

Test without paying:

```powershell
python scripts/test_payment_handoff.py --email LEAD@EMAIL.com --dry-run
python scripts/test_payment_handoff.py --email LEAD@EMAIL.com
```

Atlas P2 may remind you if delivery stays `pending`.

---

## New features in this build

| Feature | What |
|---------|------|
| **Pricing tiers** | Razorpay amount from lead pitch (`utils/pricing_tiers.py`) |
| **Post-payment handoff** | `modules/service_delivery/payment_handoff.py` |
| **Agent logs** | Each tick task → `agent_logs` table |
| **Resume dedupe** | Same incomplete lead skipped for `RESUME_COOLDOWN_MINUTES` (default 25) |
| **Production stack** | `scripts/run_production_stack.py` |

View recent agent logs:

```powershell
python scripts/list_agent_logs.py
```
