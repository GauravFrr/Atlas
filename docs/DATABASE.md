# Database — Supabase (recommended for you)

Use a **second Supabase project** for Agent-Earns (keep your music app separate).

| Goal | Supabase piece |
|------|----------------|
| Leads safe if Railway dies | **Postgres** (`DATABASE_URL`) |
| Browse leads/payments now | **Table Editor** in dashboard |
| Web UI later | Your FastAPI dashboard + Supabase data |
| Login for dashboard | **Supabase Auth** (Phase 2) |
| Demo file hosting later | **Supabase Storage** (optional) |

MongoDB Atlas does **not** fit this app (we use SQLAlchemy + SQL tables).

---

## Phase 1 — Database now (15 min)

### 1. New project

1. [supabase.com/dashboard](https://supabase.com/dashboard)
2. **New project** → name: `agent-earns` (not your music app)
3. Save the **database password**

Free plan = **2 projects** → music + agent-earns fits.

### 2. Connection string (Railway + local)

Project → **Connect** → **ORM** → **SQLAlchemy**  
Or **Database → Connection string → URI**

Use **Transaction pooler** (port **6543**) for Railway (3 services):

```text
postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
```

Add if missing:

```text
?sslmode=require
```

### 3. Railway shared variables (all 3 services)

```env
DATABASE_URL=postgresql://postgres.xxxx:password@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
```

Push latest code (includes `asyncpg` + Supabase pooler fix) → redeploy.

### 4. Verify

Atlas logs:

```text
Database initialized (Postgres): postgresql+asyncpg://postgres.xxxx:***@...pooler.supabase.com:6543/postgres
```

### 5. Browse data today

Supabase → **Table Editor** → tables `leads`, `payments`, `campaign_runs`, `agent_logs` appear after first Atlas run.

No custom UI required yet.

---

## Phase 2 — Auth for web UI (later)

Today the dashboard uses HTTP Basic (`admin` + `DASHBOARD_PASSWORD`).

**Target:** Supabase Auth (email magic link or Google) → only you (and team) see leads.

Rough plan:

1. Supabase → **Authentication** → enable Email / Google
2. Add to `.env` / Railway:

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_JWT_SECRET=your-jwt-secret-from-project-settings
```

3. Dashboard frontend: `@supabase/supabase-js` login → send JWT on API calls
4. FastAPI: verify JWT, replace `HTTPBasic` in `dashboard/app.py`

**Do not** expose the Postgres `DATABASE_URL` password to the browser — only `anon` key + RLS for any direct client access.

For server-side dashboard API, keep using `DATABASE_URL` on Railway (bypasses RLS).

---

## Phase 3 — Storage for demos (optional)

Alternative/complement to Hostinger FTP:

- Bucket `demos` (public)
- Upload HTML from `DemoPublisher` via Supabase Storage API
- Public URL: `https://xxxx.supabase.co/storage/v1/object/public/demos/{slug}/index.html`

Not wired yet — Hostinger + R2 stay default until you ask for this.

---

## Local dev

Same `DATABASE_URL` in `.env` → local Atlas and Railway share one database.

Or leave empty → local `./agent.db` only.

---

## Direct connection (port 5432) vs pooler (6543)

| URL | Use |
|-----|-----|
| **6543 pooler** | Railway (webhooks + Telegram + Atlas) ← **use this** |
| **5432 direct** | One-off migrations / `psql` from your PC |

---

## Alternatives

| Provider | When |
|----------|------|
| **Supabase** | You have account, want UI + auth path ← **you** |
| Neon | DB-only, no extras |
| SQLite volume | Quick test; data tied to Railway |

---

## Migrate local `agent.db` (optional)

```powershell
python scripts/list_leads_with_email.py
```

One-time SQLite → Postgres migration script can be added on request.
