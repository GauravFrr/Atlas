"""Campaign run persistence."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.campaign_run import CampaignRun


class CampaignRepository:
    async def create(
        self,
        session: AsyncSession,
        niche: str,
        city: str,
        leads_requested: int,
        dry_run: bool,
    ) -> CampaignRun:
        run = CampaignRun(
            niche=niche,
            city=city,
            leads_requested=leads_requested,
            dry_run=dry_run,
            status="running",
        )
        session.add(run)
        await session.flush()
        return run

    async def complete(
        self,
        session: AsyncSession,
        run: CampaignRun,
        summary: str,
    ) -> CampaignRun:
        run.status = "completed"
        run.summary = summary
        run.completed_at = datetime.now(timezone.utc)
        await session.flush()
        return run

    async def list_recent(
        self, session: AsyncSession, limit: int = 10
    ) -> list[CampaignRun]:
        result = await session.execute(
            select(CampaignRun).order_by(CampaignRun.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
