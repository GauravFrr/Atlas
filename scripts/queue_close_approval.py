"""
Queue a close-email Telegram approval (test without a real reply).

  .\\venv\\Scripts\\python.exe scripts/queue_close_approval.py --email itzmi3xel@gmail.com
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.venv_guard import check_telegram_import, ensure_project_venv

ensure_project_venv()
check_telegram_import()

from config import get_settings
from database.connection import get_session_factory, init_db
from database.repositories.lead_repository import LeadRepository
from modules.outreach.close_approval import CloseApprovalService
from utils.telegram_approval import TelegramApprovalNotifier, store_telegram_message_id


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--classification", default="interested")
    p.add_argument(
        "--reply",
        default="",
        help='Simulate their reply to pick script (e.g. "how much does it cost")',
    )
    p.add_argument(
        "--payment-only",
        action="store_true",
        help="Queue payment-link email only (after they agreed)",
    )
    args = p.parse_args()

    settings = get_settings()
    if not settings.has_telegram:
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        sys.exit(1)

    await init_db()
    factory = get_session_factory()
    async with factory() as session:
        lead = await LeadRepository().get_by_email(session, args.email.strip())
        if not lead:
            print(f"No lead for {args.email}")
            sys.exit(1)
        if args.reply.strip():
            data = dict(lead.enrichment_data or {})
            pitch_sub = (lead.pitch_subject or "quick question").strip()
            data["last_reply"] = {
                "classification": args.classification,
                "subject": pitch_sub,
                "snippet": args.reply.strip(),
            }
            lead.enrichment_data = data
            await session.commit()
            print(f"Simulated reply: {args.reply.strip()!r}")

    svc = CloseApprovalService(settings)
    if args.payment_only:
        queued = await svc.queue_payment_for_approval(lead.id)
        if not queued.get("ok"):
            print(f"Failed: {queued}")
            sys.exit(1)
        aid = queued.get("approval_id", "")
        payload = queued.get("payload") or {}
        draft = {
            "subject": payload.get("subject", ""),
            "body": payload.get("body", ""),
        }
        kind = "payment_link"
    else:
        draft = await svc.build_close_draft(
            lead,
            args.classification,
            reply_subject=str((lead.enrichment_data or {}).get("last_reply", {}).get("subject") or ""),
            reply_body=str((lead.enrichment_data or {}).get("last_reply", {}).get("snippet") or args.reply or ""),
        )
        path = Path("outputs/emails/replies") / f"reply_draft_test_{lead.id[:8]}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"To: {lead.email}\nSubject: {draft['subject']}\n\n{draft['body']}",
            encoding="utf-8",
        )
        queued = await svc.queue_for_approval(
            lead=lead,
            draft=draft,
            classification=args.classification,
            draft_path=str(path),
        )
        aid = queued.get("approval_id", "")
        kind = "interested_reply"
    tg = TelegramApprovalNotifier(settings)
    msg_id = await tg.send_approval_request(
        approval_id=aid,
        business_name=lead.business_name,
        email=lead.email or "",
        classification=args.classification if not args.payment_only else "payment_link",
        subject=str(draft.get("subject", "")),
        body=str(draft.get("body", "")),
        kind=kind,
        script_label=str(draft.get("script_label") or ""),
    )
    if msg_id and aid:
        await store_telegram_message_id(settings, aid, msg_id)
    print(f"Queued approval_id={aid} — open Telegram and tap Approve (bot must be running).")


if __name__ == "__main__":
    asyncio.run(main())
