"""
Reliable Hostinger/business SMTP send + copy to webmail Sent folder.

Hostinger webmail often shows an empty Sent folder when mail is sent via SMTP/API
only. This module:
  1. Uses the authenticated mailbox as the SMTP envelope sender (required).
  2. Optionally BCCs the sender (copy appears in Inbox).
  3. Appends the message to the IMAP Sent folder so webmail shows it.
"""

from __future__ import annotations

import imaplib
import json
import smtplib
import ssl
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path
from typing import Any

from loguru import logger

IMAP_PRESETS: dict[str, str] = {
    "hostinger": "imap.hostinger.com",
    "zoho": "imap.zoho.com",
    "google_workspace": "imap.gmail.com",
    "microsoft365": "outlook.office365.com",
    "namecheap": "mail.privateemail.com",
}

SENT_FOLDER_CANDIDATES = (
    "INBOX.Sent",
    "Sent",
    "INBOX/Sent",
    "Sent Items",
    "INBOX.Sent Items",
)


def resolve_imap_host(smtp_config: dict[str, Any], provider: str = "") -> str:
    explicit = str(smtp_config.get("imap_host") or "").strip()
    if explicit:
        return explicit
    key = (provider or str(smtp_config.get("provider") or "")).lower().strip()
    return IMAP_PRESETS.get(key, "imap.hostinger.com")


def build_outreach_message(
    *,
    from_email: str,
    from_name: str,
    to_email: str,
    subject: str,
    body: str,
    reply_to: str,
) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = formataddr((from_name, from_email)) if from_name else from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    return msg


def append_to_sent_folder(
    *,
    imap_host: str,
    user: str,
    password: str,
    raw_message: bytes,
) -> bool:
    """Copy message into the mailbox Sent folder via IMAP (shows in Hostinger webmail)."""
    try:
        mail = imaplib.IMAP4_SSL(imap_host, 993, ssl_context=ssl.create_default_context())
        mail.login(user, password)
        for folder in SENT_FOLDER_CANDIDATES:
            try:
                status = mail.append(
                    folder,
                    "\\Seen",
                    imaplib.Time2Internaldate(time.time()),
                    raw_message,
                )
                if status and status[0] == "OK":
                    logger.info(f"[SMTP] Saved copy to webmail Sent ({folder}) for {user}")
                    mail.logout()
                    return True
            except imaplib.IMAP4.error:
                continue
        logger.warning(
            f"[SMTP] Could not find Sent folder on {imap_host} for {user} "
            "(BCC copy may still be in Inbox)"
        )
        mail.logout()
    except Exception as e:
        logger.warning(f"[SMTP] IMAP Sent save failed for {user}: {e}")
    return False


def log_sent_record(
    *,
    from_email: str,
    to_email: str,
    subject: str,
    mailbox_user: str,
) -> None:
    out = Path("outputs/emails")
    out.mkdir(parents=True, exist_ok=True)
    record = {
        "at": datetime.now(timezone.utc).isoformat(),
        "mailbox": mailbox_user,
        "from": from_email,
        "to": to_email,
        "subject": subject,
    }
    log_path = out / "sent_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def send_via_smtp(
    *,
    to_email: str,
    subject: str,
    body: str,
    smtp_config: dict[str, Any],
    provider: str = "",
) -> bool:
    """
    Send outreach email. Returns True only if SMTP accepts the message.
    """
    host = str(smtp_config.get("host", ""))
    port = int(smtp_config.get("port", 587))
    user = str(smtp_config.get("user", "")).strip()
    password = str(smtp_config.get("password", ""))
    from_name = str(smtp_config.get("from_name", "") or "")
    reply_to = str(smtp_config.get("reply_to", "") or "")
    use_ssl = bool(smtp_config.get("use_ssl", False))
    bcc_self = bool(smtp_config.get("bcc_self", True))
    save_to_sent = bool(smtp_config.get("save_to_sent", True))

    if not host or not user or not password:
        logger.error("[SMTP] Incomplete config (host, user, password required)")
        return False

    # Hostinger requires envelope From == authenticated mailbox
    from_email = (str(smtp_config.get("from_email", "") or user)).strip()
    if from_email.lower() != user.lower():
        logger.warning(
            f"[SMTP] From {from_email} != login {user}; envelope sender set to {user}"
        )
        from_email = user

    if not reply_to:
        reply_to = from_email

    msg = build_outreach_message(
        from_email=from_email,
        from_name=from_name,
        to_email=to_email,
        subject=subject,
        body=body,
        reply_to=reply_to,
    )
    raw = msg.as_bytes()

    recipients = [to_email]
    if bcc_self and from_email.lower() not in to_email.lower():
        recipients.append(from_email)

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(host, port, timeout=60)
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        server.login(user, password)
        refused = server.sendmail(user, recipients, raw)
        server.quit()
        if refused:
            logger.error(f"[SMTP] Server refused recipients: {refused}")
            return False
    except Exception as e:
        logger.error(f"[SMTP] Send failed ({user} -> {to_email}): {e}")
        return False

    logger.success(
        f"[SMTP] Sent {from_email} -> {to_email}"
        + (f" (BCC {from_email})" if bcc_self and from_email not in recipients[:1] else "")
    )

    if save_to_sent:
        imap_host = resolve_imap_host(smtp_config, provider)
        append_to_sent_folder(
            imap_host=imap_host,
            user=user,
            password=password,
            raw_message=raw,
        )

    log_sent_record(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        mailbox_user=user,
    )
    return True
