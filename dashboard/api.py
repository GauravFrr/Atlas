"""Dashboard JSON API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from config import get_settings
from constants import LeadStatus
from dashboard.jobs import create_job, get_job, update_job
from dashboard.prefs import load_prefs, save_prefs
from database.connection import get_session_factory
from database.repositories.campaign_repository import CampaignRepository
from database.repositories.lead_repository import LeadRepository

router = APIRouter(prefix="/api")
_lead_repo = LeadRepository()
_campaign_repo = CampaignRepository()
UPLOAD_DIR = Path("data/lead_queue/incoming")
UPLOAD_DIR_FALLBACK = Path("data/uploads")


class SettingsUpdate(BaseModel):
    your_name: str | None = None
    autopilot_enabled: bool | None = None
    leads_per_run: int | None = None
    send_mode: str | None = None
    demo_site_base_url: str | None = None
    reply_sync_interval_minutes: int | None = None
    instantly_daily_limit: int | None = None
    safe_demo: bool | None = None


class CampaignRunRequest(BaseModel):
    csv_filename: str
    niche: str = "real_estate"
    city: str = "London"
    leads: int = Field(default=10, ge=1, le=100)
    instantly: bool = True
    safe_demo: bool = True


def _lead_to_dict(lead: Any) -> dict[str, Any]:
    reply = (lead.enrichment_data or {}).get("last_reply") or {}
    return {
        "id": lead.id,
        "business_name": lead.business_name,
        "email": lead.email,
        "status": lead.status,
        "niche": lead.niche,
        "location": lead.location,
        "phone": lead.phone,
        "website": lead.website,
        "last_contacted": lead.last_contacted.isoformat() if lead.last_contacted else None,
        "reply_classification": reply.get("classification"),
        "reply_snippet": (reply.get("snippet") or "")[:200],
    }


@router.get("/overview")
async def overview() -> dict[str, Any]:
    settings = get_settings()
    prefs = load_prefs()
    factory = get_session_factory()
    async with factory() as session:
        by_status = await _lead_repo.count_by_status(session)

    return {
        "stats": {
            "total": sum(by_status.values()),
            "contacted": by_status.get(LeadStatus.CONTACTED, 0),
            "replied": by_status.get(LeadStatus.REPLIED, 0),
            "draft_ready": by_status.get(LeadStatus.DRAFT_READY, 0),
            "skipped": by_status.get(LeadStatus.SKIPPED, 0),
        },
        "integrations": {
            "instantly": settings.has_instantly,
            "telegram": settings.has_telegram,
            "google_maps": bool(settings.google_places_api_key),
            "hunter": bool(settings.hunter_api_key),
            "netlify": bool(settings.netlify_auth_token and settings.netlify_site_id),
        },
        "prefs": prefs,
    }


@router.get("/leads")
async def list_leads(
    status: str | None = None,
    q: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        leads = await _lead_repo.list_recent(session, limit=200)

    items = [_lead_to_dict(l) for l in leads]
    if status:
        items = [x for x in items if x["status"] == status]
    if q:
        q_lower = q.lower()
        items = [
            x
            for x in items
            if q_lower in (x["business_name"] or "").lower()
            or q_lower in (x["email"] or "").lower()
        ]
    return {"items": items[:limit], "count": len(items)}


@router.get("/campaigns")
async def list_campaigns(limit: int = 20) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        runs = await _campaign_repo.list_recent(session, limit)

    return {
        "items": [
            {
                "id": r.id,
                "niche": r.niche,
                "city": r.city,
                "leads_requested": r.leads_requested,
                "leads_processed": r.leads_processed,
                "emails_sent": r.emails_sent,
                "demos_generated": r.demos_generated,
                "duplicates_skipped": r.duplicates_skipped,
                "status": r.status,
                "dry_run": r.dry_run,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    }


@router.get("/replies")
async def list_replies() -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        leads = await _lead_repo.list_recent(session, 100)

    hot = []
    for lead in leads:
        reply = (lead.enrichment_data or {}).get("last_reply")
        if reply or lead.status in (LeadStatus.REPLIED, LeadStatus.CLIENT):
            hot.append(_lead_to_dict(lead))
    return {"items": hot}


@router.get("/settings")
async def get_settings_view() -> dict[str, Any]:
    s = get_settings()
    prefs = load_prefs()
    return {
        "prefs": prefs,
        "env": {
            "agent_name": s.agent_name,
            "your_name": s.your_name,
            "demo_site_base_url": s.demo_site_base_url,
            "email_send_mode": s.email_send_mode,
            "instantly_configured": s.has_instantly,
            "instantly_campaign_id": (
                s.instantly_campaign_id[:8] + "…" if s.instantly_campaign_id else ""
            ),
            "max_emails_per_day": s.max_emails_per_day,
            "telegram_configured": s.has_telegram,
        },
        "note": "Secrets (API keys) stay in .env. Preferences below save to data/dashboard_prefs.json.",
    }


@router.post("/settings")
async def update_settings(body: SettingsUpdate) -> dict[str, Any]:
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    prefs = save_prefs(updates)
    if "leads_per_run" in updates:
        from pathlib import Path
        import json

        targets_path = Path("data/autopilot_targets.json")
        if targets_path.is_file():
            cfg = json.loads(targets_path.read_text(encoding="utf-8"))
            cfg["leads_per_run"] = updates["leads_per_run"]
            targets_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return {"ok": True, "prefs": prefs}


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a .csv file")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR_FALLBACK.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in file.filename)
    dest = UPLOAD_DIR / f"{stamp}_{safe_name}"

    content = await file.read()
    dest.write_bytes(content)

    rows = 0
    headers: list[str] = []
    try:
        import csv
        import io

        text = content.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        headers = list(reader.fieldnames or [])
        rows = sum(1 for _ in reader)
    except Exception as e:
        raise HTTPException(400, f"Invalid CSV: {e}") from e

    return {
        "filename": dest.name,
        "path": str(dest),
        "rows": rows,
        "headers": headers[:20],
    }


async def _run_campaign_task(job_id: str, req: CampaignRunRequest) -> None:
    update_job(job_id, status="running", message="Campaign started…")
    path = UPLOAD_DIR / req.csv_filename
    if not path.is_file():
        update_job(job_id, status="failed", message=f"File not found: {req.csv_filename}")
        return

    try:
        from core.campaign_orchestrator import run_campaign
        from utils.send_router import resolve_send_mode

        settings = get_settings()
        if req.safe_demo:
            settings.demo_generation_mode = "safe"
        mode = "instantly" if req.instantly else resolve_send_mode(settings, "draft")

        result = await run_campaign(
            niche=req.niche,
            city=req.city,
            leads=req.leads,
            send_mode=mode,
            csv_path=str(path),
            settings=settings,
        )
        update_job(
            job_id,
            status="completed",
            message="Campaign finished",
            result={
                "summary": result.summary_text(),
                "emails_sent": result.emails_sent,
                "processed": result.leads_processed,
            },
        )
    except Exception as e:
        update_job(job_id, status="failed", message=str(e))


@router.post("/campaign/run")
async def run_campaign_api(
    body: CampaignRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    path = UPLOAD_DIR / body.csv_filename
    if not path.is_file():
        raise HTTPException(404, "Upload CSV first")

    job = create_job()
    background_tasks.add_task(_run_campaign_task, job.id, body)
    return {"job_id": job.id, "status": "queued"}


@router.get("/campaign/job/{job_id}")
async def campaign_job_status(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "message": job.message,
        "result": job.result,
        "created_at": job.created_at,
    }


@router.post("/reply-sync")
async def reply_sync() -> dict[str, Any]:
    from modules.outreach.reply_sync import sync_instantly_replies

    result = await sync_instantly_replies(get_settings())
    return {
        "scanned": result.scanned,
        "new_replies": result.new_replies,
        "interested": result.interested,
    }


@router.get("/autopilot/status")
async def autopilot_status() -> dict[str, Any]:
    from core.autopilot import get_status

    return get_status()


@router.post("/autopilot/run")
async def autopilot_run() -> dict[str, Any]:
    from core.autopilot import run_once

    return await run_once(get_settings())


@router.post("/instantly/configure")
async def instantly_configure() -> dict[str, Any]:
    from integrations.platforms.instantly import InstantlyClient

    s = get_settings()
    prefs = load_prefs()
    limit = int(prefs.get("instantly_daily_limit") or 20)
    client = InstantlyClient(s.instantly_api_key, s.instantly_campaign_id)
    ok = await client.apply_agent_earns_preset(daily_limit=limit, activate=True)
    camp = await client.get_campaign()
    return {"ok": ok, "daily_limit": camp.get("daily_limit") if camp else None}
