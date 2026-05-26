"""
Recommended Instantly campaign settings for Agent-Earns (Mikey sequence + deliverability).
"""

from __future__ import annotations

import copy
from typing import Any

# Instantly days: 0=Sunday … 6=Saturday
WEEKDAYS_US = {
    "0": False,
    "1": True,
    "2": True,
    "3": True,
    "4": True,
    "5": True,
    "6": False,
}


def agent_earns_campaign_patch(
    current: dict[str, Any] | None = None,
    *,
    timezone: str = "America/Detroit",
    daily_limit: int = 10,
) -> dict[str, Any]:
    """
    Build PATCH body aligned with docs/INSTANTLY_CAMPAIGN_SETUP.md.
    Preserves existing sequences but fixes delays and plain-text bodies.
    """
    sequences = _normalize_sequences(
        copy.deepcopy((current or {}).get("sequences"))
    )

    patch: dict[str, Any] = {
        "daily_limit": daily_limit,
        "daily_max_leads": daily_limit,
        "email_gap": 2,
        "random_wait_max": 2,
        "stop_on_reply": True,
        "stop_on_auto_reply": True,
        "open_tracking": False,
        "link_tracking": False,
        "text_only": True,
        "first_email_text_only": True,
        "prioritize_new_leads": False,
        "insert_unsubscribe_header": True,
        "campaign_schedule": {
            "start_date": None,
            "end_date": None,
            "schedules": [
                {
                    "name": "Weekdays (Agent-Earns)",
                    "timing": {"from": "09:00", "to": "17:00"},
                    "days": dict(WEEKDAYS_US),
                    "timezone": timezone,
                }
            ],
        },
    }
    if sequences:
        patch["sequences"] = sequences
    return patch


def _normalize_sequences(sequences: list[Any] | None) -> list[Any] | None:
    if not sequences:
        return None
    out = copy.deepcopy(sequences)
    steps = out[0].get("steps") if out else None
    if not steps:
        return out

    # Step 2 → wait 2 days; step 3 → wait 3 days (Mikey doc)
    if len(steps) >= 2:
        steps[1]["delay"] = 2
        steps[1]["delay_unit"] = "days"
    if len(steps) >= 3:
        steps[2]["delay"] = 3
        steps[2]["delay_unit"] = "days"

    plain = {"body_1": "{{body_1}}", "body_2": "{{body_2}}", "body_3": "{{body_3}}"}
    for step in steps:
        for variant in step.get("variants") or []:
            body = str(variant.get("body") or "")
            for key, tpl in plain.items():
                if key in body:
                    variant["body"] = tpl
                    break
    return out
