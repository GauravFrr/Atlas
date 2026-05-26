# How to add the Mikey email sequence in Instantly

The agent writes **personalized** text per lead and sends it to Instantly via the **API** (no CSV import needed).

## How Instantly + API works (same idea you described)

1. You create the campaign in Instantly with placeholders in the sequence, e.g. `{{body_1}}` or `{{firstName}}`.
2. The agent calls the API and **adds each lead** with a `variables` object (Instantly calls this `custom_variables`).
3. When Instantly sends, it **replaces** `{{...}}` with that lead’s values.

**Agent payload (conceptually):**

```json
{
  "email": "owner@plumber.com",
  "first_name": "Mike",
  "company_name": "Austin Precision Plumbing",
  "custom_variables": {
    "firstName": "Mike",
    "companyName": "Austin Precision Plumbing",
    "company": "Austin Precision Plumbing",
    "icebreaker": "I checked out austin-precision-plumbing/ and noticed...",
    "demo_url": "https://pub-xxx.r2.dev/austin-precision-plumbing/",
    "body_1": "Hey Mike,\n\nI checked out...",
    "body_2": "...",
    "body_3": "...",
    "subject_1a": "quick question, mike",
    "subject_1b": "saw something on your site"
  }
}
```

**Your Instantly template** only needs:

```
{{body_1}}
```

Instantly fills the full email at send time — you don’t import leads manually.

---

The agent writes **personalized** text per lead.  
Your campaign only needs to **paste those variables** — not fixed text.

---

## Auto-resume campaign / accounts / warmup

Before pushing leads, the agent can call Instantly API to:

| Check | Action |
|-------|--------|
| Campaign paused (`status=2`) | `POST /campaigns/{id}/activate` |
| Sending account paused | `POST /accounts/{email}/resume` |
| Warmup off (`warmup_status≠1`) | `POST /accounts/warmup/enable` |

On by default: `INSTANTLY_AUTO_PREPARE=true` in `.env` (set `false` to disable).

Manual run:

```bash
python scripts/instantly_ensure_ready.py
```

Uses mailboxes on the campaign (`email_list` from API — e.g. `gauravdev@gauravstack.com`, `gauravxd@gauravstack.com`).

---

## Leads missing in Instantly UI?

If the agent logged “Added lead” but you only see one lead:

1. **Old bug:** `skip_if_in_workspace=true` made Instantly return HTTP 200 with **`leads_uploaded: 0`** when the email already existed in another campaign (e.g. “Real Estate - AI Automation Outreach”). Fixed in code — now uses `skip_if_in_workspace=false`.

2. **Re-push from export:**
   ```bash
   python scripts/instantly_repush_csv.py outputs/instantly/leads_afeee9d0.csv
   ```

3. **Verify via API:**
   ```bash
   python scripts/instantly_list_leads.py
   ```

4. In Instantly UI: open campaign **Agent-Earns** → **Leads** (not global “All leads” with wrong filters).

Empty **BODY** column in UI is normal — email text lives in variables `body_1`, `body_2`, etc. Sequences must use `{{body_1}}` as in the table below.

---

## Easiest setup (recommended)

Use **3 steps** in Instantly. Each body is **only one line**:

| Step | Wait after previous | Subject A | Subject B | Body |
|------|---------------------|-----------|-----------|------|
| 1 | — (Day 1) | `{{subject_1a}}` | `{{subject_1b}}` | `{{body_1}}` |
| 2 | **2 days** | `{{subject_2a}}` | `{{subject_2b}}` | `{{body_2}}` |
| 3 | **3 days** | `{{subject_3a}}` | `{{subject_3b}}` | `{{body_3}}` |

Optional 4th (ghost, ~2 weeks later):

| Step | Wait | Subject | Body |
|------|------|---------|------|
| 4 | **14 days** | `{{subject_4a}}` | `{{body_4}}` |

Turn on **Stop sequence when lead replies**.

Plain text only — no HTML, no images.

---

## Step-by-step in Instantly UI

### 1. Open your campaign

Instantly → **Campaigns** → open the campaign that matches `INSTANTLY_CAMPAIGN_ID` in `.env`.

### 2. Campaign settings (keep yours)

- Daily limit: **10** (or your choice)
- Min wait: **2 minutes**
- Warmup: **On**
- **Stop on reply:** **Yes**
- Tracking domain: `inst.gauravstack.com` (already set)

