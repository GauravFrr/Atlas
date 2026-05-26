"""
Telegram bot — approve reply emails and payment links separately.
Run: python scripts/run_telegram_approvals.py
"""

from __future__ import annotations

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from config import Settings
from modules.outreach.close_approval import CloseApprovalService
from modules.outreach.close_approval_store import register as register_approval_id


def _reply_keyboard(approval_id: str) -> InlineKeyboardMarkup:
    aid = approval_id[:8]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Approve and send reply",
                    callback_data=f"close:approve:{aid}",
                )
            ],
            [
                InlineKeyboardButton(
                    "Recreate draft",
                    callback_data=f"close:recreate:{aid}",
                ),
                InlineKeyboardButton("Skip", callback_data=f"close:skip:{aid}"),
            ],
        ]
    )


def _payment_keyboard(approval_id: str) -> InlineKeyboardMarkup:
    aid = approval_id[:8]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Approve and send payment link",
                    callback_data=f"close:approve:{aid}",
                )
            ],
            [
                InlineKeyboardButton(
                    "Recreate",
                    callback_data=f"close:recreate:{aid}",
                ),
                InlineKeyboardButton("Skip", callback_data=f"close:skip:{aid}"),
            ],
        ]
    )


def _payment_prompt_keyboard(lead_id: str) -> InlineKeyboardMarkup:
    short = lead_id.replace("-", "")[:8]
    register_approval_id(f"lead_{short}", lead_id)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Draft payment link email",
                    callback_data=f"close:paydraft:lead_{short}",
                )
            ],
            [InlineKeyboardButton("Not now", callback_data=f"close:paylater:lead_{short}")],
        ]
    )


def format_approval_message(
    *,
    business_name: str,
    email: str,
    classification: str,
    subject: str,
    body: str,
    kind: str = "interested_reply",
    script_label: str = "",
) -> str:
    preview = body if len(body) <= 1200 else body[:1200] + "\n\n... (truncated)"
    if kind == "payment_link":
        header = "PAYMENT LINK EMAIL — approve to send"
        note = "(Send only after they agreed on scope / call — not with the first reply)"
    else:
        header = "REPLY EMAIL — approve to send"
        note = "(Soft reply only — no payment link yet)"
    return "\n".join(
        [
            header,
            note,
            "━━━━━━━━━━━━━━━━━━",
            f"Lead: {business_name}",
            f"To: {email}",
            f"Class: {classification}",
            *( [f"Script: {script_label}"] if script_label else [] ),
            f"Subject: {subject}",
            "",
            preview,
            "━━━━━━━━━━━━━━━━━━",
        ]
    )


class TelegramApprovalNotifier:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._bot = None
        if settings.has_telegram:
            import telegram

            self._bot = telegram.Bot(token=settings.telegram_bot_token)

    async def send_approval_request(
        self,
        *,
        approval_id: str,
        business_name: str,
        email: str,
        classification: str,
        subject: str,
        body: str,
        kind: str = "interested_reply",
        script_label: str = "",
    ) -> int | None:
        if not self._bot or not self.settings.telegram_chat_id:
            logger.warning("[TelegramApproval] Bot not configured")
            return None
        text = format_approval_message(
            business_name=business_name,
            email=email,
            classification=classification,
            subject=subject,
            body=body,
            kind=kind,
            script_label=script_label,
        )
        kb = (
            _payment_keyboard(approval_id)
            if kind == "payment_link"
            else _reply_keyboard(approval_id)
        )
        msg = await self._bot.send_message(
            chat_id=self.settings.telegram_chat_id,
            text=text,
            reply_markup=kb,
        )
        return msg.message_id

    async def send_payment_link_prompt(
        self, *, lead_id: str, business_name: str, email: str
    ) -> None:
        """After reply is sent — offer to draft payment link as separate email."""
        if not self._bot or not self.settings.telegram_chat_id:
            return
        text = (
            f"Reply sent to {email} ({business_name}).\n\n"
            "When they agree to move forward, draft the payment-link email.\n"
            "Do not send payment with the first reply — it feels pushy."
        )
        await self._bot.send_message(
            chat_id=self.settings.telegram_chat_id,
            text=text,
            reply_markup=_payment_prompt_keyboard(lead_id),
        )


