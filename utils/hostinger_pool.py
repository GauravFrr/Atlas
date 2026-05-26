"""
Hostinger FTP demo sites (subdomains on your Hostinger account).

Shared FTP login from .env; each row is a subdomain document root.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


def _strip_ftp_host(value: str) -> str:
    v = value.strip()
    for prefix in ("ftp://", "http://", "https://"):
        if v.lower().startswith(prefix):
            v = v[len(prefix) :]
    return v.rstrip("/")


@dataclass
class HostingerDemoSite:
    name: str
    demo_base_url: str
    ftp_remote_base: str
    ftp_host: str = ""
    ftp_user: str = ""

    def resolved_host(self, settings: Any) -> str:
        return _strip_ftp_host(self.ftp_host or getattr(settings, "ftp_host", "") or "")

    def resolved_user(self, settings: Any) -> str:
        return (self.ftp_user or getattr(settings, "ftp_user", "") or "").strip()


class HostingerDemoPool:
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.sites = self._load()

    def _load(self) -> list[HostingerDemoSite]:
        path = str(getattr(self.settings, "hostinger_sites_file", "") or "").strip()
        if not path:
            return self._legacy_single_site()

        file_path = Path(path)
        if not file_path.is_file():
            return self._legacy_single_site()

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"[HostingerPool] Invalid JSON in {file_path}: {e}")
            return self._legacy_single_site()

        items = raw if isinstance(raw, list) else raw.get("sites", [])
        sites: list[HostingerDemoSite] = []
        for row in items:
            if not isinstance(row, dict):
                continue
            base = str(row.get("demo_base_url") or "").strip().rstrip("/")
            remote = str(row.get("ftp_remote_base") or "").strip().strip("/")
            user = str(row.get("ftp_user") or "").strip()
            if not base:
                continue
            if not user and not getattr(self.settings, "ftp_user", ""):
                continue
            sites.append(
                HostingerDemoSite(
                    name=str(row.get("name") or base),
                    demo_base_url=base,
                    ftp_remote_base=remote,
                    ftp_host=_strip_ftp_host(str(row.get("ftp_host") or "")),
                    ftp_user=str(row.get("ftp_user") or "").strip(),
                )
            )
        if sites:
            logger.info(
                f"[HostingerPool] {len(sites)} site(s): "
                f"{[s.name for s in sites]}"
            )
        return sites or self._legacy_single_site()

    def _legacy_single_site(self) -> list[HostingerDemoSite]:
        host = str(getattr(self.settings, "ftp_host", "") or "").strip()
        user = str(getattr(self.settings, "ftp_user", "") or "").strip()
        password = str(getattr(self.settings, "ftp_password", "") or "").strip()
        base = str(getattr(self.settings, "demo_site_base_url", "") or "").strip().rstrip(
            "/"
        )
        remote = str(getattr(self.settings, "ftp_remote_base", "") or "").strip().strip(
            "/"
        )
        if host and user and password and base and remote:
            return [
                HostingerDemoSite(
                    name="env-ftp",
                    demo_base_url=base,
                    ftp_remote_base=remote,
                )
            ]
        return []

    @property
    def enabled(self) -> bool:
        if not self.sites or not getattr(self.settings, "ftp_password", ""):
            return False
        return any(
            s.resolved_host(self.settings) and s.resolved_user(self.settings)
            for s in self.sites
        )
