"""
After Instantly sync / webhook: classify → draft reply → Telegram approval.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config import Settings
from modules.outreach.manager import Manager
from modules.outreach.reply_classifier import ReplyClass


async def auto_draft_reply_for_lead(
    settings: Settings,
    *,
    lead_id: str,
    classification: ReplyClass | str,
    subject: str = "",
    snippet: str = "",
    llm: Any | None = None,
) -> dict[str, Any]:
    """
    Queue universal-script reply + Telegram buttons (interested / unknown / not_now).
    Skips unsubscribe and auto_reply.
    """
    label = str(classification)
    if label in ("unsubscribe", "auto_reply"):
        return {"status": "skipped", "classification": label}

    if not getattr(settings, "telegram_auto_draft_on_reply", True):
        return {"status": "skipped", "reason": "auto_draft_disabled"}

    if label == "unknown" and not settings.reply_alert_on_unknown:
        return {"status": "skipped", "reason": "unknown_alerts_off"}

    mgr = Manager(settings, llm_router=llm)
    result = await mgr.handle_reply(
        reply={
            "lead_id": lead_id,
            "classification": label,
            "subject": subject,
            "snippet": snippet,
        }
    )
    logger.info(f"[ReplyHandler] auto_draft lead={lead_id[:8]} → {result.get('status')}")
    return result
