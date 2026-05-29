"""Owner-only access for Atlas Telegram bot."""

from __future__ import annotations

from telegram import Update

from config import Settings


def owner_user_ids(settings: Settings) -> set[str]:
    """Telegram user IDs allowed to use the bot (private chat user id)."""
    ids: set[str] = set()
    chat = str(settings.telegram_chat_id or "").strip()
    if chat:
        ids.add(chat)
    raw = str(getattr(settings, "telegram_owner_user_ids", "") or "").strip()
    for part in raw.replace(";", ",").split(","):
        p = part.strip()
        if p:
            ids.add(p)
    return ids


def is_owner(update: Update, settings: Settings) -> bool:
    if not settings.has_telegram:
        return False
    allowed = owner_user_ids(settings)
    if not allowed:
        return False

    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    user_id = str(update.effective_user.id) if update.effective_user else ""

    # Private chat: chat_id often equals user_id; group: must match configured chat
    if chat_id in allowed:
        return True
    if user_id in allowed:
        return True
    return False


async def reject_non_owner(update: Update, settings: Settings) -> bool:
    """Return True if request was rejected (caller should stop)."""
    if is_owner(update, settings):
        return False
    msg = update.effective_message
    if msg:
        await msg.reply_text(
            "⛔ <b>Owner only</b>\nThis bot is private to the Atlas operator.",
            parse_mode="HTML",
        )
    elif update.callback_query:
        await update.callback_query.answer("Owner only", show_alert=True)
    return True
