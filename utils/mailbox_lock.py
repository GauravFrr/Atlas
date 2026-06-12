"""
Per-lead outbound mailbox lock — same From address for every email to that lead.

Example: cold via Instantly from gaurav@gauravxd.dev → close reply + payment from that mailbox.
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


def extract_instantly_our_mailbox(payload: dict[str, Any]) -> str:
    """
    Which of *our* addresses the lead replied to (Instantly Unibox / webhook).
    Ground truth for close + payment SMTP — not the demo-domain pool pick.
    """
    if not payload:
        return ""

    def _pick(val: Any) -> str:
        if val and "@" in str(val):
            return str(val).strip().lower()
        return ""

    for key in (
        "to_address_email",
        "to_email",
        "account_email",
        "sending_account_email",
        "eaccount_email",
        "from_email_account",
    ):
        found = _pick(payload.get(key))
        if found:
            return found

    for nest_key in ("email", "message", "data"):
        nest = payload.get(nest_key)
        if isinstance(nest, dict):
            for key in ("to_address_email", "to_email", "account_email"):
                found = _pick(nest.get(key))
                if found:
                    return found

    return ""


def lock_mailbox_on_lead(
    lead: Any,
    *,
    smtp_cfg: dict[str, Any] | None = None,
    domain: OutreachDomain | None = None,
    send_channel: str = "",
    from_email: str = "",
) -> None:
    """Persist which mailbox owns this lead thread."""
    data = dict(getattr(lead, "enrichment_data", None) or {})
    resolved_from = (from_email or "").strip().lower()
    if not resolved_from and smtp_cfg:
        resolved_from = str(smtp_cfg.get("from_email") or "").strip().lower()
    if not resolved_from and domain:
        resolved_from = (domain.smtp_from_email or domain.smtp_user or "").strip().lower()

    # Instantly cold send: do not guess mailbox from demo-domain rotation.
    if send_channel == "instantly" and not resolved_from:
        if domain:
            data[LOCK_DOMAIN] = domain.name
        data["send_channel"] = "instantly"
        lead.enrichment_data = data
        logger.debug(
            f"[Mailbox] Instantly lead {getattr(lead, 'business_name', '?')} "
            f"— demo domain {domain.name if domain else '?'}; mailbox locks on reply"
        )
        return

    if resolved_from:
        data[LOCK_MAILBOX] = resolved_from
    if domain:
        data[LOCK_DOMAIN] = domain.name
    if send_channel:
        data["send_channel"] = send_channel
    lead.enrichment_data = data

    if resolved_from:
        logger.info(
            f"[Mailbox] Locked {getattr(lead, 'email', '?') or getattr(lead, 'id', '')[:8]} "
            f"→ {resolved_from}"
        )


def lock_mailbox_from_instantly(
    lead: Any,
    our_mailbox: str,
    settings: Any,
) -> None:
    """Lock from Instantly reply/webhook — the address the lead actually replied to."""
    email = (our_mailbox or "").strip().lower()
    if not email or "@" not in email:
        return
    pool = DomainPool(settings)
    domain = pool.get_by_from_email(email)
    if not domain:
        logger.warning(
            f"[Mailbox] Reply to {email} not in outreach_domains.json — "
            f"add that mailbox or run lock_lead_mailbox.py"
        )
    lock_mailbox_on_lead(
        lead,
        from_email=email,
        domain=domain,
        send_channel="instantly",
    )


def resolve_outreach_domain(
    lead: Any,
    pool: DomainPool,
    *,
    place_id: str = "",
) -> OutreachDomain | None:
    """
    Domain for demo URL / Instantly campaign hint: locked name first, else stable pick.
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
            f"[Mailbox] Locked mailbox {locked_email} not in pool — demo pick by place_id"
        )

    pid = place_id or getattr(lead, "place_id", None) or getattr(lead, "id", "") or ""
    return pool.pick(pid) if pid else pool.pick("default")


def resolve_smtp_config(
    lead: Any,
    settings: Any,
    pool: DomainPool,
    outreach_domain: OutreachDomain | None = None,
    *,
    for_close_reply: bool = False,
) -> dict[str, Any] | None:
    """
    SMTP for Telegram-approved close / payment emails.

    Always uses locked outbound_mailbox + matching Hostinger login from outreach_domains.json.
    Never sends payment from urmikexd if the thread was gaurav@gauravxd.dev.
    """
    data = getattr(lead, "enrichment_data", None) or {}
    channel = str(data.get("send_channel") or "")
    if channel == "instantly" and not for_close_reply:
        return None

    locked_email = get_locked_mailbox(lead)
    domain: OutreachDomain | None = None

    if locked_email:
        domain = pool.get_by_from_email(locked_email)
        if not domain:
            logger.error(
                f"[Mailbox] Cannot send close email — locked {locked_email} "
                f"not in {getattr(settings, 'outreach_domains_file', 'outreach_domains.json')}"
            )
            return None
    else:
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
