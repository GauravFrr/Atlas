"""Persist Atlas task results for dashboard and debugging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.agent_log import AgentLog


class AgentLogRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        task_name: str,
        module: str,
        method: str,
        priority: int,
        status: str,
        elapsed_ms: int,
        error_message: str = "",
        result: dict[str, Any] | None = None,
        tick_number: int | None = None,
    ) -> AgentLog:
        row = AgentLog(
            task_name=task_name[:120],
            module=module[:200],
            method=method[:120],
            priority=priority,
            status=status[:20],
            elapsed_ms=elapsed_ms,
            error_message=(error_message or "")[:4000] or None,
            result_json=json.dumps(result or {}, default=str)[:8000]
            if result
            else None,
            tick_number=tick_number,
            finished_at=datetime.now(timezone.utc),
        )
        session.add(row)
        await session.flush()
        return row

    async def list_recent(
        self, session: AsyncSession, *, limit: int = 50
    ) -> list[AgentLog]:
        from sqlalchemy import select

        result = await session.execute(
            select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
