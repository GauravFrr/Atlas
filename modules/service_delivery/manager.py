"""
Service delivery manager — Atlas P2 deliverables after payment.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from config import Settings
from database.connection import get_session_factory
from database.repositories.lead_repository import LeadRepository
from utils.notifier import Notifier


class Manager:
    def __init__(self, settings: Settings, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router
        self.leads = LeadRepository()
        self.notifier = Notifier(settings)

    async def complete_order(self, *, order: dict[str, Any]) -> dict[str, Any]:
        """
        P2 task: remind operator about pending delivery (manual fulfill for now).
        """
        lead_id = str(order.get("lead_id") or order.get("id") or "")
        if not lead_id:
            return {"status": "skipped", "reason": "no_lead_id"}

        factory = get_session_factory()
        async with factory() as session:
            lead = await self.leads.get_by_id(session, lead_id)
            if not lead:
                return {"status": "skipped", "reason": "lead_not_found"}

            delivery = (lead.enrichment_data or {}).get("delivery") or {}
            if delivery.get("status") != "pending":
                return {"status": "skipped", "reason": "no_pending_delivery"}

            from modules.service_delivery.payment_handoff import format_telegram_handoff

            msg = (
                "DELIVERY STILL PENDING\n"
                "━━━━━━━━━━━━━━━━━━\n"
                + format_telegram_handoff(lead, delivery)
            )
            await self.notifier.send_warn(msg)

        logger.info(f"[Delivery] Reminder sent for lead {lead_id}")
        return {"status": "reminded", "lead_id": lead_id}
