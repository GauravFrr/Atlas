"""Agent task execution log — one row per Atlas tick task."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimestampMixin, UUIDMixin


class AgentLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "agent_logs"

    task_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    method: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    elapsed_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tick_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AgentLog {self.task_name} {self.status} {self.elapsed_ms}ms>"
