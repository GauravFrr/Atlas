# How emails get sent (simple)

## Modes (pick ONE per run)

| Mode | Who actually hits Send in the inbox |
|------|--------------------------------------|
| **draft** | Nobody — files saved in `outputs/emails/` |
| **smtp** | **Agent** — using your **Hostinger mailbox** |
| **instantly** | **Instantly** — agent only uploads the lead + text |
| **auto** | Instantly if API keys exist, else Hostinger SMTP, else draft |
| **hybrid** | **Random** per lead (Instantly or SMTP) + **fallback** if first fails |

The agent does **not** send the same email twice in one run. You choose one method.

---

## Can you use Hostinger mailbox?

**Yes.** That is **SMTP mode**.

```env
SMTP_PROVIDER=hostinger
SMTP_HOST=smtp.hostinger.com
SMTP_PORT=587
SMTP_USER=hello@gauravstack.com
SMTP_PASSWORD=your_hostinger_mailbox_password
SMTP_FROM_EMAIL=hello@gauravstack.com
SMTP_FROM_NAME=Gaurav
EMAIL_SEND_MODE=smtp
```

Or put each domain in `data/outreach_domains.json` (see `HOSTINGER_MULTI_DOMAIN.md`).

Run:

```bash
python scripts/run_campaign.py --mock --niche plumber --city "Austin TX" --leads 3 --send
```

---

## Do you have to use Instantly?

**No.** Only if you want Instantly’s warmup, limits, and rotation.

```env
INSTANTLY_API_KEY=...
INSTANTLY_CAMPAIGN_ID=...
EMAIL_SEND_MODE=instantly
```

```bash
python scripts/run_campaign.py ... --instantly
```

---

## “Agent sends on its own”

That means **SMTP** (Hostinger). The Python app logs into `smtp.hostinger.com` and sends as `hello@yourdomain.com`.

**Instantly** = agent prepares lead → Instantly’s servers send from mailboxes you connected in Instantly.

---

## Multiple domains

- **Sending:** connect all domains in Instantly, OR list them in `outreach_domains.json` for SMTP rotation.
- **Demo links:** `outreach_domains.json` rotates `demo_base_url` per lead.

---

## Commands cheat sheet

```bash
# Drafts only (safe)
python scripts/run_campaign.py --mock --niche plumber --city "Austin TX" --leads 3

# Hostinger mailbox
python scripts/run_campaign.py --mock ... --send

# Instantly
python scripts/run_campaign.py --mock ... --instantly

# Auto-pick in .env: EMAIL_SEND_MODE=auto
python scripts/run_campaign.py --mock ... --send-mode auto

# Random Instantly/SMTP + fallback (recommended if you have both)
python scripts/run_campaign.py --mock ... --send-mode hybrid
```

Test one email to yourself:

```bash
python scripts/send_test_email.py --to you@gmail.com --method smtp
python scripts/send_test_email.py --to you@gmail.com --method instantly
```
