"""Command and callback handlers for Atlas Telegram bot."""

from __future__ import annotations

import io

from telegram import BotCommand, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config import Settings
from utils.telegram_approval import TelegramApprovalNotifier, store_telegram_message_id
from utils.telegram_bot import panel
from utils.telegram_bot.owner import is_owner, reject_non_owner
from utils.telegram_bot.ui import (
    back_menu_keyboard,
    help_text,
    lead_detail_keyboard,
    leads_keyboard,
    main_menu_keyboard,
    welcome_text,
)


def _settings(context: ContextTypes.DEFAULT_TYPE) -> Settings:
    return context.application.bot_data["settings"]


async def _reply_html(
    update: Update,
    text: str,
    *,
    keyboard=None,
    edit: bool = False,
) -> None:
    if edit and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise
            # User tapped same panel again (e.g. Menu while on menu)
        return
    msg = update.effective_message
    if msg:
        await msg.reply_text(
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    await _reply_html(
        update,
        welcome_text(settings),
        keyboard=main_menu_keyboard(),
    )


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    await _reply_html(update, help_text(settings), keyboard=back_menu_keyboard())


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    text = await panel.fetch_status(settings)
    await _reply_html(update, text, keyboard=back_menu_keyboard())


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    await update.effective_message.reply_text("Checking…")
    text = await panel.fetch_health(settings)
    await _reply_html(update, text, keyboard=back_menu_keyboard())


async def cmd_leads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    text, rows = await panel.fetch_leads_list(settings)
    await _reply_html(update, text, keyboard=leads_keyboard(rows))


async def cmd_replies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    text = await panel.fetch_replies(settings)
    await _reply_html(update, text, keyboard=back_menu_keyboard())


async def cmd_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    text = await panel.fetch_payments(settings)
    await _reply_html(update, text, keyboard=back_menu_keyboard())


async def cmd_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    text = await panel.fetch_delivery(settings)
    await _reply_html(update, text, keyboard=back_menu_keyboard())


async def cmd_stack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return
    text = await panel.fetch_stack(settings)
    await _reply_html(update, text, keyboard=back_menu_keyboard())


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = _settings(context)
    if await reject_non_owner(update, settings):
        return

    from database.connection import get_session_factory
    from database.repositories.lead_repository import LeadRepository
    from utils.lead_export import (
        export_help_text,
        inventory_summary_text,
        parse_export_args,
        run_export,
    )

    tokens = list(context.args or [])
    if not tokens:
        repo = LeadRepository()
        factory = get_session_factory()
        async with factory() as session:
            counts = await repo.count_by_package_tier(session)
        await _reply_html(
            update,
            inventory_summary_text(counts),
            keyboard=back_menu_keyboard(),
        )
        return

    if tokens[0].lower() in ("help", "?", "inventory"):
        if tokens[0].lower() == "inventory":
            repo = LeadRepository()
            factory = get_session_factory()
            async with factory() as session:
                counts = await repo.count_by_package_tier(session)
            await _reply_html(
                update,
                inventory_summary_text(counts),
                keyboard=back_menu_keyboard(),
            )
            return
        await _reply_html(
            update, export_help_text(), keyboard=back_menu_keyboard()
        )
        return

    parsed = parse_export_args(tokens)
    if parsed == "help":
        await _reply_html(
            update, export_help_text(), keyboard=back_menu_keyboard()
        )
        return
    if isinstance(parsed, str):
        await update.effective_message.reply_text(parsed)
        return

    await update.effective_message.reply_text(
        f"Building export… ({', '.join(parsed.label_parts())})"
    )

    repo = LeadRepository()
    factory = get_session_factory()
    async with factory() as session:
        result = await run_export(session, repo, parsed)

    if not result.files:
        await _reply_html(
            update,
            "No leads match those filters. Try <code>/export help</code>.",
            keyboard=back_menu_keyboard(),
        )
        return

    for ef in result.files:
        bio = io.BytesIO(ef.content)
        bio.name = ef.filename
        tier_note = f" · {ef.tier}" if ef.tier else ""
        caption = (
            f"📤 {ef.row_count} leads{tier_note}\n"
            f"Filters: {', '.join(parsed.label_parts())}"
        )
        if parsed.mark_sold:
            caption += f"\n✅ Marked sold{f' → {parsed.buyer}' if parsed.buyer else ''}"
        await update.effective_message.reply_document(
            document=bio,
            caption=caption,
        )


async def _on_atlas_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    settings = _settings(context)
    if not is_owner(update, settings):
        await query.answer("Owner only", show_alert=True)
        return

    await query.answer()
    data = query.data
    parts = data.split(":", 2)

    if data == "atlas:menu":
        await _reply_html(
            update,
            welcome_text(settings),
            keyboard=main_menu_keyboard(),
            edit=True,
        )
        return

    if len(parts) < 2:
        return
    action = parts[1]
    arg = parts[2] if len(parts) > 2 else ""

    if action == "help":
        await _reply_html(update, help_text(settings), keyboard=back_menu_keyboard(), edit=True)
    elif action == "status":
        text = await panel.fetch_status(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "health":
        text = await panel.fetch_health(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "leads":
        text, rows = await panel.fetch_leads_list(settings)
        await _reply_html(update, text, keyboard=leads_keyboard(rows), edit=True)
    elif action == "replies":
        text = await panel.fetch_replies(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "payments":
        text = await panel.fetch_payments(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "delivery":
        text = await panel.fetch_delivery(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "stack":
        text = await panel.fetch_stack(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "export":
        from database.connection import get_session_factory
        from database.repositories.lead_repository import LeadRepository
        from utils.lead_export import export_help_text, inventory_summary_text

        if arg == "help":
            await _reply_html(
                update, export_help_text(), keyboard=back_menu_keyboard(), edit=True
            )
            return
        repo = LeadRepository()
        factory = get_session_factory()
        async with factory() as session:
            counts = await repo.count_by_package_tier(session)
        await _reply_html(
            update,
            inventory_summary_text(counts),
            keyboard=back_menu_keyboard(),
            edit=True,
        )
    elif action == "sync":
        await query.edit_message_text("🔄 Syncing Instantly inbox…")
        text = await panel.run_instantly_sync(settings)
        await _reply_html(update, text, keyboard=back_menu_keyboard(), edit=True)
    elif action == "lead" and arg:
        text = await panel.fetch_lead_detail(settings, arg)
        if not text:
            await query.edit_message_text("Lead not found.")
            return
        lead_id = await panel.resolve_lead_id(arg)
        kb = lead_detail_keyboard(lead_id or arg)
        await _reply_html(update, text, keyboard=kb, edit=True)
    elif action == "draft" and arg:
        await _queue_reply_draft(update, settings, arg)
    elif action == "paylink" and arg:
        await _queue_payment_draft(update, settings, arg)


async def _queue_reply_draft(
    update: Update, settings: Settings, short: str
) -> None:
    from modules.outreach.close_approval import CloseApprovalService

    lead_id = await panel.resolve_lead_id(short)
    if not lead_id:
        await update.callback_query.edit_message_text("Lead not found.")
        return

    svc = CloseApprovalService(settings)
    from database.connection import get_session_factory

    factory = get_session_factory()
    async with factory() as session:
        lead = await svc.repo.get_by_id(session, lead_id)
    if not lead:
        await update.callback_query.edit_message_text("Lead not found.")
        return

    data = lead.enrichment_data or {}
    last = data.get("last_reply") or {}
    draft = await svc.build_close_draft(
        lead,
        str(last.get("classification") or "interested"),
        reply_subject=str(last.get("subject") or lead.pitch_subject or ""),
        reply_body=str(last.get("snippet") or "Interested — following up"),
    )
    queued = await svc.queue_for_approval(
        lead=lead,
        draft=draft,
        classification=str(last.get("classification") or "interested"),
    )
    if not queued.get("ok"):
        await update.callback_query.edit_message_text(
            f"Failed: {queued.get('error', 'unknown')}"
        )
        return
    aid = str(queued.get("approval_id") or "")
    tg = TelegramApprovalNotifier(settings)
    msg_id = await tg.send_approval_request(
        approval_id=aid,
        business_name=lead.business_name,
        email=lead.email or "",
        classification=str(last.get("classification") or "interested"),
        subject=draft["subject"],
        body=draft["body"],
        kind="interested_reply",
    )
    if msg_id:
        await store_telegram_message_id(settings, aid, msg_id)
    await update.callback_query.edit_message_text(
        "✉️ Reply draft sent above — review & tap Approve."
    )


async def _queue_payment_draft(
    update: Update, settings: Settings, short: str
) -> None:
    from modules.outreach.close_approval import CloseApprovalService

    lead_id = await panel.resolve_lead_id(short)
    if not lead_id:
        await update.callback_query.edit_message_text("Lead not found.")
        return

    svc = CloseApprovalService(settings)
    result = await svc.queue_payment_for_approval(lead_id)
    if not result.get("ok"):
        await update.callback_query.edit_message_text(
            f"Could not create payment draft: {result.get('error')}"
        )
        return

    new_id = str(result.get("approval_id") or "")
    payload = result.get("payload") or {}
    lead, approval = await svc.get_pending(new_id)
    if not lead:
        await update.callback_query.edit_message_text("Draft queued but lead missing.")
        return

    tg = TelegramApprovalNotifier(settings)
    body = approval.get("body") if approval else ""
    subj = approval.get("subject") if approval else ""
    msg_id = await tg.send_approval_request(
        approval_id=new_id,
        business_name=lead.business_name,
        email=lead.email or "",
        classification="payment_link",
        subject=subj,
        body=body,
        kind="payment_link",
    )
    if msg_id:
        await store_telegram_message_id(settings, new_id, msg_id)
    await update.callback_query.edit_message_text(
        "💳 Payment-link draft above — approve to send."
    )


def register_handlers(app: Application) -> None:
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("leads", cmd_leads))
    app.add_handler(CommandHandler("replies", cmd_replies))
    app.add_handler(CommandHandler("payments", cmd_payments))
    app.add_handler(CommandHandler("delivery", cmd_delivery))
    app.add_handler(CommandHandler("stack", cmd_stack))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CallbackQueryHandler(_on_atlas_callback, pattern=r"^atlas:"))


async def _post_init(app: Application) -> None:
    settings: Settings = app.bot_data["settings"]
    name = settings.telegram_bot_display_name or "Atlas"
    commands = [
        BotCommand("start", "Open control panel"),
        BotCommand("menu", "Main menu"),
        BotCommand("status", "Pipeline counts"),
        BotCommand("health", "API health check"),
        BotCommand("leads", "Recent leads"),
        BotCommand("replies", "Pending reply drafts"),
        BotCommand("payments", "Pending payment links"),
        BotCommand("delivery", "Delivery queue"),
        BotCommand("stack", "Env configuration"),
        BotCommand("export", "Export lead CSV (tier/geo filters)"),
        BotCommand("help", "All commands"),
    ]
    await app.bot.set_my_commands(commands)
    await app.bot.set_my_description(
        f"{name} — private control panel for Agent-Earns outreach, "
        "approvals, Razorpay payments, and delivery."
    )
    await app.bot.set_my_short_description(
        f"{name} · Agent-Earns owner bot"
    )
