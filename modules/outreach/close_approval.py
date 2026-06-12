"""
Close-email approval — draft → Telegram buttons → Instantly reply (or SMTP fallback) on approve.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import Settings
from constants import LeadStatus
from database.connection import get_session_factory
from database.models.lead import Lead
from database.repositories.lead_repository import LeadRepository
from modules.outreach.close_approval_store import (
    build_approval_payload,
    extract_payment_url,
    new_approval_id,
    register,
    resolve,
    unregister,
)
from modules.outreach.reply_drafter import draft_payment_link_reply, draft_reply_for_lead


class CloseApprovalService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo = LeadRepository()

    async def build_close_draft(
        self,
        lead: Lead,
        classification: str,
        *,
        reply_subject: str = "",
        reply_body: str = "",
    ) -> dict[str, str]:
        """Universal script (1–8, objections, close) — no payment unless script=close text only."""
        draft = draft_reply_for_lead(
            lead,
            self.settings,
            classification=classification,
            reply_subject=reply_subject,
            reply_body=reply_body,
        )
        # Never attach Razorpay here — payment is a separate approved email
        if draft.get("script_id") == "close":
            draft["kind"] = "close_reply"
        draft["payment_url"] = ""
        return draft

    async def build_payment_draft(self, lead: Lead) -> dict[str, Any]:
        """Payment-link email — use after they agree on scope / call."""
        if not self.settings.has_razorpay:
            return {"ok": False, "error": "razorpay_not_configured"}

        from modules.payment_handler.manager import Manager as PaymentManager

        pm = PaymentManager(self.settings)
        link_result = await pm.create_link_for_lead(lead.id)
        if not link_result.get("ok") or not link_result.get("short_url"):
            return {"ok": False, "error": "payment_link_failed", "raw": link_result}

        amt = int(link_result.get("amount_inr") or pm.default_amount_inr())
        url = str(link_result["short_url"])
        draft = draft_payment_link_reply(
            lead, self.settings, payment_url=url, amount_inr=amt
        )
        draft["payment_url"] = url
        draft["kind"] = "payment_link"
        return {"ok": True, "draft": draft, "amount_inr": amt}

    async def queue_for_approval(
        self,
        *,
        lead: Lead,
        draft: dict[str, str],
        classification: str,
        draft_path: str,
    ) -> dict[str, Any]:
        """Persist pending approval on lead + index file."""
        approval_id = new_approval_id()
        payload = build_approval_payload(
            approval_id=approval_id,
            lead_id=lead.id,
            subject=draft["subject"],
            body=draft["body"],
            classification=classification,
            payment_url=draft.get("payment_url") or extract_payment_url(draft["body"]),
            draft_path=draft_path,
        )
        payload["kind"] = draft.get("kind") or "interested_reply"
        register(approval_id, lead.id)

        factory = get_session_factory()
        async with factory() as session:
            row = await self.repo.get_by_id(session, lead.id)
            if not row:
                return {"ok": False, "error": "lead_not_found"}
            data = dict(row.enrichment_data or {})
            data["close_approval"] = payload
            data["reply_draft_path"] = draft_path
            data["pending_reply_action"] = False
            row.enrichment_data = data
            if row.status not in (LeadStatus.CLIENT, LeadStatus.UNSUBSCRIBED):
                row.status = LeadStatus.REPLIED
            await session.commit()

        return {"ok": True, "approval_id": approval_id, "payload": payload}

    async def get_pending(self, approval_id: str) -> tuple[Lead | None, dict[str, Any] | None]:
        lead_id = resolve(approval_id)
        if not lead_id:
            return None, None
        factory = get_session_factory()
        async with factory() as session:
            lead = await self.repo.get_by_id(session, lead_id)
            if not lead:
                return None, None
            approval = (lead.enrichment_data or {}).get("close_approval") or {}
            if approval.get("id") != approval_id:
                return lead, None
            if approval.get("status") != "pending":
                return lead, approval
            return lead, approval

    async def approve_and_send(self, approval_id: str) -> dict[str, Any]:
        lead, approval = await self.get_pending(approval_id)
        if not lead or not approval:
            return {"ok": False, "error": "not_found_or_already_handled"}

        email = (lead.email or "").strip()
        if not email:
            return {"ok": False, "error": "lead_has_no_email"}

        send_channel = ""
        sent = False

        if self.settings.close_send_via_instantly and self.settings.has_instantly:
            from modules.outreach.instantly_reply_send import (
                send_approved_reply_via_instantly,
            )

            instantly_result = await send_approved_reply_via_instantly(
                self.settings,
                lead,
                subject=str(approval.get("subject") or ""),
                body=str(approval.get("body") or ""),
            )
            if instantly_result.get("ok"):
                sent = True
                send_channel = "instantly"
            elif not self.settings.close_send_smtp_fallback:
                err = instantly_result.get("error") or "instantly_reply_failed"
                logger.warning(f"[CloseApproval] Instantly reply failed: {err}")
                return {"ok": False, "error": err, "instantly": instantly_result}
            else:
                logger.warning(
                    f"[CloseApproval] Instantly reply failed ({instantly_result.get('error')}) "
                    "— trying SMTP fallback"
                )

        if not sent:
            from core.campaign_orchestrator import CampaignOrchestrator

            orch = CampaignOrchestrator(self.settings)
            smtp_cfg = orch._smtp_for_close_reply(lead, None)
            domain = (
                orch.domain_pool.get_by_from_email(str(smtp_cfg.get("from_email") or ""))
                if smtp_cfg
                else None
            )
            if not smtp_cfg:
                logger.warning("[CloseApproval] No SMTP for locked mailbox / domain pool")
                return {"ok": False, "error": "smtp_not_configured"}

            sent = orch.email_engine.send_email(
                to_email=email,
                subject=approval["subject"],
                body=approval["body"],
                smtp_config=smtp_cfg,
                dry_run=False,
            )
            if sent:
                from utils.mailbox_lock import lock_mailbox_on_lead

                lock_mailbox_on_lead(
                    lead,
                    smtp_cfg=smtp_cfg,
                    domain=domain,
                    send_channel=str(
                        (lead.enrichment_data or {}).get("send_channel") or "smtp"
                    ),
                )
                send_channel = "smtp"
            if not sent:
                return {"ok": False, "error": "smtp_send_failed"}

        from utils.mailbox_lock import merge_mailbox_lock_into

        factory = get_session_factory()
        async with factory() as session:
            row = await self.repo.get_by_id(session, lead.id)
            if row:
                data = merge_mailbox_lock_into(dict(row.enrichment_data or {}), lead)
                ca = dict(data.get("close_approval") or {})
                ca["status"] = "sent"
                ca["sent_at"] = datetime.now(timezone.utc).isoformat()
                data["close_approval"] = ca
                data["close_email_sent_at"] = ca["sent_at"]
                data["pending_reply_action"] = False
                data["ready_for_payment_link"] = True
                row.enrichment_data = data
                await session.commit()

        unregister(approval_id)
        logger.success(
            f"[CloseApproval] Sent reply email to {email} via {send_channel or 'unknown'}"
        )

        return {
            "ok": True,
            "email": email,
            "lead_id": lead.id,
            "send_channel": send_channel,
            "offer_payment_link": self.settings.has_razorpay,
        }

    async def queue_payment_for_approval(self, lead_id: str) -> dict[str, Any]:
        """Second step: payment link email after interested reply was sent."""
        factory = get_session_factory()
        async with factory() as session:
            lead = await self.repo.get_by_id(session, lead_id)
            if not lead:
                return {"ok": False, "error": "lead_not_found"}

        built = await self.build_payment_draft(lead)
        if not built.get("ok"):
            return built

        draft = built["draft"]
        out_dir = Path("outputs/emails/replies")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = (lead.email or lead.id or "lead")[:40].replace("@", "_at_")
        path = out_dir / f"payment_draft_{safe}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.txt"
        path.write_text(
            f"To: {lead.email}\nSubject: {draft['subject']}\n\n{draft['body']}",
            encoding="utf-8",
        )
        return await self.queue_for_approval(
            lead=lead,
            draft=draft,
            classification="payment_link",
            draft_path=str(path),
        )

    async def recreate(self, approval_id: str) -> dict[str, Any]:
        lead_id = resolve(approval_id)
        if not lead_id:
            return {"ok": False, "error": "not_found"}

        factory = get_session_factory()
        async with factory() as session:
            lead = await self.repo.get_by_id(session, lead_id)
            if not lead:
                return {"ok": False, "error": "lead_not_found"}
            classification = (lead.enrichment_data or {}).get("close_approval", {}).get(
                "classification"
            ) or (lead.enrichment_data or {}).get("last_reply", {}).get(
                "classification", "interested"
            )

        kind = (lead.enrichment_data or {}).get("close_approval", {}).get("kind")
        if kind == "payment_link":
            built = await self.build_payment_draft(lead)
            if not built.get("ok"):
                return built
            draft = built["draft"]
        else:
            last = (lead.enrichment_data or {}).get("last_reply") or {}
            draft = await self.build_close_draft(
                lead,
                classification,
                reply_subject=str(last.get("subject") or ""),
                reply_body=str(last.get("snippet") or ""),
            )
        out_dir = Path("outputs/emails/replies")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = (lead.email or lead.id or "lead")[:40].replace("@", "_at_")
        path = out_dir / f"reply_draft_{safe}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.txt"
        path.write_text(
            f"To: {lead.email}\nSubject: {draft['subject']}\n\n{draft['body']}",
            encoding="utf-8",
        )

        unregister(approval_id)
        result = await self.queue_for_approval(
            lead=lead,
            draft=draft,
            classification=classification,
            draft_path=str(path),
        )
        return {
            "ok": True,
            "approval_id": result.get("approval_id"),
            "draft": draft,
            "draft_path": str(path),
        }

    async def skip(self, approval_id: str) -> dict[str, Any]:
        lead, approval = await self.get_pending(approval_id)
        if not lead:
            return {"ok": False, "error": "not_found"}

        factory = get_session_factory()
        async with factory() as session:
            row = await self.repo.get_by_id(session, lead.id)
            if row:
                data = dict(row.enrichment_data or {})
                ca = dict(data.get("close_approval") or {})
                ca["status"] = "skipped"
                data["close_approval"] = ca
                data["pending_reply_action"] = False
                row.enrichment_data = data
                await session.commit()

        unregister(approval_id)
        return {"ok": True, "lead_id": lead.id}
