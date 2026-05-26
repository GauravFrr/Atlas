"""
Lead ORM Model — Full schema for discovered leads.
Maps directly to the 'leads' table in SQLite.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from constants import LeadStatus


class Lead(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    # Source
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    place_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    campaign_run_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    # Lead info
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    niche: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    # Intelligence
    problem_detected: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    score_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    enrichment_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    demo_site_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pitch_subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pitch_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), default=LeadStatus.NEW, nullable=False, index=True
    )
    last_contacted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_followup: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    sequence_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<Lead id={self.id[:8]} name={self.business_name} score={self.score} status={self.status}>"

    @property
    def is_hot(self) -> bool:
        from constants import LEAD_SCORE_HOT
        return self.score >= LEAD_SCORE_HOT

    @property
    def is_contactable(self) -> bool:
        return self.status == LeadStatus.NEW and bool(self.email)
