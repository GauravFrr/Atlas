"""Data for Atlas Telegram owner panel."""

from __future__ import annotations

from typing import Any

from config import Settings
from constants import LeadStatus
from database.connection import get_session_factory
from database.repositories.lead_repository import LeadRepository
from database.repositories.payment_repository import PaymentRepository
from utils.telegram_bot.ui import esc, header_block


def lead_short_id(lead_id: str) -> str:
    return lead_id.replace("-", "")[:8]


async def fetch_status(settings: Settings) -> str:
    repo = LeadRepository()
    factory = get_session_factory()
    async with factory() as session:
        counts = await repo.count_by_status(session)
        inv = await repo.count_inventory_summary(session)
        pending_replies = await repo.list_unread_replies(session, limit=20)
        deliveries = await repo.list_pending_deliveries(session, limit=20)

    lines = [
        header_block(settings, "Pipeline status"),
        "",
        "<b>Inventory</b>",
        f"  • Total in DB — {inv['total']}",
        f"  • <b>Has email</b> (sellable) — {inv['with_email']}",
        f"  • No email (saved only) — {inv['no_email']}",
        "",
        "<b>Outreach pipeline</b> (has email)",
        f"  • new — {counts.get(LeadStatus.NEW, 0)}",
        f"  • draft_ready — {counts.get(LeadStatus.DRAFT_READY, 0)}",
        f"  • contacted — {counts.get(LeadStatus.CONTACTED, 0)}",
        f"  • replied — {counts.get(LeadStatus.REPLIED, 0)}",
    ]
    tiers = inv.get("tier_counts") or {}
    if tiers:
        lines.extend(["", "<b>Sell packages</b> (has email)"])
        for tier in ("exclusive", "enriched", "standard", "basic"):
            n = tiers.get(tier, 0)
            if n:
                lines.append(f"  • {tier} — {n}")
        unsorted = tiers.get("unsorted", 0)
        if unsorted:
            lines.append(f"  • unsorted — {unsorted}")

    skipped = counts.get(LeadStatus.SKIPPED, 0)
    if skipped:
        lines.extend(
            [
                "",
                f"<b>Skipped — {skipped}</b> <i>(mostly no email; kept for /export)</i>",
            ]
        )
        for reason, n in list((inv.get("skip_reasons") or {}).items())[:3]:
            lines.append(f"  • {esc(reason)} — {n}")

    lines.extend(
        [
            "",
            f"🔔 <b>Need reply draft:</b> {len(pending_replies)}",
            f"📦 <b>Pending delivery:</b> {len(deliveries)}",
            "",
            "<i>Tip: /export for CSV · add HUNTER_API_KEY + GOOGLE_PLACES for more emails</i>",
        ]
    )
    return "\n".join(lines)


async def fetch_health(settings: Settings) -> str:
    from utils.health_checker import HealthChecker

    report = await HealthChecker(settings).check_all()
    lines = [header_block(settings, "System health"), ""]
    for name, data in sorted(report.items()):
        if isinstance(data, Exception):
            lines.append(f"❌ <code>{esc(name)}</code> — error")
            continue
        ok = data.get("healthy", False)
        icon = "✅" if ok else "❌"
        extra = data.get("bot_name") or data.get("error") or ""
        suffix = f" ({esc(extra)})" if extra and not ok else ""
        if ok and data.get("bot_name"):
            suffix = f" — {esc(data['bot_name'])}"
        lines.append(f"{icon} <code>{esc(name)}</code>{suffix}")
    return "\n".join(lines)


async def fetch_leads_list(settings: Settings, limit: int = 8) -> tuple[str, list[tuple[str, str, str]]]:
    from core.lead_sources import available_hunt_modes, hunt_mode_label

    repo = LeadRepository()
    factory = get_session_factory()
    rows: list[tuple[str, str, str]] = []
    async with factory() as session:
        leads = await repo.list_recent_outreach(session, limit=limit)
        inv = await repo.count_inventory_summary(session)

    lines = [header_block(settings, "Outreach leads (has email)"), ""]
    if not leads:
        modes = available_hunt_modes(settings)
        mode_hint = hunt_mode_label(modes[0]) if modes else "m10"
        lines.extend(
            [
                "<i>No leads with email yet.</i>",
                "",
                f"Inventory: {inv.get('with_email', 0)} sellable · "
                f"{inv.get('no_email', 0)} no-email saved",
                "",
                "Atlas was hunting <b>app store apps</b> (M07) — those rarely have emails.",
                f"Production now uses: <code>{esc(', '.join(modes[:4]))}…</code>",
                "",
                "<i>/export for inventory · /status for full breakdown</i>",
            ]
        )
        return "\n".join(lines), rows

    for lead in leads:
        short = lead_short_id(lead.id)
        email = (lead.email or "")[:28]
        data = lead.enrichment_data or {}
        hunt = str(data.get("hunt_mode") or lead.source or "")[:12]
        label = f"{lead.business_name[:22]} · {lead.status}"
        rows.append((short, label, lead.status))
        lines.append(
            f"• <b>{esc(lead.business_name)}</b>\n"
            f"  <code>{esc(email)}</code> · {esc(lead.status)}"
            + (f" · <i>{esc(hunt)}</i>" if hunt else "")
        )
    lines.append("\n<i>Tap a lead below for actions.</i>")
    return "\n".join(lines), rows


