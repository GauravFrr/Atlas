"""
Master Agent Class — Atlas.
Manages lifecycle (startup/run/shutdown), registers all modules,
handles global exceptions, and coordinates all subsystems.
"""

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from loguru import logger

from config import Settings
from constants import AgentState
from exceptions import AgentBaseError

# TYPE_CHECKING guard — imports used ONLY for type hints, not at runtime.
# This prevents circular imports while still giving Pylance full type info.
if TYPE_CHECKING:
    from core.state_machine import AgentStateMachine
    from core.decision_engine import DecisionEngine, TaskDecision
    from core.memory_manager import MemoryManager
    from core.constitution import AgentConstitution
    from core.loop import AgentLoop
    from llm.router import LLMRouter
    from utils.notifier import Notifier


class Agent:
    """
    Atlas — The Autonomous AI Earning Agent.

    This is the central coordinator. It does NOT do the work itself —
    it delegates to specialized modules via the decision engine + loop.

    Usage:
        agent = Agent(settings=get_settings())
        await agent.run()           # Runs forever
        await agent.tick()          # Single cycle (for testing)
    """

    def __init__(self, settings: Settings, dry_run: bool = False) -> None:
        self.settings = settings
        self.dry_run = dry_run
        self.started_at: Optional[datetime] = None

        # Core subsystems — None until startup() is called.
        # Typed via TYPE_CHECKING imports above so Pylance resolves all methods.
        self.state_machine: Optional["AgentStateMachine"] = None
        self.decision_engine: Optional["DecisionEngine"] = None
        self.memory_manager: Optional["MemoryManager"] = None
        self.constitution: Optional["AgentConstitution"] = None
        self.llm_router: Optional["LLMRouter"] = None
        self.notifier: Optional["Notifier"] = None
        self.loop: Optional["AgentLoop"] = None

    async def startup(self) -> None:
        """Initialize all subsystems in correct dependency order."""
        logger.info("Initializing agent subsystems...")
        self.started_at = datetime.now(timezone.utc)

        # 1. Constitution first (defines what we are allowed to do)
        from core.constitution import AgentConstitution
        self.constitution = AgentConstitution()
        logger.info("Constitution loaded")

        # 2. State machine
        from core.state_machine import AgentStateMachine
        self.state_machine = AgentStateMachine()
        logger.info("State machine initialized")

        # 3. Notifier (needed early so all subsequent errors can alert the human)
        from utils.notifier import Notifier
        self.notifier = Notifier(settings=self.settings)
        logger.info("Notifier ready")

        # 4. LLM Router
        from llm.router import LLMRouter
        self.llm_router = LLMRouter(settings=self.settings)
        logger.info("LLM router ready")

        # 5. Decision Engine
        from core.decision_engine import DecisionEngine
        self.decision_engine = DecisionEngine(settings=self.settings)
        logger.info("Decision engine ready")

        # 6. Memory Manager (DB session injected later when DB is built)
        from core.memory_manager import MemoryManager
        self.memory_manager = MemoryManager(db_session_factory=None)
        logger.info("Memory manager ready")

        # 7. Main Loop
        from core.loop import AgentLoop
        self.loop = AgentLoop(agent=self)
        logger.info("Agent loop ready")

        # Transition from STARTING → IDLE
        await self.state_machine.transition_to(AgentState.IDLE, "startup_complete")

        if self.dry_run:
            logger.warning("DRY RUN MODE: No emails sent, no payments processed")

        # Notify human that Atlas is live
        await self.notifier.send_info(
            f"Atlas started successfully\n"
            f"Environment: {self.settings.agent_env}\n"
            f"Dry run: {self.dry_run}\n"
            f"Features enabled: {sum(self.settings.get_enabled_features().values())}"
        )

        logger.success("All subsystems initialized. Atlas is operational.")

    async def run(self) -> None:
        """
        Main run method — starts agent and runs the 30-min tick loop forever.
        Called from main.py alongside the dashboard server.
        """
        await self.startup()
        assert self.loop is not None, "Loop not initialized after startup"
        await self.loop.run()

    async def tick(self, dry_run: bool = False) -> dict:
        """
        Run a single agent tick (for testing / one-shot runs).
        Auto-initializes if startup() hasn't been called yet.
        """
        if self.state_machine is None:
            await self.startup()

        assert self.decision_engine is not None, "Decision engine not initialized"

        logger.info("Running single test tick (blueprint loop)...")
        assert self.loop is not None
        await self.loop._run_tick()
        return {"task": "tick_complete", "dry_run": dry_run}

    async def build_current_state(self) -> dict:
        """
        Assembles the current agent state snapshot for the decision engine.
        Blueprint: unread replies, follow-ups due, pipeline counts from DB.
        """
        now_utc = datetime.now(timezone.utc)
        state: dict = {
            "timestamp": now_utc.isoformat(),
            "new_fiverr_orders": [],
            "payment_webhooks_pending": [],
            "unread_replies": [],
            "pending_deliverables": [],
            "followups_due": [],
            "leads_ready_for_outreach": [],
            "leads_due_for_followup": [],
            "emails_sent_today": 0,
            "uncontacted_leads_count": 0,
            "content_scheduled": [],
            "is_sunday": now_utc.weekday() == 6,
        }

        try:
            from database.connection import get_session_factory
            from database.repositories.lead_repository import LeadRepository

            repo = LeadRepository()
            factory = get_session_factory()
            async with factory() as session:
                state["emails_sent_today"] = await repo.count_emails_sent_today(session)
                state["unread_replies"] = await repo.list_unread_replies(session, limit=10)
                due = await repo.list_followups_due(session, limit=10)
                state["followups_due"] = [
                    {
                        "lead_id": lead.id,
                        "email": lead.email,
                        "business_name": lead.business_name,
                        "sequence_step": lead.sequence_step,
                        "send_channel": (lead.enrichment_data or {}).get("send_channel"),
                    }
                    for lead in due
                ]
                state["leads_due_for_followup"] = state["followups_due"]
                state["uncontacted_leads_count"] = await repo.count_uncontacted_with_email(
                    session
                )

                from database.repositories.payment_repository import PaymentRepository

                pay_repo = PaymentRepository()
                state["payment_webhooks_pending"] = await pay_repo.list_webhook_pending(
                    session, limit=5
                )
        except Exception as e:
            logger.warning(f"[State] DB snapshot partial: {e}")

        return state

    async def log_task_result(
        self,
        task: "TaskDecision",
        result: dict,
        elapsed_ms: int,
        success: bool,
        error: str = "",
        *,
        tick_number: int | None = None,
    ) -> None:
        """Persists task execution result to agent_logs table."""
        status = "success" if success else "failed"
        logger.debug(
            f"Task log: {task.task_name} | {status} | {elapsed_ms}ms"
            + (f" | Error: {error}" if error else "")
        )
        try:
            from database.connection import get_session_factory
            from database.repositories.agent_log_repository import AgentLogRepository

            factory = get_session_factory()
            async with factory() as session:
                await AgentLogRepository().create(
                    session,
                    task_name=task.task_name,
                    module=task.module,
                    method=task.method,
                    priority=task.priority,
                    status=status,
                    elapsed_ms=elapsed_ms,
                    error_message=error,
                    result=result if isinstance(result, dict) else {},
                    tick_number=tick_number,
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"[AgentLog] Could not persist task log: {e}")

    async def pause(self) -> None:
        """Pause the agent loop (initiated by human via dashboard)."""
        assert self.state_machine is not None and self.notifier is not None
        logger.warning("Agent paused by human")
        await self.state_machine.transition_to(AgentState.PAUSED, "human_pause")
        await self.notifier.send_info("Agent paused via dashboard")

    async def resume(self) -> None:
        """Resume agent from paused state."""
        assert self.state_machine is not None
        logger.info("Agent resumed by human")
        await self.state_machine.transition_to(AgentState.IDLE, "human_resume")

    async def shutdown(self) -> None:
        """Graceful shutdown — finishes current task then stops cleanly."""
        logger.info("Shutdown initiated")
        if self.loop is not None:
            self.loop.stop()
        if self.state_machine is not None:
            await self.state_machine.transition_to(AgentState.SHUTDOWN, "graceful_shutdown")
        if self.notifier is not None:
            await self.notifier.send_info("Atlas shutting down gracefully")
        logger.info("Atlas shutdown complete")

    def get_status(self) -> dict:
        """Returns current agent status dict for the dashboard API."""
        return {
            "name": self.settings.agent_name,
            "state": (
                self.state_machine.state
                if self.state_machine is not None
                else AgentState.STARTING
            ),
            "uptime_seconds": (
                (datetime.now(timezone.utc) - self.started_at).total_seconds()
                if self.started_at is not None
                else 0
            ),
            "tick_count": self.loop.tick_count if self.loop is not None else 0,
            "dry_run": self.dry_run,
            "features": self.settings.get_enabled_features(),
        }
