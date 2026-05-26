"""
Netlify credit-based plan checks (300/month, keep 50 reserve, 15 per production deploy).

GET https://api.netlify.com/api/v1/accounts → capabilities.credits { included, used }
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
from loguru import logger

API = "https://api.netlify.com/api/v1"
# Production deploy ≈ 15 credits (Netlify docs)
DEFAULT_DEPLOY_COST = 15


@dataclass
class NetlifyCreditStatus:
    account_name: str
    team_name: str
    included: int
    used: int
    remaining: int
    usable: bool
    reason: str


_cache: dict[str, tuple[float, NetlifyCreditStatus]] = {}
_CACHE_TTL_SEC = 300


def _min_remaining(settings: Any, override: int | None = None) -> int:
    if override is not None and override > 0:
        return override
    reserve = int(getattr(settings, "netlify_credits_reserve", 50) or 50)
    floor = int(getattr(settings, "netlify_credits_min_remaining", 50) or 50)
    return max(reserve, floor)


def _deploy_cost(settings: Any) -> int:
    return int(getattr(settings, "netlify_deploy_credit_cost", DEFAULT_DEPLOY_COST) or DEFAULT_DEPLOY_COST)


def fetch_credit_status(
    auth_token: str,
    *,
    pool_name: str = "netlify",
    settings: Any | None = None,
    min_remaining_override: int | None = None,
    force_disabled: bool = False,
    use_cache: bool = True,
) -> NetlifyCreditStatus:
    """Read team credit balance for this personal access token."""
    settings = settings or object()
    cache_key = auth_token[-12:]
    if use_cache and cache_key in _cache:
        ts, status = _cache[cache_key]
        if time.time() - ts < _CACHE_TTL_SEC:
            return status

    min_need = _min_remaining(settings, min_remaining_override)
    deploy_cost = _deploy_cost(settings)

    if force_disabled:
        status = NetlifyCreditStatus(
            account_name=pool_name,
            team_name="",
            included=0,
            used=0,
            remaining=0,
            usable=False,
            reason="disabled in config (manual skip)",
        )
        _cache[cache_key] = (time.time(), status)
        return status

    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.get(
                API + "/accounts",
                headers={"Authorization": f"Bearer {auth_token.strip()}"},
            )
        if resp.status_code == 401:
            status = NetlifyCreditStatus(
                account_name=pool_name,
                team_name="",
                included=0,
                used=0,
                remaining=0,
                usable=False,
                reason="token invalid (401)",
            )
            _cache[cache_key] = (time.time(), status)
            return status
        if resp.status_code != 200:
            status = NetlifyCreditStatus(
                account_name=pool_name,
                team_name="",
                included=0,
                used=0,
                remaining=0,
                usable=False,
                reason=f"credits API {resp.status_code}",
            )
            _cache[cache_key] = (time.time(), status)
            return status

        teams = resp.json()
        if not teams:
            status = NetlifyCreditStatus(
                account_name=pool_name,
                team_name="",
                included=0,
                used=0,
                remaining=0,
                usable=False,
                reason="no Netlify team on token",
            )
            _cache[cache_key] = (time.time(), status)
            return status

        team = teams[0]
        team_name = str(team.get("name") or "")
        caps = team.get("capabilities") or {}
        credits = caps.get("credits") or {}
        included = int(credits.get("included") or 0)
        used = int(credits.get("used") or 0)
        remaining = max(0, included - used)

        block_exceeded = bool(
            (caps.get("block_builds_when_usage_exceeded") or {}).get("included")
        )

        if remaining <= min_need:
            reason = (
                f"only {remaining} credits left (need >{min_need} reserve; "
                f"{used}/{included} used)"
            )
            usable = False
        elif remaining < deploy_cost + min_need:
            reason = (
                f"{remaining} left — not enough for deploy (~{deploy_cost}) "
                f"and {min_need} reserve"
            )
            usable = False
        elif block_exceeded and remaining <= min_need + 10:
            reason = f"usage blocked on team (remaining {remaining})"
            usable = False
        else:
            reason = f"OK ({remaining} left, {used}/{included} used)"
            usable = True

        status = NetlifyCreditStatus(
            account_name=pool_name,
            team_name=team_name,
            included=included,
            used=used,
            remaining=remaining,
            usable=usable,
            reason=reason,
        )
        _cache[cache_key] = (time.time(), status)
        return status
    except Exception as e:
        status = NetlifyCreditStatus(
            account_name=pool_name,
            team_name="",
            included=0,
            used=0,
            remaining=0,
            usable=False,
            reason=f"credits check failed: {e}",
        )
        _cache[cache_key] = (time.time(), status)
        return status


def invalidate_cache(auth_token: str) -> None:
    _cache.pop(auth_token[-12:], None)
