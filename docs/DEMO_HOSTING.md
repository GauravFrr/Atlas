# Demo hosting stack

**Your setup (default `auto` + `DEMO_HOST_STRATEGY=random`):**

Each demo randomly picks one host:

- `https://demos.gauravxd.dev/{slug}/`
- `https://demos.urmikexd.me/{slug}/`
- **Netlify** (pool in `.env` + `data/netlify_accounts.json`)

If that host fails, the others are tried in the same shuffled order, then **Cloudflare R2** last (`DEMO_PREFER_R2=false`).

Old fixed order: `DEMO_HOST_STRATEGY=priority` (Netlify → Hostinger → R2).

## Recommended at 70%+ Netlify usage

### Option A — Cloudflare R2 (best for volume)

1. Create a free Cloudflare account → R2 bucket → enable public access or custom domain.
2. In `.env`:

```env
DEMO_UPLOAD_MODE=auto
DEMO_PREFER_R2=true
DEMO_SITE_BASE_URL=https://demos.gauravxd.dev
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
```

See `docs/GAURAVXD_R2_DOMAIN.md` for custom domain setup.

Demos upload to R2; Netlify is skipped unless R2 fails.

### Option B — Hostinger FTP (you already pay for hosting)

```env
DEMO_UPLOAD_MODE=ftp
DEMO_SITE_BASE_URL=https://gauravxd.dev/demos
FTP_HOST=ftp.hostinger.com
FTP_USER=...
FTP_PASSWORD=...
FTP_REMOTE_BASE=public_html/demos
```

Unlimited demos on your own disk — no Netlify bandwidth.

### Option C — Extra Netlify sites you own (manual)

If you create a **second real Netlify account** (your own email, verified normally):

1. Create a new site → Site settings → copy **Site ID** and create a **Personal access token**.
2. Copy `data/netlify_accounts.example.json` → `data/netlify_accounts.json`.
3. Add the backup site (primary stays in `.env`).

```env
NETLIFY_ACCOUNTS_FILE=data/netlify_accounts.json
```

The agent rotates deploys across accounts and falls back to R2/FTP if deploy fails (e.g. credits exhausted).

## Modes

| `DEMO_UPLOAD_MODE` | Behavior |
|--------------------|----------|
| `auto` | Netlify pool → R2 → FTP (or R2 first if `DEMO_PREFER_R2=true`) |
| `netlify` | Netlify pool only |
| `r2` | R2 only |
| `ftp` | FTP only |
| `local` | No upload; URL from `DEMO_SITE_BASE_URL` only |

## Why not temp-mail automation?

- Against Netlify ToS and often illegal (fraudulent account creation).
- Accounts get deleted; tokens stop working mid-campaign.
- R2/FTP are cheaper, stable, and already built into this repo.
