"""
Resume incomplete leads from the memory bank (SQLite).

When autopilot stops mid-pipeline, each lead row keeps partial progress.
On the next run we finish missing steps before hunting new prospects.

Pipeline steps (in order):
  demo → email → publish → draft → send
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from constants import LeadStatus
from database.models.lead import Lead
from core.lead_maps import lead_to_maps_scan
from modules.outreach.icebreaker import preset_icebreaker
from utils.platform_domains import is_blocked_email, is_platform_url

# Order matters for logging and dependency checks
STEP_DEMO = "demo"
STEP_EMAIL = "email"
STEP_PUBLISH = "publish"
STEP_DRAFT = "draft"
STEP_SEND = "send"

ALL_STEPS = (STEP_DEMO, STEP_EMAIL, STEP_PUBLISH, STEP_DRAFT, STEP_SEND)

_DONE_STATUSES = frozenset({
    LeadStatus.CONTACTED,
    LeadStatus.REPLIED,
    LeadStatus.CLIENT,
    LeadStatus.UNSUBSCRIBED,
    LeadStatus.REJECTED,
    LeadStatus.SKIPPED,
})


@dataclass
class LeadResumePlan:
    lead_id: str
    place_id: str
    business_name: str
    missing: list[str] = field(default_factory=list)
    status: str = ""
    has_email: bool = False

    @property
    def is_complete(self) -> bool:
        return not self.missing


def _enrichment(lead: Lead) -> dict[str, Any]:
    return dict(lead.enrichment_data or {})


def assess_lead(lead: Lead) -> LeadResumePlan:
    """Return which pipeline steps still need to run for this lead."""
    missing: list[str] = []
    data = _enrichment(lead)
    email = (lead.email or "").strip()
    valid_email = bool(email) and not is_blocked_email(email)

    if lead.status in _DONE_STATUSES:
        return LeadResumePlan(
            lead_id=lead.id,
            place_id=lead.place_id or lead.id,
            business_name=lead.business_name,
            missing=[],
            status=lead.status,
            has_email=valid_email,
        )

    # Email-first: nothing else until we have a contact address
    if not valid_email:
        missing.append(STEP_EMAIL)
        ordered = [STEP_EMAIL]
        return LeadResumePlan(
            lead_id=lead.id,
            place_id=lead.place_id or lead.id,
            business_name=lead.business_name,
            missing=ordered,
            status=lead.status,
            has_email=False,
        )

    skip_demo = bool(preset_icebreaker(lead_to_maps_scan(lead)))
    demo_path = lead.demo_site_path
    has_demo_file = bool(demo_path and Path(demo_path).is_file())

    if not skip_demo and not has_demo_file:
        missing.append(STEP_DEMO)

    if has_demo_file and not data.get("demo_url"):
        missing.append(STEP_PUBLISH)

    has_draft = bool(
        (lead.pitch_subject or "").strip() and (lead.pitch_body or "").strip()
    )
    if not has_draft:
        missing.append(STEP_DRAFT)

    if (
        has_draft
        and lead.status in (LeadStatus.NEW, LeadStatus.DRAFT_READY, LeadStatus.PENDING_EMAIL)
        and STEP_DRAFT not in missing
    ):
        missing.append(STEP_SEND)

    # Stable step order
    ordered = [s for s in ALL_STEPS if s in missing]

    return LeadResumePlan(
        lead_id=lead.id,
        place_id=lead.place_id or lead.id,
        business_name=lead.business_name,
        missing=ordered,
        status=lead.status,
        has_email=valid_email,
    )


def merge_enrichment(lead: Lead, **kwargs: Any) -> None:
    data = _enrichment(lead)
    data.update({k: v for k, v in kwargs.items() if v is not None})
    lead.enrichment_data = data


def is_resume_deferred(lead: Lead, cooldown_minutes: int) -> bool:
    """Skip re-processing same incomplete lead every Atlas tick."""
    if cooldown_minutes <= 0:
        return False
    until_raw = _enrichment(lead).get("resume_deferred_until")
    if not until_raw:
        return False
    try:
        until = datetime.fromisoformat(str(until_raw).replace("Z", "+00:00"))
        if until.tzinfo is None:
            until = until.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return False
    return datetime.now(timezone.utc) < until


def mark_resume_deferred(lead: Lead, cooldown_minutes: int) -> None:
    """Backoff after a resume attempt that did not finish the pipeline."""
    if cooldown_minutes <= 0:
        return
    until = datetime.now(timezone.utc) + timedelta(minutes=cooldown_minutes)
    merge_enrichment(
        lead,
        resume_deferred_until=until.isoformat(),
        resume_last_attempt_at=datetime.now(timezone.utc).isoformat(),
    )


def persist_maps_meta(lead: Lead, maps_lead: MapsScanResult, *, demo_url: str | None = None) -> None:
    """Keep hunt_mode / channel context on the DB row for resume."""
    raw = dict((maps_lead.raw or {}))
    data = _enrichment(lead)
    if raw.get("hunt_mode"):
        data["hunt_mode"] = raw["hunt_mode"]
    if raw:
        data["raw"] = {**(data.get("raw") or {}), **raw}
    if demo_url:
        data["demo_url"] = demo_url
    if maps_lead.email and not is_blocked_email(maps_lead.email):
        data["last_enriched_email"] = maps_lead.email
    lead.enrichment_data = data


async def run_resume_queue(
    settings: Any,
    *,
    max_leads: int = 10,
    send_mode: str | None = None,
) -> dict[str, Any]:
    """Entry point for autopilot and scripts — finish incomplete DB leads first."""
    from core.campaign_orchestrator import CampaignOrchestrator
    from utils.send_router import resolve_send_mode

    mode = resolve_send_mode(
        settings, send_mode or settings.email_send_mode or "instantly"
    )
    orch = CampaignOrchestrator(settings)
    return await orch.process_incomplete_queue(max_leads=max_leads, send_mode=mode)
