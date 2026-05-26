"""
Push Agent-Earns leads into an Instantly.ai campaign (your 2 mailboxes + warmup + limits).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from integrations.platforms.instantly import InstantlyClient
from modules.lead_finder.scanners.google_maps import MapsScanResult
from modules.outreach.icebreaker import generate_icebreaker, preset_icebreaker
from modules.outreach.mikey_sequence import build_sequence, lead_template_variables
from utils.spam_check import check_outreach_copy


def _split_name_from_business(business_name: str) -> tuple[str, str]:
    """Best-effort; many local leads are company-only."""
    parts = business_name.replace(",", " ").split()
    if len(parts) >= 2 and parts[0].lower() not in ("austin", "the", "mr", "dr"):
        return parts[0], " ".join(parts[1:3])
    return "there", business_name


def _lead_names(maps_lead: MapsScanResult) -> tuple[str, str]:
    raw = getattr(maps_lead, "raw", None) or {}
    first = (raw.get("first_name") or "").strip()
    last = (raw.get("last_name") or "").strip()
    if first:
        return first, last
    return _split_name_from_business(maps_lead.business_name)


async def lead_custom_variables_async(
    maps_lead: MapsScanResult,
    demo_url: str | None,
    your_name: str,
    llm: Any | None = None,
) -> dict[str, str]:
    from modules.outreach.icebreaker import generate_icebreaker

    ib = preset_icebreaker(maps_lead) or await generate_icebreaker(
        maps_lead, demo_url, llm=llm
    )
    seq = build_sequence(maps_lead, your_name, demo_url=demo_url, steps=4, icebreaker=ib)
    vars_ = lead_template_variables(maps_lead, ib, demo_url)
    vars_["phone"] = maps_lead.phone or ""
    for i, mail in enumerate(seq, start=1):
        vars_[f"subject_{i}"] = mail["subject"]
        vars_[f"subject_{i}a"] = mail["subject"]
        vars_[f"subject_{i}b"] = mail.get("subject_b", mail["subject"])
        vars_[f"body_{i}"] = mail["body"]
    vars_["subject"] = seq[0]["subject"]
    vars_["subject_a"] = seq[0]["subject"]
    vars_["subject_b"] = seq[0].get("subject_b", "")
    vars_["body"] = seq[0]["body"]
    vars_["body_1"] = seq[0]["body"]
    return vars_


def lead_custom_variables(
    maps_lead: MapsScanResult,
    demo_url: str | None,
    your_name: str,
) -> dict[str, str]:
    from modules.outreach.icebreaker import fallback_icebreaker

    ib = preset_icebreaker(maps_lead) or fallback_icebreaker(maps_lead, demo_url)
    seq = build_sequence(maps_lead, your_name, demo_url=demo_url, steps=4, icebreaker=ib)
    vars_ = lead_template_variables(maps_lead, ib, demo_url)
    vars_["phone"] = maps_lead.phone or ""
    for i, mail in enumerate(seq, start=1):
        vars_[f"subject_{i}"] = mail["subject"]
        vars_[f"subject_{i}a"] = mail["subject"]
        vars_[f"subject_{i}b"] = mail.get("subject_b", mail["subject"])
        vars_[f"body_{i}"] = mail["body"]
    vars_["subject"] = seq[0]["subject"]
    vars_["subject_a"] = seq[0]["subject"]
    vars_["subject_b"] = seq[0].get("subject_b", "")
    vars_["body"] = seq[0]["body"]
    vars_["body_1"] = seq[0]["body"]
    return vars_


def export_instantly_csv(
    rows: list[dict[str, str]],
    path: Path,
) -> Path:
    """Backup CSV for manual Instantly import if API fails."""
    import csv

    if not rows:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"[Instantly] CSV export: {path}")
    return path


class InstantlyPush:
    def __init__(self, settings: Any, llm: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm
        self._api_key = getattr(settings, "instantly_api_key", "") or ""
        self.client = InstantlyClient(
            api_key=getattr(settings, "instantly_api_key", "") or "",
            campaign_id=getattr(settings, "instantly_campaign_id", "") or "",
        )

    @property
    def is_configured(self) -> bool:
        return self.client.is_configured

    async def push_lead(
        self,
        maps_lead: MapsScanResult,
        demo_url: str | None,
        your_name: str,
        campaign_id: str | None = None,
    ) -> bool:
        if not maps_lead.email:
            logger.warning(f"[Instantly] No email for {maps_lead.business_name}")
            return False

        client = self.client
        if getattr(self.settings, "instantly_auto_prepare", True):
            await client.ensure_send_ready()
        cid = (campaign_id or "").strip()
        if cid and cid != self.client.campaign_id:
            client = InstantlyClient(self._api_key, cid)

        first, last = _lead_names(maps_lead)
        if self.llm:
            variables = await lead_custom_variables_async(
                maps_lead, demo_url, your_name, llm=self.llm
            )
        else:
            variables = lead_custom_variables(maps_lead, demo_url, your_name)

        body = variables.get("body_1") or variables.get("body", "")
        subject = variables.get("subject_1a") or variables.get("subject", "")
        ok, hits = check_outreach_copy(subject, body)
        if not ok:
            logger.warning(
                f"[Instantly] Spam phrases in copy for {maps_lead.email}: {', '.join(hits)}"
            )
            if getattr(self.settings, "strict_spam_check", False):
                return False

        result = await client.add_leads_bulk(
            [
                InstantlyClient._lead_payload(
                    maps_lead.email,
                    first,
                    last,
                    maps_lead.business_name,
                    variables,
                )
            ],
            skip_if_in_workspace=False,
            skip_if_in_campaign=False,
        )
        if not result.ok and result.skipped_count:
            logger.info(
                f"[Instantly] Tip: {maps_lead.email} may exist in another campaign. "
                "Check Instantly → Leads or move them to Agent-Earns in the UI."
            )
        return result.ok

    def append_csv_row(
        self,
        maps_lead: MapsScanResult,
        demo_url: str | None,
        your_name: str,
    ) -> dict[str, str]:
        variables = lead_custom_variables(maps_lead, demo_url, your_name)
        first, last = _lead_names(maps_lead)
        row = {
            "email": maps_lead.email or "",
            "first_name": first,
            "last_name": last,
            "company_name": maps_lead.business_name,
            **variables,
        }
        return row
