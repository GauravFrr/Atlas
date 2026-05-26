"""
SMTP presets for business email on your own domain (not personal Gmail).
Set SMTP_PROVIDER in .env and fill SMTP_USER / SMTP_PASSWORD for your mailbox.
"""

from __future__ import annotations

SMTP_PRESETS: dict[str, dict[str, int | str]] = {
    # Zoho Mail — free tier works with custom domain (gauravxd.dev)
    "zoho": {"host": "smtp.zoho.com", "port": 587, "ssl_port": 465},
    # Google Workspace — hi@gauravxd.dev (use App Password for that mailbox, not personal Gmail)
    "google_workspace": {"host": "smtp.gmail.com", "port": 587, "ssl_port": 465},
    # Microsoft 365 / Outlook business
    "microsoft365": {"host": "smtp.office365.com", "port": 587, "ssl_port": 587},
    # Hostinger / cPanel-style (confirm in your hosting panel)
    "hostinger": {"host": "smtp.hostinger.com", "port": 587, "ssl_port": 465},
    # Namecheap Private Email
    "namecheap": {"host": "mail.privateemail.com", "port": 587, "ssl_port": 465},
}
