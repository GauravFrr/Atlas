"""
Post-payment delivery handoff (blueprint §22 steps 6–7).

When Razorpay confirms: mark delivery pending, store checklist on lead, Telegram operator.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import Settings
from constants import LeadStatus
from database.models.lead import Lead
from database.models.payment import Payment
from utils.pricing_tiers import payment_description_for_lead, pitch_key_for_lead

# pitch_key → human label + delivery steps
_CHECKLISTS: dict[str, tuple[str, list[str]]] = {
    "website": (
        "Landing page + lead capture",
        [
            "Review approved demo / scope with client",
            "Finalize copy + contact form fields",
            "Deploy to Hostinger (or client DNS)",
            "Connect domain + SSL",
            "Send live URL + 1-page handoff email",
        ],
    ),
    "website_full": (
        "Website rebuild package",
        [
            "Audit current site + save assets",
            "Rebuild mobile-first pages from demo",
            "Forms, SSL, speed check",
            "Deploy + DNS cutover (or staging first)",
            "Send live URL + short Loom/walkthrough",
        ],
    ),
    "automation": (
        "AI chatbot & automation",
        [
            "Confirm site access / embed point",
            "Configure chatbot + lead capture rules",
            "Test booking / reply flows",
            "Send embed code or install for client",
            "30-min handoff call or loom",
        ],
    ),
    "youtube": (
        "Channel / content package",
        [
            "Confirm channel + brand guidelines",
            "Deliver content pack / scripts",
            "Schedule or hand off posting plan",
            "Send delivery zip + next steps",
        ],
    ),
}


def demo_url_for_lead(lead: Lead, settings: Settings) -> str:
    data = lead.enrichment_data or {}
    return str(data.get("demo_url") or data.get("public_demo_url") or "").strip()


def build_delivery_record(
    lead: Lead,
    payment: Payment,
    settings: Settings,
) -> dict[str, Any]:
    pitch_key = pitch_key_for_lead(lead)
    label, steps = _CHECKLISTS.get(pitch_key, _CHECKLISTS["website"])
    amount_inr = int(payment.amount_paise / 100)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "status": "pending",
        "started_at": now,
        "payment_id": payment.id,
        "razorpay_payment_id": payment.razorpay_payment_id or "",
        "amount_inr": amount_inr,
        "pitch_key": pitch_key,
        "package_label": label,
        "description": payment.description or payment_description_for_lead(lead, settings),
        "demo_url": demo_url_for_lead(lead, settings),
        "checklist": steps,
        "completed_steps": [],
    }


def format_telegram_handoff(lead: Lead, delivery: dict[str, Any]) -> str:
    lines = [
        "PAID — START DELIVERY",
        "━━━━━━━━━━━━━━━━━━",
        f"Client: {lead.business_name}",
        f"Email: {lead.email or '—'}",
        f"Amount: ₹{delivery.get('amount_inr', 0):,}",
        f"Package: {delivery.get('package_label', '—')}",
    ]
    demo = str(delivery.get("demo_url") or "").strip()
    if demo:
        lines.append(f"Demo: {demo}")
    if lead.website:
        lines.append(f"Site: {lead.website}")
    lines.append(f"Lead ID: {lead.id}")
    lines.append("")
    lines.append("CHECKLIST:")
    for i, step in enumerate(delivery.get("checklist") or [], 1):
        lines.append(f"  {i}. [ ] {step}")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("Mark done in DB or finish checklist, then deliver.")
    return "\n".join(lines)


async def start_delivery_after_payment(
    lead: Lead,
    payment: Payment,
    settings: Settings,
    *,
    notifier: Any | None = None,
) -> dict[str, Any]:
    """
    Attach delivery record to lead and notify operator.
    Call after payment is confirmed and lead.status = CLIENT.
    """
    if lead.status != LeadStatus.CLIENT:
        logger.warning(f"[Delivery] Lead {lead.id} not CLIENT ({lead.status})")

    data = dict(lead.enrichment_data or {})
    existing = data.get("delivery") or {}
    if existing.get("status") == "pending" and existing.get("payment_id") == payment.id:
        delivery = existing
        logger.info(f"[Delivery] Handoff already started for payment {payment.id}")
    else:
        delivery = build_delivery_record(lead, payment, settings)
        data["delivery"] = delivery
        data["payment_id"] = payment.id
        data["payment_link"] = payment.short_url or data.get("payment_link")
        lead.enrichment_data = data

    msg = format_telegram_handoff(lead, delivery)
    if notifier is None:
        from utils.notifier import Notifier

        notifier = Notifier(settings)
    await notifier.send_payment_delivery_handoff(msg)

    logger.success(
        f"[Delivery] Handoff started: {lead.business_name} | {delivery.get('package_label')}"
    )
    return {"ok": True, "delivery": delivery, "lead_id": lead.id}
