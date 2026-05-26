"""Payment repository — Razorpay links and webhook queue."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import PaymentStatus
from database.models.payment import Payment


class PaymentRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        lead_id: str | None,
        amount_paise: int,
        description: str,
        customer_email: str | None,
        customer_name: str | None,
        razorpay_payment_link_id: str,
        short_url: str,
        reference_id: str | None = None,
        notes: dict | None = None,
    ) -> Payment:
        row = Payment(
            lead_id=lead_id,
            amount_paise=amount_paise,
            description=description,
            customer_email=customer_email,
            customer_name=customer_name,
            razorpay_payment_link_id=razorpay_payment_link_id,
            short_url=short_url,
            reference_id=reference_id or lead_id,
            notes=notes or {},
            status=PaymentStatus.PENDING,
        )
        session.add(row)
        await session.flush()
        return row

    async def get_by_id(
        self, session: AsyncSession, payment_id: str
    ) -> Optional[Payment]:
        result = await session.execute(
            select(Payment).where(Payment.id == payment_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_link_id(
        self, session: AsyncSession, link_id: str
    ) -> Optional[Payment]:
        result = await session.execute(
            select(Payment).where(Payment.razorpay_payment_link_id == link_id).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_lead(
        self, session: AsyncSession, lead_id: str, *, pending_only: bool = False
    ) -> Optional[Payment]:
        q = select(Payment).where(Payment.lead_id == lead_id)
        if pending_only:
            q = q.where(Payment.status == PaymentStatus.PENDING)
        result = await session.execute(q.order_by(Payment.created_at.desc()).limit(1))
        return result.scalar_one_or_none()

    async def list_webhook_pending(
        self, session: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(Payment)
            .where(Payment.webhook_pending.is_(True))
            .order_by(Payment.updated_at.asc())
            .limit(limit)
        )
        return [
            {
                "payment_id": p.id,
                "lead_id": p.lead_id,
                "razorpay_payment_link_id": p.razorpay_payment_link_id,
                "payload": p.webhook_payload or {},
            }
            for p in result.scalars()
        ]

    async def queue_webhook(
        self,
        session: AsyncSession,
        payment: Payment,
        payload: dict[str, Any],
    ) -> Payment:
        payment.webhook_pending = True
        payment.webhook_payload = payload
        await session.flush()
        return payment

    async def confirm(
        self,
        session: AsyncSession,
        payment: Payment,
        *,
        razorpay_payment_id: str | None = None,
        payload: dict | None = None,
    ) -> Payment:
        payment.status = PaymentStatus.CONFIRMED
        payment.webhook_pending = False
        payment.confirmed_at = datetime.now(timezone.utc)
        if razorpay_payment_id:
            payment.razorpay_payment_id = razorpay_payment_id
        if payload:
            payment.webhook_payload = payload
        await session.flush()
        return payment
