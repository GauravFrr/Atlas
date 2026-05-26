"""
Method 17 — Cold Email Core
TARGET: Local businesses, SaaS, agencies
EARN: Variable (selling websites, lead gen, etc.)
LOGIC: Draft hyper-personalized plain-text emails using LLM and send via SMTP.
"""

from __future__ import annotations

import re
from pathlib import Path
from loguru import logger
from typing import Any

# Import MapsScanResult to type hint our lead source
from modules.lead_finder.scanners.google_maps import MapsScanResult
from modules.outreach.icebreaker import generate_icebreaker
from modules.outreach.mikey_sequence import build_email_1, build_sequence_async
from modules.outreach.smtp_delivery import send_via_smtp


def format_email_body(body: str) -> str:
    """
    Add blank lines between beats only when the body is one dense paragraph.

    If the text already has line breaks (Gaurav templates), return unchanged.
    Otherwise split only on completed sentences (. ! ?) — never on em-dashes or commas.
    """
    text = body.strip()
    if not text:
        return text

    # Author already chose line breaks — do not re-split
    if "\n" in text:
        return text

    signoff = ""
    if re.search(r'^[—\-–]', text, re.MULTILINE):
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if lines and re.match(r'^[—\-–]', lines[-1]):
            signoff = lines[-1]
            text = " ".join(lines[:-1]).strip()

    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', text) if p.strip()]
    if not parts:
        return text

    formatted = "\n\n".join(parts)
    if signoff:
        formatted = f"{formatted}\n\n{signoff}"
    return formatted


class ColdEmailEngine:
    """
    Engine for drafting and sending personalized outreach emails.
    Supports basic SMTP (Gmail, Outlook, Custom Domains).
    Recommended: No tracking pixels to ensure high deliverability (bypass spam filters).
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def draft_pitch(
        self,
        lead: MapsScanResult,
        your_name: str,
        your_business: str,
        demo_url: str | None = None,
        use_llm: bool = False,
    ) -> dict[str, str]:
        """
        Mikey strategy: icebreaker + Email 1 (Day 1). LLM improves icebreaker when available.
        """
        logger.info(f"[M17] Drafting pitch for {lead.business_name} (Mikey sequence)...")

        from modules.outreach.website_pitch import cache_pitch_on_lead, ensure_website_audit
        from utils.contact_greeting import ensure_contact_name

        await ensure_website_audit(lead, self.settings)
        await ensure_contact_name(lead, self.settings)
        plan = cache_pitch_on_lead(lead)
        logger.info(
            f"[M17] {lead.business_name}: service={plan.service.value} "
            f"tier={plan.tier.value} — {plan.service_label}"
        )

        if not demo_url and lead.demo_site_path and getattr(
            self.settings, "demo_site_base_url", None
        ):
            base = str(self.settings.demo_site_base_url).rstrip("/")
            slug = Path(lead.demo_site_path).stem
            demo_url = f"{base}/{slug}/index.html"

        sender = your_name.strip() or "Gaurav"
        from modules.outreach.icebreaker import preset_icebreaker

        icebreaker = preset_icebreaker(lead) or await generate_icebreaker(
            lead, demo_url, llm=self.llm
        )
        draft = build_email_1(
            lead, icebreaker, demo_url=demo_url, sender_name=sender
        )
        return draft

    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        smtp_config: dict[str, Any] | None = None,
        dry_run: bool = True
    ) -> bool:
        """
        Sends an email via SMTP or simulates sending in dry_run mode.
        smtp_config should contain: host, port, user, password.
        """
        if dry_run:
            logger.info(f"[M17] Local copy for: {to_email}")
            logger.info(f"[M17] Subject: {subject}")
            
            out_dir = Path("outputs/emails")
            out_dir.mkdir(parents=True, exist_ok=True)
            
            safe_name = "".join(c if c.isalnum() else "_" for c in to_email.split("@")[0]).lower()
            file_path = out_dir / f"draft_{safe_name}.txt"
            
            # Never re-split templates; format_email_body only fixes dense LLM paragraphs
            if "\n" not in body.strip():
                body = format_email_body(body)
            content = f"TO: {to_email}\nSUBJECT: {subject}\n\n{body}"
            file_path.write_text(content, encoding="utf-8")
            logger.success(f"[M17] Saved draft to {file_path}")
            return True

        if not smtp_config:
            logger.error("[M17] Cannot send email: No SMTP config provided.")
            return False

        cfg = dict(smtp_config)
        if "bcc_self" not in cfg:
            cfg["bcc_self"] = getattr(self.settings, "smtp_bcc_self", True)
        if "save_to_sent" not in cfg:
            cfg["save_to_sent"] = getattr(self.settings, "smtp_save_to_sent", True)
        if "provider" not in cfg:
            cfg["provider"] = getattr(self.settings, "smtp_provider", "")

        ok = send_via_smtp(
            to_email=to_email,
            subject=subject,
            body=body,
            smtp_config=cfg,
            provider=str(cfg.get("provider", "")),
        )
        if ok:
            logger.success(f"[M17] Successfully sent email to {to_email}")
        return ok
