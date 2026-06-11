"""
Lead Repository — Memory bank for campaign deduplication and lead persistence.
Ensures the agent never processes or emails the same business twice.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from loguru import logger
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import LeadSource, LeadStatus
from database.models.lead import Lead
from modules.lead_finder.scanners.google_maps import MapsScanResult


def _normalize_key(text: str) -> str:
    """Lowercase alphanumeric key for fuzzy business matching."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())


class LeadRepository:
    """All lead read/write operations for the memory bank."""

    async def is_already_known(
        self,
        session: AsyncSession,
        place_id: str | None,
        business_name: str,
        city: str,
        email: str | None = None,
    ) -> bool:
        """
        Returns True if this business was ever seen before (any campaign).
        Checks place_id, email, then normalized name + city.
        Includes soft-deleted rows (e.g. discarded no-email) so we do not re-burn quota.
        """
        if place_id:
            result = await session.execute(
                select(Lead.id).where(Lead.place_id == place_id).limit(1)
            )
            if result.scalar_one_or_none():
                return True

        if email:
            existing = await self.get_by_email(session, email)
            if existing:
                return True

        name_key = _normalize_key(business_name)
        city_key = _normalize_key(city)
        if not name_key:
            return False

        result = await session.execute(
            select(Lead).where(Lead.is_deleted.is_(False))
        )
        for lead in result.scalars():
            if (
                _normalize_key(lead.business_name) == name_key
                and _normalize_key(lead.location or "") == city_key
            ):
                return True
        return False

    async def was_emailed(
        self,
        session: AsyncSession,
        place_id: str | None,
        email: str | None,
    ) -> bool:
        """True if we already sent (or attempted) outreach to this lead."""
        contacted_statuses = {
            LeadStatus.CONTACTED,
            LeadStatus.REPLIED,
            LeadStatus.CLIENT,
        }

        if email:
            result = await session.execute(
                select(Lead).where(
                    Lead.email == email,
                    Lead.status.in_(contacted_statuses),
                    Lead.is_deleted.is_(False),
                ).limit(1)
            )
            if result.scalar_one_or_none():
                return True

        if place_id:
            result = await session.execute(
                select(Lead).where(
                    Lead.place_id == place_id,
                    Lead.status.in_(contacted_statuses),
                    Lead.is_deleted.is_(False),
                ).limit(1)
            )
            if result.scalar_one_or_none():
                return True

        return False

    async def count_emails_sent_today(self, session: AsyncSession) -> int:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await session.execute(
            select(func.count(Lead.id)).where(
                Lead.status == LeadStatus.CONTACTED,
                Lead.last_contacted >= today_start,
                Lead.is_deleted.is_(False),
            )
        )
        return result.scalar_one() or 0

    async def get_by_email(
        self, session: AsyncSession, email: str
    ) -> Optional[Lead]:
        result = await session.execute(
            select(Lead).where(
                Lead.email == email,
                Lead.is_deleted.is_(False),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_place_id_any(
        self, session: AsyncSession, place_id: str
    ) -> Optional[Lead]:
        """Find lead by place_id including soft-deleted rows."""
        result = await session.execute(
            select(Lead).where(Lead.place_id == place_id).limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _source_from_maps(maps_lead: MapsScanResult) -> str:
        raw = getattr(maps_lead, "raw", None) or {}
        hunt = str(raw.get("hunt_mode") or "").strip().lower()
        if hunt:
            return hunt[:50]
        return LeadSource.GOOGLE_MAPS

    @staticmethod
    def _base_enrichment(maps_lead: MapsScanResult) -> dict:
        return {
            "address": maps_lead.address,
            "rating": maps_lead.rating,
            "review_count": maps_lead.review_count,
            "country": maps_lead.country,
        }

    async def refresh_package_tier(self, session: AsyncSession, lead: Lead) -> Lead:
        from utils.lead_package_tier import classify_package_tier

        lead.package_tier = classify_package_tier(lead)
        await session.flush()
        return lead

    async def _find_existing_maps(
        self,
        session: AsyncSession,
        maps_lead: MapsScanResult,
    ) -> Lead | None:
        existing = None
        if maps_lead.place_id:
            existing = await self.get_by_place_id(session, maps_lead.place_id)
            if not existing:
                existing = await self.get_by_place_id_any(session, maps_lead.place_id)
        if not existing and maps_lead.email:
            existing = await self.get_by_email(session, maps_lead.email)
        return existing

    async def upsert_inventory_from_maps(
        self,
        session: AsyncSession,
        maps_lead: MapsScanResult,
        campaign_run_id: str,
        *,
        for_outreach: bool = False,
    ) -> Lead:
        """
        Save every hunted lead to the memory bank (sell + outreach).
        Keeps contacted/replied rows; never soft-deletes for missing email.
        """
        from utils.lead_package_tier import sync_maps_enrichment

        existing = await self._find_existing_maps(session, maps_lead)
        base_score = 8 if not maps_lead.has_website else 5

        if existing:
            existing.is_deleted = False
            existing.deleted_at = None
            existing.campaign_run_id = campaign_run_id
            existing.business_name = maps_lead.business_name or existing.business_name
            if maps_lead.email:
                existing.email = maps_lead.email
            existing.phone = maps_lead.phone or existing.phone
            existing.website = (
                maps_lead.website_url
                if maps_lead.website_url is not None
                else existing.website
            )
            existing.location = maps_lead.city or existing.location
            existing.niche = maps_lead.niche or existing.niche
            existing.source = self._source_from_maps(maps_lead)
            if existing.score < base_score:
                existing.score = base_score
            data = dict(existing.enrichment_data or {})
            data.update(self._base_enrichment(maps_lead))
            existing.enrichment_data = data
            sync_maps_enrichment(existing, maps_lead)
            if for_outreach and existing.status in (
                LeadStatus.SKIPPED,
                LeadStatus.PENDING_EMAIL,
            ):
                existing.status = LeadStatus.NEW
            await self.refresh_package_tier(session, existing)
            return existing

        lead = Lead(
            source=self._source_from_maps(maps_lead),
            place_id=maps_lead.place_id,
            campaign_run_id=campaign_run_id,
            business_name=maps_lead.business_name or "Unknown",
            email=maps_lead.email,
            phone=maps_lead.phone,
            website=maps_lead.website_url,
            location=maps_lead.city,
            niche=maps_lead.niche,
            problem_detected="no_website" if not maps_lead.has_website else "has_website",
            score=base_score,
            status=LeadStatus.NEW if maps_lead.email else LeadStatus.SKIPPED,
            enrichment_data=self._base_enrichment(maps_lead),
        )
        session.add(lead)
        await session.flush()
        sync_maps_enrichment(lead, maps_lead)
        await self.refresh_package_tier(session, lead)
        return lead

    async def create_from_maps(
        self,
        session: AsyncSession,
        maps_lead: MapsScanResult,
        campaign_run_id: str,
    ) -> Lead:
        return await self.upsert_inventory_from_maps(
            session, maps_lead, campaign_run_id, for_outreach=True
        )

    async def update_after_demo(
        self,
        session: AsyncSession,
        lead: Lead,
        demo_site_path: str,
    ) -> Lead:
        lead.demo_site_path = demo_site_path
        await session.flush()
        return lead

    async def update_after_draft(
        self,
        session: AsyncSession,
        lead: Lead,
        subject: str,
        body: str,
        email: str | None = None,
    ) -> Lead:
        lead.pitch_subject = subject
        lead.pitch_body = body
        if email:
            existing = await session.execute(
                select(Lead).where(Lead.email == email, Lead.id != lead.id)
            )
            if existing.scalar_one_or_none():
                logger.warning(
                    f"[DB] Email {email} already on another lead — pitch saved without re-assigning email ({lead.business_name})"
                )
            else:
                lead.email = email
        resolved = (lead.email or "").strip()
        lead.status = LeadStatus.DRAFT_READY if resolved else LeadStatus.PENDING_EMAIL
        await self.refresh_package_tier(session, lead)
        return lead

    async def mark_contacted(
        self,
        session: AsyncSession,
        lead: Lead,
        *,
        send_channel: str = "",
    ) -> Lead:
        lead.status = LeadStatus.CONTACTED
        lead.last_contacted = datetime.now(timezone.utc)
        lead.sequence_step = 0
        data = dict(lead.enrichment_data or {})
        if send_channel:
            data["send_channel"] = send_channel
        lead.enrichment_data = data
        from modules.outreach.sequence_schedule import schedule_next_followup

        schedule_next_followup(lead)
        await self.refresh_package_tier(session, lead)
        return lead

    async def record_reply(
        self,
        session: AsyncSession,
        lead: Lead,
        *,
        classification: str,
        subject: str,
        snippet: str,
        instantly_email_id: str,
    ) -> Lead:
        """Store last reply metadata and set lead status from classification."""
        data = dict(lead.enrichment_data or {})
        data["last_reply"] = {
            "classification": classification,
            "subject": subject,
            "snippet": snippet[:500],
            "instantly_email_id": instantly_email_id,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        lead.enrichment_data = data

        needs_action = classification in ("interested", "unknown")

        if classification == "interested":
            lead.status = LeadStatus.REPLIED
        elif classification == "unsubscribe":
            lead.status = LeadStatus.UNSUBSCRIBED
            lead.next_followup = None
        elif classification == "not_now":
            lead.status = LeadStatus.REJECTED
            lead.next_followup = None
        elif classification == "unknown" and lead.status == LeadStatus.CONTACTED:
            lead.status = LeadStatus.REPLIED

        if needs_action:
            data["pending_reply_action"] = True
            lead.next_followup = None
        lead.enrichment_data = data

        await self.refresh_package_tier(session, lead)
        return lead

    async def discard_no_email(
        self,
        session: AsyncSession,
        lead: Lead,
        *,
        reason: str = "no_email",
    ) -> None:
        """Keep lead in DB for resale inventory; skip outreach only."""
        lead.is_deleted = False
        lead.deleted_at = None
        lead.status = LeadStatus.SKIPPED
        lead.problem_detected = reason
        lead.demo_site_path = None
        lead.pitch_subject = None
        lead.pitch_body = None
        lead.next_followup = None
        lead.updated_at = datetime.now(timezone.utc)
        await self.refresh_package_tier(session, lead)

    async def mark_skipped(
        self,
        session: AsyncSession,
        maps_lead: MapsScanResult,
        campaign_run_id: str,
        reason: str,
    ) -> Lead:
        lead = await self.upsert_inventory_from_maps(
            session, maps_lead, campaign_run_id
        )
        lead.status = LeadStatus.SKIPPED
        lead.problem_detected = reason
        await self.refresh_package_tier(session, lead)
        return lead

    async def reset_mock_leads(
        self, session: AsyncSession, niche: str, city: str
    ) -> int:
        """Remove mock leads for this niche/city so --fresh can re-insert same place_ids."""
        from modules.lead_finder.mock_leads import mock_place_id_prefix

        prefix = mock_place_id_prefix(niche, city)
        result = await session.execute(
            delete(Lead).where(Lead.place_id.like(f"{prefix}%"))
        )
        await session.flush()
        return result.rowcount or 0

    async def get_by_place_id(
        self, session: AsyncSession, place_id: str
    ) -> Optional[Lead]:
        result = await session.execute(
            select(Lead).where(
                Lead.place_id == place_id,
                Lead.is_deleted.is_(False),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_package_tier(self, session: AsyncSession) -> dict[str, int]:
        result = await session.execute(
            select(Lead.package_tier, func.count(Lead.id))
            .where(Lead.is_deleted.is_(False), Lead.email.is_not(None))
            .group_by(Lead.package_tier)
        )
        return {row[0] or "unsorted": row[1] for row in result.all()}

    async def list_by_package_tier(
        self,
        session: AsyncSession,
        tier: str,
        *,
        limit: int = 500,
        exclude_contacted: bool = False,
    ) -> list[Lead]:
        q = select(Lead).where(
            Lead.is_deleted.is_(False),
            Lead.package_tier == tier,
            Lead.email.is_not(None),
        )
        if exclude_contacted:
            q = q.where(
                Lead.status.not_in(
                    (
                        LeadStatus.CONTACTED,
                        LeadStatus.REPLIED,
                        LeadStatus.CLIENT,
                    )
                )
            )
        result = await session.execute(
            q.order_by(Lead.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def mark_package_sold(
        self,
        session: AsyncSession,
        lead: Lead,
        *,
        buyer: str = "",
    ) -> Lead:
        data = dict(lead.enrichment_data or {})
        data["lead_package_sold"] = True
        if buyer:
            data["lead_package_buyer"] = buyer
        data["lead_package_sold_at"] = datetime.now(timezone.utc).isoformat()
        lead.enrichment_data = data
        await self.refresh_package_tier(session, lead)
        return lead

    async def count_by_status(self, session: AsyncSession) -> dict[str, int]:
        result = await session.execute(
            select(Lead.status, func.count(Lead.id))
            .where(Lead.is_deleted.is_(False))
            .group_by(Lead.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def list_recent(
        self, session: AsyncSession, limit: int = 50
    ) -> list[Lead]:
        result = await session.execute(
            select(Lead)
            .where(Lead.is_deleted.is_(False))
            .order_by(Lead.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self, session: AsyncSession, lead_id: str
    ) -> Optional[Lead]:
        result = await session.execute(
            select(Lead).where(Lead.id == lead_id, Lead.is_deleted.is_(False)).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_unread_replies(
        self, session: AsyncSession, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Leads needing a drafted close reply (P1 — blueprint handle_email_reply)."""
        result = await session.execute(
            select(Lead)
            .where(
                Lead.is_deleted.is_(False),
                Lead.status.in_((LeadStatus.REPLIED, LeadStatus.CONTACTED)),
            )
            .order_by(Lead.updated_at.desc())
            .limit(max(limit * 3, limit))
        )
        out: list[dict[str, Any]] = []
        for lead in result.scalars():
            data = lead.enrichment_data or {}
            if not data.get("pending_reply_action"):
                continue
            last = data.get("last_reply") or {}
            out.append(
                {
                    "lead_id": lead.id,
                    "from": lead.email or lead.business_name,
                    "email": lead.email,
                    "business_name": lead.business_name,
                    "classification": last.get("classification", "unknown"),
                    "subject": last.get("subject", ""),
                    "snippet": last.get("snippet", ""),
                }
            )
            if len(out) >= limit:
                break
        return out

    async def list_followups_due(
        self, session: AsyncSession, limit: int = 10
    ) -> list[Lead]:
        """CONTACTED leads past next_followup (SMTP-owned sequence only)."""
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Lead)
            .where(
                Lead.is_deleted.is_(False),
                Lead.status == LeadStatus.CONTACTED,
                Lead.next_followup.is_not(None),
                Lead.next_followup <= now,
                Lead.email.is_not(None),
            )
            .order_by(Lead.next_followup.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_reply_handled(
        self,
        session: AsyncSession,
        lead: Lead,
        *,
        draft_path: str = "",
    ) -> Lead:
        data = dict(lead.enrichment_data or {})
        data["pending_reply_action"] = False
        if draft_path:
            data["reply_draft_path"] = draft_path
        lead.enrichment_data = data
        await session.flush()
        return lead

    async def advance_followup(
        self, session: AsyncSession, lead: Lead
    ) -> Lead:
        from modules.outreach.sequence_schedule import advance_followup_step

        advance_followup_step(lead)
        await session.flush()
        return lead

    async def count_uncontacted_with_email(
        self, session: AsyncSession
    ) -> int:
        result = await session.execute(
            select(func.count(Lead.id)).where(
                Lead.is_deleted.is_(False),
                Lead.status.in_(
                    (LeadStatus.NEW, LeadStatus.DRAFT_READY, LeadStatus.PENDING_EMAIL)
                ),
                Lead.email.is_not(None),
            )
        )
        return result.scalar_one() or 0

    async def list_incomplete(
        self,
        session: AsyncSession,
        limit: int = 20,
        *,
        resume_cooldown_minutes: int = 25,
    ) -> list[Lead]:
        """
        Leads that started outreach but still need demo/email/draft/send.
        Oldest first so stopped runs continue in order.
        """
        from core.lead_resume import assess_lead, is_resume_deferred

        fetch = max(limit * 4, limit)
        result = await session.execute(
            select(Lead)
            .where(
                Lead.is_deleted.is_(False),
                Lead.status.in_(
                    (
                        LeadStatus.NEW,
                        LeadStatus.DRAFT_READY,
                        LeadStatus.PENDING_EMAIL,
                    )
                ),
            )
            .order_by(Lead.updated_at.asc())
            .limit(fetch)
        )
        out: list[Lead] = []
        for lead in result.scalars():
            if is_resume_deferred(lead, resume_cooldown_minutes):
                continue
            if assess_lead(lead).missing:
                out.append(lead)
            if len(out) >= limit:
                break
        return out

    async def list_pending_deliveries(
        self,
        session: AsyncSession,
        *,
        limit: int = 10,
    ) -> list[Lead]:
        """Paid clients with delivery.checklist still pending (Atlas P2)."""
        result = await session.execute(
            select(Lead)
            .where(
                Lead.is_deleted.is_(False),
                Lead.status == LeadStatus.CLIENT,
            )
            .order_by(Lead.updated_at.desc())
            .limit(max(limit * 5, 20))
        )
        out: list[Lead] = []
        for lead in result.scalars():
            delivery = (lead.enrichment_data or {}).get("delivery") or {}
            if delivery.get("status") == "pending":
                out.append(lead)
            if len(out) >= limit:
                break
        return out
