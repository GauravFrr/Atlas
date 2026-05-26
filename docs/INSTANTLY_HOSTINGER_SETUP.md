# Instantly + Hostinger mailboxes (new workspace)

Use this when your **old** Instantly account only allows 2 mailboxes. Create a **new** workspace (Growth plan or higher for API v2), connect all Hostinger inboxes, and let **Instantly warmup** run before cold outreach.

---

## Can the agent connect mailboxes for you?

| Method | Who does it |
|--------|-------------|
| **Manual (recommended first time)** | You — ~5 min per inbox in Instantly UI |
| **Script (API)** | You run locally — API key + passwords stay in `.env` only |

We **cannot** log into your Instantly dashboard from here. Never paste API keys or email passwords in Telegram/chat.

---

## Your four mailboxes (from `data/outreach_domains.json`)

| Email | Brand domain |
|-------|----------------|
| `gaurav@gauravxd.dev` | gauravxd.dev |
| `gauravdev@gauravxd.dev` | gauravxd.dev |
| `mike@urmikexd.me` | urmikexd.me |
| `gauravdev@urmikexd.me` | urmikexd.me |

Landing sites (Netlify) are only used as **demo links** in email copy — not “connected” to Instantly.

---

## Part A — New Instantly account

1. Sign up for a **new** Instantly workspace (Growth Outreach or higher).
2. **Settings → Integrations → API** → create an **API v2** key with scopes:
   - `accounts:create`, `accounts:read`, `accounts:update` (or `all:all`)
3. Put in `.env` (replace old key if this workspace replaces the old one):

```env
INSTANTLY_API_KEY=your_v2_key_here
INSTANTLY_CAMPAIGN_ID=
EMAIL_SEND_MODE=instantly
```

4. Ensure `SMTP_PASSWORD=` in `.env` is the Hostinger password used by these mailboxes (or set per-row in `outreach_domains.json`).

---

## Part B — Manual connect (copy/paste per mailbox)

For **each** email above:

1. [Email Accounts](https://app.instantly.ai/app/accounts) → **Add New** → **IMAP/SMTP**
2. Enter:

| Field | Value |
|-------|--------|
| Email | `gaurav@gauravxd.dev` (full address) |
| IMAP host | `imap.hostinger.com` |
| IMAP port | `993` |
| IMAP security | SSL |
| SMTP host | `smtp.hostinger.com` |
| SMTP port | `587` (TLS) — if fail, try `465` SSL |
| Username | same full email |
| Password | Hostinger mailbox password |

3. After **Connected** → toggle **Warmup ON**
4. Repeat for all 4 addresses

**DNS (each domain in Hostinger hPanel):** add SPF/DKIM/DMARC Instantly and Hostinger show — fixes spam long-term.

---

## Part C — Script connect (optional)

After API key and `SMTP_PASSWORD` are in `.env`:

```powershell
cd F:\Agent-Earns
.\venv\Scripts\activate
python scripts/connect_instantly_mailboxes.py --dry-run
python scripts/connect_instantly_mailboxes.py
```

One mailbox only:

```powershell
python scripts/connect_instantly_mailboxes.py --only gaurav@gauravxd.dev
```

---

## Part D — Campaign + agent

1. Instantly → **Campaigns** → create e.g. “Plumber outreach — gauravxd”
2. **Sequences** use variables: `{{subject_1}}`, `{{body_1}}`, `{{demo_url}}`, etc. (see `docs/INSTANTLY_SETUP.md`)
3. **Settings** → attach **all 4** warmed accounts as senders
4. Copy campaign UUID → `INSTANTLY_CAMPAIGN_ID=...`
5. Run agent with Instantly (not raw SMTP):

```powershell
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 3 --instantly
```

---

## Warmup rules (important)

- **2–3 weeks** warmup before scaling cold volume
- Start **5–10 emails/day** per inbox in Instantly
- Do **not** use `EMAIL_SEND_MODE=smtp` for cold until warmup health is good
- Telegram **reply** sends can still use SMTP + mailbox lock on the same From address

---

## Fix “DNS Error” on all accounts (your screenshot)

The script **connected** all 4 mailboxes and enabled warmup. Instantly still shows **DNS Error** until **gauravxd.dev** and **urmikexd.me** have correct DNS in **Hostinger** (2 domains = “2 domains failed DNS check”).

### Per domain (do both `gauravxd.dev` and `urmikexd.me`)

1. **Hostinger hPanel** → **Emails** → **Manage** on the domain → **Connect Domain** / **DNS records** → tab **Protect your reputation** (or **Expected records**).
2. Add what Hostinger shows (usually):
   - **MX** — receive replies
   - **SPF** (TXT on `@`) — only **one** SPF per domain:
     ```
     v=spf1 include:_spf.mail.hostinger.com ~all
     ```
     [Hostinger SPF guide](https://www.hostinger.com/support/1583673-what-is-the-spf-record-for-hostinger-email/)
   - **DKIM** (TXT or CNAME Hostinger gives you)
     [Hostinger DKIM guide](https://www.hostinger.com/support/4456413-what-are-the-dkim-records-for-hostinger-email/)
   - **DMARC** (TXT on `_dmarc`):
     ```
     v=DMARC1; p=none; rua=mailto:you@gauravxd.dev
     ```
     [Hostinger DMARC guide](https://www.hostinger.com/support/8412851-how-to-add-a-dmarc-record-for-hostinger-email/)
3. **Delete duplicate SPF** TXT records if you have old ones (only one SPF allowed).
4. Wait **1–24 hours** for DNS propagation.
5. Instantly → **Email Accounts** → **Test domain setup** → fix anything still red.
6. Per account → **⋯** → **Reconnect email account** if status stays wrong after DNS is green.

Warmup (green flame) only helps deliverability **after** DNS passes. Until then health stays **0%**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| API 401 | Regenerate v2 key; not v1 key |
| `limit must be <= 100` warning | Fixed in script; harmless if accounts still created |
| Connect fails | Wrong password; try SMTP port 465 |
| DNS Error (all accounts) | MX + SPF + DKIM + DMARC in Hostinger for both domains |
| Still spam | DNS + 2–3 weeks warmup; volume too high |
| Agent not sending | `INSTANTLY_CAMPAIGN_ID` wrong; campaign paused |

---

## Old vs new workspace

- Email accounts live in **one workspace only**
- Point `.env` `INSTANTLY_API_KEY` at the **new** workspace after migration
- Old 2-mailbox account can stay for gauravstack.com or be retired
