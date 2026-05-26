# Business email for outreach (@gauravxd.dev)

Send cold emails **from your domain** (e.g. `hello@gauravxd.dev`) — not your personal Gmail inbox.

The agent uses **SMTP** with the mailbox your domain provider gives you. That is separate from Landingsite (website) and from R2 (demos).

---

## Step 1 — Create a mailbox on your domain

Pick **one** provider and create an address like:

- `hello@gauravxd.dev` or `gaurav@gauravxd.dev`

| Provider | Good for | Cost |
|----------|----------|------|
| **Zoho Mail** | Indie domains, simple SMTP | Free (1 domain) |
| **Google Workspace** | Gmail UI for @gauravxd.dev | Paid |
| **Microsoft 365** | Outlook for @gauravxd.dev | Paid |
| **Hostinger / Namecheap email** | If you bought email with the domain | Often bundled |

**Landingsite** hosts your portfolio; it does **not** replace this. You need an **email host** for `@gauravxd.dev`.

### Zoho (recommended if you want free)

1. [https://www.zoho.com/mail/](https://www.zoho.com/mail/) → add domain `gauravxd.dev`
2. Add the DNS records Zoho shows (MX + TXT) where your domain DNS lives
3. Create mailbox `hello@gauravxd.dev`
4. Zoho → **Settings** → **Mail Accounts** → **SMTP** → note server `smtp.zoho.com`

---

## Step 2 — Create an app password (not your login password)

Use a **dedicated SMTP password** from the provider:

| Provider | Where |
|----------|--------|
| Zoho | Security → App Passwords → generate for "Agent Earns" |
| Google Workspace | Google Account → Security → 2FA → App passwords |
| Microsoft | Account security → App password |

This is for **`hello@gauravxd.dev`**, not `you@gmail.com`.

---

## Step 3 — `.env` for Agent-Earns

Example for **Zoho** + `hello@gauravxd.dev`:

```env
YOUR_NAME=Gaurav
YOUR_EMAIL=hello@gauravxd.dev

SMTP_PROVIDER=zoho
SMTP_USER=hello@gauravxd.dev
SMTP_PASSWORD=your_zoho_app_password_here
SMTP_FROM_EMAIL=hello@gauravxd.dev
SMTP_FROM_NAME=Gaurav
SMTP_PORT=587
SMTP_USE_SSL=false
```

Example for **Google Workspace** (`@gauravxd.dev` on Google):

```env
SMTP_PROVIDER=google_workspace
SMTP_USER=hello@gauravxd.dev
SMTP_PASSWORD=your_workspace_app_password
SMTP_FROM_EMAIL=hello@gauravxd.dev
SMTP_FROM_NAME=Gaurav
```

If your host gave custom SMTP host/port:

```env
SMTP_PROVIDER=custom
SMTP_HOST=mail.gauravxd.dev
SMTP_PORT=587
SMTP_USER=hello@gauravxd.dev
SMTP_PASSWORD=...
```

---

## Step 4 — Test send

```bash
.\venv\Scripts\python scripts\test_smtp_send.py --to your-test@gmail.com
```

Check inbox: **From** should show `Gaurav <hello@gauravxd.dev>`.

---

## Step 5 — Campaign with live send

```bash
.\venv\Scripts\python scripts\run_campaign.py --mock --niche plumber --city "Austin TX" --leads 1 --send
```

Start with **mock** and a real address you control before emailing strangers.

---

## FAQ

**Is this my personal Gmail password?**  
No. Use only the mailbox on **gauravxd.dev** and its app password.

**Can I use Gmail API (GMAIL_* in .env)?**  
Optional later. SMTP + business address is enough for now.

**Deliverability**  
Send low volume at first (5–10/day). Warm up the new mailbox; avoid spam words.
