"""
Outreach Manager — blueprint P1/P2 tasks for Atlas loop.

  handle_reply   — draft close email, alert human (Telegram)
  send_followups — SMTP sequence steps 2–4 (Instantly leads: DB tracking only)
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import Settings
from core.lead_maps import lead_to_maps_scan
from database.connection import get_session_factory
from database.repositories.lead_repository import LeadRepository
from modules.outreach.mikey_sequence import build_email_2, build_email_3, build_email_ghost
from modules.outreach.close_approval import CloseApprovalService
from utils.notifier import Notifier
from utils.telegram_approval import TelegramApprovalNotifier


class Manager:
    """Called by core.loop._execute_task via decision engine."""

    def __init__(self, settings: Settings, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router
        self.repo = LeadRepository()
        self.notifier = Notifier(settings)

    async def handle_reply(self, *, reply: dict[str, Any]) -> dict[str, Any]:
        """
        P1: Draft response for interested/unknown reply; notify human to send.
        """
        lead_id = reply.get("lead_id")
        if not lead_id:
            return {"status": "skipped", "reason": "no_lead_id"}

        factory = get_session_factory()
        async with factory() as session:
            lead = await self.repo.get_by_id(session, lead_id)
            if not lead:
                return {"status": "skipped", "reason": "lead_not_found"}

            classification = reply.get("classification") or "unknown"
            if classification == "auto_reply":
                await self.repo.mark_reply_handled(session, lead)
                await session.commit()
                return {"status": "closed", "classification": classification}

            approval_svc = CloseApprovalService(self.settings)
            draft = await approval_svc.build_close_draft(
                lead,
                classification,
                reply_subject=str(reply.get("subject") or ""),
                reply_body=str(reply.get("snippet") or ""),
            )

            out_dir = Path("outputs/emails/replies")
            out_dir.mkdir(parents=True, exist_ok=True)
            safe = (lead.email or lead.id or "lead")[:40].replace("@", "_at_")
            path = out_dir / f"reply_draft_{safe}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.txt"
            script_note = ""
            if draft.get("script_label"):
                script_note = f"Script: {draft.get('script_id')} — {draft['script_label']}\n\n"
            path.write_text(
                f"To: {lead.email}\nSubject: {draft['subject']}\n\n{script_note}{draft['body']}",
                encoding="utf-8",
            )

            await self.repo.mark_reply_handled(session, lead, draft_path=str(path))
            await session.commit()

            business_name = lead.business_name
            lead_email = lead.email or ""

        queued = await approval_svc.queue_for_approval(
            lead=lead,
            draft=draft,
            classification=classification,
            draft_path=str(path),
        )
        approval_id = queued.get("approval_id", "")

        telegram_msg_id = None
        if self.settings.has_telegram and getattr(
            self.settings, "telegram_close_approval", True
        ):
            tg = TelegramApprovalNotifier(self.settings)
            telegram_msg_id = await tg.send_approval_request(
                approval_id=approval_id,
                business_name=business_name,
                email=lead_email,
                classification=classification,
                subject=draft["subject"],
                body=draft["body"],
                kind=str(draft.get("kind") or "interested_reply"),
                script_label=str(draft.get("script_label") or ""),
            )
            if telegram_msg_id and approval_id:
                from utils.telegram_approval import store_telegram_message_id

                await store_telegram_message_id(
                    self.settings, approval_id, telegram_msg_id
                )
        else:
            snippet = (reply.get("snippet") or "")[:200]
            await self.notifier.send_urgent(
                f"Reply draft ready ({classification}) — start telegram bot for buttons\n"
                f"Lead: {business_name}\n"
                f"Email: {lead_email}\n"
                f"File: {path}\n\n"
                f"Preview:\n{snippet}"
            )

        logger.success(
            f"[Outreach] Close draft queued for Telegram approval: {path} id={approval_id}"
        )
        return {
            "status": "awaiting_approval",
            "lead_id": lead_id,
            "classification": classification,
            "draft_path": str(path),
            "approval_id": approval_id,
            "telegram_message_id": telegram_msg_id,
        }

    async def send_followups(self, *, leads: list[Any] | None = None) -> dict[str, Any]:
        """
        P2: Send next sequence email for SMTP leads; advance Instantly leads in DB only.
        """
        stats = {"processed": 0, "sent": 0, "tracked": 0, "skipped": 0, "errors": []}
        factory = get_session_factory()
        daily_cap = self.settings.max_emails_per_day

        async with factory() as session:
            if leads and isinstance(leads[0], dict):
                due_ids = [x.get("lead_id") for x in leads if x.get("lead_id")]
                due: list[Any] = []
                for lid in due_ids:
                    row = await self.repo.get_by_id(session, lid)
                    if row:
                        due.append(row)
            elif leads:
                due = list(leads)
            else:
                due = await self.repo.list_followups_due(session, limit=5)

            if not due:
                return stats

            sent_today = await self.repo.count_emails_sent_today(session)

            for lead in due:
                stats["processed"] += 1
                channel = (lead.enrichment_data or {}).get("send_channel") or "smtp"

                if channel == "instantly":
                    await self.repo.advance_followup(session, lead)
                    stats["tracked"] += 1
                    logger.info(
                        f"[Follow-up] {lead.business_name}: Instantly campaign owns sequence "
                        f"(step → {lead.sequence_step})"
                    )
                    continue

                if sent_today >= daily_cap:
                    stats["skipped"] += 1
                    stats["errors"].append("daily_cap_reached")
                    break

                if not (lead.email or "").strip():
                    stats["skipped"] += 1
                    continue

                try:
                    ok = await self._send_smtp_followup(lead)
                    if ok:
                        await self.repo.advance_followup(session, lead)
                        sent_today += 1
                        stats["sent"] += 1
                    else:
                        stats["skipped"] += 1
                except Exception as e:
                    stats["errors"].append(str(e))
                    logger.warning(f"[Follow-up] {lead.business_name}: {e}")

            await session.commit()

        logger.info(f"[Follow-up] done: {stats}")
        return stats

    async def _send_smtp_followup(self, lead: Any) -> bool:
        """Send email 2, 3, or ghost based on sequence_step."""
        from core.campaign_orchestrator import CampaignOrchestrator

        maps = lead_to_maps_scan(lead)
        step = int(lead.sequence_step or 0)
        sender = self.settings.your_name or "Gaurav"

        if step == 0:
            mail = build_email_2(maps, sender_name=sender)
        elif step == 1:
            mail = build_email_3(maps, sender_name=sender)
        elif step == 2:
            mail = build_email_ghost(maps, sender_name=sender)
        else:
            logger.info(f"[Follow-up] {lead.business_name}: sequence complete")
            return False

        orch = CampaignOrchestrator(self.settings)
        orch.llm = self.llm
        domain = orch._domain_for_lead(lead, maps.place_id)
        smtp_cfg = orch._smtp_for_lead(lead, domain)
        if not smtp_cfg:
            logger.warning("[Follow-up] No SMTP mailbox configured")
            return False

        ok = orch.email_engine.send_email(
            to_email=lead.email or "",
            subject=mail["subject"],
            body=mail["body"],
            smtp_config=smtp_cfg,
            dry_run=False,
        )
        if ok:
            from utils.mailbox_lock import lock_mailbox_on_lead

            lock_mailbox_on_lead(lead, smtp_cfg=smtp_cfg, domain=domain, send_channel="smtp")
            logger.success(
                f"[Follow-up] SMTP step {step + 1} → {lead.email} "
                f"from {smtp_cfg.get('from_email', '')} ({lead.business_name})"
            )
        return ok
