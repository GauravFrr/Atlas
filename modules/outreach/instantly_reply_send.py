"""
Send Telegram-approved close / payment emails via Instantly Unibox reply API.

Keeps the conversation in the same thread + From address as cold outreach.
Falls back to Hostinger SMTP when Instantly context is missing (optional).
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config import Settings
from integrations.platforms.instantly import InstantlyClient
from utils.mailbox_lock import (
    extract_instantly_our_mailbox,
    get_locked_mailbox,
    lock_mailbox_from_instantly,
)


def _reply_uuid_from_lead(lead: Any) -> str:
    data = getattr(lead, "enrichment_data", None) or {}
    last = data.get("last_reply") or {}
    eid = str(last.get("instantly_email_id") or "").strip()
    if eid and eid.lower() not in ("webhook", "unknown", "none"):
        return eid
    return ""


def _re_subject(subject: str, fallback: str = "") -> str:
    sub = (subject or fallback or "").strip()
    if not sub:
        return "Re: your message"
    if sub.lower().startswith("re:"):
        return sub
    return f"Re: {sub}"


async def resolve_instantly_reply_context(
    settings: Settings,
    lead: Any,
    *,
    client: InstantlyClient | None = None,
) -> dict[str, str]:
    """
    Build eaccount + reply_to_uuid for POST /api/v2/emails/reply.
    Uses stored last_reply id, then fetches latest Unibox received email for the lead.
    """
    out: dict[str, str] = {"eaccount": "", "reply_to_uuid": ""}
    if not settings.has_instantly:
        return out

    ic = client or InstantlyClient(
        settings.instantly_api_key,
        settings.instantly_campaign_id,
    )
    if not ic.is_configured:
        return out

    reply_id = _reply_uuid_from_lead(lead)
    eaccount = get_locked_mailbox(lead)
    lead_email = str(getattr(lead, "email", "") or "").strip().lower()

    items: list[dict[str, Any]] = []
    if lead_email and (not reply_id or not eaccount):
        items, _ = await ic.list_emails(
            campaign_id=settings.instantly_campaign_id,
            email_type="received",
            lead_email=lead_email,
            limit=10,
        )

    if not reply_id and items:
        reply_id = str(items[0].get("id") or "").strip()

    if not eaccount and items:
        eaccount = extract_instantly_our_mailbox(items[0])

    if reply_id and not eaccount and lead_email:
        email_row = await ic.get_email(reply_id)
        if email_row:
            eaccount = extract_instantly_our_mailbox(email_row)

    out["reply_to_uuid"] = reply_id
    out["eaccount"] = eaccount.strip().lower()
    return out


async def send_approved_reply_via_instantly(
    settings: Settings,
    lead: Any,
    *,
    subject: str,
    body: str,
    client: InstantlyClient | None = None,
) -> dict[str, Any]:
    """Reply in the Instantly thread (close script or payment link)."""
    if not settings.has_instantly:
        return {"ok": False, "error": "instantly_not_configured", "channel": ""}

    ic = client or InstantlyClient(
        settings.instantly_api_key,
        settings.instantly_campaign_id,
    )
    if not ic.is_configured:
        return {"ok": False, "error": "instantly_not_configured", "channel": ""}

    ctx = await resolve_instantly_reply_context(settings, lead, client=ic)
    reply_id = ctx.get("reply_to_uuid") or ""
    eaccount = ctx.get("eaccount") or ""

    if not reply_id:
        return {
            "ok": False,
            "error": "missing_instantly_reply_id",
            "channel": "instantly",
            "hint": "Sync replies or wait for webhook with email_id",
        }
    if not eaccount:
        return {
            "ok": False,
            "error": "missing_instantly_eaccount",
            "channel": "instantly",
            "hint": "Lock mailbox from reply or connect account in Instantly",
        }

    data = getattr(lead, "enrichment_data", None) or {}
    last = data.get("last_reply") or {}
    re_subject = _re_subject(subject, str(last.get("subject") or ""))

    result = await ic.send_reply(
        eaccount=eaccount,
        reply_to_uuid=reply_id,
        subject=re_subject,
        body_text=body,
    )
    if not result.get("ok"):
        return {
            "ok": False,
            "error": result.get("error") or "instantly_reply_failed",
            "channel": "instantly",
            "raw": result,
        }

    lock_mailbox_from_instantly(lead, eaccount, settings)
    logger.success(
        f"[Instantly] Reply sent to {getattr(lead, 'email', '?')} "
        f"from {eaccount} (thread {reply_id[:8]}...)"
    )
    return {
        "ok": True,
        "channel": "instantly",
        "eaccount": eaccount,
        "reply_to_uuid": reply_id,
        "email_id": result.get("email_id"),
    }
