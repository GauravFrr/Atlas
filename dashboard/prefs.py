"""Dashboard-editable preferences (merged at runtime, does not replace .env secrets)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PREFS_PATH = Path("data/dashboard_prefs.json")

DEFAULTS: dict[str, Any] = {
    "your_name": "Gaurav",
    "autopilot_enabled": True,
    "leads_per_run": 10,
    "send_mode": "instantly",
    "demo_site_base_url": "",
    "reply_sync_interval_minutes": 15,
    "instantly_daily_limit": 20,
    "safe_demo": True,
}


def load_prefs() -> dict[str, Any]:
    out = dict(DEFAULTS)
    if PREFS_PATH.is_file():
        try:
            out.update(json.loads(PREFS_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def save_prefs(updates: dict[str, Any]) -> dict[str, Any]:
    current = load_prefs()
    allowed = set(DEFAULTS.keys())
    for key, val in updates.items():
        if key in allowed:
            current[key] = val
    PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREFS_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current
