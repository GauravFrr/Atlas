"""Pending close-email approvals (Telegram inline buttons)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

INDEX_PATH = Path("data/close_approval_index.json")


def _load_index() -> dict[str, str]:
    if not INDEX_PATH.is_file():
        return {}
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_index(data: dict[str, str]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def new_approval_id() -> str:
    return uuid.uuid4().hex[:8]


def register(approval_id: str, lead_id: str) -> None:
    data = _load_index()
    data[approval_id] = lead_id
    _save_index(data)


def resolve(approval_id: str) -> str | None:
    return _load_index().get(approval_id)


def unregister(approval_id: str) -> None:
    data = _load_index()
    if approval_id in data:
        del data[approval_id]
        _save_index(data)


def build_approval_payload(
    *,
    approval_id: str,
    lead_id: str,
    subject: str,
    body: str,
    classification: str,
    payment_url: str = "",
    draft_path: str = "",
) -> dict[str, Any]:
    return {
        "id": approval_id,
        "lead_id": lead_id,
        "subject": subject,
        "body": body,
        "classification": classification,
        "payment_url": payment_url,
        "draft_path": draft_path,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "telegram_message_id": None,
    }


def extract_payment_url(body: str) -> str:
    for line in body.splitlines():
        if "rzp.io" in line or "razorpay" in line.lower():
            for part in line.split():
                if part.startswith("http"):
                    return part.strip()
    return ""
