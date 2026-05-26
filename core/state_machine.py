"""
State Machine — Agent state management.
States are persisted to DB so they survive restarts.
All transitions are validated — agent can't jump to an invalid state.
"""

import asyncio
import inspect
from datetime import datetime, timezone
from typing import Callable
from loguru import logger

from constants import AgentState
from exceptions import AgentBaseError


# Valid state transitions (from_state -> [allowed_to_states])
VALID_TRANSITIONS: dict[str, list[str]] = {
    AgentState.STARTING: [AgentState.IDLE, AgentState.ERROR, AgentState.SHUTDOWN],
    AgentState.IDLE:     [AgentState.WORKING, AgentState.PAUSED, AgentState.SLEEPING, AgentState.SHUTDOWN],
    AgentState.WORKING:  [AgentState.IDLE, AgentState.PAUSED, AgentState.ERROR, AgentState.SHUTDOWN],
    AgentState.PAUSED:   [AgentState.IDLE, AgentState.SHUTDOWN],
    AgentState.ERROR:    [AgentState.IDLE, AgentState.SHUTDOWN],
    AgentState.SLEEPING: [AgentState.IDLE, AgentState.SHUTDOWN],
    AgentState.SHUTDOWN: [],  # Terminal state
}


class StateMachineError(AgentBaseError):
    """Invalid state transition attempted."""
    def __init__(self, from_state: str, to_state: str):
        super().__init__(
            f"Invalid state transition: {from_state} -> {to_state}",
            {"from": from_state, "to": to_state, "allowed": VALID_TRANSITIONS.get(from_state, [])}
        )


class AgentStateMachine:
    """
    Manages agent state with validation and persistence.
    
    Usage:
        sm = AgentStateMachine()
        await sm.transition_to(AgentState.WORKING)
    """

    def __init__(self):
        self._state = AgentState.STARTING
        self._previous_state: str | None = None
        self._state_entered_at: datetime = datetime.now(timezone.utc)
        self._listeners: list[Callable] = []
        self._state_history: list[dict] = []
        self._lock = asyncio.Lock()

    @property
    def state(self) -> str:
        return self._state

    @property
    def previous_state(self) -> str | None:
        return self._previous_state

    @property
    def is_working(self) -> bool:
        return self._state == AgentState.WORKING

    @property
    def is_paused(self) -> bool:
        return self._state == AgentState.PAUSED

    @property
    def is_operational(self) -> bool:
        """Agent is in a state where it can do work."""
        return self._state in (AgentState.IDLE, AgentState.WORKING, AgentState.SLEEPING)

    @property
    def time_in_current_state(self) -> float:
        """Seconds spent in current state."""
        return (datetime.now(timezone.utc) - self._state_entered_at).total_seconds()

    async def transition_to(self, new_state: str, reason: str = "") -> None:
        """
        Transition to a new state with validation.
        Thread-safe via asyncio lock.
        """
        async with self._lock:
            allowed = VALID_TRANSITIONS.get(self._state, [])
            if new_state not in allowed:
                raise StateMachineError(self._state, new_state)

            old_state = self._state
            self._previous_state = old_state
            self._state = new_state
            self._state_entered_at = datetime.now(timezone.utc)

            # Record history
            self._state_history.append({
                "from": old_state,
                "to": new_state,
                "reason": reason,
                "at": self._state_entered_at.isoformat(),
            })

            logger.info(f"State: {old_state} -> {new_state}" + (f" ({reason})" if reason else ""))

            # Notify listeners
            for listener in self._listeners:
                try:
                    if inspect.iscoroutinefunction(listener):
                        await listener(old_state, new_state)
                    else:
                        listener(old_state, new_state)
                except Exception as e:
                    logger.warning(f"State listener error: {e}")

    def add_listener(self, fn: Callable) -> None:
        """Register a callback that fires on every state transition."""
        self._listeners.append(fn)

    def get_history(self) -> list[dict]:
        """Returns full state transition history."""
        return self._state_history.copy()

    def summary(self) -> dict:
        return {
            "current_state": self._state,
            "previous_state": self._previous_state,
            "time_in_state_seconds": self.time_in_current_state,
            "is_operational": self.is_operational,
            "transition_count": len(self._state_history),
        }