async def store_telegram_message_id(
    settings: Settings, approval_id: str, message_id: int
) -> None:
    from database.connection import get_session_factory
    from database.repositories.lead_repository import LeadRepository
    from modules.outreach.close_approval_store import resolve

    lead_id = resolve(approval_id)
    if not lead_id:
        return
    factory = get_session_factory()
    async with factory() as session:
        lead = await LeadRepository().get_by_id(session, lead_id)
        if not lead:
            return
        data = dict(lead.enrichment_data or {})
        ca = dict(data.get("close_approval") or {})
        ca["telegram_message_id"] = message_id
        data["close_approval"] = ca
        lead.enrichment_data = data
        await session.commit()


def build_application(settings: Settings) -> Application:
    if not settings.has_telegram:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.add_handler(CallbackQueryHandler(_on_callback, pattern=r"^close:"))
    return app


async def _on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    settings: Settings = context.application.bot_data["settings"]
    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    if chat_id != str(settings.telegram_chat_id).strip():
        await query.answer("Unauthorized", show_alert=True)
        return

    parts = query.data.split(":", 2)
    if len(parts) != 3:
        await query.answer("Invalid action")
        return

    _, action, token = parts
    svc = CloseApprovalService(settings)
    tg = TelegramApprovalNotifier(settings)

    await query.answer()

    if action == "paydraft":
        from modules.outreach.close_approval_store import resolve

        lead_id = resolve(token)
        if not lead_id:
            await query.edit_message_text(text="Lead not found.")
            return
        result = await svc.queue_payment_for_approval(lead_id)
        if not result.get("ok"):
            await query.edit_message_text(
                text=f"Could not draft payment email: {result.get('error')}"
            )
            return
        new_id = str(result.get("approval_id") or "")
        draft = (result.get("payload") or {}) if isinstance(result.get("payload"), dict) else {}
        lead, approval = await svc.get_pending(new_id)
        if not lead:
            await query.edit_message_text(text="Draft queued but lead missing.")
            return
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
        await query.edit_message_text(text="Payment-link draft above — review then approve.")
        return

    if action == "paylater":
        await query.edit_message_text(
            text="OK — send payment link later from queue_close_approval or when they confirm."
        )
        return

    approval_id = token
    if action == "approve":
        lead_before, approval = await svc.get_pending(approval_id)
        kind = (approval or {}).get("kind", "interested_reply")
        result = await svc.approve_and_send(approval_id)
        if result.get("ok"):
            if kind == "payment_link":
                await query.edit_message_text(
                    text=(
                        f"Payment link email sent to {result.get('email')}.\n"
                        "Webhook will alert when they pay."
                    )
                )
            else:
                await query.edit_message_text(
                    text=f"Reply sent to {result.get('email')} (no payment link)."
                )
                if result.get("offer_payment_link") and lead_before:
                    await tg.send_payment_link_prompt(
                        lead_id=lead_before.id,
                        business_name=lead_before.business_name,
                        email=lead_before.email or "",
                    )
        else:
            await query.edit_message_text(
                text=(
                    f"Send failed: {result.get('error', 'unknown')}\n"
                    "Check SMTP in .env."
                )
            )

    elif action == "recreate":
        await query.edit_message_text(text="Recreating draft...")
        result = await svc.recreate(approval_id)
        if not result.get("ok"):
            await query.edit_message_text(
                text=f"Recreate failed: {result.get('error', 'unknown')}"
            )
            return
        new_id = str(result.get("approval_id") or "")
        draft = result.get("draft") or {}
        lead, approval = await svc.get_pending(new_id)
        if lead and approval:
            kind = str(approval.get("kind") or draft.get("kind") or "interested_reply")
            msg_id = await tg.send_approval_request(
                approval_id=new_id,
                business_name=lead.business_name,
                email=lead.email or "",
                classification=str(approval.get("classification", "interested")),
                subject=str(draft.get("subject", "")),
                body=str(draft.get("body", "")),
                kind=kind,
            )
            if msg_id:
                await store_telegram_message_id(settings, new_id, msg_id)
        await query.edit_message_text(text="New draft above.")

    elif action == "skip":
        result = await svc.skip(approval_id)
        if result.get("ok"):
            await query.edit_message_text(text="Skipped — no email sent.")
        else:
            await query.edit_message_text(text=f"Skip failed: {result.get('error')}")

    else:
        await query.answer("Unknown action")
