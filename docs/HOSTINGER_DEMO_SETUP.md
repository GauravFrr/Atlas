# Hostinger FTP demos (fallback after Netlify)

**Stack order:** Netlify → **Hostinger** (`demos.gauravxd.dev`, `demos.urmikexd.me`) → Cloudflare R2 last.

Both subdomains are listed in `data/hostinger_sites.json`. Add one FTP login in `.env` (`FTP_USER` / `FTP_PASSWORD`).

If hPanel shows **Domain: Action required** on `demos.gauravxd.dev`, open that card and complete DNS/verification so HTTPS works before campaigns go live.

---

## urmikexd.me on Hostinger (yes — do this)

### 1. Create FTP user in hPanel

1. Log in to [Hostinger hPanel](https://hpanel.hostinger.com).
2. **Websites** → **urmikexd.me** → **Files** → **FTP Accounts**.
3. Create an account (or use existing), e.g.:
   - User: `mike@urmikexd.me` or the system FTP user shown
   - Password: strong password
   - Directory: `public_html` (default)

Note the **FTP hostname** (often `ftp.hostinger.com` or `ftp.urmikexd.me`).

### 2. Upload path (no extra `demos/` folder)

In **File Manager** → open **`public_html`** (the web root):

- Agent creates one folder per lead: `{slug}/`
- File on disk: `public_html/{slug}/index.html`
- Public URL (subdomain site): `https://demos.urmikexd.me/{slug}/index.html`

Do **not** nest `public_html/public_html/...` — FTP may log in at account `/` or inside `/public_html`; the deployer handles both.

### 2b. Subdomain `demos.urmikexd.me` (separate site in hPanel — your setup)

If hPanel shows **demos.urmikexd.me** as its own website (SSL installing, etc.):

- Files live in: `domains/demos.urmikexd.me/public_html/`
- Upload path per demo: `domains/demos.urmikexd.me/public_html/{slug}/index.html`
- Public URL: `https://demos.urmikexd.me/{slug}/index.html`

Wait until **SSL** finishes (green/active) before testing HTTPS links.

```env
FTP_HOST=ftp.hostinger.com
FTP_USER=mike@urmikexd.me
FTP_PASSWORD=your_ftp_password
FTP_REMOTE_BASE=domains/demos.urmikexd.me/public_html
DEMO_SITE_BASE_URL=https://demos.urmikexd.me
```

If FTP login lands in main `public_html` only, use File Manager once to confirm the folder path, then match `FTP_REMOTE_BASE` exactly.

### 3. Add to `.env` (main domain path style)

If demos are a **folder** on the main site instead of a subdomain site:

```env
FTP_REMOTE_BASE=
DEMO_SITE_BASE_URL=https://demos.urmikexd.me
```

Leave `ftp_remote_base` empty in `data/hostinger_sites.json` — uploads go straight to `public_html/{slug}/`.

For **FTP-only** campaigns:

```env
DEMO_UPLOAD_MODE=ftp
```

### 4. Test

```powershell
python scripts\test_ftp_demo.py
```

(Create script or manual: run campaign with `DEMO_UPLOAD_MODE=ftp` and one mock lead.)

---

## gauravxd.dev on Hostinger (your new setup)

hPanel shows **gauravxd.dev** with hosting **Active** and domain **registered at another provider** (DNS pointed to Hostinger).

You can host demos on Hostinger FTP for this domain — same idea as `demos.urmikexd.me`.

### Step A — Add subdomain for demos (recommended)

1. hPanel → **gauravxd.dev** → **Domains** → **Subdomains**
2. Create **`demos`** → `demos.gauravxd.dev`
3. Wait for **SSL** to finish

Upload path (typical):

`domains/demos.gauravxd.dev/public_html/{slug}/index.html`

Public URL: `https://demos.gauravxd.dev/{slug}/index.html`

### Step B — `.env` when using Hostinger for gauravxd demos

```env
FTP_HOST=ftp.hostinger.com
FTP_USER=gaurav@gauravxd.dev
FTP_PASSWORD=your_ftp_password
FTP_REMOTE_BASE=domains/demos.gauravxd.dev/public_html
DEMO_SITE_BASE_URL=https://demos.gauravxd.dev
```

Use the FTP user from **gauravxd.dev** → **Files** → **FTP Accounts** (may differ from urmikexd).

### Landingsite vs Hostinger (important)

| If DNS now points to Hostinger… | What happens |
|--------------------------------|--------------|
| Root `https://gauravxd.dev` | Shows whatever is in Hostinger `public_html` (not Landingsite unless you copied the site) |
| You still want Landingsite portfolio | Keep **Landingsite DNS** on `@` / `www`, use **only** `demos.gauravxd.dev` on Hostinger, **or** use **Cloudflare** to split records (see `docs/GAURAVXD_R2_DOMAIN.md`) |

**Agent-Earns only needs a demo subdomain** — it does not need the whole portfolio on Hostinger.

### Alternative: Cloudflare R2 for `demos.gauravxd.dev`

Still valid if R2 custom domain is connected — no Hostinger disk used. Use either **R2** or **Hostinger FTP** for `demos.gauravxd.dev`, not both on the same subdomain.

### One FTP block in `.env`

The app has **one** FTP target at a time. Pick:

- **gauravxd** demos → `DEMO_SITE_BASE_URL=https://demos.gauravxd.dev` + gauravxd FTP path, **or**
- **urmikexd** demos → `DEMO_SITE_BASE_URL=https://demos.urmikexd.me` + urmikexd FTP path

Use **R2 + Netlify** as primary and FTP as fallback for whichever domain you configure.

---

## Recommended combo (Netlify + R2 + Hostinger)

```env
DEMO_UPLOAD_MODE=auto
DEMO_PREFER_R2=true

# Primary links in emails (gauravxd demos subdomain)
DEMO_SITE_BASE_URL=https://demos.gauravxd.dev

# Cloudflare R2 (uncomment your keys)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com

# Netlify pool (fallback)
NETLIFY_AUTH_TOKEN=...
NETLIFY_SITE_ID=...
NETLIFY_ACCOUNTS_FILE=data/netlify_accounts.json

# Hostinger FTP (last fallback — urmikexd disk)
FTP_HOST=ftp.hostinger.com
FTP_USER=mike@urmikexd.me
FTP_PASSWORD=...
FTP_REMOTE_BASE=public_html/demos
```

**Order with `auto` + `DEMO_PREFER_R2=true`:**  
R2 → (if fail) Netlify pool → (if fail) Hostinger FTP.

When FTP is used as fallback, demo URLs use `DEMO_SITE_BASE_URL`. Keep that as `https://demos.gauravxd.dev` so emails stay on-brand; FTP is only emergency hosting unless you set `DEMO_SITE_BASE_URL=https://urmikexd.me/demos` for urmikexd-only campaigns.

---

## Your mailboxes (already on Hostinger)

| Domain | Email hosting | Demo hosting |
|--------|---------------|--------------|
| urmikexd.me | Hostinger | Hostinger FTP `urmikexd.me/demos` |
| gauravxd.dev | (Landingsite site) | R2 `demos.gauravxd.dev` |
| Outreach SMTP | `gaurav@gauravxd.dev`, `mike@urmikexd.me`, etc. | — |

Email and demo hosting are separate: SMTP can stay on Hostinger mailboxes while demos use R2 on gauravxd.