async def fetch_lead_detail(settings: Settings, short: str) -> str | None:
    lead = await _resolve_lead(short)
    if not lead:
        return None
    data = lead.enrichment_data or {}
    delivery = data.get("delivery") or {}
    lines = [
        header_block(settings, "Lead detail"),
        "",
        f"<b>{esc(lead.business_name)}</b>",
        f"📧 <code>{esc(lead.email)}</code>",
        f"📌 Status: <code>{esc(lead.status)}</code>",
        f"🆔 <code>{esc(lead.id)}</code>",
    ]
    if lead.demo_url:
        lines.append(f"🌐 {esc(lead.demo_url)}")
    if data.get("outbound_mailbox"):
        lines.append(f"📮 Locked: <code>{esc(data['outbound_mailbox'])}</code>")
    last = data.get("last_reply") or {}
    if last.get("snippet"):
        lines.append(f"\n<b>Last reply</b>\n<i>{esc(str(last.get('snippet'))[:400])}</i>")
    if delivery.get("status") == "pending":
        lines.append("\n📦 <b>Delivery pending</b>")
    return "\n".join(lines)


async def fetch_replies(settings: Settings) -> str:
    repo = LeadRepository()
    factory = get_session_factory()
    async with factory() as session:
        items = await repo.list_unread_replies(session, limit=10)

    lines = [header_block(settings, "Replies needing action"), ""]
    if not items:
        lines.append("✅ <i>No pending reply drafts.</i>")
        return "\n".join(lines)

    for it in items:
        lines.append(
            f"• <b>{esc(it['business_name'])}</b>\n"
            f"  <code>{esc(it['email'])}</code> · {esc(it['classification'])}\n"
            f"  <i>{esc(str(it.get('snippet', ''))[:120])}</i>"
        )
    lines.append(
        "\nUse <code>queue_close_approval.py --email …</code> or tap lead → Draft reply."
    )
    return "\n".join(lines)


async def fetch_payments(settings: Settings) -> str:
    repo = LeadRepository()
    pay_repo = PaymentRepository()
    factory = get_session_factory()
    lines = [header_block(settings, "Payments"), ""]
    async with factory() as session:
        leads = await repo.list_recent(session, limit=30)
        pending: list[tuple[Any, Any]] = []
        for lead in leads:
            if lead.status == LeadStatus.CLIENT:
                continue
            pay = await pay_repo.get_by_lead(session, lead.id, pending_only=True)
            if pay and pay.short_url:
                pending.append((lead, pay))

    if not pending:
        lines.append("<i>No pending payment links.</i>")
        return "\n".join(lines)

    for lead, pay in pending[:10]:
        inr = int(pay.amount_paise / 100)
        lines.append(
            f"• <b>{esc(lead.business_name)}</b>\n"
            f"  INR {inr:,} — <code>{esc(pay.short_url)}</code>"
        )
    return "\n".join(lines)


async def fetch_delivery(settings: Settings) -> str:
    repo = LeadRepository()
    factory = get_session_factory()
    async with factory() as session:
        items = await repo.list_pending_deliveries(session, limit=10)

    lines = [header_block(settings, "Delivery queue"), ""]
    if not items:
        lines.append("✅ <i>No pending deliveries.</i>")
        return "\n".join(lines)

    for lead in items:
        d = (lead.enrichment_data or {}).get("delivery") or {}
        pkg = d.get("package_label") or "Package"
        lines.append(
            f"• <b>{esc(lead.business_name)}</b>\n"
            f"  {esc(pkg)} · <code>{esc(lead.email)}</code>"
        )
    return "\n".join(lines)


async def fetch_stack(settings: Settings) -> str:
    flags = [
        ("Instantly", settings.has_instantly),
        ("SMTP / Hostinger", settings.has_smtp),
        ("Razorpay", settings.has_razorpay),
        ("Telegram", settings.has_telegram),
        ("Gemini", settings.has_gemini),
        ("Groq", settings.has_groq),
        ("Google Places", bool(settings.google_places_api_key)),
    ]
    lines = [header_block(settings, "Configured stack"), ""]
    for name, ok in flags:
        lines.append(f"{'✅' if ok else '○'} {esc(name)}")
    from utils.send_router import describe_mode, resolve_send_mode

    raw = getattr(settings, "email_send_mode", "instantly") or "instantly"
    resolved = resolve_send_mode(settings, raw)
    lines.append(f"\n📤 Cold send: <code>{esc(resolved)}</code>")
    lines.append(f"<i>{esc(describe_mode(resolved))}</i>")
    lines.append(
        "<i>Replies: Instantly webhook + /replies · SMTP only for approved close emails</i>"
    )
    return "\n".join(lines)


async def run_instantly_sync(settings: Settings) -> str:
    if not settings.has_instantly:
        return "❌ Instantly not configured in .env"
    from modules.outreach.reply_sync import sync_instantly_replies

    result = await sync_instantly_replies(settings)
    return "\n".join(
        [
            header_block(settings, "Instantly sync"),
            "",
            f"Scanned: <b>{result.scanned}</b>",
            f"New replies: <b>{result.new_replies}</b>",
            f"Interested: <b>{result.interested}</b>",
            f"Errors: <b>{len(result.errors)}</b>",
        ]
    )


async def _resolve_lead(short: str):
    from sqlalchemy import select

    from database.models.lead import Lead

    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(Lead).where(Lead.is_deleted.is_(False)).limit(500)
        )
        for lead in result.scalars():
            if lead_short_id(lead.id) == short[:8]:
                return lead
    return None


async def resolve_lead_id(short: str) -> str | None:
    lead = await _resolve_lead(short)
    return lead.id if lead else None
