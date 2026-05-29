"""Atlas Telegram bot — owner control panel + close-email approvals."""

from __future__ import annotations

__all__ = ["build_application"]


def build_application(settings):
    """Lazy import avoids circular dependency with utils.telegram_approval."""
    from utils.telegram_bot.app import build_application as _build

    return _build(settings)
