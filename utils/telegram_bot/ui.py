"""HTML messages and inline keyboards for Atlas Telegram bot."""

from __future__ import annotations

from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import Settings
from constants import AGENT_DEFAULT_NAME, APP_NAME


def esc(text: object) -> str:
    return escape(str(text or ""))


def bot_title(settings: Settings) -> str:
    name = (
        getattr(settings, "telegram_bot_display_name", None)
        or AGENT_DEFAULT_NAME
    )
    return str(name).strip() or AGENT_DEFAULT_NAME


def header_block(settings: Settings, subtitle: str = "") -> str:
    biz = (settings.your_business_name or settings.your_name or "Operator").strip()
    lines = [
        f"<b>🤖 {esc(bot_title(settings))}</b>",
        f"<i>{esc(APP_NAME)} · {esc(biz)}</i>",
    ]
    if subtitle:
        lines.append(f"<code>{esc(subtitle)}</code>")
    lines.append("━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Status", callback_data="atlas:status"),
                InlineKeyboardButton("❤️ Health", callback_data="atlas:health"),
            ],
            [
                InlineKeyboardButton("📋 Leads", callback_data="atlas:leads"),
                InlineKeyboardButton("💬 Replies", callback_data="atlas:replies"),
            ],
            [
                InlineKeyboardButton("💰 Payments", callback_data="atlas:payments"),
                InlineKeyboardButton("📦 Delivery", callback_data="atlas:delivery"),
            ],
            [
                InlineKeyboardButton("🔄 Sync Instantly", callback_data="atlas:sync"),
                InlineKeyboardButton("⚙️ Stack", callback_data="atlas:stack"),
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="atlas:help"),
                InlineKeyboardButton("🏠 Menu", callback_data="atlas:menu"),
            ],
        ]
    )


def back_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🏠 Main menu", callback_data="atlas:menu")]]
    )


def leads_keyboard(lead_rows: list[tuple[str, str, str]]) -> InlineKeyboardMarkup:
    """Rows of (short_id, label, status)."""
    buttons: list[list[InlineKeyboardButton]] = []
    for short_id, label, _status in lead_rows[:8]:
        buttons.append(
            [
                InlineKeyboardButton(
                    label[:60],
                    callback_data=f"atlas:lead:{short_id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton("🏠 Menu", callback_data="atlas:menu")])
    return InlineKeyboardMarkup(buttons)


def lead_detail_keyboard(lead_id: str) -> InlineKeyboardMarkup:
    short = lead_id.replace("-", "")[:8]
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✉️ Draft reply",
                    callback_data=f"atlas:draft:{short}",
                ),
                InlineKeyboardButton(
                    "💳 Payment link",
                    callback_data=f"atlas:paylink:{short}",
                ),
            ],
            [
                InlineKeyboardButton("📋 All leads", callback_data="atlas:leads"),
                InlineKeyboardButton("🏠 Menu", callback_data="atlas:menu"),
            ],
        ]
    )


def welcome_text(settings: Settings) -> str:
    return "\n".join(
        [
            header_block(settings, "Owner control panel"),
            "",
            "Cold outreach · approvals · payments · delivery",
            "",
            "Use the buttons below or commands:",
            "/menu · /status · /health · /leads · /help",
            "",
            "<i>Only you can use this bot.</i>",
        ]
    )


def help_text(settings: Settings) -> str:
    return "\n".join(
        [
            header_block(settings, "Commands"),
            "",
            "<b>Panel</b>",
            "/start /menu — Main menu",
            "/status — Leads & pipeline counts",
            "/health — API + DB checks",
            "/leads — Recent leads (tap to act)",
            "/replies — Needs close draft",
            "/payments — Pending Razorpay links",
            "/delivery — Paid, not delivered",
            "/stack — What's configured in .env",
            "",
            "<b>Approvals</b>",
            "Reply & payment emails arrive here with",
            "✅ Approve · 🔄 Recreate · ⏭ Skip",
            "",
            "<b>After a real pay</b>",
            "Razorpay webhook → PAID checklist",
        ]
    )
