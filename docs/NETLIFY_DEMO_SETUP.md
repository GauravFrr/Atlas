# Netlify demo hosting (automated) — no Cloudflare nameservers

The agent uploads each demo HTML to **Netlify** after generation.  
Your portfolio on **Landingsite** (`gauravxd.dev`) stays unchanged.

---

## What you get

| Link type | Example |
|-----------|---------|
| Netlify default | `https://agent-demos.netlify.app/austin-precision-plumbing/index.html` |
| Custom subdomain (optional) | `https://demos.gauravxd.dev/austin-precision-plumbing/index.html` |

Custom subdomain = **one CNAME record** in Landingsite DNS (`demos` → your Netlify site).  
**Not** a full nameserver change to Cloudflare.

---

## Step 1 — Create a Netlify site (one time, ~5 min)

1. Sign up at [https://app.netlify.com](https://app.netlify.com)
2. **Add new site** → **Deploy manually** (empty site is fine)
3. Site name e.g. `agent-demos` → URL `https://agent-demos.netlify.app`
4. **Site configuration** → **Site information** → copy **Site ID** (UUID)
5. **User settings** → **Applications** → **Personal access tokens** → create token  
   - Scopes: at least **sites** read/write (deploy)

---

## Step 2 — Add to `.env`

```env
DEMO_UPLOAD_MODE=netlify
DEMO_SITE_BASE_URL=https://agent-demos.netlify.app
NETLIFY_AUTH_TOKEN=nfp_xxxxxxxx
NETLIFY_SITE_ID=your-site-uuid-here
```

Comment out or remove R2 vars if you only use Netlify.  
Or keep R2 as backup and use `DEMO_UPLOAD_MODE=auto` (Netlify wins when both are set).

---

## Step 3 — Test upload

```bash
python scripts/test_netlify_upload.py
```

Opens the printed URL in your browser. If it loads, campaigns will use the same links automatically.

---

## Step 4 (optional) — `demos.gauravxd.dev` on Landingsite

1. Netlify → **Domain management** → **Add domain** → `demos.gauravxd.dev`
2. Netlify shows a target like `agent-demos.netlify.app`
3. In **Landingsite** (where `gauravxd.dev` DNS lives) add:

   | Type | Name | Value |
   |------|------|--------|
   | CNAME | `demos` | `agent-demos.netlify.app` |

4. Wait for SSL (Netlify provisions it)
5. Update `.env`:

```env
DEMO_SITE_BASE_URL=https://demos.gauravxd.dev
```

Root site `gauravxd.dev` still points to Landingsite.

---

## How automation works

Each campaign demo:

1. Saves `outputs/demos/{slug}.html`
2. Netlify API deploys `{slug}/index.html` to your site
3. Email gets `DEMO_SITE_BASE_URL/{slug}/index.html`

No drag-and-drop, no file manager.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Netlify not configured` | Set all three: token, site ID, `DEMO_SITE_BASE_URL` |
| 401 on deploy | Regenerate token with deploy scope |
| 404 on URL | Wait 1–2 min after first deploy; path must end with `/index.html` |
| Wrong site | Check `NETLIFY_SITE_ID` matches the site in Netlify UI |

---

## Auto mode priority

```env
DEMO_UPLOAD_MODE=auto
```

Order: **Netlify** (if configured) → R2 → FTP → local URL only.
