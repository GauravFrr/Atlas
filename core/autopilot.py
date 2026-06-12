"""
Autopilot — full autonomy: find leads, pitch, sync replies. User does nothing.

Order each cycle:
  1. Sync Instantly replies (money)
  2. Optional bonus CSV if user dropped one
  3. Hunt leads on Google Maps (all niches × cities — agent finds clients)
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import Settings, get_settings
from core.lead_hunter import all_hunt_targets, hunt_and_outreach, pick_next_target
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository

STATE_PATH = Path("data/autopilot_state.json")
DONE_DIR = Path("data/lead_queue/done")
QUEUE_DIRS = ["data/lead_queue/incoming", "data/uploads"]


def _load_state() -> dict[str, Any]:
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "processed_csvs": [],
        "rotation_index": 0,
        "last_run": None,
        "last_action": None,
    }


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _leads_per_run(settings: Settings) -> int:
    configured = int(getattr(settings, "autopilot_leads_per_run", 0) or 0)
    if configured > 0:
        return configured
    try:
        p = Path("data/dashboard_prefs.json")
        if p.is_file():
            data = json.loads(p.read_text(encoding="utf-8"))
            return int(data.get("leads_per_run") or 20)
    except Exception:
        pass
    return 20


def _find_next_csv(state: dict[str, Any]) -> Path | None:
    processed = set(state.get("processed_csvs") or [])
    for rel in QUEUE_DIRS:
        d = Path(rel)
        if d.is_dir():
            for path in sorted(d.glob("*.csv"), key=lambda p: p.stat().st_mtime):
                if path.name not in processed:
                    return path
    return None


def _infer_campaign_params(csv_path: Path) -> tuple[str, str]:
    import csv

    niches: list[str] = []
    cities: list[str] = []
    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 50:
                    break
                r = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
                for key in ("niche", "industry", "vertical"):
                    if r.get(key):
                        niches.append(r[key].lower().replace(" ", "_")[:40])
                for key in ("city", "location", "market"):
                    if r.get(key):
                        cities.append(r[key])
    except Exception:
        pass
    niche = Counter(niches).most_common(1)[0][0] if niches else "local_service"
    city = Counter(cities).most_common(1)[0][0] if cities else "US"
    return niche, city


async def _emails_sent_today() -> int:
    repo = LeadRepository()
    factory = get_session_factory()
    async with factory() as session:
        return await repo.count_emails_sent_today(session)


async def run_once(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    await init_db()
    state = _load_state()
    leads_per_run = _leads_per_run(settings)
    daily_cap = min(leads_per_run, settings.max_emails_per_day)
    sent_today = await _emails_sent_today()
    remaining = max(0, daily_cap - sent_today)

    result: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "hunting",
        "detail": "Agent is finding leads",
    }

    if settings.has_instantly:
        try:
            from modules.outreach.reply_sync import sync_instantly_replies

            sync = await sync_instantly_replies(settings)
            if sync.interested:
                result["replies"] = {
                    "interested": sync.interested,
                    "new": sync.new_replies,
                }
        except Exception as e:
            logger.warning(f"[Autopilot] Reply sync: {e}")

    from utils.send_router import resolve_send_mode

    send_mode = resolve_send_mode(settings, settings.email_send_mode or "instantly")

    if remaining <= 0:
        result["action"] = "daily_cap_reached"
        result["detail"] = f"Daily cap hit ({sent_today} sent). Hunting resumes tomorrow."
        state["last_run"] = result["timestamp"]
        state["last_action"] = result["action"]
        _save_state(state)
        return result

    resume_stats: dict[str, Any] = {}
    if getattr(settings, "resume_incomplete_on_start", True):
        try:
            from core.lead_resume import run_resume_queue

            resume_cap = min(
                int(getattr(settings, "resume_max_per_run", 10) or 10),
                remaining,
            )
            resume_stats = await run_resume_queue(
                settings, max_leads=resume_cap, send_mode=send_mode
            )
            sent_resume = int(resume_stats.get("sent") or 0)
            remaining = max(0, remaining - sent_resume)
            sent_today += sent_resume
            if resume_stats.get("queued"):
                result["resume"] = resume_stats
                logger.info(
                    f"[Autopilot] Resume queue: {resume_stats.get('resumed', 0)}/"
                    f"{resume_stats.get('queued', 0)} leads, {sent_resume} sent"
                )
        except Exception as e:
            logger.warning(f"[Autopilot] Resume queue failed: {e}")

    if remaining <= 0:
        result["action"] = "resume_only_cap"
        result["detail"] = (
            f"Finished incomplete leads ({resume_stats.get('sent', 0)} sent). "
            "Daily cap full — new hunt tomorrow."
        )
        state["last_run"] = result["timestamp"]
        state["last_action"] = result["action"]
        _save_state(state)
        return result
    if send_mode == "draft" and not settings.has_instantly and not settings.has_smtp:
        result["detail"] = "Add INSTANTLY_API_KEY or SMTP to .env — agent cannot send yet"
        return result

    # Bonus: user CSV (optional)
    csv_path = _find_next_csv(state)
    if csv_path:
        niche, city = _infer_campaign_params(csv_path)
        logger.info(f"[Autopilot] Bonus CSV → {csv_path.name}")

        from core.campaign_orchestrator import run_campaign

        campaign = await run_campaign(
            niche=niche,
            city=city,
            leads=remaining,
            send_mode=send_mode,
            csv_path=str(csv_path),
            settings=settings,
        )
        processed = list(state.get("processed_csvs") or [])
        processed.append(csv_path.name)
        state["processed_csvs"] = processed[-200:]
        DONE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(csv_path), str(DONE_DIR / csv_path.name))
        except Exception:
            pass
        state["last_run"] = result["timestamp"]
        state["last_action"] = "csv_campaign"
        _save_state(state)
        result.update(
            {
                "action": "csv_campaign",
                "detail": f"Bonus batch {csv_path.name}",
                "niche": niche,
                "city": city,
                "emails_sent": campaign.emails_sent,
                "processed": campaign.leads_processed,
            }
        )
        return result

    # Main job: agent hunts leads itself (Google Maps rotation)
    rotation_index = int(state.get("rotation_index") or 0)
    source_index = int(state.get("source_index") or 0)
    next_target, _ = pick_next_target(rotation_index)

    from core.lead_sources import hunt_mode_label, normalize_mode, pick_hunt_mode

    next_mode, _ = pick_hunt_mode(source_index, settings)
    next_mode = normalize_mode(next_mode)
    result["hunting"] = f"{hunt_mode_label(next_mode)}: {next_target['niche']} @ {next_target['city']}"

    campaign, hunt_meta = await hunt_and_outreach(
        settings,
        leads=remaining,
        send_mode=send_mode,
        rotation_index=rotation_index,
        source_index=source_index,
    )

    state["rotation_index"] = hunt_meta.get("rotation_index", rotation_index)
    state["source_index"] = hunt_meta.get("source_index", source_index)
    state["last_run"] = result["timestamp"]

    if hunt_meta.get("blocked") == "google_places_api_key":
        state["last_action"] = "need_google_api"
        _save_state(state)
        result.update(
            {
                "action": "need_google_api",
                "detail": "LEAD_SCAN_SOURCE=google but API key missing. Use auto or osm for free hunt.",
                "next_hunt": hunt_meta.get("would_hunt"),
                "markets_in_rotation": len(all_hunt_targets()),
            }
        )
        return result

    if campaign and (campaign.leads_processed > 0 or campaign.emails_sent > 0):
        state["last_action"] = "hunt_and_send"
        _save_state(state)
        result.update(
            {
                "action": "hunt_and_send",
                "detail": f"{hunt_meta.get('hunt_mode_label')} — {hunt_meta.get('niche')} @ {hunt_meta.get('city')}",
                "niche": hunt_meta.get("niche"),
                "city": hunt_meta.get("city"),
                "hunt_mode": hunt_meta.get("hunt_mode"),
                "emails_sent": campaign.emails_sent,
                "processed": campaign.leads_processed,
                "markets_in_rotation": len(all_hunt_targets()),
                "lead_modes": hunt_meta.get("available_modes"),
            }
        )
        return result

    state["last_action"] = "hunt_no_new"
    _save_state(state)
    result.update(
        {
            "action": "hunt_no_new",
            "detail": "Hunted new markets — all contacts already in memory. Rotating…",
            "markets_in_rotation": len(all_hunt_targets()),
            "attempts": hunt_meta.get("attempts"),
        }
    )
    return result


def _print_cycle_summary(result: dict[str, Any], *, cycle: int) -> None:
    action = result.get("action", "?")
    detail = result.get("detail", "")
    logger.info(f"[Cycle #{cycle}] {action}: {detail}")
    if result.get("resume"):
        r = result["resume"]
        logger.info(
            f"  Resume: {r.get('resumed', 0)}/{r.get('queued', 0)} leads, "
            f"{r.get('sent', 0)} sent"
        )
    if result.get("emails_sent"):
        logger.info(
            f"  Outreach: {result.get('emails_sent', 0)} sent, "
            f"{result.get('processed', 0)} processed"
        )
    if result.get("replies"):
        rep = result["replies"]
        if rep.get("interested") or rep.get("new"):
            logger.info(
                f"  Replies: {rep.get('new', 0)} new, "
                f"{rep.get('interested', 0)} interested"
            )


async def run_forever(settings: Settings | None = None) -> None:
    """
    Autonomous earning loop — runs until Ctrl+C.

    Each cycle (A→Z):
      - Sync Instantly replies
      - Finish incomplete leads in SQLite
      - Process bonus CSVs in data/lead_queue/incoming/
      - Hunt leads, build demos, draft + send email
    """
    settings = settings or get_settings()
    await init_db()

    interval_min = max(5, int(getattr(settings, "agent_loop_interval_minutes", 30) or 30))
    sleep_sec = interval_min * 60
    cycle = 0

    logger.info("=" * 60)
    logger.info(f"  {settings.agent_name} | Agent-Earns — FULL AUTOPILOT")
    logger.info(f"  Cycle every {interval_min} min | Ctrl+C to stop")
    logger.info("  Pipeline: resume → replies → hunt → demo → email → send")
    logger.info("=" * 60)

    try:
        from utils.notifier import Notifier

        notifier = Notifier(settings=settings)
        await notifier.send_info(
            f"{settings.agent_name} started (full autopilot)\n"
            f"Cycle: every {interval_min} min\n"
            "Finding leads and sending outreach automatically."
        )
    except Exception:
        pass

    while True:
        cycle += 1
        started = datetime.now(timezone.utc)
        logger.info(f"─── Autonomous cycle #{cycle} | {started.strftime('%H:%M UTC')} ───")

        try:
            result = await run_once(settings)
            _print_cycle_summary(result, cycle=cycle)
        except Exception as e:
            logger.exception(f"[Cycle #{cycle}] Failed: {e}")

        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        wait = max(60.0, sleep_sec - elapsed)
        logger.info(
            f"Cycle #{cycle} done in {elapsed:.0f}s. "
            f"Next cycle in {wait / 60:.1f} min."
        )
        await asyncio.sleep(wait)


def _print_cycle_summary(result: dict[str, Any], *, cycle: int) -> None:
    action = result.get("action", "unknown")
    detail = result.get("detail", "")
    print(f"\n--- Cycle #{cycle} | {action} ---")
    print(f"  {detail}")
    if result.get("resume"):
        r = result["resume"]
        print(
            f"  Resume: {r.get('resumed', 0)}/{r.get('queued', 0)} leads, "
            f"{r.get('sent', 0)} sent"
        )
    if result.get("replies"):
        rep = result["replies"]
        print(f"  Replies: {rep.get('new', 0)} new, {rep.get('interested', 0)} interested")
    if result.get("emails_sent") is not None:
        print(
            f"  Outreach: {result.get('emails_sent', 0)} sent, "
            f"{result.get('processed', 0)} processed"
        )
    if result.get("hunting"):
        print(f"  Next hunt: {result['hunting']}")
    print()


async def run_forever(settings: Settings | None = None) -> None:
    """
    Run the full earning agent 24/7 until Ctrl+C.

    Each cycle (automatic, no human input):
      1. Sync Instantly replies
      2. Finish incomplete leads in agent.db
      3. Process bonus CSVs if dropped in data/lead_queue/incoming/
      4. Hunt leads → demos → emails → Instantly/SMTP
      5. Sleep → repeat
    """
    settings = settings or get_settings()
    await init_db()

    interval_min = max(5, int(getattr(settings, "agent_loop_interval_minutes", 30) or 30))
    interval_sec = interval_min * 60

    logger.info("=" * 60)
    logger.info("  Agent-Earns — FULL AUTOPILOT (A → Z)")
    logger.info(f"  Cycle every {interval_min} minutes. Ctrl+C to stop.")
    logger.info("=" * 60)

    if settings.has_telegram:
        try:
            from utils.notifier import Notifier

            await Notifier(settings).send_info(
                f"{settings.agent_name} started — full autopilot every {interval_min}m"
            )
        except Exception as e:
            logger.debug(f"Startup Telegram notify skipped: {e}")

    cycle = 0
    while True:
        cycle += 1
        started = datetime.now(timezone.utc)
        logger.info(f"─── Autonomous cycle #{cycle} ───")

        try:
            result = await run_once(settings)
            _print_cycle_summary(result, cycle=cycle)
        except Exception as e:
            logger.exception(f"Cycle #{cycle} failed: {e}")
            print(f"\n--- Cycle #{cycle} | error ---\n  {e}\n")

        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        sleep_sec = max(60, interval_sec - elapsed)
        logger.info(
            f"Cycle #{cycle} done in {elapsed:.0f}s. "
            f"Next cycle in {sleep_sec / 60:.1f} min."
        )
        await asyncio.sleep(sleep_sec)


def get_status() -> dict[str, Any]:
    state = _load_state()
    settings = get_settings()
    idx = int(state.get("rotation_index") or 0)
    src_idx = int(state.get("source_index") or 0)
    nxt, _ = pick_next_target(idx)
    nxt_csv = _find_next_csv(state)
    total = len(all_hunt_targets())

    from core.lead_sources import available_hunt_modes, hunt_mode_label, pick_hunt_mode

    modes = available_hunt_modes(settings)
    mode_id, _ = pick_hunt_mode(src_idx, settings)
    mode_label = hunt_mode_label(mode_id)

    if nxt_csv:
        msg = f"Bonus CSV {nxt_csv.name}, then {mode_label}"
    else:
        msg = f"Next: {mode_label} → {nxt['niche']} @ {nxt['city']} ({len(modes)} modes, {total} markets)"

    return {
        "last_action": state.get("last_action"),
        "last_run": state.get("last_run"),
        "next_hunt": f"{nxt['niche']} @ {nxt['city']}",
        "next_csv": nxt_csv.name if nxt_csv else None,
        "markets_in_rotation": total,
        "google_maps_ready": bool(settings.google_places_api_key),
        "osm_free_ready": True,
        "lead_scan_source": settings.lead_scan_source or "auto",
        "lead_modes": modes,
        "next_hunt_mode": mode_id,
        "source_index": src_idx,
        "message": msg,
        "mode": "full_autopilot",
    }
