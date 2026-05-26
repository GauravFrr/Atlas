"""
Clean up bad YouTube/M06 outreach from the pre-fix autopilot run.

Default: dry-run (report only). Use --apply to change the DB.

  python scripts/cleanup_youtube_bad_leads.py
  python scripts/cleanup_youtube_bad_leads.py --apply
  python scripts/cleanup_youtube_bad_leads.py --apply --reset-m06
  python scripts/cleanup_youtube_bad_leads.py --apply --instantly-remove

Actions:
  1. List M06 leads (place_id m06/*) and flag blocked / missing emails
  2. Clear blocked emails (e.g. *@youtube.com) and undo false "contacted" state
  3. Clear youtube.com from website column; strip garbage contact names in enrichment_data
  4. Optional --reset-m06: soft-delete all m06/* leads so campaigns can re-process them
  5. Optional --instantly-remove: remove bad email from Instantly campaign via API
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger
from sqlalchemy import or_, select

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from constants import LeadStatus
from database.connection import get_session_factory, init_db
from database.models.lead import Lead
from integrations.platforms.instantly import InstantlyClient
from utils.platform_domains import is_blocked_email, is_platform_url

DEFAULT_BAD_EMAIL = "johnhebda@youtube.com"
M06_PREFIX = "m06/"


def _safe_print(text: str) -> None:
    """Avoid Windows console UnicodeEncodeError on channel titles."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


def _is_m06_lead(lead: Lead) -> bool:
    pid = (lead.place_id or "").lower()
    if pid.startswith(M06_PREFIX):
        return True
    web = (lead.website or "").lower()
    return "youtube.com/channel/" in web or "youtube.com/@" in web


def _garbage_contact(data: dict | None) -> bool:
    if not data:
        return False
    for key in ("contact_first_name", "first_name", "owner_first_name", "contact_name"):
        val = str(data.get(key) or "").strip()
        if not val:
            continue
        from utils.contact_greeting import looks_like_first_name

        if not looks_like_first_name(val.split()[0]):
            return True
    return False


async def _list_m06_leads(session) -> list[Lead]:
    result = await session.execute(
        select(Lead).where(
            Lead.is_deleted.is_(False),
            or_(
                Lead.place_id.like(f"{M06_PREFIX}%"),
                Lead.website.ilike("%youtube.com/channel/%"),
                Lead.website.ilike("%youtube.com/@%"),
            ),
        )
    )
    return list(result.scalars().all())


async def _leads_with_blocked_email(session) -> list[Lead]:
    result = await session.execute(select(Lead).where(Lead.is_deleted.is_(False)))
    return [l for l in result.scalars() if l.email and is_blocked_email(l.email)]


async def cleanup_db(
    *,
    apply: bool,
    bad_email: str,
    reset_m06: bool,
) -> dict[str, int]:
    stats = {
        "m06_listed": 0,
        "m06_no_real_email": 0,
        "blocked_email_cleared": 0,
        "contacted_reset": 0,
        "website_cleared": 0,
        "garbage_name_cleared": 0,
        "m06_soft_deleted": 0,
    }

    factory = get_session_factory()
    async with factory() as session:
        m06_leads = await _list_m06_leads(session)
        stats["m06_listed"] = len(m06_leads)

        print("\n=== M06 / YouTube leads ===\n")
        print(f"{'Business':<36} {'Email':<28} {'Status':<14} {'Website'}")
        print("-" * 110)

        for lead in m06_leads:
            email = (lead.email or "").strip() or "—"
            web = (lead.website or "")[:40] or "—"
            if not lead.email or is_blocked_email(lead.email or ""):
                stats["m06_no_real_email"] += 1
                flag = " [no real email]"
            elif is_platform_url(lead.website):
                flag = " [platform website]"
            else:
                flag = ""
            _safe_print(
                f"{lead.business_name[:35]:<36} {email[:27]:<28} "
                f"{lead.status:<14} {web}{flag}"
            )

        blocked = await _leads_with_blocked_email(session)
        targets = blocked
        if bad_email and bad_email not in {l.email for l in blocked}:
            r = await session.execute(
                select(Lead).where(
                    Lead.email == bad_email.strip().lower(),
                    Lead.is_deleted.is_(False),
                )
            )
            extra = r.scalar_one_or_none()
            if extra and extra not in targets:
                targets.append(extra)

        if targets:
            print(f"\n=== Blocked / bad emails ({len(targets)} lead(s)) ===\n")
            for lead in targets:
                _safe_print(
                    f"  {lead.business_name} | {lead.email} | status={lead.status} | "
                    f"place_id={lead.place_id}"
                )

        if not apply:
            print("\n[DRY RUN] No DB changes. Pass --apply to fix.\n")
            if reset_m06:
                print(f"Would soft-delete {len(m06_leads)} m06/* lead(s).\n")
            return stats

        for lead in targets:
            old_status = lead.status
            lead.email = None
            stats["blocked_email_cleared"] += 1
            if old_status == LeadStatus.CONTACTED:
                lead.status = LeadStatus.DRAFT_READY
                lead.last_contacted = None
                stats["contacted_reset"] += 1
            elif old_status not in (
                LeadStatus.PENDING_EMAIL,
                LeadStatus.SKIPPED,
                LeadStatus.UNSUBSCRIBED,
            ):
                lead.status = LeadStatus.PENDING_EMAIL

        for lead in m06_leads:
            if lead.website and is_platform_url(lead.website):
                lead.website = None
                stats["website_cleared"] += 1
            data = dict(lead.enrichment_data or {})
            if _garbage_contact(data):
                for key in (
                    "contact_first_name",
                    "first_name",
                    "owner_first_name",
                    "contact_name",
                ):
                    data.pop(key, None)
                lead.enrichment_data = data
                stats["garbage_name_cleared"] += 1
            if lead.contact_name and _garbage_contact(
                {"contact_first_name": lead.contact_name}
            ):
                lead.contact_name = None
                stats["garbage_name_cleared"] += 1

        if reset_m06:
            now = datetime.now(timezone.utc)
            for lead in m06_leads:
                lead.soft_delete()
                stats["m06_soft_deleted"] += 1
            print(f"\nSoft-deleted {stats['m06_soft_deleted']} M06 lead(s) for re-scan.\n")

        await session.commit()
        print("\n[APPLY] Database updated.\n")

    return stats


