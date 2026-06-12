"""
Instantly.ai — push leads + variables into your warmed campaign (2 mailboxes, limits, warmup).
API: https://developer.instantly.ai/
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import httpx
from loguru import logger

# Instantly campaign.status (observed): 1=active, 2=paused
CAMPAIGN_STATUS_ACTIVE = 1
# Account status / warmup_status: 1=active/on, other values = paused or off
ACCOUNT_STATUS_ACTIVE = 1
WARMUP_STATUS_ACTIVE = 1


@dataclass
class AddLeadsResult:
    ok: bool
    leads_uploaded: int = 0
    skipped_count: int = 0
    invalid_email_count: int = 0
    raw: dict[str, Any] | None = None
    error: str = ""


class InstantlyClient:
    V2_BASE = "https://api.instantly.ai/api/v2"

    def __init__(self, api_key: str, campaign_id: str) -> None:
        self.api_key = api_key.strip()
        self.campaign_id = campaign_id.strip()
        self._prepare_done = False

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.campaign_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def add_lead(
        self,
        email: str,
        *,
        first_name: str = "",
        last_name: str = "",
        company_name: str = "",
        custom_variables: dict[str, str] | None = None,
        skip_if_in_workspace: bool = False,
        skip_if_in_campaign: bool = False,
    ) -> bool:
        """Add one lead to the Instantly campaign with personalization variables."""
        payload = self._lead_payload(
            email=email,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            custom_variables=custom_variables or {},
        )
        result = await self.add_leads_bulk(
            [payload],
            skip_if_in_workspace=skip_if_in_workspace,
            skip_if_in_campaign=skip_if_in_campaign,
        )
        return result.ok

    async def add_leads_bulk(
        self,
        leads: list[dict[str, Any]],
        *,
        skip_if_in_workspace: bool = False,
        skip_if_in_campaign: bool = False,
    ) -> AddLeadsResult:
        if not self.is_configured:
            logger.error("[Instantly] Missing API key or campaign ID")
            return AddLeadsResult(ok=False, error="not configured")

        body_v2 = {
            "campaign_id": self.campaign_id,
            "skip_if_in_workspace": skip_if_in_workspace,
            "skip_if_in_campaign": skip_if_in_campaign,
            "leads": leads,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            last_error = ""
            for attempt in range(1, 4):
                try:
                    resp = await client.post(
                        f"{self.V2_BASE}/leads/add",
                        headers=self._headers(),
                        json=body_v2,
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json() if resp.content else {}
                        uploaded = int(data.get("leads_uploaded") or 0)
                        skipped = int(data.get("skipped_count") or 0)
                        invalid = int(data.get("invalid_email_count") or 0)
                        duplicated = int(data.get("duplicated_leads") or 0)
                        blocklist = int(data.get("in_blocklist") or 0)
                        dup_in_payload = int(
                            data.get("duplicate_email_count") or 0
                        )
                        emails = [
                            (lead.get("email") or "?")
                            for lead in leads
                        ]
                        if uploaded > 0:
                            created = data.get("created_leads") or []
                            for c in created:
                                logger.success(
                                    f"[Instantly] Added {c.get('email', '?')} "
                                    f"to campaign {self.campaign_id[:8]}..."
                                )
                            return AddLeadsResult(
                                ok=True,
                                leads_uploaded=uploaded,
                                skipped_count=skipped,
                                invalid_email_count=invalid,
                                raw=data,
                            )
                        if duplicated > 0:
                            logger.info(
                                f"[Instantly] Lead already in this campaign "
                                f"({duplicated} duplicated): {', '.join(emails)}"
                            )
                            return AddLeadsResult(
                                ok=True,
                                leads_uploaded=0,
                                skipped_count=skipped,
                                invalid_email_count=invalid,
                                raw=data,
                            )
                        last_error = (
                            f"0 uploaded for {', '.join(emails)} "
                            f"(skipped={skipped}, invalid={invalid}, "
                            f"duplicated={duplicated}, blocklist={blocklist}, "
                            f"dup_in_request={dup_in_payload})"
                        )
                        logger.warning(f"[Instantly] {last_error}")
                        logger.warning(
                            f"[Instantly] API response: {str(data)[:500]}"
                        )
                        if skipped and skip_if_in_workspace:
                            last_error += (
                                " Tip: lead may exist in another campaign — "
                                "move in Instantly UI or delete old test lead."
                            )
                        return AddLeadsResult(
                            ok=False,
                            leads_uploaded=0,
                            skipped_count=skipped,
                            invalid_email_count=invalid,
                            raw=data,
                            error=last_error,
                        )
                    last_error = f"HTTP {resp.status_code}: {resp.text[:400]}"
                    logger.warning(
                        f"[Instantly] v2 add attempt {attempt}/3 failed: {last_error}"
                    )
                except Exception as e:
                    last_error = repr(e)
                    logger.warning(
                        f"[Instantly] v2 request attempt {attempt}/3 error: {last_error}"
                    )
                if attempt < 3:
                    await asyncio.sleep(2 * attempt)

            logger.error(
                f"[Instantly] Could not add lead(s) after 3 tries. Last error: {last_error}"
            )
            return AddLeadsResult(ok=False, error=last_error)

    async def get_campaign(self) -> dict[str, Any] | None:
        if not self.is_configured:
            return None
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.V2_BASE}/campaigns/{self.campaign_id}",
                headers=self._headers(),
            )
            if resp.status_code != 200:
                logger.warning(
                    f"[Instantly] get campaign failed ({resp.status_code}): "
                    f"{resp.text[:300]}"
                )
                return None
            return resp.json()

    async def patch_campaign(self, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Partial update (schedule, limits, sequences, etc.)."""
        if not self.is_configured:
            return None
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.patch(
                f"{self.V2_BASE}/campaigns/{self.campaign_id}",
                headers=self._headers(),
                json=updates,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.success(
                    f"[Instantly] Campaign updated: {data.get('name', self.campaign_id[:8])}"
                )
                return data
            logger.error(
                f"[Instantly] patch campaign failed ({resp.status_code}): "
                f"{resp.text[:500]}"
            )
            return None

    async def apply_agent_earns_preset(
        self,
        *,
        timezone: str = "America/Detroit",
        daily_limit: int = 10,
        activate: bool = True,
    ) -> bool:
        """Apply deliverability-safe defaults from campaign_presets.py."""
        from integrations.platforms.campaign_presets import agent_earns_campaign_patch

        current = await self.get_campaign()
        patch = agent_earns_campaign_patch(
            current, timezone=timezone, daily_limit=daily_limit
        )
        updated = await self.patch_campaign(patch)
        if not updated:
            return False
        await self.ensure_send_ready(force=True)
        if activate and updated.get("status") != CAMPAIGN_STATUS_ACTIVE:
            return await self.activate_campaign()
        return True

    async def activate_campaign(self) -> bool:
        """Start or resume the campaign (POST .../campaigns/{id}/activate)."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.V2_BASE}/campaigns/{self.campaign_id}/activate",
                headers=self._headers(),
                json={},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.success(
                    f"[Instantly] Campaign activated: {data.get('name', self.campaign_id[:8])} "
                    f"(status={data.get('status')})"
                )
                return True
            logger.warning(
                f"[Instantly] activate campaign failed ({resp.status_code}): "
                f"{resp.text[:400]}"
            )
            return False

    async def list_accounts(self, limit: int = 100) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.V2_BASE}/accounts",
                headers=self._headers(),
                params={"limit": limit},
            )
            if resp.status_code != 200:
                logger.warning(
                    f"[Instantly] list accounts failed ({resp.status_code}): "
                    f"{resp.text[:300]}"
                )
                return []
            data = resp.json()
            return data.get("items") or data.get("accounts") or []

    async def create_imap_account(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        imap_host: str,
        imap_port: int,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        signature: str = "",
    ) -> dict[str, Any] | None:
        """
        Connect a Hostinger (or other) mailbox via IMAP/SMTP (provider_code=1).
        Requires API key scopes: accounts:create (API v2 only).
        """
        payload: dict[str, Any] = {
            "email": email.strip().lower(),
            "first_name": first_name.strip() or "Team",
            "last_name": last_name.strip() or ".",
            "provider_code": 1,
            "imap_username": username.strip(),
            "imap_password": password,
            "imap_host": imap_host.strip(),
            "imap_port": int(imap_port),
            "smtp_username": username.strip(),
            "smtp_password": password,
            "smtp_host": smtp_host.strip(),
            "smtp_port": int(smtp_port),
        }
        if signature:
            payload["signature"] = signature
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self.V2_BASE}/accounts",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.success(f"[Instantly] Connected account {email}")
                return data
            logger.error(
                f"[Instantly] connect {email} failed ({resp.status_code}): "
                f"{resp.text[:500]}"
            )
            return None

    async def resume_account(self, email: str) -> bool:
        encoded = quote(email.strip(), safe="")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.V2_BASE}/accounts/{encoded}/resume",
                headers=self._headers(),
                json={},
            )
            if resp.status_code in (200, 201):
                logger.success(f"[Instantly] Resumed sending account {email}")
                return True
            logger.warning(
                f"[Instantly] resume {email} failed ({resp.status_code}): "
                f"{resp.text[:300]}"
            )
            return False

    async def enable_warmup(self, emails: list[str]) -> bool:
        if not emails:
            return True
        body = {"emails": [e.strip() for e in emails if e.strip()]}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.V2_BASE}/accounts/warmup/enable",
                headers=self._headers(),
                json=body,
            )
            if resp.status_code in (200, 201):
                job = resp.json()
                logger.success(
                    f"[Instantly] Warmup enable queued for {len(body['emails'])} "
                    f"account(s) (job {str(job.get('id', ''))[:8]}...)"
                )
                return True
            logger.warning(
                f"[Instantly] warmup enable failed ({resp.status_code}): "
                f"{resp.text[:400]}"
            )
            return False

    async def ensure_send_ready(
        self,
        *,
        force: bool = False,
        extra_sender_emails: list[str] | None = None,
    ) -> bool:
        """
        Resume campaign if paused, resume inactive sending accounts,
        enable warmup if paused. Safe to call before each push (cached per client).
        """
        if not self.is_configured:
            return False
        if self._prepare_done and not force:
            return True

        campaign = await self.get_campaign()
        if not campaign:
            return False

        name = campaign.get("name") or self.campaign_id[:8]
        status = campaign.get("status")
        if status != CAMPAIGN_STATUS_ACTIVE:
            logger.info(
                f"[Instantly] Campaign '{name}' is not active (status={status}) — starting..."
            )
            await self.activate_campaign()
        else:
            logger.debug(f"[Instantly] Campaign '{name}' already active")

        sender_emails = list(campaign.get("email_list") or [])
        for e in extra_sender_emails or []:
            if e and e not in sender_emails:
                sender_emails.append(e)

        if not sender_emails:
            logger.warning(
                "[Instantly] No sending accounts on campaign — add mailboxes in Instantly UI"
            )
            self._prepare_done = True
            return True

        by_email = {
            (a.get("email") or "").lower(): a
            for a in await self.list_accounts()
        }

        need_warmup: list[str] = []
        for email in sender_emails:
            acc = by_email.get(email.lower())
            if not acc:
                logger.warning(f"[Instantly] Account not found in workspace: {email}")
                continue

            acc_status = acc.get("status")
            if acc_status != ACCOUNT_STATUS_ACTIVE:
                logger.info(
                    f"[Instantly] Sending account {email} inactive (status={acc_status}) "
                    "— resuming..."
                )
                await self.resume_account(email)

            warmup_status = acc.get("warmup_status")
            if warmup_status != WARMUP_STATUS_ACTIVE:
                logger.info(
                    f"[Instantly] Warmup off for {email} (warmup_status={warmup_status}) "
                    "— enabling..."
                )
                need_warmup.append(email)

        if need_warmup:
            await self.enable_warmup(need_warmup)

        self._prepare_done = True
        logger.info("[Instantly] Send readiness check complete")
        return True

    async def list_campaign_leads(self, limit: int = 100) -> list[dict[str, Any]]:
        """List leads currently in this campaign (for debugging)."""
        if not self.is_configured:
            return []
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.V2_BASE}/leads/list",
                headers=self._headers(),
                json={"campaign": self.campaign_id, "limit": limit},
            )
            if resp.status_code != 200:
                logger.warning(f"[Instantly] list leads failed: {resp.text[:300]}")
                return []
            return resp.json().get("items") or []

    async def list_emails(
        self,
        *,
        campaign_id: str | None = None,
        email_type: str | None = "received",
        is_unread: bool | None = None,
        limit: int = 50,
        starting_after: str | None = None,
        min_timestamp_created: str | None = None,
        lead_email: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """
        List Unibox emails (rate limit: 20 req/min).
        email_type: received | sent | manual
        Returns (items, next_starting_after).
        """
        if not self.api_key:
            return [], None

        params: dict[str, Any] = {"limit": min(max(limit, 1), 100)}
        cid = (campaign_id or self.campaign_id).strip()
        if cid:
            params["campaign_id"] = cid
        if email_type:
            params["email_type"] = email_type
        if is_unread is not None:
            params["is_unread"] = is_unread
        if starting_after:
            params["starting_after"] = starting_after
        if min_timestamp_created:
            params["min_timestamp_created"] = min_timestamp_created
        if lead_email:
            params["lead"] = lead_email.strip()
        params["sort_order"] = "desc"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.V2_BASE}/emails",
                headers=self._headers(),
                params=params,
            )
            if resp.status_code != 200:
                logger.warning(
                    f"[Instantly] list emails failed ({resp.status_code}): "
                    f"{resp.text[:300]}"
                )
                return [], None
            data = resp.json() if resp.content else {}
            items = data.get("items") or []
            next_cursor = data.get("next_starting_after")
            return items, next_cursor

    async def get_email(self, email_id: str) -> dict[str, Any] | None:
        """Fetch one Unibox email by id (for reply context)."""
        eid = (email_id or "").strip()
        if not self.api_key or not eid:
            return None
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{self.V2_BASE}/emails/{eid}",
                headers=self._headers(),
            )
            if resp.status_code != 200:
                logger.warning(
                    f"[Instantly] get email {eid[:8]}... failed ({resp.status_code}): "
                    f"{resp.text[:300]}"
                )
                return None
            return resp.json() if resp.content else None

    async def send_reply(
        self,
        *,
        eaccount: str,
        reply_to_uuid: str,
        subject: str,
        body_text: str,
        body_html: str = "",
    ) -> dict[str, Any]:
        """
        Reply in an existing Unibox thread (POST /api/v2/emails/reply).
        Requires API scopes: emails:create or emails:all.
        """
        account = (eaccount or "").strip().lower()
        reply_id = (reply_to_uuid or "").strip()
        if not self.api_key:
            return {"ok": False, "error": "missing_api_key"}
        if not account or "@" not in account:
            return {"ok": False, "error": "invalid_eaccount"}
        if not reply_id:
            return {"ok": False, "error": "missing_reply_to_uuid"}

        body: dict[str, str] = {"text": (body_text or "").strip()}
        if body_html.strip():
            body["html"] = body_html.strip()

        payload: dict[str, Any] = {
            "eaccount": account,
            "reply_to_uuid": reply_id,
            "subject": (subject or "Re:").strip(),
            "body": body,
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self.V2_BASE}/emails/reply",
                headers=self._headers(),
                json=payload,
            )
            if resp.status_code in (200, 201):
                data = resp.json() if resp.content else {}
                sent_id = str(data.get("id") or "")
                logger.success(
                    f"[Instantly] Reply queued from {account} "
                    f"(in reply to {reply_id[:8]}...)"
                )
                return {"ok": True, "email_id": sent_id, "raw": data}

            err = resp.text[:500]
            logger.error(
                f"[Instantly] reply failed ({resp.status_code}): {err}"
            )
            return {
                "ok": False,
                "error": f"HTTP {resp.status_code}",
                "detail": err,
            }

    @staticmethod
    def _lead_payload(
        email: str,
        first_name: str,
        last_name: str,
        company_name: str,
        custom_variables: dict[str, str],
    ) -> dict[str, Any]:
        row: dict[str, Any] = {
            "email": email.strip(),
            "first_name": first_name.strip() or "there",
            "last_name": last_name.strip(),
            "company_name": company_name.strip(),
        }
        if custom_variables:
            row["custom_variables"] = custom_variables
        return row
