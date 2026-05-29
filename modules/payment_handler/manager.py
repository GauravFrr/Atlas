"""
Payment Manager — Razorpay links + webhook processing (blueprint P1).
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config import Settings
from constants import LeadStatus, PaymentStatus
from database.connection import get_session_factory
from database.repositories.lead_repository import LeadRepository
from database.repositories.payment_repository import PaymentRepository
from modules.payment_handler.providers.razorpay_client import RazorpayClient
from utils.notifier import Notifier


class Manager:
    def __init__(self, settings: Settings, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router
        self.razorpay = RazorpayClient(settings)
        self.payments = PaymentRepository()
        self.leads = LeadRepository()
        self.notifier = Notifier(settings)

    def default_amount_inr(self) -> int:
        return int(getattr(self.settings, "razorpay_default_amount_inr", 3999) or 3999)

    async def create_link_for_lead(
        self,
        lead_id: str,
        *,
        amount_inr: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create Razorpay payment link and persist to DB."""
        if not self.razorpay.is_configured:
            return {"ok": False, "error": "razorpay_not_configured"}

        factory = get_session_factory()
        async with factory() as session:
            lead = await self.leads.get_by_id(session, lead_id)
            if not lead:
                return {"ok": False, "error": "lead_not_found"}

            existing = await self.payments.get_by_lead(
                session, lead_id, pending_only=True
            )
            if existing and existing.short_url:
                return {
                    "ok": True,
                    "payment_id": existing.id,
                    "short_url": existing.short_url,
                    "amount_inr": int(existing.amount_paise / 100),
                    "reused": True,
                }

            if amount_inr is None:
                from utils.pricing_tiers import (
                    amount_inr_for_lead,
                    payment_description_for_lead,
                )

                tier_inr = amount_inr_for_lead(lead, self.settings)
                amount = tier_inr if tier_inr else self.default_amount_inr()
            else:
                amount = amount_inr

            if description:
                desc = description[:250]
            else:
                from utils.pricing_tiers import payment_description_for_lead

                desc = payment_description_for_lead(lead, self.settings)[:250]
            email = (lead.email or "").strip()
            if not email:
                return {"ok": False, "error": "lead_has_no_email"}

            data = await self.razorpay.create_payment_link(
                amount_inr=amount,
                description=desc,
                customer_name=lead.business_name,
                customer_email=email,
                reference_id=lead.id,
                notes={
                    "lead_id": lead.id,
                    "business": lead.business_name[:80],
                },
            )

            link_id = str(data.get("id") or "")
            short_url = str(data.get("short_url") or "")
            if not link_id or not short_url:
                return {"ok": False, "error": "razorpay_no_link", "raw": data}

            row = await self.payments.create(
                session,
                lead_id=lead.id,
                amount_paise=int(data.get("amount") or amount * 100),
                description=desc,
                customer_email=email,
                customer_name=lead.business_name,
                razorpay_payment_link_id=link_id,
                short_url=short_url,
                reference_id=lead.id,
                notes={"lead_id": lead.id},
            )
            await session.commit()

        return {
            "ok": True,
            "payment_id": row.id,
            "short_url": short_url,
            "amount_inr": amount,
        }

    async def process_webhook(self, *, webhook: dict[str, Any]) -> dict[str, Any]:
        """Confirm payment from queued webhook payload (Atlas P1)."""
        payload = webhook.get("payload") or webhook
        payment_id = webhook.get("payment_id")

        factory = get_session_factory()
        async with factory() as session:
            payment = None
            if payment_id:
                payment = await self.payments.get_by_id(session, payment_id)
            if not payment:
                payment = await self._find_payment_from_payload(session, payload)

            if not payment:
                return {"status": "ignored", "reason": "payment_not_found"}

            if payment.status == PaymentStatus.CONFIRMED:
                payment.webhook_pending = False
                await session.commit()
                return {"status": "already_confirmed", "payment_id": payment.id}

            rz_payment_id = self._extract_payment_id(payload)
            await self.payments.confirm(
                session,
                payment,
                razorpay_payment_id=rz_payment_id,
                payload=payload,
            )

            lead_for_handoff = None
            if payment.lead_id:
                lead_for_handoff = await self.leads.get_by_id(session, payment.lead_id)
                if lead_for_handoff:
                    lead_for_handoff.status = LeadStatus.CLIENT
                    data = dict(lead_for_handoff.enrichment_data or {})
                    data["payment_id"] = payment.id
                    data["payment_link"] = payment.short_url
                    lead_for_handoff.enrichment_data = data

            await session.commit()

            if lead_for_handoff:
                from modules.service_delivery.payment_handoff import (
                    start_delivery_after_payment,
                )

                await start_delivery_after_payment(
                    lead_for_handoff,
                    payment,
                    self.settings,
                    notifier=self.notifier,
                )
                client = lead_for_handoff.business_name
            else:
                amount_inr = payment.amount_paise / 100
                client = payment.customer_name or payment.customer_email or "Client"
                await self.notifier.send_payment_received(
                    amount=f"₹{amount_inr:,.0f}",
                    client=client,
                    method="Razorpay",
                )

        logger.success(f"[Payment] Confirmed {payment.id} for {client}")
        return {"status": "confirmed", "payment_id": payment.id}

    async def handle_webhook_payload(
        self, payload: dict[str, Any], *, queue_only: bool = False
    ) -> dict[str, Any]:
        """
        Called from HTTP webhook. Verifies event, confirms or queues for Atlas.
        """
        event = str(payload.get("event") or "")
        if event not in (
            "payment_link.paid",
            "payment.captured",
            "order.paid",
        ):
            return {"status": "ignored", "event": event}

        factory = get_session_factory()
        async with factory() as session:
            payment = await self._find_payment_from_payload(session, payload)
            if not payment:
                return {"status": "ignored", "reason": "payment_not_found"}

            if payment.status == PaymentStatus.CONFIRMED:
                return {"status": "already_confirmed"}

            if queue_only:
                await self.payments.queue_webhook(session, payment, payload)
                await session.commit()
                return {"status": "queued", "payment_id": payment.id}

        return await self.process_webhook(
            {"payment_id": payment.id, "payload": payload}
        )

    async def _find_payment_from_payload(
        self, session: Any, payload: dict[str, Any]
    ) -> Any | None:
        entity = payload.get("payload") or {}
        if isinstance(entity, dict) and "payment_link" in entity:
            pl = entity.get("payment_link", {}).get("entity", {})
            link_id = pl.get("id")
            if link_id:
                return await self.payments.get_by_link_id(session, str(link_id))

        if isinstance(entity, dict) and "payment" in entity:
            pay = entity.get("payment", {}).get("entity", {})
            notes = pay.get("notes") or {}
            lead_id = notes.get("lead_id")
            if lead_id:
                return await self.payments.get_by_lead(session, str(lead_id))

        # Flat fallback (tests)
        link_id = payload.get("payment_link_id") or payload.get("id")
        if link_id:
            return await self.payments.get_by_link_id(session, str(link_id))
        return None

    @staticmethod
    def _extract_payment_id(payload: dict[str, Any]) -> str | None:
        entity = payload.get("payload") or {}
        if isinstance(entity, dict) and "payment" in entity:
            pay = entity.get("payment", {}).get("entity", {})
            pid = pay.get("id")
            if pid:
                return str(pid)
        return None
