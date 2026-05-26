"""
Per-lead outbound mailbox lock — same From address for every email to that lead.

Example: first cold email from gaurav@gauravxd.dev → all replies/follow-ups use that mailbox.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from utils.domain_pool import DomainPool, OutreachDomain

LOCK_MAILBOX = "outbound_mailbox"
LOCK_DOMAIN = "outbound_domain_name"
LOCK_FIELDS = (LOCK_MAILBOX, LOCK_DOMAIN, "send_channel")


def merge_mailbox_lock_into(data: dict[str, Any], lead: Any) -> dict[str, Any]:
    """Copy lock fields from lead into a dict before DB save (avoids losing lock on partial updates)."""
    out = dict(data)
    src = getattr(lead, "enrichment_data", None) or {}
    for key in LOCK_FIELDS:
        val = src.get(key)
        if val:
            out[key] = val
    return out


def get_locked_mailbox(lead: Any) -> str:
    data = getattr(lead, "enrichment_data", None) or {}
    return str(data.get(LOCK_MAILBOX) or "").strip().lower()


def get_locked_domain_name(lead: Any) -> str:
    data = getattr(lead, "enrichment_data", None) or {}
    return str(data.get(LOCK_DOMAIN) or "").strip()


def lock_mailbox_on_lead(
    lead: Any,
    *,
    smtp_cfg: dict[str, Any] | None = None,
    domain: OutreachDomain | None = None,
    send_channel: str = "",
) -> None:
    """Persist which mailbox sent to this lead (call after first successful outbound)."""
    data = dict(getattr(lead, "enrichment_data", None) or {})
    from_email = ""
    if smtp_cfg:
        from_email = str(smtp_cfg.get("from_email") or "").strip().lower()
    if not from_email and domain:
        from_email = (domain.smtp_from_email or domain.smtp_user or "").strip().lower()

    if from_email:
        data[LOCK_MAILBOX] = from_email
    if domain:
        data[LOCK_DOMAIN] = domain.name
    if send_channel:
        data["send_channel"] = send_channel
    lead.enrichment_data = data
    if from_email:
        logger.info(
            f"[Mailbox] Locked {getattr(lead, 'email', '?') or lead.id[:8]} "
            f"→ {from_email}"
        )


def resolve_outreach_domain(
    lead: Any,
    pool: DomainPool,
    *,
    place_id: str = "",
) -> OutreachDomain | None:
    """
    Domain for this lead: locked name/email first, else stable pick by place_id.
    """
    if not pool.enabled:
        return None

    locked_name = get_locked_domain_name(lead)
    if locked_name:
        found = pool.get_by_name(locked_name)
        if found:
            return found
        logger.warning(
            f"[Mailbox] Locked domain '{locked_name}' missing from pool — re-picking"
        )

    locked_email = get_locked_mailbox(lead)
    if locked_email:
        found = pool.get_by_from_email(locked_email)
        if found:
            return found
        logger.warning(
            f"[Mailbox] Locked mailbox {locked_email} not in pool — using .env SMTP"
        )
        return None

    pid = place_id or getattr(lead, "place_id", None) or getattr(lead, "id", "") or ""
    return pool.pick(pid) if pid else pool.pick("default")


def resolve_smtp_config(
    lead: Any,
    settings: Any,
    pool: DomainPool,
    outreach_domain: OutreachDomain | None = None,
) -> dict[str, Any] | None:
    """
    SMTP config for this lead — always uses locked outbound_mailbox when set.
    """
    data = getattr(lead, "enrichment_data", None) or {}
    channel = str(data.get("send_channel") or "")
    if channel == "instantly":
        return None

    locked_email = get_locked_mailbox(lead)
    domain = outreach_domain or resolve_outreach_domain(lead, pool)

    if domain and domain.has_smtp():
        cfg = domain.get_smtp_config(
            getattr(settings, "your_name", "") or "Gaurav",
            settings=settings,
        )
        if locked_email:
            cfg = dict(cfg)
            cfg["from_email"] = locked_email
            cfg["reply_to"] = locked_email
        return cfg

    if not settings.has_smtp:
        return None

    cfg = dict(settings.get_smtp_config())
    if locked_email:
        cfg["from_email"] = locked_email
        cfg["reply_to"] = locked_email
    return cfg
