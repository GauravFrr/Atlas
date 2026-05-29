"""
Instantly webhook receiver — reply_received → DB + Telegram.

Run:
  python scripts/run_instantly_webhook.py

In Instantly: Settings → Webhooks → add URL:
  https://YOUR-NGROK-URL/webhooks/instantly
Event: reply_received
Optional header X-Webhook-Secret = INSTANTLY_WEBHOOK_SECRET from .env
"""

from __future__ import annotations

from typing import Any

from fastapi import (  # noqa: F401 — Request reused
    BackgroundTasks,
    FastAPI,
    Header,
    HTTPException,
    Request,
)
from loguru import logger

from config import get_settings
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from modules.outreach.reply_classifier import classify_reply_async
from modules.outreach.reply_sync import STATE_FILE
from utils.notifier import Notifier

app = FastAPI(title="Agent-Earns Webhooks")
_repo = LeadRepository()
_init_done = False


async def _ensure_db() -> None:
    global _init_done
    if not _init_done:
        await init_db()
        _init_done = True


def _extract_lead_email(payload: dict[str, Any]) -> str:
    for key in ("lead_email", "email", "lead"):
        val = payload.get(key)
        if val and "@" in str(val):
            return str(val).strip().lower()
    # Nested lead object (some Instantly payloads)
    lead_obj = payload.get("lead")
    if isinstance(lead_obj, dict):
        for key in ("email", "lead_email"):
            val = lead_obj.get(key)
            if val and "@" in str(val):
                return str(val).strip().lower()
    return ""


def _extract_body(payload: dict[str, Any]) -> tuple[str, str]:
    subject = str(
        payload.get("reply_subject")
        or payload.get("email_subject")
        or payload.get("subject")
        or ""
    )
    body = str(
        payload.get("reply_text")
        or payload.get("reply_text_snippet")
        or payload.get("email_text")
        or ""
    )
    return subject, body


@app.post("/webhooks/instantly")
async def instantly_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str | None = Header(default=None),
) -> dict[str, str]:
    settings = get_settings()
    secret = (settings.instantly_webhook_secret or "").strip()
    if secret and x_webhook_secret != secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored", "reason": "invalid_json"}

    event = str(payload.get("event_type") or payload.get("type") or "").lower()
    allowed = (
        "reply_received",
        "auto_reply_received",
        "lead_interested",  # Instantly UI "Interested" tag
    )
    if event and event not in allowed:
        logger.info(f"[Webhook] Ignored event: {event}")
        return {"status": "ignored", "event": event}

    if event == "auto_reply_received":
        return {"status": "ignored", "reason": "auto_reply"}

    # Heavy work (LLM classify + DB + Telegram) runs after we ACK.
    # Instantly disables webhooks that don't return 2xx quickly.
    background_tasks.add_task(_process_reply_event, payload, event)
    return {"status": "accepted", "event": event or "reply_received"}


async def _process_reply_event(payload: dict[str, Any], event: str) -> None:
    """Slow path — runs in background so the webhook ACKs immediately."""
    settings = get_settings()
    try:
        await _ensure_db()

        if event == "lead_interested":
            email = _extract_lead_email(payload)
            subject = str(
                payload.get("reply_subject") or payload.get("email_subject") or ""
            )
            body = str(
                payload.get("reply_text")
                or payload.get("reply_text_snippet")
                or "Marked interested in Instantly"
            )
            label: str | None = "interested"
        else:
            email = _extract_lead_email(payload)
            subject, body = _extract_body(payload)
            label = None

        eid = str(payload.get("email_id") or payload.get("id") or "")

        llm = None
        if settings.has_gemini or settings.has_groq:
            from llm.router import LLMRouter

            llm = LLMRouter(settings)

        if label is None:
            label = await classify_reply_async(subject, body, llm=llm)
        notifier = Notifier(settings)
        logger.info(f"[Webhook] event={event} email={email!r} label={label}")

        factory = get_session_factory()
        async with factory() as session:
            lead = await _repo.get_by_email(session, email) if email else None
            if lead:
                await _repo.record_reply(
                    session,
                    lead,
                    classification=label,
                    subject=subject,
                    snippet=body[:500],
                    instantly_email_id=eid or "webhook",
                )
            await session.commit()
            lead_id = lead.id if lead else ""

        if lead_id and label in ("interested", "unknown", "not_now"):
            from modules.outreach.reply_handler import auto_draft_reply_for_lead

            try:
                await auto_draft_reply_for_lead(
                    settings,
                    lead_id=lead_id,
                    classification=label,
                    subject=subject,
                    snippet=body[:500],
                    llm=llm,
                )
            except Exception as e:
                logger.warning(f"[Webhook] auto_draft failed: {e}")
        elif label == "interested" and email:
            await notifier.send_warn(
                f"Reply from {email} but lead not in agent.db.\n"
                f"Run: python scripts/sync_instantly_replies.py\n"
                f"Or: python scripts/queue_close_approval.py --email {email}"
            )
        elif label == "unsubscribe":
            await notifier.send_warn(f"Unsubscribe webhook: {email}")

        if eid:
            import json

            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            seen: set[str] = set()
            if STATE_FILE.is_file():
                try:
                    seen = set(
                        json.loads(STATE_FILE.read_text()).get("seen_email_ids") or []
                    )
                except Exception:
                    pass
            seen.add(eid)
            STATE_FILE.write_text(
                json.dumps({"seen_email_ids": list(seen)[-5000:]}),
                encoding="utf-8",
            )

        logger.success(f"[Webhook] processed {email} → {label}")
    except Exception as e:
        logger.exception(f"[Webhook] background processing failed: {e}")


@app.get("/webhooks/razorpay")
async def razorpay_webhook_probe() -> dict[str, str]:
    """Browser / Razorpay URL check — real events use POST."""
    return {
        "status": "ok",
        "message": "Razorpay webhook endpoint ready. Events are delivered via POST only.",
    }


@app.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(
        default=None, alias="X-Razorpay-Signature"
    ),
) -> dict[str, str]:
    from api.razorpay_webhook import handle_razorpay_webhook

    return await handle_razorpay_webhook(request, x_razorpay_signature)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
