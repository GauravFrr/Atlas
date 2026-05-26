"""
Rotate outreach across multiple domains (Hostinger mailboxes + demo URLs).

Picks are stable per lead (same place_id → same domain every time).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class OutreachDomain:
    name: str
    demo_base_url: str
    smtp_host: str = "smtp.hostinger.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = ""
    smtp_use_ssl: bool = False
    instantly_campaign_id: str = ""

    def has_smtp(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def get_smtp_config(
        self, fallback_name: str, settings: Any | None = None
    ) -> dict[str, str | int | bool]:
        from_email = (self.smtp_from_email or self.smtp_user).strip()
        cfg: dict[str, str | int | bool] = {
            "host": self.smtp_host,
            "port": self.smtp_port,
            "user": self.smtp_user,
            "password": self.smtp_password,
            "from_email": from_email,
            "from_name": (self.smtp_from_name or fallback_name).strip(),
            "reply_to": from_email,
            "use_ssl": self.smtp_use_ssl,
        }
        if settings is not None:
            cfg["bcc_self"] = bool(getattr(settings, "smtp_bcc_self", True))
            cfg["save_to_sent"] = bool(getattr(settings, "smtp_save_to_sent", True))
            cfg["imap_host"] = str(getattr(settings, "smtp_imap_host", "") or "")
            cfg["provider"] = str(getattr(settings, "smtp_provider", "") or "")
        return cfg


class DomainPool:
    """Load multiple domains from JSON; pick one per lead."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.domains: list[OutreachDomain] = self._load()

    def _load(self) -> list[OutreachDomain]:
        path = getattr(self.settings, "outreach_domains_file", "") or ""
        if not path:
            return []

        file_path = Path(path)
        if not file_path.is_file():
            logger.debug(f"[DomainPool] No file at {file_path}")
            return []

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"[DomainPool] Invalid JSON in {file_path}: {e}")
            return []

        items = raw if isinstance(raw, list) else raw.get("domains", [])
        domains: list[OutreachDomain] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            base = (row.get("demo_base_url") or "").strip()
            if not base:
                continue
            pwd = str(row.get("smtp_password") or "").strip()
            if pwd in ("", "$SMTP_PASSWORD", "${SMTP_PASSWORD}"):
                pwd = str(getattr(self.settings, "smtp_password", "") or "").strip()
            domains.append(
                OutreachDomain(
                    name=str(row.get("name") or base),
                    demo_base_url=base.rstrip("/"),
                    smtp_host=str(row.get("smtp_host") or "smtp.hostinger.com"),
                    smtp_port=int(row.get("smtp_port") or 587),
                    smtp_user=str(row.get("smtp_user") or ""),
                    smtp_password=pwd,
                    smtp_from_email=str(row.get("smtp_from_email") or ""),
                    smtp_from_name=str(row.get("smtp_from_name") or ""),
                    smtp_use_ssl=bool(row.get("smtp_use_ssl", False)),
                    instantly_campaign_id=str(row.get("instantly_campaign_id") or ""),
                )
            )
        logger.info(f"[DomainPool] Loaded {len(domains)} domain(s): {[d.name for d in domains]}")
        return domains

    @property
    def enabled(self) -> bool:
        return len(self.domains) > 0

    def get_by_name(self, name: str) -> OutreachDomain | None:
        name = (name or "").strip()
        for d in self.domains:
            if d.name == name:
                return d
        return None

    def get_by_from_email(self, email: str) -> OutreachDomain | None:
        email = (email or "").strip().lower()
        if not email:
            return None
        for d in self.domains:
            fe = (d.smtp_from_email or d.smtp_user or "").strip().lower()
            if fe == email:
                return d
        return None

    def pick(self, place_id: str) -> OutreachDomain | None:
        if not self.domains:
            return None
        digest = hashlib.sha256(place_id.encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % len(self.domains)
        chosen = self.domains[idx]
        logger.info(
            f"[DomainPool] {place_id[:20]}... → {chosen.name} ({chosen.smtp_from_email or chosen.smtp_user})"
        )
        return chosen
