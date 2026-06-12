"""
Master Agent Loop — The heartbeat of Atlas.
Runs every 30 minutes, calls decision engine, executes selected task.
Handles errors gracefully and keeps running no matter what.
"""

import asyncio
import importlib
from datetime import datetime, timezone
from loguru import logger

from constants import AgentState, SCHEDULER_TIMEZONE
from exceptions import AgentBaseError, ConstitutionViolationError
from config import Settings


def _tick_interval_seconds(settings: Settings) -> int:
    """Blueprint: MAIN LOOP every 30 mins (configurable)."""
    minutes = int(getattr(settings, "agent_loop_interval_minutes", 30) or 30)
    return max(5, minutes) * 60


class AgentLoop:
    """
    The main execution loop for Atlas.
    
    Each 'tick' represents one cycle:
    1. Read current state from DB
    2. Ask decision engine for next task
    3. Execute the task
    4. Log results
    5. Sleep until next tick
    """

    def __init__(self, agent):
        self._agent = agent
        self._running = False
        self._tick_count = 0
        self._errors_this_session = 0
        self.settings: Settings = agent.settings

    async def run(self) -> None:
        """Starts the main loop. Runs forever until shutdown signal."""
        self._running = True
        interval = _tick_interval_seconds(self.settings)
        logger.info(f"Main loop started. Tick interval: {interval // 60} minutes")

        while self._running:
            tick_start = datetime.now(timezone.utc)
            self._tick_count += 1

            logger.info(f"─── Tick #{self._tick_count} | {tick_start.strftime('%Y-%m-%d %H:%M UTC')} ───")

            try:
                await self._run_tick()
            except ConstitutionViolationError as e:
                # Constitution violations are FATAL — alert and stop
                logger.critical(f"CONSTITUTION VIOLATION: {e}")
                await self._agent.notifier.send_urgent(
                    f"CONSTITUTION VIOLATION DETECTED\n{e}\nAgent stopping immediately."
                )
                self._running = False
                break
            except Exception as e:
                self._errors_this_session += 1
                logger.exception(f"Tick error (#{self._errors_this_session}): {e}")

                if self._errors_this_session >= 5:
                    await self._agent.notifier.send_urgent(
                        f"Agent has errored {self._errors_this_session} times this session.\n"
                        f"Last error: {e}\nPlease check the logs."
                    )
                    # Reset error count after alerting
                    self._errors_this_session = 0

            # Calculate sleep time (accounting for tick execution time)
            elapsed = (datetime.now(timezone.utc) - tick_start).total_seconds()
            sleep_time = max(60, _tick_interval_seconds(self.settings) - elapsed)

            logger.info(f"Tick #{self._tick_count} complete in {elapsed:.1f}s. Next tick in {sleep_time/60:.1f}m")
            await asyncio.sleep(sleep_time)

    async def _run_tick(self) -> None:
        """Execute one tick of the agent loop (ULTIMATE_AGENT_BLUEPRINT_V3)."""
        # Pre-tick: reply sync + finish incomplete leads (P2 + pipeline in DB)
        if self.settings.has_instantly:
            try:
                from modules.outreach.reply_sync import sync_instantly_replies

                await sync_instantly_replies(self.settings)
            except Exception as e:
                logger.warning(f"[Tick] Reply sync: {e}")

        # Resume + hunt order lives in core.autopilot.run_once (avoid running resume twice).

        # 1. Read current agent state
        agent_state = await self._agent.build_current_state()

        # 2. Ask decision engine what to do next
        task = await self._agent.decision_engine.decide(agent_state)

        if task is None:
            logger.info("No tasks needed. Sleeping...")
            await self._agent.state_machine.transition_to(AgentState.SLEEPING, "no_tasks")
            return

        logger.info(f"Selected task: {task.task_name} (priority={task.priority})")

        # 3. Mark as working
        await self._agent.state_machine.transition_to(AgentState.WORKING, task.task_name)

        # 4. Execute the task
        start = datetime.now(timezone.utc)
        try:
            result = await self._execute_task(task)
            elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            logger.success(f"Task '{task.task_name}' completed in {elapsed_ms}ms")

            # 5. Log to DB
            await self._agent.log_task_result(
                task, result, elapsed_ms, success=True, tick_number=self._tick_count
            )

        except AgentBaseError as e:
            elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            logger.error(f"Task '{task.task_name}' failed: {e}")
            await self._agent.log_task_result(
                task,
                {},
                elapsed_ms,
                success=False,
                error=str(e),
                tick_number=self._tick_count,
            )
            raise

        # 6. Return to idle
        await self._agent.state_machine.transition_to(AgentState.IDLE, "task_complete")

    async def _execute_task(self, task) -> dict:
        """
        Dynamically loads and executes a task module.
        Example: module="modules.lead_finder.manager" method="run_all_sources"
        """
        try:
            mod = importlib.import_module(task.module)
            manager_class = getattr(mod, "Manager", None)

            if manager_class:
                manager = manager_class(
                    settings=self.settings,
                    llm_router=self._agent.llm_router,
                )
                method = getattr(manager, task.method)
                return await method(**task.context)
            else:
                fn = getattr(mod, task.method)
                if task.module == "core.autopilot":
                    return await fn(settings=self.settings)
                return await fn(**task.context)

        except ImportError as e:
            logger.warning(f"Module not yet implemented: {task.module} ({e})")
            return {"status": "skipped", "reason": "module_not_implemented"}

    def stop(self) -> None:
        """Signals the loop to stop after current tick completes."""
        logger.info("Stop signal received. Will stop after current tick.")
        self._running = False

    @property
    def tick_count(self) -> int:
        return self._tick_count