### 3. Add custom variables (one time)

Go to **Campaign** → **Variables** / **Custom fields** (wording varies).

Add these names **exactly** (copy-paste):

```
firstName
companyName
icebreaker
demo_url
body_1
body_2
body_3
body_4
subject_1a
subject_1b
subject_2a
subject_2b
subject_3a
subject_3b
subject_4a
```

The agent fills them when you run with `--instantly` or `--send-mode hybrid`.

### 4. Sequence → Step 1 (Email 1)

- **Subject line A:** `{{subject_1a}}`
- **Subject line B:** `{{subject_1b}}`
- **Body:** only this:

```
{{body_1}}
```

- Delay before step 1: **0 days** (sends when lead is added)

### 5. Sequence → Step 2 (Email 2)

- **Wait:** **2 days** after step 1
- **Subject A:** `{{subject_2a}}`
- **Subject B:** `{{subject_2b}}`
- **Body:**

```
{{body_2}}
```

### 6. Sequence → Step 3 (Email 3)

- **Wait:** **3 days** after step 2
- **Subject A:** `{{subject_3a}}`
- **Subject B:** `{{subject_3b}}`
- **Body:**

```
{{body_3}}
```

### 7. Optional — Step 4 (ghost)

- **Wait:** **14 days** after step 3
- **Subject:** `{{subject_4a}}`
- **Body:** `{{body_4}}`

### 8. Activate campaign

Status = **Active** so new leads from the agent get emails.

---

## What `body_1` looks like (example)

The agent generates something like this (plain text, under 100 words):

```
Hey Mike,

I checked out austin-precision-plumbing/ and noticed you're not online yet — most plumber businesses in Austin TX still handle new enquiries manually.

I build modern websites and simple lead capture for local plumber businesses — so when someone finds you online or reaches out after hours, you look professional and don't lose jobs to slow follow-up.

I put together a quick preview for Austin Precision Plumbing if you want a look:
https://pub-xxxxx.r2.dev/austin-precision-plumbing/

Would that kind of system be useful for what you're building at Austin Precision Plumbing?

— Mikey
```

You do **not** type this in Instantly — only `{{body_1}}`.

---

## Real estate niche

Same 3 steps with `{{body_1}}`, `{{body_2}}`, `{{body_3}}`.

Run agent with:

```bash
python scripts/run_campaign.py --niche real_estate --city "Austin TX" --leads 5 --instantly
```

Email 1 offer line will be your **AI chatbot + automation** copy automatically.

---

## Alternative: build the email inside Instantly

If you prefer a fixed template + only the icebreaker changes:

**Step 1 body:**

```
Hey {{firstName}},

{{icebreaker}}

I build modern websites and simple lead capture for local businesses — so when someone finds you online, you look professional and don't lose jobs to slow follow-up.

{{demo_url}}

Would that be useful for what you're building at {{companyName}}?

— Mikey
```

Use **real estate** offer paragraph in Instantly if that niche only.

This needs you to maintain copy in Instantly; **Option A (`{{body_1}}`) is easier** because the agent owns the full text.

---

## Test before bulk send

1. Run agent for **1 lead** with your email as test:

   Add your email to a mock lead or send:

   ```bash
   python scripts/send_test_email.py --to YOUR@gmail.com --method instantly
   ```

2. In Instantly → **Leads** → open the lead → check custom variables are filled.

3. Send **Preview** in Instantly if available.

---

## Timing cheat sheet (Mikey strategy)

| Email | Strategy day | Instantly wait |
|-------|----------------|----------------|
| 1 | Day 1 | 0 days from add |
| 2 | Day 3 | +2 days after email 1 |
| 3 | Day 6 | +3 days after email 2 |
| Ghost | ~Day 20 | +14 days after email 3 |

---

## When agent runs

```bash
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 3 --instantly
```

Or:

```bash
python scripts/run_campaign.py ... --send-mode hybrid
```

Check: Instantly → **Leads** → new row with variables populated.

---

## If emails send blank

- Body must be exactly `{{body_1}}` not `{{body1}}` or `{body_1}`
- Variable names in Instantly must match the list in step 3
- Campaign must be **Active**
- Lead must have been added **by API** after templates were saved
