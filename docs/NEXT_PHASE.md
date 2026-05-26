# Agent-Earns — Next phase (after Week-1 proof)

Week 1 proved the pipeline: **mock lead → demo (R2) → email (Gaurav) → Instantly**.

Phase 2 is **real outreach that converts**, not more plumbing.

---

## Phase 2A — Ship-ready outreach (do this first)

### 1. One clean production test (today)

- Delete old test leads in Instantly (wrong `body_1` / Mikey / broken URLs).
- Re-run:

```bash
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 1 --instantly --test-to YOUR@gmail.com
```

- Confirm in Instantly lead: `— Gaurav`, link ends with `/index.html`, campaign **resumed**.

### 2. Deliverability (spam → inbox)

| Action | Why |
|--------|-----|
| Mark test as **Not spam** in Gmail | Trains your address on the sender |
| Stop re-sending the same test 4× to one Gmail | Looks like abuse |
| Keep Instantly: 10/day, 2 min gap, warmup on, stop on reply | Already set |
| Optional: `demos.gauravxd.dev` on R2 (see `docs/GAURAVXD_R2_DOMAIN.md`) | Shorter, trusted links vs `pub-….r2.dev` |

### 3. Live leads (when Google Places billing works)

```bash
# .env: GOOGLE_PLACES_API_KEY=...
python scripts/run_campaign.py --niche plumber --city "Austin TX" --leads 5 --instantly
```

- Leads without email: enrich with Hunter (`HUNTER_API_KEY`) or skip until manual email added.
- No `--test-to` (real business emails only).

---

## Phase 2B — Lead intake & quality

| Feature | Status |
|---------|--------|
| **CSV import** | Done — `--csv data/leads.csv` |
| **Spam word check** | Done — warns on push; `--strict-spam` blocks |
| **Demo hosting options** | Done — see `docs/DEMO_HOSTING_OPTIONS.md` (R2 pub URL = no NS change) |
| **Hostinger FTP demos** | Done — `DEMO_UPLOAD_MODE=ftp` |
| Google Maps live scan | Blocked on API billing |
| Hunter email enrich | Wired — `HUNTER_API_KEY` |
| `pricing_tiers.json` | Not wired yet |

```bash
python scripts/run_campaign.py --csv data/leads.csv --niche real_estate --city London --leads 2 --instantly
```

---

## Phase 2C — Replies & close

| Feature | Status | Goal |
|---------|--------|------|
| Instantly reply sync | **Done** | `scripts/sync_instantly_replies.py`, `run_reply_daemon.py`, webhook — see `docs/REPLY_SYNC.md` |
| Reply classifier (LLM) | **Done** | Keywords + optional LLM; Telegram hot alerts |
| Fiverr / close scripts | Partial | `data/close_templates/interested_reply.txt` |
| Sequence timing | Instantly handles Day 2/3 | Agent only needs Email 1 quality |

You already have Email 2/3 in `mikey_sequence.py` → pushed as `body_2`, `body_3` to Instantly.

---

## Phase 3 — Autopilot

| Feature | Goal |
|---------|------|
| Daily cron / `scripts/daily_campaign.py` | Set `DAILY_CAMPAIGN_CSV` in `.env` |
| Dashboard | **Done** — `python scripts/run_dashboard.py` (admin + `DASHBOARD_PASSWORD`) |
| Multi-city rotation | `TARGET_CITIES` in `google_maps.py` |
| Metrics | Sent / opened / replied in `agent.db` + Instantly analytics |
| `demos.gauravxd.dev` | Custom domain on R2 for all preview links |

---

## What’s done (don’t redo)

- Campaign orchestrator + memory bank dedup
- Hybrid / Instantly / SMTP send router
- Mikey-style Email 1 (Saw … But noticed …)
- R2 upload + **`/index.html`** public URLs
- Instantly variables: `body_1`, `body_2`, `body_3`, subjects
- `--mock --fresh --test-to` for safe E2E tests
- Sign-off: **Gaurav** via `YOUR_NAME`

---

## Recommended order (this week)

1. **Phase 2A** — one fixed Instantly test to inbox (not spam).
2. **Google Places OR CSV** — first 5–10 *real* prospects (not your Gmail).
3. **`demos.gauravxd.dev`** — link trust (optional but high impact).
4. **Hunter** — emails for leads with websites only.
5. **Reply handling** — so interested replies don’t get lost.

---

## Commands cheat sheet

```bash
# E2E test (your inbox)
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 1 --instantly --test-to you@gmail.com

# Live (when Places API ready)
python scripts/run_campaign.py --niche plumber --city "Austin TX" --leads 5 --instantly

# Draft only (no send)
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 3

# Health check
python scripts/test_all_apis.py
```

---

## Blockers you already know

| Blocker | Workaround |
|---------|------------|
| Google Places billing | `--mock` or CSV leads |
| Test emails in spam | Not spam + fewer self-tests + custom demo domain |
| Old Instantly `body_1` | Delete lead & re-push with `--fresh` |

When you pick the first item to implement (CSV import, spam filter, reply webhook, or custom domain), say which one and we build it next.
