# Demo hosting stack

**Default (`DEMO_UPLOAD_MODE=auto`, `DEMO_SKIP_NETLIFY=true`):**

1. **Hostinger FTP** — `data/hostinger_sites.json` (`demos.gauravxd.dev`, `demos.urmikexd.me`)
2. **Cloudflare R2** — if FTP fails and R2 credentials are set

Netlify is **off** unless you set `DEMO_SKIP_NETLIFY=false` and `DEMO_UPLOAD_MODE=netlify`.

## `.env` (recommended)

```env
DEMO_UPLOAD_MODE=auto
DEMO_SITE_BASE_URL=https://demos.urmikexd.me
DEMO_HOST_STRATEGY=priority
DEMO_SKIP_NETLIFY=true
DEMO_PREFER_R2=false

FTP_PASSWORD=your_ftp_password
HOSTINGER_SITES_FILE=data/hostinger_sites.json
```

Match mailbox demo URLs in `data/outreach_domains.json` (gauravxd mailboxes → `demos.gauravxd.dev`, urmikexd → `demos.urmikexd.me`).

## Cloudflare R2 fallback

```env
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
```

See `docs/GAURAVXD_R2_DOMAIN.md` for custom domain setup.

## Modes

| `DEMO_UPLOAD_MODE` | Behavior |
|--------------------|----------|
| `auto` | Hostinger pool → R2 (or R2 first if `DEMO_PREFER_R2=true`) |
| `ftp` | Hostinger only |
| `r2` | R2 only |
| `netlify` | Netlify only (requires `DEMO_SKIP_NETLIFY=false`) |
| `local` | No upload; URL from `DEMO_SITE_BASE_URL` only |

| `DEMO_HOST_STRATEGY` | Behavior (auto mode) |
|----------------------|-------------------------|
| `priority` | Try each Hostinger site in order, then R2 |
| `random` | Shuffle Hostinger sites per demo, then R2 |

## Failed uploads

If upload fails, the outreach email **omits** the demo link (no fake URLs).

Test FTP: `python scripts/test_ftp_demo.py`
