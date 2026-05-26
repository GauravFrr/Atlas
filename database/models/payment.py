"""Payment ORM — Razorpay links and confirmation status."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from constants import PaymentProvider, PaymentStatus
from database.base import Base, TimestampMixin, UUIDMixin


class Payment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "payments"

    lead_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(
        String(32), default=PaymentProvider.RAZORPAY, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=PaymentStatus.PENDING, nullable=False, index=True
    )
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    razorpay_payment_link_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    short_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    notes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    webhook_pending: Mapped[bool] = mapped_column(default=False, nullable=False)
    webhook_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
