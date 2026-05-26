# Demo hosting — without changing nameservers

You **do not** need Cloudflare nameserver changes for demos to work.

---

## Option 1 — Keep R2 public URL (recommended, already working)

- Upload uses Cloudflare **R2 API** (S3 keys in `.env`).
- Public link looks like:  
  `https://pub-xxxxx.r2.dev/your-slug/index.html`
- **No DNS / nameserver change** at your registrar.
- Custom domain (`demos.gauravxd.dev` on R2) is optional — skip it if you cannot move NS.

```env
DEMO_UPLOAD_MODE=r2
DEMO_SITE_BASE_URL=https://pub-YOUR_BUCKET.r2.dev
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
R2_ENDPOINT_URL=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
```

---

## Option 2 — Hostinger FTP (same DNS you already use)

If `gauravxd.dev` is on **Hostinger** and you have **web hosting** (File Manager / FTP):

1. In hPanel create folder: `public_html/demos/`
2. Add `.env`:

```env
DEMO_UPLOAD_MODE=ftp
DEMO_SITE_BASE_URL=https://gauravxd.dev/demos
FTP_HOST=ftp.hostinger.com
FTP_USER=your_ftp_user
FTP_PASSWORD=your_ftp_password
FTP_REMOTE_BASE=public_html/demos
```

3. Agent uploads `public_html/demos/{slug}/index.html`
4. Link in email: `https://gauravxd.dev/demos/austin-precision-plumbing/index.html`

**No nameserver change** — only files on your existing Hostinger site.

---

## Option 3 — Manual upload (`local`)

Generate HTML locally; you upload anywhere (Hostinger, Netlify drop, Google Drive public link, etc.):

```env
DEMO_UPLOAD_MODE=local
DEMO_SITE_BASE_URL=https://gauravxd.dev/demos
```

Files saved under `outputs/demos/`. You upload and fix the URL yourself.

---

## Option 4 — Netlify (automated — recommended if skipping Cloudflare)

Agent uploads each demo via **Netlify API**. No file manager, no Cloudflare.

**Setup:** [NETLIFY_DEMO_SETUP.md](NETLIFY_DEMO_SETUP.md)

```env
DEMO_UPLOAD_MODE=netlify
DEMO_SITE_BASE_URL=https://agent-demos.netlify.app
NETLIFY_AUTH_TOKEN=nfp_...
NETLIFY_SITE_ID=uuid-from-netlify
```

Test:

```bash
python scripts/test_netlify_upload.py
```

Optional: `demos.gauravxd.dev` → CNAME in Landingsite DNS only (not nameserver move).

---

## Auto mode (default)

```env
DEMO_UPLOAD_MODE=auto
```

Uses **Netlify** if configured, else R2, else FTP, else local URL only.

---

## Landingsite portfolio

`gauravxd.dev` on **Landingsite** stays as-is. Demos can live on:

- `pub-….r2.dev` (separate from portfolio), or
- `gauravxd.dev/demos/...` via Hostinger FTP (subfolder, not Landingsite editor)

Do **not** use `docs/GAURAVXD_R2_DOMAIN.md` unless you are ready to move DNS to Cloudflare.
