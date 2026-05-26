"""
Draft reply emails from universal_reply_scripts.md (Mikey scripts).

Routes by what they actually said — pricing, portfolio, not interested, etc.
Payment link is a separate email (never in script 1).
"""

from __future__ import annotations

from database.models.lead import Lead
from modules.outreach.universal_scripts import (
    pick_script_id,
    render_script,
    script_label,
)


def _reply_subject(lead: Lead) -> str:
    data = dict(lead.enrichment_data or {})
    last = data.get("last_reply") or {}
    if last.get("subject"):
        sub = str(last["subject"]).strip()
        return sub if sub.lower().startswith("re:") else f"Re: {sub}"
    pitch = (lead.pitch_subject or "").strip()
    if pitch:
        return pitch if pitch.lower().startswith("re:") else f"Re: {pitch}"
    company = (lead.business_name or "your business")[:40]
    return f"Re: {company}"


def _last_reply_text(lead: Lead) -> tuple[str, str]:
    data = dict(lead.enrichment_data or {})
    last = data.get("last_reply") or {}
    return str(last.get("subject") or ""), str(last.get("snippet") or "")


def draft_reply_for_lead(
    lead: Lead,
    settings: object,
    *,
    classification: str = "interested",
    reply_subject: str = "",
    reply_body: str = "",
) -> dict[str, str]:
    """Pick universal script from reply content + classification."""
    sub = reply_subject or _last_reply_text(lead)[0]
    body = reply_body or _last_reply_text(lead)[1]
    script_id = pick_script_id(lead, sub, body, classification=classification)
    draft = render_script(script_id, lead, settings)
    draft["script_id"] = script_id
    draft["script_label"] = script_label(script_id)
    draft["kind"] = "close_reply" if script_id == "close" else "interested_reply"
    return draft


def draft_interested_reply(
    lead: Lead,
    settings: object,
    *,
    classification: str = "interested",
) -> dict[str, str]:
    """Backward-compatible entry — routes via universal scripts."""
    return draft_reply_for_lead(lead, settings, classification=classification)


def draft_payment_link_reply(
    lead: Lead,
    settings: object,
    *,
    payment_url: str,
    amount_inr: int,
) -> dict[str, str]:
    """After close script / verbal yes — payment only (golden rule: not in script 1)."""
    first = _reply_subject(lead)
    from modules.outreach.universal_scripts import _first_name

    sender = getattr(settings, "your_name", None) or "Gaurav"
    name = _first_name(lead)
    body = (
        f"Hey {name},\n\n"
        "Really looking forward to working on this.\n\n"
        f"Here's the secure payment link for the package (INR {amount_inr:,}):\n"
        f"{payment_url}\n\n"
        "UPI, card, or netbanking — link valid 7 days. "
        "Once it comes through I'll confirm and we'll lock your kickoff date "
        "(usually 3–5 days from start).\n\n"
        f"— {sender}"
    )
    return {
        "subject": first,
        "body": body.strip(),
        "kind": "payment_link",
        "script_id": "payment",
        "script_label": "Payment link",
    }


def draft_ghost_reply(lead: Lead, settings: object, step: int) -> dict[str, str]:
    """Ghost follow-up 1–3 from universal scripts."""
    sid = f"ghost_{min(max(step, 1), 3)}"
    draft = render_script(sid, lead, settings)
    draft["script_id"] = sid
    draft["kind"] = "ghost"
    return draft
