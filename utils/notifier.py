"""
Notifier — Dispatches alerts via Telegram (primary) and logs.
Priority levels: INFO | WARN | URGENT
"""

import asyncio
from loguru import logger
from config import Settings
from constants import NotifyPriority


class Notifier:
    """
    Sends notifications to the human operator via Telegram.
    Falls back to logging if Telegram is not configured.
    
    Usage:
        notifier = Notifier(settings)
        await notifier.send_urgent("New order received!")
        await notifier.send_info("Daily summary: 23 emails sent")
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._telegram_bot = None
        self._chat_id = settings.telegram_chat_id

        if settings.has_telegram:
            try:
                self._init_telegram()
            except Exception as e:
                logger.warning(f"Telegram init failed: {e}. Alerts will be logged only.")

    def _init_telegram(self) -> None:
        """Initialize Telegram bot."""
        import telegram
        self._telegram_bot = telegram.Bot(token=self.settings.telegram_bot_token)
        logger.info("Telegram bot initialized")

    async def send_urgent(self, message: str) -> None:
        """Send urgent alert (red). Human MUST see this."""
        formatted = f"🔴 URGENT ALERT\n━━━━━━━━━━━━━━━━━━\n{message}\n━━━━━━━━━━━━━━━━━━"
        logger.critical(f"URGENT: {message}")
        await self._send(formatted)

    async def send_warn(self, message: str) -> None:
        """Send warning notification (yellow)."""
        formatted = f"🟡 WARNING\n{message}"
        logger.warning(f"WARN: {message}")
        await self._send(formatted)

    async def send_info(self, message: str) -> None:
        """Send informational notification (green)."""
        formatted = f"🟢 {message}"
        logger.info(f"NOTIFY: {message}")
        await self._send(formatted)

    async def send_payment_received(self, amount: str, client: str, method: str) -> None:
        """Notify of a payment received."""
        msg = (
            f"💰 PAYMENT RECEIVED\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Amount: {amount}\n"
            f"Client: {client}\n"
            f"Method: {method}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Agent starting work now."
        )
        await self.send_urgent(msg)

    async def send_new_order(self, order_id: str, service: str, budget: str) -> None:
        """Notify of a new Fiverr order."""
        msg = (
            f"New Fiverr Order Received\n"
            f"Order #: {order_id}\n"
            f"Service: {service}\n"
            f"Budget: {budget}\n\n"
            f"Review in dashboard."
        )
        await self.send_urgent(msg)

    async def send_hot_reply(self, sender: str, subject: str, snippet: str) -> None:
        """Notify of a positive email reply."""
        msg = (
            f"🔥 HOT REPLY\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"From: {sender}\n"
            f"Subject: {subject}\n\n"
            f'"{snippet[:200]}"\n\n'
            f"Draft reply ready for review."
        )
        await self.send_urgent(msg)

    async def send_daily_summary(self, stats: dict) -> None:
        """Send the daily 9PM summary."""
        msg = (
            f"📊 DAILY SUMMARY\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Leads found: {stats.get('leads_found', 0)}\n"
            f"Emails sent: {stats.get('emails_sent', 0)} (limit: {self.settings.max_emails_per_day})\n"
            f"Open rate: {stats.get('open_rate', 0):.1f}%\n"
            f"Replies: {stats.get('replies', 0)}\n"
            f"Orders delivered: {stats.get('orders_delivered', 0)}\n"
            f"Revenue today: {stats.get('revenue_today', '₹0')}\n"
            f"Month total: {stats.get('month_total', '₹0')}\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        await self.send_info(msg)

    async def _send(self, message: str) -> None:
        """Internal: dispatches the message to Telegram."""
        if self._telegram_bot and self._chat_id:
            try:
                await self._telegram_bot.send_message(
                    chat_id=self._chat_id,
                    text=message,
                    parse_mode=None,  # Plain text (no markdown parsing issues)
                )
                return
            except Exception as e:
                logger.warning(f"Telegram send failed: {e}")

        # Fallback: just log it (notification won't reach phone, but at least logged)
        logger.info(f"[NOTIFICATION - not sent to Telegram] {message}")
