# Demo links on gauravxd.dev (portfolio on Landingsite + demos on Cloudflare R2)

## What you want

| URL | Host | Purpose |
|-----|------|---------|
| `https://gauravxd.dev` | **Landingsite** | Your portfolio (unchanged) |
| `https://demos.gauravxd.dev/austin-precision-plumbing/` | **Cloudflare R2** | Client demo previews (agent uploads here) |

Your cold emails use the **demos.** subdomain only. Portfolio stays on Landingsite.

---

## Big picture

```
gauravxd.dev          →  Landingsite (your existing site)
demos.gauravxd.dev    →  Cloudflare R2 bucket "agent-demos"
```

R2 does **not** replace Landingsite. You only add a **subdomain** for HTML demos.

---

## Step 1 — Cloudflare account + add your domain

1. Go to [https://dash.cloudflare.com](https://dash.cloudflare.com) (free plan).
2. **Add a site** → enter `gauravxd.dev`.
3. Cloudflare shows two nameservers, e.g.  
   `ada.ns.cloudflare.com`  
   `bob.ns.cloudflare.com`

Keep this tab open.

---

## Step 2 — Copy Landingsite DNS into Cloudflare (keep portfolio working)

Before changing nameservers, note how Landingsite points your domain:

1. Log in to **Landingsite** (where `gauravxd.dev` is connected).
2. Find **DNS** or **domain settings** — copy what they use for the root site, usually:
   - **A record** `@` → an IP address, **or**
   - **CNAME** `www` → something like `sites.landingsite.ai` (example — use *your* value)

3. In **Cloudflare** → `gauravxd.dev` → **DNS** → **Records**, add the **same** records Landingsite uses:

   | Type | Name | Content | Proxy |
   |------|------|---------|-------|
   | A or CNAME | `@` | (Landingsite IP or host) | Proxied (orange cloud) is OK |
   | CNAME | `www` | (Landingsite target if you use www) | Proxied OK |

4. **Do not** add `demos` yet — R2 will do that in Step 4.

5. Open `https://gauravxd.dev` in a private window after Step 3 — it should still show your portfolio (may take up to an hour after NS change).

---

## Step 3 — Point the domain to Cloudflare nameservers

Where you bought / manage `gauravxd.dev` (Landingsite domain page, Namecheap, GoDaddy, etc.):

1. Find **Nameservers** / **DNS servers**.
2. Replace Landingsite/default NS with the **two Cloudflare nameservers** from Step 1.
3. Save.

Propagation: 15 minutes – 48 hours (often under 1 hour).

Landingsite hosting does **not** stop — only **DNS** is answered by Cloudflare, which forwards `@` and `www` to Landingsite like before.

---

## Step 4 — Connect R2 bucket to `demos.gauravxd.dev`

1. Cloudflare dashboard → **R2** → bucket **agent-demos** (you already created this).
2. **Settings** → **Custom Domains** → **Connect Domain**.
3. Type: `demos.gauravxd.dev` → Continue.
4. Cloudflare adds the DNS record automatically (because the zone is on Cloudflare).
5. Wait until status is **Active** and SSL shows ready.

Test in browser (after you upload once):

`https://demos.gauravxd.dev/austin-precision-plumbing/`

---

## Step 5 — Agent `.env` (your machine)

```env
# Trustworthy links in emails — NOT pub-xxxxx.r2.dev
DEMO_SITE_BASE_URL=https://demos.gauravxd.dev

# R2 upload (you already have these)
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=agent-demos
R2_ENDPOINT_URL=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
R2_AUTO_UPLOAD=true
```

---

## Step 6 — Test upload + campaign

```bash
cd f:\Agent-Earns
.\venv\Scripts\activate
.\venv\Scripts\python scripts\test_r2_upload.py outputs\demos\austin-precision-plumbing.html
```

URL should look like:

`https://demos.gauravxd.dev/austin-precision-plumbing/`

Then:

```bash
.\venv\Scripts\python scripts\run_campaign.py --mock --fresh --niche plumber --city "Austin TX" --leads 1
```

Check `outputs/emails/draft_*.txt` — link must use `demos.gauravxd.dev` and the business slug.

---

## If Landingsite will not let you change nameservers

Some setups lock DNS inside Landingsite only. Options:

1. **Ask Landingsite support** whether you can add a **CNAME** record:  
   `demos` → (target Cloudflare shows when connecting R2 custom domain).  
   R2 custom domain may still require the zone on Cloudflare — if connect fails, use option 2.

2. **Use Cloudflare nameservers** (Step 3) — recommended; portfolio keeps working if Step 2 records match Landingsite.

3. **Temporary:** keep `pub-xxxxx.r2.dev` in `DEMO_SITE_BASE_URL` until DNS is fixed (links work but look less trusted).

---

## FAQ

**Will my portfolio break?**  
No, if `@` / `www` in Cloudflare match what Landingsite used before.

**Can I use `gauravxd.dev/demo/...` without subdomain?**  
Harder with Landingsite on root. `demos.gauravxd.dev` is the standard pattern.

**Old long R2 links?**  
Delete old objects in R2 bucket or ignore them; new uploads use `business-name/index.html`.

**Email line clients see:**  
`Preview I put together for Austin Precision Plumbing:`  
`https://demos.gauravxd.dev/austin-precision-plumbing/`
 