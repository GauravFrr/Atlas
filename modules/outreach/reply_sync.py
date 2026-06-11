"""
Sync Instantly Unibox replies → update leads in DB → Telegram alerts for hot replies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import Settings
from constants import LeadStatus
from database.connection import get_session_factory
from database.repositories.lead_repository import LeadRepository
from integrations.platforms.instantly import InstantlyClient
from modules.outreach.reply_classifier import (
    ReplyClass,
    classify_reply,
    classify_reply_async,
)
from utils.notifier import Notifier

def reply_state_file() -> Path:
    """Persist reply dedupe next to agent.db (or data/ for Postgres-only deploys)."""
    from database.connection import RAILWAY_DATA_DIR, get_database_url

    if RAILWAY_DATA_DIR.is_dir():
        return RAILWAY_DATA_DIR / "instantly_reply_state.json"
    try:
        from sqlalchemy.engine import make_url

        parsed = make_url(get_database_url())
        if parsed.drivername.startswith("sqlite") and parsed.database:
            db_path = Path(parsed.database)
            if db_path.parent.is_dir():
                return db_path.parent / "instantly_reply_state.json"
    except Exception:
        pass
    return Path("data/instantly_reply_state.json")
UE_TYPE_RECEIVED = 2


@dataclass
class ReplySyncResult:
    scanned: int = 0
    new_replies: int = 0
    interested: int = 0
    not_now: int = 0
    unsubscribe: int = 0
    auto_reply: int = 0
    unknown: int = 0
    skipped_seen: int = 0
    errors: list[str] = field(default_factory=list)


def _email_body(item: dict[str, Any]) -> str:
    body = item.get("body") or {}
    if isinstance(body, dict):
        return (body.get("text") or body.get("html") or "").strip()
    return str(body).strip()


def _is_incoming_reply(item: dict[str, Any]) -> bool:
    if item.get("is_auto_reply") in (1, True):
        return False
    ue = item.get("ue_type")
    if ue == UE_TYPE_RECEIVED:
        return True
    # API filter email_type=received; keep guard
    return True


class InstantlyReplySync:
    def __init__(self, settings: Settings, llm: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm
        self.client = InstantlyClient(
            settings.instantly_api_key,
            settings.instantly_campaign_id,
        )
        self.repo = LeadRepository()
        self.notifier = Notifier(settings)
        reply_state_file().parent.mkdir(parents=True, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    def _load_seen(self) -> set[str]:
        path = reply_state_file()
        if not path.is_file():
            return set()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return set(data.get("seen_email_ids") or [])
        except Exception:
            return set()

    def _save_seen(self, seen: set[str], max_ids: int = 5000) -> None:
        ids = list(seen)[-max_ids:]
        reply_state_file().write_text(
            json.dumps({"seen_email_ids": ids}, indent=0),
            encoding="utf-8",
        )

    async def sync_once(self, *, limit: int = 50) -> ReplySyncResult:
        out = ReplySyncResult()
        if not self.is_configured:
            out.errors.append("Instantly not configured")
            return out

        seen = self._load_seen()
        items, _ = await self.client.list_emails(
            campaign_id=self.settings.instantly_campaign_id,
            email_type="received",
            limit=limit,
        )
        out.scanned = len(items)

        factory = get_session_factory()
        async with factory() as session:
            for item in items:
                eid = str(item.get("id") or "")
                if not eid or eid in seen:
                    out.skipped_seen += 1
                    continue
                if not _is_incoming_reply(item):
                    seen.add(eid)
                    continue

                lead_email = (item.get("lead") or "").strip().lower()
                if not lead_email:
                    # Incoming from lead: from_address may be lead; to is our mailbox
                    from_addr = (item.get("from_address_email") or "").strip().lower()
                    if from_addr and "@" in from_addr:
                        lead_email = from_addr

                subject = str(item.get("subject") or "")
                body = _email_body(item)
                if classify_reply(subject, body) == "auto_reply":
                    out.auto_reply += 1
                    seen.add(eid)
                    continue

                label: ReplyClass = await classify_reply_async(
                    subject, body, llm=self.llm
                )
                out.new_replies += 1
                if label == "interested":
                    out.interested += 1
                elif label == "not_now":
                    out.not_now += 1
                elif label == "unsubscribe":
                    out.unsubscribe += 1
                elif label == "auto_reply":
                    out.auto_reply += 1
                else:
                    out.unknown += 1

                lead = await self.repo.get_by_email(session, lead_email) if lead_email else None
                if lead:
                    await self.repo.record_reply(
                        session,
                        lead,
                        classification=label,
                        subject=subject,
                        snippet=body[:500],
                        instantly_email_id=eid,
                    )
                else:
                    logger.info(
                        f"[Reply] {lead_email or '?'} not in memory bank — {label}"
                    )

                await self._notify(label, lead_email, subject, body, lead)
                if lead:
                    await self._auto_draft(label, lead, subject, body)
                seen.add(eid)

            await session.commit()

        self._save_seen(seen)
        return out

    async def _auto_draft(
        self,
        label: ReplyClass,
        lead: Any,
        subject: str,
        body: str,
    ) -> None:
        from modules.outreach.reply_handler import auto_draft_reply_for_lead

        try:
            await auto_draft_reply_for_lead(
                self.settings,
                lead_id=lead.id,
                classification=label,
                subject=subject,
                snippet=body[:500],
                llm=self.llm,
            )
        except Exception as e:
            logger.warning(f"[Reply] auto_draft failed for {lead.business_name}: {e}")

    async def _notify(
        self,
        label: ReplyClass,
        email: str,
        subject: str,
        body: str,
        lead: Any | None,
    ) -> None:
        biz = lead.business_name if lead else email
        snippet = body[:200] if body else subject

        if label == "interested":
            # Telegram approval message is sent by handle_reply; skip duplicate hot ping
            if not getattr(self.settings, "telegram_auto_draft_on_reply", True):
                await self.notifier.send_hot_reply(email or biz, subject, snippet)
        elif label == "unsubscribe":
            await self.notifier.send_warn(
                f"Unsubscribe: {email}\n{biz}\nRemove from Instantly if needed."
            )
        elif label == "not_now":
            await self.notifier.send_info(f"Not now: {biz} ({email})")
        elif label == "unknown" and self.settings.reply_alert_on_unknown:
            await self.notifier.send_info(
                f"New reply (review): {biz}\n{subject}\n{snippet[:120]}..."
            )


async def sync_instantly_replies(settings: Settings | None = None) -> ReplySyncResult:
    settings = settings or __import__("config", fromlist=["get_settings"]).get_settings()
    llm = None
    if settings.has_gemini or settings.has_groq:
        from llm.router import LLMRouter

        llm = LLMRouter(settings)
    sync = InstantlyReplySync(settings, llm=llm)
    result = await sync.sync_once(limit=settings.instantly_reply_sync_limit)
    logger.info(
        f"[Reply sync] scanned={result.scanned} new={result.new_replies} "
        f"hot={result.interested} skip_seen={result.skipped_seen}"
    )
    return result
