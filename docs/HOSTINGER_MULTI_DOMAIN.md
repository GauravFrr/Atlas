# Multiple Hostinger domains (random rotation)

Use several domains (gauravstack.com, gauravxd.dev, …) so each lead gets:

- A **demo link** on one of your domains (spread reputation)
- Optionally a **different mailbox** when using SMTP
- Optionally a **different Instantly campaign** per domain

Rotation is **stable per lead** (same business always gets the same domain), not chaotic random every time.

---

## What rotates vs what Instantly already does

| Piece | Who handles it |
|-------|----------------|
| **Sending mailboxes** on many domains | **Instantly** (connect all domains + mailboxes in Instantly UI) |
| **Demo URL domain** in the email | **Agent** (this feature) |
| **SMTP from address** (if you use `--send`) | **Agent** (picks domain from JSON) |

If you use **Instantly only**, you still add multiple domains in Instantly for sending. The JSON file mainly changes **`demo_base_url`** per lead so links look like `demos.gauravstack.com` vs `demos.gauravxd.dev`.

---

## Setup

### 1. Hostinger — one mailbox per domain

For each domain in Hostinger:

1. **Emails** → create `hello@yourdomain.com`
2. Note SMTP: usually `smtp.hostinger.com`, port `587`
3. Use that mailbox’s password (or app password)

### 2. Demo URLs per domain

Each domain needs a public URL for demos:

- **Same R2 bucket**, multiple custom domains in Cloudflare (e.g. `demos.gauravstack.com` + `demos.gauravxd.dev` → same files), **or**
- Keep one `pub-....r2.dev` URL on all entries until DNS is ready

### 3. Copy config file

```bash
copy data\outreach_domains.example.json data\outreach_domains.json
```

Edit `data/outreach_domains.json` — add every Hostinger domain (passwords stay local; file is gitignored).

### 4. `.env`

```env
OUTREACH_DOMAINS_FILE=data/outreach_domains.json

# Still need one R2 upload target (same bucket for all)
DEMO_SITE_BASE_URL=https://pub-xxxxx.r2.dev
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
R2_ENDPOINT_URL=...

# Instantly (optional — one default campaign)
INSTANTLY_API_KEY=...
INSTANTLY_CAMPAIGN_ID=...
```

Per-domain Instantly campaign (optional):

```json
"instantly_campaign_id": "uuid-for-this-domain-only"
```

---

## Example JSON

```json
[
  {
    "name": "gauravstack",
    "demo_base_url": "https://demos.gauravstack.com",
    "smtp_user": "hello@gauravstack.com",
    "smtp_password": "..."
  },
  {
    "name": "gauravxd",
    "demo_base_url": "https://demos.gauravxd.dev",
    "smtp_user": "hello@gauravxd.dev",
    "smtp_password": "..."
  }
]
```

Lead A → always gauravstack  
Lead B → always gauravxd  
Lead C → back to gauravstack (if 2 domains, hash alternates)

---

## Run campaign

```bash
python scripts/run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 5
```

Watch logs: `[Domain] Using 'gauravstack' for ...`

---

## Instantly + multiple domains (recommended)

1. Connect **all** Hostinger mailboxes in Instantly (you already have 2 on gauravstack.com).
2. Add more domains in Instantly the same way.
3. Instantly **rotates senders** — no extra agent code needed for sending.
4. Use `outreach_domains.json` so **demo links** match the brand domain you want in each email.

---

## Security

- Put real passwords only in `data/outreach_domains.json`
- Do not commit that file (listed in `.gitignore`)
