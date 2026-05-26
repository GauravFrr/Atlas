# Razorpay payments (blueprint §22)

## `.env`

```bash
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
RAZORPAY_DEFAULT_AMOUNT_INR=3999
RAZORPAY_PAYMENT_LINK_EXPIRE_DAYS=7
```

## Create link manually

```bash
python scripts/create_payment_link.py --email client@business.com
```

## Webhook server (Instantly + Razorpay)

**Option A — Python ngrok (no CLI):**

```bash
# .env: NGROK_AUTHTOKEN from https://dashboard.ngrok.com/get-started/your-authtoken
python scripts/run_webhooks_tunnel.py
```

**Option B — local only (no Razorpay until you tunnel):**

```bash
python scripts/run_instantly_webhook.py --port 8787
ngrok http 8787   # requires ngrok CLI from https://ngrok.com/download
```

Razorpay Dashboard → Webhooks:

- URL: `https://YOUR-NGROK/webhooks/razorpay`
- Secret: `RAZORPAY_WEBHOOK_SECRET`
- Events: `payment_link.paid`, `payment.captured`

## Agent flow

1. Lead replies **interested** → `handle_reply` drafts close email + **Razorpay link** in body.
2. Client pays → webhook confirms → lead → `client` status → **Telegram** payment alert.
3. Atlas P1 can run `process_payment_webhook` if webhook was queued.

## Test mode

Use Razorpay **test** keys. Test card: see [Razorpay test docs](https://razorpay.com/docs/payments/payments/test-card-details/).
