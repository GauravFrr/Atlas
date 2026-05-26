# Agent-Earns — agent instructions

## Before every task

Read first:

1. `docs/ULTIMATE_AGENT_BLUEPRINT_V3.md`
2. `docs/AGENT_EARNING_METHODS.md`

Do not invent startup or pipeline logic that conflicts with those docs.

## How to start (one command)

```bash
python start_agent.py
```

This runs the blueprint flow: **startup → health check → 30-minute Atlas loop → decision engine → execute**.

Test one cycle:

```bash
python start_agent.py --once
```

Optional dashboard: `python main.py` (Atlas + UI on port 8000).

## Lead pipeline (email-first)

1. Find email (scan, YouTube About, Hunter/scrape) **before** any demo or draft.
2. If no email → lead is discarded (soft-deleted); no LLM demo spend.
3. Cleanup old rows: `python scripts/cleanup_no_email_leads.py`

## Payments (Razorpay)

- Keys: `RAZORPAY_*` in `.env` — see `docs/PAYMENTS.md`
- Reply scripts: `data/close_templates/universal_reply_scripts.md` (website leads use `script_1_website.txt`)
- Payment link = **separate** approved email (not in first reply)
- Webhooks local: `python scripts/run_instantly_webhook.py` — production: `docs/RAILWAY.md`
- Telegram: `python scripts/run_telegram_approvals.py` + auto-draft on Instantly reply/webhook

## Outreach rules (blueprint)

| Lead | Pitch |
|------|--------|
| No website | Website + lead capture |
| Outdated site | Rebuild |
| Modern site | Automation only (not new website) |

Supporting docs: `docs/MIKEY_EMAIL_STRATEGY.md`, `docs/DEMO_HOSTING.md`, `docs/INSTANTLY_SETUP.md`.

**Mailbox lock:** First successful outbound sets `enrichment_data.outbound_mailbox`; all later SMTP (follow-ups, Telegram-approved replies, payment) reuse that From. Backfill: `python scripts/lock_lead_mailbox.py --email … --from …`.

**Production stack:** `python scripts/run_production_stack.py` — webhooks + Telegram. See `docs/PRODUCTION_RUN.md`.
