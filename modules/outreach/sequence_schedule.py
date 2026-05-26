"""
Follow-up timing — blueprint EMAIL_SEQUENCE_DAYS (0, 4, 8, 14, 21).
SMTP/hybrid-SMTP leads: agent sends steps 2–4. Instantly leads: campaign handles sequence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from constants import EMAIL_SEQUENCE_DAYS
from database.models.lead import Lead


def schedule_next_followup(lead: Lead, *, from_dt: datetime | None = None) -> None:
    """
    Set next_followup from last_contacted + EMAIL_SEQUENCE_DAYS[sequence_step + 1].
    Clears next_followup when the sequence is complete.
    """
    channel = (lead.enrichment_data or {}).get("send_channel") or ""
    if channel == "instantly":
        lead.next_followup = None
        return

    base = from_dt or lead.last_contacted or datetime.now(timezone.utc)
    next_idx = int(lead.sequence_step or 0) + 1
    if next_idx >= len(EMAIL_SEQUENCE_DAYS):
        lead.next_followup = None
        return
    days = EMAIL_SEQUENCE_DAYS[next_idx]
    lead.next_followup = base + timedelta(days=days)


def advance_followup_step(lead: Lead) -> bool:
    """Bump sequence_step and schedule the next touch. Returns False if sequence finished."""
    lead.sequence_step = int(lead.sequence_step or 0) + 1
    next_idx = lead.sequence_step + 1
    if next_idx >= len(EMAIL_SEQUENCE_DAYS):
        lead.next_followup = None
        return False
    schedule_next_followup(lead)
    return True
