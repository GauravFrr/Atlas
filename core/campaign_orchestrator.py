"""
Campaign Orchestrator — Hands-free pipeline for local business outreach.

    await run_campaign(niche="plumber", city="Austin TX", leads=10)

Flow:
  1. Scan leads (Maps / OSM / YouTube / CSV)
  2. Memory bank dedup
  3. Resolve email first — discard lead if none (no demo/LLM spend)
  4. Generate demo → publish → draft → send
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from config import Settings, get_settings
from database.connection import init_db
from database.repositories import CampaignRepository, LeadRepository
from database.session import get_session
from llm.router import LLMRouter
from modules.lead_finder.csv_leads import load_csv_leads
from modules.lead_finder.mock_leads import generate_mock_leads, override_emails_for_test
from utils.spam_check import check_outreach_copy
from modules.lead_finder.scanners.google_maps import GoogleMapsScanner, MapsScanResult
from modules.lead_finder.scanners.osm_maps import OSMMapsScanner
from modules.outreach.cold_email import ColdEmailEngine
from modules.outreach.icebreaker import preset_icebreaker
from integrations.hosting.demo_publisher import DemoPublisher
from modules.outreach.instantly_push import InstantlyPush, export_instantly_csv
from utils.domain_pool import DomainPool, OutreachDomain
from utils.email_enricher import EmailEnricher
from utils.send_router import SendMode, pick_hybrid_channel
from core.lead_email_gate import maps_has_email, remove_local_demo, resolve_email_for_maps


@dataclass
class CampaignLeadResult:
    business_name: str
    place_id: str
    status: str  # processed | skipped_duplicate | discarded_no_email | error
    demo_path: str | None = None
    email: str | None = None
    draft_path: str | None = None
    sent: bool = False
    error: str | None = None


@dataclass
class CampaignResult:
    campaign_id: str
    niche: str
    city: str
    leads_requested: int
    leads_processed: int = 0
    demos_generated: int = 0
    emails_drafted: int = 0
    emails_sent: int = 0
    duplicates_skipped: int = 0
    no_email_count: int = 0
    errors_count: int = 0
    dry_run: bool = True
    mock_mode: bool = False
    csv_mode: bool = False
    scan_source: str = ""  # google_maps | openstreetmap | csv | mock
    lead_results: list[CampaignLeadResult] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""

    def summary_text(self) -> str:
        if self.csv_mode:
            source = "CSV import"
        elif self.mock_mode:
            source = "MOCK LEADS (no Google API)"
        elif self.scan_source:
            source = self.scan_source.replace("_", " ").title()
        else:
            source = "Google Maps"
        return (
            f"Campaign {self.campaign_id[:8]} | {self.niche} @ {self.city}\n"
            f"  Source:    {source}\n"
            f"  Requested: {self.leads_requested}\n"
            f"  Processed: {self.leads_processed}\n"
            f"  Demos:     {self.demos_generated}\n"
            f"  Drafted:   {self.emails_drafted}\n"
            f"  Sent:      {self.emails_sent}\n"
            f"  Skipped:   {self.duplicates_skipped} (already in memory bank)\n"
            f"  No email:  {self.no_email_count}\n"
            f"  Errors:    {self.errors_count}\n"
            f"  Mode:      {'DRY RUN' if self.dry_run else 'LIVE SEND'}"
        )


class CampaignOrchestrator:
    """
    Stitches Maps Scanner -> Demo Generator -> Cold Email Engine
    with SQLite memory bank deduplication.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        llm_router: LLMRouter | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm_router or LLMRouter(self.settings)
        self.scanner = GoogleMapsScanner(self.settings, self.llm)
        self.osm_scanner = OSMMapsScanner(self.settings)
        self.email_engine = ColdEmailEngine(self.settings, self.llm)
        self.enricher = EmailEnricher(self.settings)
        self.lead_repo = LeadRepository()
        self.campaign_repo = CampaignRepository()
        self.demo_publisher = DemoPublisher(self.settings)
        self.instantly = InstantlyPush(self.settings, llm=self.llm)
        self.domain_pool = DomainPool(self.settings)

    def _demo_slug(self, demo_path: str) -> str:
        return Path(demo_path).stem

    @staticmethod
    def _safe_path_token(value: str, max_len: int = 48) -> str:
        """Filesystem-safe token (place_id like osm/node/123 must not contain /)."""
        s = "".join(c if c.isalnum() else "_" for c in value.replace("/", "_"))
        while "__" in s:
            s = s.replace("__", "_")
        return s.strip("_").lower()[:max_len] or "lead"

    def _demo_public_url(
        self, demo_path: str | None, demo_base_url: str | None = None
    ) -> str | None:
        base = demo_base_url or self.settings.demo_site_base_url
        if not demo_path or not base:
            return None
        return self.demo_publisher.public_url_for_slug(
            self._demo_slug(demo_path), demo_base_url=base
        )

    async def _resolve_demo_url(
        self, demo_path: str | None, demo_base_url: str | None = None
    ) -> str | None:
        """Upload to Hostinger/R2; return None if upload fails (no fake URLs in emails)."""
        if not demo_path:
            return None
        base = demo_base_url or self.settings.demo_site_base_url
        if not base:
            return None
        slug = self._demo_slug(demo_path)
        mode = (getattr(self.settings, "demo_upload_mode", "auto") or "auto").lower()
        if mode == "local":
            return self._demo_public_url(demo_path, demo_base_url=base)
        uploaded = await self.demo_publisher.publish(
            demo_path, slug=slug, demo_base_url=base
        )
        if uploaded:
            return uploaded
        logger.warning("[Demo] Upload failed — email will omit demo link")
        return None

    async def _fetch_leads(
        self,
        niche: str,
        city: str,
        limit: int,
        hunt_mode: str = "m10_no_website",
    ) -> tuple[list[MapsScanResult], str]:
        from core.lead_fetcher import fetch_leads

        return await fetch_leads(
            self.settings,
            self.llm,
            niche=niche,
            city=city,
            limit=limit,
            hunt_mode=hunt_mode,
            scan_local_fn=self._scan_local_leads,
        )

    async def _scan_local_leads(
        self,
        niche: str,
        city: str,
        limit: int,
        *,
        no_website_only: bool = True,
    ) -> tuple[list[MapsScanResult], str]:
        """Google Maps and/or free OpenStreetMap depending on settings."""
        mode = (self.settings.lead_scan_source or "auto").lower()
        has_google = bool(self.settings.google_places_api_key)

        if mode == "osm" or (mode == "auto" and not has_google):
            leads = await self.osm_scanner.scan(
                niche=niche, city=city, limit=limit, no_website_only=no_website_only
            )
            return leads, "openstreetmap"

        leads = await self.scanner.scan(
            niche=niche, city=city, limit=limit, no_website_only=no_website_only
        )
        if leads or mode == "google":
            return leads, "google_maps"

        logger.info("[Campaign] Google returned 0 — trying free OpenStreetMap fallback")
        osm_leads = await self.osm_scanner.scan(
            niche=niche, city=city, limit=limit, no_website_only=no_website_only
        )
        return osm_leads, "openstreetmap"

    async def run_campaign(
        self,
        niche: str,
        city: str,
        leads: int = 10,
        send_mode: SendMode = "draft",
        scan_buffer_multiplier: int = 3,
        use_mock: bool = False,
        fresh_mock: bool = False,
        test_to: str | None = None,
        csv_path: str | None = None,
        hunt_mode: str = "m10_no_website",
    ) -> CampaignResult:
        """
        Run a full outreach campaign end-to-end.

        Args:
            niche: Business type, e.g. "plumber"
            city: Target city, e.g. "Austin TX"
            leads: How many NEW businesses to process
            send_mode: draft | smtp | instantly | auto | hybrid (random + fallback)
            scan_buffer_multiplier: Scan extra leads to account for duplicates
            use_mock: If True, use fake leads (no Google Places API / billing required)
            fresh_mock: If True with use_mock, clear mock leads from memory bank first (re-test)
            test_to: With use_mock, send all leads to this inbox (plus-tags for uniqueness)
            csv_path: Import leads from CSV (no Google API)
            hunt_mode: no_website | outdated | low_reviews | apollo
        """
        if not self.settings.has_gemini and not self.settings.has_groq:
            raise RuntimeError("No LLM API key configured (GEMINI_API_KEY or GROQ_API_KEY)")

        if csv_path and (use_mock or test_to):
            raise ValueError("Use either --csv or --mock/--test-to, not both")

        scan_mode = (self.settings.lead_scan_source or "auto").lower()
        if (
            not csv_path
            and not use_mock
            and scan_mode == "google"
            and not self.settings.google_places_api_key
        ):
            raise RuntimeError(
                "LEAD_SCAN_SOURCE=google but GOOGLE_PLACES_API_KEY is missing. "
                "Set the key or use LEAD_SCAN_SOURCE=auto (free OSM) or osm."
            )

        await init_db()

        started = datetime.now(timezone.utc)
        outcome = CampaignResult(
            campaign_id="",
            niche=niche,
            city=city,
            leads_requested=leads,
            dry_run=send_mode == "draft",
            mock_mode=use_mock,
            csv_mode=bool(csv_path),
            started_at=started.isoformat(),
        )

        scan_limit = max(leads * scan_buffer_multiplier, leads + 5, 25)
        if csv_path:
            mode_label = "CSV"
        elif use_mock:
            mode_label = "MOCK"
        else:
            mode_label = f"LIVE ({hunt_mode})"
        logger.info(
            f"Campaign starting [{mode_label}]: {niche} in {city} | target={leads} leads | "
            f"scan_limit={scan_limit} | dry_run={outcome.dry_run} | send_mode={send_mode}"
        )

        if (
            send_mode in ("instantly", "hybrid")
            and not outcome.dry_run
            and self.instantly.is_configured
            and getattr(self.settings, "instantly_auto_prepare", True)
        ):
            await self.instantly.client.ensure_send_ready(force=True)

        if csv_path:
            raw_leads = load_csv_leads(
                csv_path,
                default_niche=niche,
                default_city=city,
                limit=scan_limit,
            )
            logger.info(f"CSV import: {len(raw_leads)} leads from {csv_path}")
        elif use_mock:
            raw_leads = generate_mock_leads(niche=niche, city=city, count=scan_limit)
            if test_to:
                override_emails_for_test(raw_leads, test_to)
                logger.info(f"Mock emails routed to {test_to} (+tags per lead)")
            logger.info(f"Mock scan generated {len(raw_leads)} sample leads (no Google API)")
        else:
            raw_leads, scan_source = await self._fetch_leads(
                niche, city, scan_limit, hunt_mode=hunt_mode
            )
            outcome.scan_source = scan_source
            logger.info(
                f"Lead scan mode={hunt_mode} source={scan_source} → {len(raw_leads)} raw leads"
            )

        for lead in raw_leads:
            lead.raw = {**(lead.raw or {}), "hunt_mode": hunt_mode}

        async with get_session() as session:
            if use_mock and fresh_mock:
                cleared = await self.lead_repo.reset_mock_leads(session, niche, city)
                if cleared:
                    logger.info(
                        f"[Memory] Cleared {cleared} mock lead(s) for {niche} @ {city} (--fresh)"
                    )

            campaign_run = await self.campaign_repo.create(
                session, niche, city, leads, outcome.dry_run
            )
            outcome.campaign_id = campaign_run.id

            new_leads = await self._filter_new_leads(
                session, raw_leads, leads, campaign_run.id, outcome
            )
            campaign_run_id = campaign_run.id
            emails_sent_today = await self.lead_repo.count_emails_sent_today(session)

        daily_cap = self.settings.max_emails_per_day
        instantly_csv_rows: list[dict[str, str]] = []

        for maps_lead in new_leads:
            try:
                async with get_session() as session:
                    lead_result = await self._process_one_lead(
                        session=session,
                        maps_lead=maps_lead,
                        campaign_run_id=campaign_run_id,
                        send_mode=send_mode,
                        emails_sent_today=emails_sent_today,
                        daily_cap=daily_cap,
                        instantly_csv_rows=instantly_csv_rows,
                    )
            except Exception as e:
                logger.error(
                    f"Lead failed ({maps_lead.business_name}): {e} — continuing"
                )
                lead_result = CampaignLeadResult(
                    business_name=maps_lead.business_name,
                    place_id=maps_lead.place_id,
                    status="error",
                    error=str(e),
                )

            outcome.lead_results.append(lead_result)

            if lead_result.status == "processed":
                outcome.leads_processed += 1
                if lead_result.demo_path:
                    outcome.demos_generated += 1
                if lead_result.draft_path:
                    outcome.emails_drafted += 1
                if lead_result.sent:
                    outcome.emails_sent += 1
                    emails_sent_today += 1
            elif lead_result.status == "skipped_duplicate":
                outcome.duplicates_skipped += 1
            elif lead_result.status in ("discarded_no_email", "saved_no_email"):
                outcome.no_email_count += 1
            elif lead_result.status == "error":
                outcome.errors_count += 1

        if instantly_csv_rows:
            csv_path = Path("outputs/instantly") / f"leads_{campaign_run_id[:8]}.csv"
            export_instantly_csv(instantly_csv_rows, csv_path)

        async with get_session() as session:
            campaign_run = await self.campaign_repo.get_by_id(session, campaign_run_id)
            if campaign_run:
                campaign_run.leads_processed = outcome.leads_processed
                campaign_run.demos_generated = outcome.demos_generated
                campaign_run.emails_drafted = outcome.emails_drafted
                campaign_run.emails_sent = outcome.emails_sent
                campaign_run.duplicates_skipped = outcome.duplicates_skipped
                campaign_run.no_email_count = outcome.no_email_count
                campaign_run.errors_count = outcome.errors_count
                summary = outcome.summary_text()
                await self.campaign_repo.complete(session, campaign_run, summary)

        outcome.completed_at = datetime.now(timezone.utc).isoformat()
        logger.success(f"\n{outcome.summary_text()}")
        return outcome

    @staticmethod
    def _normalize_business_key(name: str, city: str) -> str:
        key = "".join(c for c in (name or "").lower() if c.isalnum())
        city_key = "".join(c for c in (city or "").lower() if c.isalnum())[:20]
        return f"{key}_{city_key}" if key else ""

    def _dedupe_raw_leads(self, raw_leads: list[MapsScanResult]) -> list[MapsScanResult]:
        """Same business or email twice in one scan batch (common with OSM node/way dupes)."""
        seen_keys: set[str] = set()
        seen_emails: set[str] = set()
        out: list[MapsScanResult] = []
        for lead in raw_leads:
            bk = self._normalize_business_key(lead.business_name, lead.city)
            em = (lead.email or "").strip().lower()
            if bk and bk in seen_keys:
                continue
            if em and em in seen_emails:
                continue
            if bk:
                seen_keys.add(bk)
            if em:
                seen_emails.add(em)
            out.append(lead)
        if len(out) < len(raw_leads):
            logger.info(
                f"[Dedup] {len(raw_leads)} → {len(out)} leads (removed duplicate biz/email in batch)"
            )
        return out

    async def _filter_new_leads(
        self,
        session: Any,
        raw_leads: list[MapsScanResult],
        target: int,
        campaign_run_id: str,
        outcome: CampaignResult,
    ) -> list[MapsScanResult]:
        """Save every hunted lead; return only new ones for outreach processing."""
        raw_leads = self._dedupe_raw_leads(raw_leads)
        new_leads: list[MapsScanResult] = []

        for maps_lead in raw_leads:
            await self.lead_repo.upsert_inventory_from_maps(
                session, maps_lead, campaign_run_id
            )

        for maps_lead in raw_leads:
            if len(new_leads) >= target:
                break

            if await self.lead_repo.is_already_known(
                session,
                maps_lead.place_id,
                maps_lead.business_name,
                maps_lead.city,
                email=maps_lead.email,
            ):
                logger.info(
                    f"[Memory] Skipping duplicate: {maps_lead.business_name} "
                    f"({maps_lead.place_id})"
                )
                outcome.lead_results.append(
                    CampaignLeadResult(
                        business_name=maps_lead.business_name,
                        place_id=maps_lead.place_id,
                        status="skipped_duplicate",
                    )
                )
                outcome.duplicates_skipped += 1
                continue

            new_leads.append(maps_lead)

        logger.info(f"{len(new_leads)} new leads after memory bank filter")
        return new_leads

    def _smtp_config_for(
        self, outreach_domain: OutreachDomain | None
    ) -> dict[str, str | int | bool] | None:
        if outreach_domain and outreach_domain.has_smtp():
            return outreach_domain.get_smtp_config(
                self.settings.your_name, settings=self.settings
            )
        if self.settings.has_smtp:
            return self.settings.get_smtp_config()
        return None

    def _domain_for_lead(self, lead: Any, place_id: str = "") -> OutreachDomain | None:
        from utils.mailbox_lock import resolve_outreach_domain

        if not self.domain_pool.enabled:
            return None
        return resolve_outreach_domain(
            lead, self.domain_pool, place_id=place_id or getattr(lead, "place_id", "") or ""
        )

    def _smtp_for_lead(
        self,
        lead: Any,
        outreach_domain: OutreachDomain | None = None,
        *,
        for_close_reply: bool = False,
    ) -> dict[str, str | int | bool] | None:
        from utils.mailbox_lock import resolve_smtp_config

        return resolve_smtp_config(
            lead,
            self.settings,
            self.domain_pool,
            outreach_domain,
            for_close_reply=for_close_reply,
        )

    def _smtp_for_close_reply(
        self,
        lead: Any,
        outreach_domain: OutreachDomain | None = None,
    ) -> dict[str, str | int | bool] | None:
        """SMTP for Telegram-approved reply / payment (even if cold send was Instantly)."""
        return self._smtp_for_lead(lead, outreach_domain, for_close_reply=True)

    def _save_local_draft(
        self, to_email: str, subject: str, body: str
    ) -> str:
        self.email_engine.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            dry_run=True,
        )
        return self._last_draft_path(to_email)

    async def _discard_no_email(
        self,
        session: Any,
        maps_lead: MapsScanResult,
        campaign_run_id: str,
        *,
        db_lead: Any | None = None,
        reason: str = "no_email",
    ) -> None:
        """Skip outreach without email — lead stays in DB for resale inventory."""
        remove_local_demo(db_lead.demo_site_path if db_lead else maps_lead.demo_site_path)
        if db_lead:
            await self.lead_repo.discard_no_email(session, db_lead, reason=reason)
        else:
            await self.lead_repo.mark_skipped(
                session, maps_lead, campaign_run_id, reason
            )
        logger.info(
            f"[Email gate] Saved inventory only (no email): {maps_lead.business_name}"
        )

    async def _ensure_email_or_discard(
        self,
        session: Any,
        maps_lead: MapsScanResult,
        campaign_run_id: str,
        *,
        db_lead: Any | None = None,
    ) -> bool:
        """Resolve email; discard lead if still none. Returns True if OK to continue."""
        from utils.contact_greeting import ensure_contact_name

        await resolve_email_for_maps(maps_lead, self.settings, self.enricher)
        await ensure_contact_name(maps_lead, self.settings)

        if maps_has_email(maps_lead):
            if db_lead:
                from utils.lead_package_tier import sync_maps_enrichment

                if not db_lead.email:
                    db_lead.email = maps_lead.email
                sync_maps_enrichment(db_lead, maps_lead)
                await self.lead_repo.refresh_package_tier(session, db_lead)
            return True

        await self._discard_no_email(
            session, maps_lead, campaign_run_id, db_lead=db_lead
        )
        return False

    async def _try_instantly(
        self,
        maps_lead: MapsScanResult,
        draft: dict[str, str],
        demo_url: str | None,
        outreach_domain: OutreachDomain | None,
        instantly_csv_rows: list[dict[str, str]],
    ) -> bool:
        instantly_csv_rows.append(
            self.instantly.append_csv_row(
                maps_lead, demo_url, self.settings.your_name
            )
        )
        if not self.instantly.is_configured:
            logger.warning("[Instantly] Not configured")
            return False
        cid = (
            outreach_domain.instantly_campaign_id
            if outreach_domain and outreach_domain.instantly_campaign_id
            else self.settings.instantly_campaign_id
        )
        ok_spam, hits = check_outreach_copy(
            draft.get("subject", ""), draft.get("body", "")
        )
        if not ok_spam:
            logger.warning(
                f"[Spam] Phrases in draft for {maps_lead.email}: {', '.join(hits)}"
            )
            if self.settings.strict_spam_check:
                return False

        ok = await self.instantly.push_lead(
            maps_lead,
            demo_url=demo_url,
            your_name=self.settings.your_name,
            campaign_id=cid or None,
        )
        if ok:
            logger.success(f"[Instantly] Queued {maps_lead.email}")
        return ok

    def _try_smtp(
        self,
        maps_lead: MapsScanResult,
        draft: dict[str, str],
        outreach_domain: OutreachDomain | None,
        *,
        db_lead: Any | None = None,
    ) -> bool:
        lead = db_lead
        domain = outreach_domain
        if lead is not None:
            domain = domain or self._domain_for_lead(lead, maps_lead.place_id)
            smtp_cfg = self._smtp_for_lead(lead, domain)
        else:
            smtp_cfg = self._smtp_config_for(domain)
        if not smtp_cfg:
            logger.warning("[SMTP] No mailbox configured")
            return False
        ok = self.email_engine.send_email(
            to_email=maps_lead.email or "",
            subject=draft["subject"],
            body=draft["body"],
            smtp_config=smtp_cfg,
            dry_run=False,
        )
        if ok:
            from utils.mailbox_lock import lock_mailbox_on_lead

            if lead is not None:
                lock_mailbox_on_lead(
                    lead, smtp_cfg=smtp_cfg, domain=domain, send_channel="smtp"
                )
            logger.success(
                f"[SMTP] Sent to {maps_lead.email} from {smtp_cfg.get('from_email', '')}"
            )
        return ok

    async def _send_with_hybrid(
        self,
        maps_lead: MapsScanResult,
        draft: dict[str, str],
        demo_url: str | None,
        outreach_domain: OutreachDomain | None,
        instantly_csv_rows: list[dict[str, str]],
        *,
        db_lead: Any | None = None,
    ) -> tuple[bool, str]:
        """Returns (sent, channel_used) where channel is instantly or smtp."""
        primary = pick_hybrid_channel(maps_lead.place_id, self.settings)
        logger.info(f"[Hybrid] {maps_lead.business_name} → try {primary} first")

        if primary == "instantly":
            if await self._try_instantly(
                maps_lead, draft, demo_url, outreach_domain, instantly_csv_rows
            ):
                if db_lead and outreach_domain:
                    from utils.mailbox_lock import lock_mailbox_on_lead

                    lock_mailbox_on_lead(
                        db_lead, domain=outreach_domain, send_channel="instantly"
                    )
                return True, "instantly"
            logger.warning("[Hybrid] Instantly failed → SMTP fallback")
            if self._try_smtp(maps_lead, draft, outreach_domain, db_lead=db_lead):
                return True, "smtp"
            return False, ""

        if self._try_smtp(maps_lead, draft, outreach_domain, db_lead=db_lead):
            return True, "smtp"
        logger.warning("[Hybrid] SMTP failed → Instantly fallback")
        if await self._try_instantly(
            maps_lead, draft, demo_url, outreach_domain, instantly_csv_rows
        ):
            if db_lead and outreach_domain:
                from utils.mailbox_lock import lock_mailbox_on_lead

                lock_mailbox_on_lead(
                    db_lead, domain=outreach_domain, send_channel="instantly"
                )
            return True, "instantly"
        return False, ""

    async def process_incomplete_queue(
        self,
        *,
        max_leads: int = 10,
        send_mode: SendMode | None = None,
    ) -> dict[str, Any]:
        """
        Finish leads saved in SQLite when a previous run stopped mid-pipeline.
        Runs before new hunting in autopilot.
        """
        from core.lead_resume import assess_lead
        from utils.send_router import resolve_send_mode

        if send_mode is None:
            send_mode = resolve_send_mode(
                self.settings, self.settings.email_send_mode or "instantly"
            )

        stats: dict[str, Any] = {
            "queued": 0,
            "resumed": 0,
            "sent": 0,
            "errors": 0,
            "steps_done": {},
        }

        cooldown = int(getattr(self.settings, "resume_cooldown_minutes", 25) or 25)
        from core.lead_resume import is_resume_deferred, mark_resume_deferred

        async with get_session() as session:
            incomplete = await self.lead_repo.list_incomplete(
                session, max_leads, resume_cooldown_minutes=cooldown
            )
            if not incomplete:
                logger.info("[Resume] No incomplete leads in memory bank")
                return stats

            stats["queued"] = len(incomplete)
            logger.info(f"[Resume] {len(incomplete)} lead(s) need finishing work")

            resume_jobs: list[tuple[str, list[str], str]] = []
            for lead in incomplete:
                plan = assess_lead(lead)
                logger.info(
                    f"[Resume] {lead.business_name}: missing={plan.missing} "
                    f"(status={lead.status})"
                )
                if plan.missing:
                    resume_jobs.append((lead.id, plan.missing, lead.business_name))

            campaign_run = await self.campaign_repo.create(
                session,
                "resume",
                "queue",
                len(incomplete),
                send_mode == "draft",
            )
            campaign_run_id = campaign_run.id
            emails_sent_today = await self.lead_repo.count_emails_sent_today(session)

        if (
            send_mode in ("instantly", "hybrid")
            and send_mode != "draft"
            and self.instantly.is_configured
            and getattr(self.settings, "instantly_auto_prepare", True)
        ):
            await self.instantly.client.ensure_send_ready(force=False)

        daily_cap = self.settings.max_emails_per_day
        instantly_csv_rows: list[dict[str, str]] = []

        # One DB session per lead — LLM/FTP can take 60s+; savepoints + Postgres break.
        for lead_id, missing, business_name in resume_jobs:
            async with get_session() as session:
                db_lead = await self.lead_repo.get_by_id(session, lead_id)
                if not db_lead:
                    continue
                if is_resume_deferred(db_lead, cooldown):
                    logger.debug(f"[Resume] Deferred {business_name} (cooldown)")
                    continue
                plan = assess_lead(db_lead)
                if not plan.missing:
                    continue
                try:
                    sent = await self._resume_one_lead(
                        session=session,
                        db_lead=db_lead,
                        missing=plan.missing,
                        campaign_run_id=campaign_run_id,
                        send_mode=send_mode,
                        emails_sent_today=emails_sent_today,
                        daily_cap=daily_cap,
                        instantly_csv_rows=instantly_csv_rows,
                    )
                    stats["resumed"] += 1
                    for step in plan.missing:
                        stats["steps_done"][step] = stats["steps_done"].get(step, 0) + 1
                    if sent:
                        stats["sent"] += 1
                        emails_sent_today += 1
                    if assess_lead(db_lead).missing:
                        mark_resume_deferred(db_lead, cooldown)
                except Exception as e:
                    stats["errors"] += 1
                    mark_resume_deferred(db_lead, cooldown)
                    logger.error(f"[Resume] Failed {business_name}: {e}")

        if instantly_csv_rows:
            csv_out = Path("outputs/instantly") / f"resume_{campaign_run_id[:8]}.csv"
            export_instantly_csv(instantly_csv_rows, csv_out)

        logger.success(
            f"[Resume] Done: {stats['resumed']}/{stats['queued']} resumed, "
            f"{stats['sent']} sent, {stats['errors']} errors"
        )
        return stats

    async def _resume_one_lead(
        self,
        session: Any,
        db_lead: Any,
        missing: list[str],
        campaign_run_id: str,
        send_mode: SendMode,
        emails_sent_today: int,
        daily_cap: int,
        instantly_csv_rows: list[dict[str, str]],
    ) -> bool:
        """Run only the missing steps for one stored lead. Returns True if email was sent."""
        from core.lead_resume import (
            STEP_DEMO,
            STEP_DRAFT,
            STEP_EMAIL,
            STEP_PUBLISH,
            STEP_SEND,
            lead_to_maps_scan,
            persist_maps_meta,
        )

        maps_lead = lead_to_maps_scan(db_lead)
        if db_lead.email:
            maps_lead.email = db_lead.email
        if not db_lead.campaign_run_id:
            db_lead.campaign_run_id = campaign_run_id

        # Email-first: drop orphan demos / pending rows with no contact
        if STEP_EMAIL in missing or not maps_has_email(maps_lead):
            if not await self._ensure_email_or_discard(
                session,
                maps_lead,
                campaign_run_id,
                db_lead=db_lead,
            ):
                return False
            missing = [s for s in missing if s != STEP_EMAIL]

        outreach_domain = self._domain_for_lead(db_lead, maps_lead.place_id)

        demo_path = db_lead.demo_site_path
        demo_url = (dict(db_lead.enrichment_data or {})).get("demo_url")

        if STEP_DEMO in missing:
            logger.info(f"[Resume] Generating demo for {maps_lead.business_name}")
            demo_path = await self.scanner.generate_demo_site(maps_lead)
            if demo_path:
                await self.lead_repo.update_after_demo(session, db_lead, demo_path)
                maps_lead.demo_site_path = demo_path
                demo_url = None

        demo_base = outreach_domain.demo_base_url if outreach_domain else None

        if STEP_PUBLISH in missing or (demo_path and not demo_url):
            logger.info(f"[Resume] Publishing demo for {maps_lead.business_name}")
            demo_url = await self._resolve_demo_url(
                demo_path, demo_base_url=demo_base
            )
            persist_maps_meta(db_lead, maps_lead, demo_url=demo_url)
        elif demo_url:
            pass
        elif demo_path:
            demo_url = await self._resolve_demo_url(
                demo_path, demo_base_url=demo_base
            )
            persist_maps_meta(db_lead, maps_lead, demo_url=demo_url)

        if STEP_DRAFT in missing:
            logger.info(f"[Resume] Drafting email for {maps_lead.business_name}")
            draft = await self.email_engine.draft_pitch(
                lead=maps_lead,
                your_name=self.settings.your_name,
                your_business=self.settings.your_business_name or "Digital Agency",
                demo_url=demo_url,
            )
            await self.lead_repo.update_after_draft(
                session,
                db_lead,
                draft["subject"],
                draft["body"],
                email=maps_lead.email,
            )
        else:
            draft = {
                "subject": db_lead.pitch_subject or "",
                "body": db_lead.pitch_body or "",
            }

        persist_maps_meta(db_lead, maps_lead, demo_url=demo_url)
        sent = False

        if STEP_SEND in missing and (maps_lead.email or "").strip():
            already = await self.lead_repo.was_emailed(
                session, maps_lead.place_id, maps_lead.email
            )
            if already:
                logger.warning(
                    f"[Resume] Already sent to {maps_lead.email} — skip send"
                )
            elif send_mode != "draft" and emails_sent_today < daily_cap:
                ch = ""
                if send_mode == "hybrid":
                    sent, ch = await self._send_with_hybrid(
                        maps_lead,
                        draft,
                        demo_url,
                        outreach_domain,
                        instantly_csv_rows,
                        db_lead=db_lead,
                    )
                elif send_mode == "instantly":
                    sent = await self._try_instantly(
                        maps_lead,
                        draft,
                        demo_url,
                        outreach_domain,
                        instantly_csv_rows,
                    )
                    ch = "instantly" if sent else ""
                    if sent and outreach_domain:
                        from utils.mailbox_lock import lock_mailbox_on_lead

                        lock_mailbox_on_lead(
                            db_lead, domain=outreach_domain, send_channel="instantly"
                        )
                elif send_mode == "smtp":
                    sent = self._try_smtp(
                        maps_lead, draft, outreach_domain, db_lead=db_lead
                    )
                    ch = "smtp" if sent else ""
                else:
                    sent = False
                if sent and ch:
                    await self.lead_repo.mark_contacted(
                        session, db_lead, send_channel=ch
                    )
            elif emails_sent_today >= daily_cap:
                logger.warning("[Resume] Daily cap reached — send deferred")

        await session.flush()
        return sent

    async def _process_one_lead(
        self,
        session: Any,
        maps_lead: MapsScanResult,
        campaign_run_id: str,
        send_mode: SendMode,
        emails_sent_today: int,
        daily_cap: int,
        instantly_csv_rows: list[dict[str, str]],
    ) -> CampaignLeadResult:
        result = CampaignLeadResult(
            business_name=maps_lead.business_name,
            place_id=maps_lead.place_id,
            status="processed",
        )

        try:
            db_lead = await self.lead_repo.upsert_inventory_from_maps(
                session, maps_lead, campaign_run_id, for_outreach=True
            )

            # Email-first — no demo/draft until contact email exists
            if not await self._ensure_email_or_discard(
                session, maps_lead, campaign_run_id, db_lead=db_lead
            ):
                result.status = "saved_no_email"
                return result

            result.email = maps_lead.email

            from modules.outreach.website_pitch import (
                cache_pitch_on_lead,
                ensure_website_audit,
            )
            from utils.lead_package_tier import sync_maps_enrichment

            await ensure_website_audit(maps_lead, self.settings)
            cache_pitch_on_lead(maps_lead)
            sync_maps_enrichment(db_lead, maps_lead)
            await self.lead_repo.refresh_package_tier(session, db_lead)

            outreach_domain = self._domain_for_lead(db_lead, maps_lead.place_id)
            if outreach_domain:
                logger.info(
                    f"[Domain] Using '{outreach_domain.name}' for {maps_lead.business_name}"
                )

            if preset_icebreaker(maps_lead):
                logger.info(
                    f"[CSV] Skipping demo for {maps_lead.business_name} "
                    "(using Icebreaker from CSV)"
                )
                demo_path = None
            else:
                demo_path = await self.scanner.generate_demo_site(maps_lead)
            result.demo_path = demo_path or maps_lead.demo_site_path
            if result.demo_path:
                await self.lead_repo.update_after_demo(session, db_lead, result.demo_path)

            demo_base = (
                outreach_domain.demo_base_url if outreach_domain else None
            )
            demo_url = await self._resolve_demo_url(result.demo_path, demo_base_url=demo_base)
            from core.lead_resume import persist_maps_meta

            persist_maps_meta(db_lead, maps_lead, demo_url=demo_url)
            draft = await self.email_engine.draft_pitch(
                lead=maps_lead,
                your_name=self.settings.your_name,
                your_business=self.settings.your_business_name or "Digital Agency",
                demo_url=demo_url,
            )

            await self.lead_repo.update_after_draft(
                session,
                db_lead,
                draft["subject"],
                draft["body"],
                email=maps_lead.email,
            )
            persist_maps_meta(db_lead, maps_lead, demo_url=demo_url)

            if maps_lead.email:
                already_sent = await self.lead_repo.was_emailed(
                    session, maps_lead.place_id, maps_lead.email
                )
                if already_sent:
                    logger.warning(
                        f"[Memory] Already emailed {maps_lead.email} — draft only"
                    )
                    self.email_engine.send_email(
                        to_email=maps_lead.email,
                        subject=draft["subject"],
                        body=draft["body"],
                        dry_run=True,
                    )
                    result.draft_path = str(
                        Path("outputs/emails")
                        / f"draft_{self._safe_path_token(maps_lead.place_id)}.txt"
                    )
                elif send_mode != "draft" and emails_sent_today < daily_cap:
                    sent = False
                    ch = ""
                    if send_mode == "hybrid":
                        sent, ch = await self._send_with_hybrid(
                            maps_lead,
                            draft,
                            demo_url,
                            outreach_domain,
                            instantly_csv_rows,
                            db_lead=db_lead,
                        )
                    elif send_mode == "instantly":
                        sent = await self._try_instantly(
                            maps_lead,
                            draft,
                            demo_url,
                            outreach_domain,
                            instantly_csv_rows,
                        )
                        ch = "instantly" if sent else ""
                        if sent and outreach_domain:
                            from utils.mailbox_lock import lock_mailbox_on_lead

                            lock_mailbox_on_lead(
                                db_lead,
                                domain=outreach_domain,
                                send_channel="instantly",
                            )
                    elif send_mode == "smtp":
                        sent = self._try_smtp(
                            maps_lead, draft, outreach_domain, db_lead=db_lead
                        )
                        ch = "smtp" if sent else ""

                    result.draft_path = self._save_local_draft(
                        maps_lead.email,
                        draft["subject"],
                        draft["body"],
                    )
                    result.sent = sent
                    if sent and ch:
                        await self.lead_repo.mark_contacted(
                            session, db_lead, send_channel=ch
                        )
                else:
                    if emails_sent_today >= daily_cap:
                        logger.warning("Daily email cap reached — draft only")
                    self.email_engine.send_email(
                        to_email=maps_lead.email,
                        subject=draft["subject"],
                        body=draft["body"],
                        dry_run=True,
                    )
                    result.draft_path = self._last_draft_path(maps_lead.email)

        except Exception as e:
            logger.exception(f"Failed processing {maps_lead.business_name}: {e}")
            result.status = "error"
            result.error = str(e)

        return result

    def _last_draft_path(self, email: str) -> str:
        safe = "".join(c if c.isalnum() else "_" for c in email.split("@")[0]).lower()
        return str(Path("outputs/emails") / f"draft_{safe}.txt")


async def run_campaign(
    niche: str,
    city: str,
    leads: int = 10,
    send_mode: SendMode = "draft",
    use_mock: bool = False,
    fresh_mock: bool = False,
    test_to: str | None = None,
    csv_path: str | None = None,
    hunt_mode: str = "m10_no_website",
    settings: Settings | None = None,
) -> CampaignResult:
    """
    One-line campaign entry point.

        result = await run_campaign("plumber", "Austin TX", leads=3, use_mock=True)
        result = await run_campaign(..., send_mode="hybrid")
    """
    orchestrator = CampaignOrchestrator(settings=settings)
    return await orchestrator.run_campaign(
        niche=niche,
        city=city,
        leads=leads,
        send_mode=send_mode,
        use_mock=use_mock,
        fresh_mock=fresh_mock,
        test_to=test_to,
        csv_path=csv_path,
        hunt_mode=hunt_mode,
    )