async def cleanup_instantly(
    bad_email: str,
    *,
    apply: bool,
) -> None:
    settings = get_settings()
    client = InstantlyClient(
        settings.instantly_api_key, settings.instantly_campaign_id
    )
    if not client.is_configured:
        print("[Instantly] Not configured — skip.\n")
        return

    items = await client.list_campaign_leads(limit=100)
    matches = [
        x
        for x in items
        if (x.get("email") or "").strip().lower() == bad_email.strip().lower()
    ]
    if not matches:
        print(f"[Instantly] No lead '{bad_email}' in campaign (checked {len(items)}).\n")
        return

    print(f"\n=== Instantly campaign ({len(matches)} match) ===\n")
    for row in matches:
        print(f"  email={row.get('email')} id={row.get('id')} status={row.get('status')}")

    if not apply:
        print("\n[DRY RUN] Pass --apply --instantly-remove to delete from Instantly.\n")
        return

    async with httpx.AsyncClient(timeout=60.0) as http:
        for row in matches:
            lid = str(row.get("id") or "").strip()
            if not lid:
                logger.warning(f"[Instantly] No id for {row.get('email')} — delete in UI")
                continue
            resp = await http.delete(
                f"{client.V2_BASE}/leads/{lid}",
                headers=client._headers(),
            )
            if resp.status_code in (200, 204):
                logger.success(f"[Instantly] Deleted lead {lid} ({bad_email})")
            else:
                logger.error(
                    f"[Instantly] Delete {lid} failed {resp.status_code}: {resp.text[:300]}"
                )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--apply",
        action="store_true",
        help="Write DB changes (default is dry-run)",
    )
    p.add_argument(
        "--bad-email",
        default=DEFAULT_BAD_EMAIL,
        help=f"Email to clear from DB and Instantly (default: {DEFAULT_BAD_EMAIL})",
    )
    p.add_argument(
        "--reset-m06",
        action="store_true",
        help="Soft-delete all m06/* leads so memory bank allows re-processing",
    )
    p.add_argument(
        "--instantly-remove",
        action="store_true",
        help="With --apply, delete --bad-email from Instantly campaign",
    )
    return p.parse_args()


async def main() -> None:
    args = parse_args()
    await init_db()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\nAgent-Earns YouTube cleanup [{mode}]\n")

    stats = await cleanup_db(
        apply=args.apply,
        bad_email=args.bad_email,
        reset_m06=args.reset_m06,
    )

    if args.instantly_remove or args.bad_email:
        await cleanup_instantly(
            args.bad_email,
            apply=args.apply and args.instantly_remove,
        )

    print("Summary:")
    for k, v in stats.items():
        if v:
            print(f"  {k}: {v}")
    if not args.apply:
        print("\nRe-run with:  python scripts/cleanup_youtube_bad_leads.py --apply --reset-m06 --instantly-remove")


if __name__ == "__main__":
    asyncio.run(main())
