"""
CampaignRun ORM Model — One row per orchestrated campaign execution.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, UUIDMixin, TimestampMixin


class CampaignRun(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaign_runs"

    niche: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    leads_requested: Mapped[int] = mapped_column(Integer, nullable=False)
    leads_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    demos_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails_drafted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    emails_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    no_email_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CampaignRun id={self.id[:8]} niche={self.niche} "
            f"city={self.city} processed={self.leads_processed}>"
        )
