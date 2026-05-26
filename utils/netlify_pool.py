"""
Rotate across multiple Netlify sites — skip teams with low credits (50 credit reserve).

Primary from .env; optional data/netlify_accounts.json when NETLIFY_ENV_ONLY=false.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from utils.netlify_credits import NetlifyCreditStatus, fetch_credit_status


@dataclass
class NetlifyAccount:
    name: str
    auth_token: str
    site_id: str
    demo_base_url: str
    disabled: bool = False
    min_credits_remaining: int = 0
    credit_status: NetlifyCreditStatus | None = field(default=None, repr=False)

    def is_ready(self) -> bool:
        return bool(self.auth_token and self.site_id and self.demo_base_url)


class NetlifyAccountPool:
    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.accounts: list[NetlifyAccount] = self._load()
        self._refresh_credit_statuses()

    def _primary(self) -> NetlifyAccount | None:
        token = str(getattr(self.settings, "netlify_auth_token", "") or "").strip()
        site = str(getattr(self.settings, "netlify_site_id", "") or "").strip()
        base = str(getattr(self.settings, "demo_site_base_url", "") or "").strip()
        if token and site and base:
            force = bool(getattr(self.settings, "netlify_skip_primary", False))
            return NetlifyAccount(
                name="env-primary",
                auth_token=token,
                site_id=site,
                demo_base_url=base.rstrip("/"),
                disabled=force,
            )
        return None

    def _load(self) -> list[NetlifyAccount]:
        accounts: list[NetlifyAccount] = []
        primary = self._primary()
        if primary:
            accounts.append(primary)

        env_only = bool(getattr(self.settings, "netlify_env_only", True))
        if env_only:
            if accounts:
                logger.info("[NetlifyPool] env-only: .env primary (+ credit filter)")
            return accounts

        path = str(getattr(self.settings, "netlify_accounts_file", "") or "").strip()
        if not path:
            return accounts

        file_path = Path(path)
        if not file_path.is_file():
            return accounts

        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"[NetlifyPool] Invalid JSON in {file_path}: {e}")
            return accounts

        items = raw if isinstance(raw, list) else raw.get("accounts", [])
        seen_sites: set[str] = {a.site_id for a in accounts}
        for row in items:
            if not isinstance(row, dict):
                continue
            token = str(row.get("auth_token") or "").strip()
            site = str(row.get("site_id") or "").strip()
            base = str(row.get("demo_base_url") or "").strip().rstrip("/")
            if not token or not site or not base:
                continue
            if site in seen_sites:
                continue
            seen_sites.add(site)
            accounts.append(
                NetlifyAccount(
                    name=str(row.get("name") or site[:8]),
                    auth_token=token,
                    site_id=site,
                    demo_base_url=base,
                    disabled=bool(row.get("disabled") or row.get("skip")),
                    min_credits_remaining=int(row.get("min_credits_remaining") or 0),
                )
            )

        logger.info(
            f"[NetlifyPool] {len(accounts)} account(s): {[a.name for a in accounts]}"
        )
        return accounts

    def _refresh_credit_statuses(self) -> None:
        min_default = int(
            getattr(self.settings, "netlify_credits_min_remaining", 50) or 50
        )
        for acct in self.accounts:
            override = acct.min_credits_remaining or None
            acct.credit_status = fetch_credit_status(
                acct.auth_token,
                pool_name=acct.name,
                settings=self.settings,
                min_remaining_override=override,
                force_disabled=acct.disabled,
            )
            st = acct.credit_status
            if st.usable:
                logger.info(
                    f"[NetlifyPool] {acct.name} ({st.team_name}): {st.reason}"
                )
            else:
                logger.warning(
                    f"[NetlifyPool] SKIP {acct.name}: {st.reason}"
                )

    def usable_accounts(self, *, refresh: bool = False) -> list[NetlifyAccount]:
        if refresh:
            self._refresh_credit_statuses()
        return [
            a
            for a in self.accounts
            if a.is_ready() and a.credit_status and a.credit_status.usable
        ]

    @property
    def enabled(self) -> bool:
        return len(self.usable_accounts()) > 0

    def pick(self, slug: str) -> NetlifyAccount | None:
        usable = self.usable_accounts()
        if not usable:
            return None
        digest = hashlib.sha256(slug.encode("utf-8")).hexdigest()
        idx = int(digest[:8], 16) % len(usable)
        return usable[idx]

    def ordered_for_fallback(self, slug: str) -> list[NetlifyAccount]:
        usable = self.usable_accounts()
        if not usable:
            return []
        first = self.pick(slug)
        if not first:
            return list(usable)
        rest = [a for a in usable if a.site_id != first.site_id]
        return [first, *rest]

    def shuffled(self) -> list[NetlifyAccount]:
        order = list(self.usable_accounts())
        random.shuffle(order)
        return order
