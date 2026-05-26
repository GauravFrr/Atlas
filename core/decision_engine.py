"""
Decision Engine — Task priority and routing.
Reads current agent state and returns the highest-priority task to execute next.

Priority Rules:
  1 (Immediate): New Fiverr order / payment webhook / client email reply
  2 (Urgent):    Follow-ups due / pending deliverables
  3 (Standard):  New leads to contact / content to publish
  4 (Low):       Hunt for new leads / write content
  5 (Weekly):    Performance analysis / strategy update
"""

from datetime import datetime, timezone
from loguru import logger

from constants import Priority
from config import Settings


class TaskDecision:
    """Represents a task decision from the engine."""
    def __init__(
        self,
        priority: int,
        task_name: str,
        module: str,
        method: str,
        context: dict | None = None,
    ):
        self.priority = priority
        self.task_name = task_name
        self.module = module
        self.method = method
        self.context = context or {}

    def __repr__(self) -> str:
        return f"<Task priority={self.priority} name={self.task_name} module={self.module}>"


class DecisionEngine:
    """
    Decides what the agent should do next based on current state.
    
    Called every agent tick (every 30 minutes).
    Returns the highest-priority pending task.
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    async def decide(self, agent_state: dict) -> TaskDecision | None:
        """
        Evaluate current state and return the next task.
        
        agent_state contains:
            - pending_orders: list of undelivered orders
            - unread_replies: list of email replies to handle
            - leads_due_for_followup: leads in sequence that need follow-up
            - emails_sent_today: count of emails sent today
            - new_fiverr_orders: new orders detected
            - content_scheduled: content queued for publishing
            - is_sunday: True if today is Sunday (triggers weekly review)
        """
        now = datetime.now(timezone.utc)
        hour_ist = (now.hour + 5) % 24 + (1 if now.minute >= 30 else 0)  # Approximate IST

        # ── PRIORITY 1: Immediate ──────────────────────────────────────
        if agent_state.get("new_fiverr_orders"):
            order = agent_state["new_fiverr_orders"][0]
            logger.info(f"P1: New Fiverr order detected: {order.get('id', 'unknown')}")
            return TaskDecision(
                priority=Priority.IMMEDIATE,
                task_name="handle_fiverr_order",
                module="modules.service_delivery.manager",
                method="handle_new_order",
                context={"order": order},
            )

        if agent_state.get("payment_webhooks_pending"):
            webhook = agent_state["payment_webhooks_pending"][0]
            logger.info("P1: Pending payment webhook to process")
            return TaskDecision(
                priority=Priority.IMMEDIATE,
                task_name="process_payment_webhook",
                module="modules.payment_handler.manager",
                method="process_webhook",
                context={"webhook": webhook},
            )

        if agent_state.get("unread_replies"):
            reply = agent_state["unread_replies"][0]
            logger.info(f"P1: Client reply from {reply.get('from', 'unknown')}")
            return TaskDecision(
                priority=Priority.IMMEDIATE,
                task_name="handle_email_reply",
                module="modules.outreach.manager",
                method="handle_reply",
                context={"reply": reply},
            )

        # ── PRIORITY 2: Urgent ─────────────────────────────────────────
        if agent_state.get("pending_deliverables"):
            order = agent_state["pending_deliverables"][0]
            logger.info(f"P2: Pending deliverable for order {order.get('id')}")
            return TaskDecision(
                priority=Priority.URGENT,
                task_name="complete_deliverable",
                module="modules.service_delivery.manager",
                method="complete_order",
                context={"order": order},
            )

        if agent_state.get("followups_due"):
            leads = agent_state["followups_due"][:5]  # Process up to 5 at once
            logger.info(f"P2: {len(leads)} follow-ups due")
            return TaskDecision(
                priority=Priority.URGENT,
                task_name="send_followups",
                module="modules.outreach.manager",
                method="send_followups",
                context={"leads": leads},
            )

        # ── PRIORITY 3: Autopilot — hunt leads + send (24/7, no human) ──
        emails_sent = agent_state.get("emails_sent_today", 0)
        if emails_sent < self.settings.max_emails_per_day:
            logger.info(
                f"P3: Autopilot hunt+send ({emails_sent}/{self.settings.max_emails_per_day} today)"
            )
            return TaskDecision(
                priority=Priority.STANDARD,
                task_name="autopilot_outreach",
                module="core.autopilot",
                method="run_once",
                context={},
            )

        if agent_state.get("content_scheduled") and 8 <= hour_ist <= 10:
            logger.info("P3: Publishing scheduled content")
            return TaskDecision(
                priority=Priority.STANDARD,
                task_name="publish_content",
                module="modules.content_writer.manager",
                method="publish_scheduled",
                context={},
            )

        # ── PRIORITY 4: Low — autopilot if outside business hours still check queue ──
        if emails_sent < self.settings.max_emails_per_day:
            return TaskDecision(
                priority=Priority.LOW,
                task_name="autopilot_outreach",
                module="core.autopilot",
                method="run_once",
                context={},
            )

        return None

    def get_daily_targets(self) -> dict:
        """Returns the target metrics for today."""
        return {
            "emails_to_send": min(50, self.settings.max_emails_per_day),
            "leads_to_find": 100,
            "content_pieces": 1,
            "orders_to_complete": "all_pending",
        }
