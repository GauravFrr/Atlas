# Instantly.ai + Agent-Earns (gauravstack.com, 2 mailboxes)

You already run **Instantly** with warmed mailboxes, daily limits, and tracking on **gauravstack.com**.  
The agent does **not** replace Instantly — it:

1. Finds leads + builds demos + writes Gaurav copy  
2. **Pushes each lead** into your Instantly campaign with variables (`demo_url`, `body_1`, …)  
3. **Instantly sends** from your 2 mailboxes using your limits (10/day, 2 min gap, warmup)

You do **not** need personal Gmail SMTP or Zoho if you use this path.

---

## Your Instantly settings (keep as-is)

| Setting | Your value | Note |
|---------|------------|------|
| Daily limit | 10 emails | Agent respects `max_emails_per_day` too |
| Min wait | 2 minutes | Instantly handles between sends |
| Warmup | On | Keep enabled |
| Tracking | `inst.gauravstack.com` | CNAME already verified |
| Mailboxes | 2 | Connected in Instantly |

---

## Step 1 — API key

1. Instantly → **Settings** → **Integrations** → **API** (or API v2)  
2. Create API key → copy to `.env`:

```env
INSTANTLY_API_KEY=your_api_key_here
```

---

## Step 2 — Campaign ID

1. Instantly → **Campaigns** → open your plumber / local outreach campaign (or create one)  
2. Copy **Campaign ID** (UUID in URL or campaign settings)  

```env
INSTANTLY_CAMPAIGN_ID=your-campaign-uuid-here
```

Campaign must be **Active** (or set to start when leads are added).

---

## Step 3 — Email templates in Instantly (match agent variables)

In the campaign sequence, use **custom variables** the agent sends:

| Variable | Use in template |
|----------|-----------------|
| `{{business_name}}` | Company name |
| `{{demo_url}}` | Link to R2 demo |
| `{{body_1}}` | Full plain-text Email 1 (optional: use whole body) |
| `{{body_2}}` | Follow-up 2 |
| `{{body_3}}` | Follow-up 3 |
| `{{subject_1}}` | Subject line email 1 |

**Option A — Simple (recommended):**  
- Step 1 subject: `{{subject_1}}`  
- Step 1 body: paste only:

```
{{body_1}}
```

- Step 2 body: `{{body_2}}`  
- Step 3 body: `{{body_3}}`  

The agent fills `body_1` with the full Gaurav sequence (greeting, demo link, sign-off).

**Option B — Instantly editor with inline vars:**  
Write your own template but insert `{{demo_url}}` and `{{business_name}}` where needed.

In Instantly → **Campaign** → **Variables** / custom fields: names must match exactly (`body_1`, `demo_url`, …).

---

## Step 4 — `.env` (minimal for Instantly path)

```env
YOUR_NAME=Gaurav

# Demos (R2 — pub URL or demos.gauravxd.dev later)
DEMO_SITE_BASE_URL=https://pub-xxxxx.r2.dev
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
R2_ENDPOINT_URL=https://YOUR_ACCOUNT.r2.cloudflarestorage.com
R2_AUTO_UPLOAD=true

# Instantly (sending)
INSTANTLY_API_KEY=...
INSTANTLY_CAMPAIGN_ID=...

# Optional: cap agent pushes per day (align with Instantly 10/day)
MAX_EMAILS_PER_DAY=10
```

You can leave **SMTP_*** empty when using `--instantly`.

---

## Step 5 — Run agent → Instantly

Dry run (drafts + CSV, no API push):

```bash
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 3
```

Live push to Instantly:

```bash
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 3 --instantly
```

Check:

- Instantly → campaign → **Leads** (new rows)  
- `outputs/instantly/leads_*.csv` (backup import)  
- `outputs/emails/draft_*.txt` (local copy)

---

## Flow diagram

```
Agent-Earns                    Instantly.ai
───────────                    ───────────
Mock/Maps leads
     ↓
Generate demo → R2 URL
     ↓
Gaurav email 1/2/3 text
     ↓
API: add lead + variables  →  Campaign queue
                              ↓
                         Mailbox 1 or 2
                              ↓
                         Prospect inbox
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API 401 | Regenerate `INSTANTLY_API_KEY` |
| Lead not added | Wrong `INSTANTLY_CAMPAIGN_ID`; campaign paused |
| Email blank | Template must use `{{body_1}}` not hardcoded text |
| Over daily limit | Lower `--leads` or Instantly daily cap (you use 10) |

---

## gauravxd.dev vs gauravstack.com

- **Instantly sending:** gauravstack.com mailboxes (already set up)  
- **Portfolio:** gauravxd.dev on Landingsite (unchanged)  
- **Demos:** R2 link in `{{demo_url}}` (custom domain optional later)
