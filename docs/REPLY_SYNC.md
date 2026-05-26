# Reply sync & alerts

When leads reply in Instantly, Agent-Earns can tag them in `agent.db` and ping you on **Telegram**.

## Setup

1. `.env`:
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   INSTANTLY_API_KEY=...
   INSTANTLY_CAMPAIGN_ID=...
   ```

2. **Poll (simple)** — run every 15 min or leave daemon on:
   ```bash
   python scripts/sync_instantly_replies.py
   python scripts/run_reply_daemon.py
   ```

3. **Webhook (instant)** — optional:
   ```bash
   python scripts/run_instantly_webhook.py --port 8787
   ```
   Expose with ngrok, add URL in Instantly → Webhooks → `reply_received`.  
   Set `INSTANTLY_WEBHOOK_SECRET` and same value in Instantly header `X-Webhook-Secret`.

## Classifications

| Label | DB status | Alert |
|--------|-----------|--------|
| interested | `replied` | 🔥 URGENT Telegram |
| not_now | `rejected` | info |
| unsubscribe | `unsubscribed` | warning |
| unknown | `replied` | optional (`REPLY_ALERT_ON_UNKNOWN=true`) |

Interested/unknown replies set `pending_reply_action` on the lead. The Atlas loop (P1) runs `modules.outreach.manager.handle_reply`, saves a draft under `outputs/emails/replies/`, and pings Telegram.

Copy for interested replies: `data/close_templates/interested_reply.txt`

## Follow-ups (SMTP only)

Leads sent via **SMTP** get `next_followup` scheduled (days 4, 8, 14, 21). **Instantly** leads rely on your Instantly campaign sequence; the agent only advances `sequence_step` in DB.

Atlas P2 runs `send_followups` when `followups_due` is non-empty.

## Daily automation

```bash
# .env: DAILY_CAMPAIGN_CSV=d:\batch2.csv
python scripts/daily_campaign.py
```

Task Scheduler (Windows): run `daily_campaign.py` once per day.
