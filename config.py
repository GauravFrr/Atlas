"""
Pydantic Settings — validates and loads all environment variables at startup.
If a required variable is missing, the app fails immediately with a clear error.
"""

from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars
    )

    # ══════════════════════════════════════════
    # AGENT
    # ══════════════════════════════════════════
    agent_name: str = Field(default="Atlas")
    agent_env: str = Field(default="development")
    agent_log_level: str = Field(default="INFO")
    agent_loop_interval_minutes: int = Field(
        default=30,
        description="Minutes between autonomous cycles when running start_agent.py",
    )
    dashboard_password: str = Field(default="change_me")
    dashboard_port: int = Field(default=8000)
    database_url: str = Field(
        default="",
        description=(
            "SQLAlchemy async URL. Postgres: postgresql://... (Neon/Supabase). "
            "SQLite: sqlite+aiosqlite:////app/data/agent.db. "
            "Empty = ./agent.db locally, or /app/data/agent.db when volume mounted."
        ),
    )

    # ══════════════════════════════════════════
    # LLM (required)
    # ══════════════════════════════════════════
    gemini_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    # ══════════════════════════════════════════
    # GOOGLE APIs
    # ══════════════════════════════════════════
    gmail_client_id: str = Field(default="")
    gmail_client_secret: str = Field(default="")
    gmail_refresh_token: str = Field(default="")
    gmail_sender_address: str = Field(default="")
    google_places_api_key: str = Field(default="")
    google_analytics_id: str = Field(default="")
    # auto = Google Maps if key set, else free OpenStreetMap; google | osm force one source
    lead_scan_source: str = Field(default="auto")

    # ══════════════════════════════════════════
    # SOCIAL MEDIA
    # ══════════════════════════════════════════
    reddit_client_id: str = Field(default="")
    reddit_secret: str = Field(default="")
    reddit_username: str = Field(default="")
    twitter_bearer_token: str = Field(default="")
    twitter_api_key: str = Field(default="")
    twitter_api_secret: str = Field(default="")
    buffer_access_token: str = Field(default="")
    medium_integration_token: str = Field(default="")

    # ══════════════════════════════════════════
    # PAYMENTS
    # ══════════════════════════════════════════
    razorpay_key_id: str = Field(default="")
    razorpay_key_secret: str = Field(default="")
    razorpay_webhook_secret: str = Field(default="")
    razorpay_default_amount_inr: int = Field(
        default=3999,
        description="Default Razorpay link amount in INR (intro website package)",
    )
    pricing_tiers_file: str = Field(
        default="data/pricing_tiers.json",
        description="USD tier prices → INR via usd_to_inr_rate for payment links",
    )
    usd_to_inr_rate: float = Field(
        default=85.0,
        description="Multiply pricing_tiers USD intro prices to get INR for Razorpay",
    )
    razorpay_payment_link_expire_days: int = Field(default=7)
    binance_api_key: str = Field(default="")
    binance_secret: str = Field(default="")
    binance_pay_id: str = Field(default="")
    usdt_trc20_address: str = Field(default="")

    # ══════════════════════════════════════════
    # DESIGN
    # ══════════════════════════════════════════
    replicate_api_token: str = Field(default="")
    canva_api_key: str = Field(default="")
    unsplash_access_key: str = Field(default="")
    pexels_api_key: str = Field(default="")

    # ══════════════════════════════════════════
    # FREELANCE PLATFORMS
    # ══════════════════════════════════════════
    fiverr_api_key: str = Field(default="")
    fiverr_username: str = Field(default="gauravstack")
    gumroad_access_token: str = Field(default="")

    # ══════════════════════════════════════════
    # COMMUNICATION
    # ══════════════════════════════════════════
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")
    telegram_bot_display_name: str = Field(
        default="Atlas",
        description="Name shown in Telegram bot profile and panel headers",
    )
    telegram_owner_user_ids: str = Field(
        default="",
        description="Comma-separated Telegram user IDs allowed besides TELEGRAM_CHAT_ID (owner-only bot)",
    )
    telegram_close_approval: bool = Field(
        default=True,
        description="Send close-email drafts to Telegram with Approve / Recreate / Skip buttons",
    )
    telegram_auto_draft_on_reply: bool = Field(
        default=True,
        description="Instantly/webhook/sync → draft reply + Telegram approval automatically",
    )
    telegram_use_webhook: bool = Field(
        default=False,
        description="Use webhook mode (auto on Railway when RAILWAY_PUBLIC_DOMAIN is set)",
    )
    telegram_webhook_url: str = Field(
        default="",
        description="Full public webhook URL; default https://RAILWAY_PUBLIC_DOMAIN/telegram/webhook",
    )
    telegram_webhook_path: str = Field(
        default="telegram/webhook",
        description="URL path segment for Telegram POST updates (Railway webhook mode)",
    )
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")

    # ══════════════════════════════════════════
    # DATA ENRICHMENT
    # ══════════════════════════════════════════
    hunter_api_key: str = Field(default="")
    apollo_api_key: str = Field(default="")
    youtube_api_key: str = Field(default="")
    listen_notes_api_key: str = Field(default="")
    producthunt_api_token: str = Field(default="")
    exchangerate_api_key: str = Field(default="")

    # ══════════════════════════════════════════
    # SAFETY LIMITS
    # ══════════════════════════════════════════
    max_emails_per_day: int = Field(default=400)
    max_leads_per_day: int = Field(default=200)
    resume_incomplete_on_start: bool = Field(
        default=True,
        description="On autopilot start, finish stored leads (demo/email/draft/send) before new hunt",
    )
    resume_max_per_run: int = Field(
        default=10,
        description="Max incomplete leads to resume per autopilot cycle",
    )
    resume_cooldown_minutes: int = Field(
        default=25,
        description="Skip re-resuming same incomplete lead within N minutes (Atlas 30m loop)",
    )
    min_lead_score: int = Field(default=6)
    email_cooldown_days: int = Field(default=3)
    max_revisions_per_order: int = Field(default=2)
    quality_score_threshold: float = Field(default=7.0)

    # ══════════════════════════════════════════
    # YOUR INFO
    # ══════════════════════════════════════════
    your_name: str = Field(default="Gaurav")
    your_business_name: str = Field(default="")
    your_email: str = Field(default="")
    your_upi_id: str = Field(default="")
    your_bank_account: str = Field(default="")
    your_wise_email: str = Field(default="")

    # ══════════════════════════════════════════
    # CAMPAIGN / OUTREACH
    # ══════════════════════════════════════════
    demo_site_base_url: str = Field(
        default="",
        description="Public base URL for demo sites (R2 pub URL or custom domain)",
    )
    r2_account_id: str = Field(
        default="",
        description="Cloudflare account ID (for R2 S3 endpoint)",
    )
    r2_access_key_id: str = Field(default="", description="R2 S3 access key ID")
    r2_secret_access_key: str = Field(default="", description="R2 S3 secret access key")
    r2_bucket_name: str = Field(default="agent-demos", description="R2 bucket name")
    r2_endpoint_url: str = Field(
        default="",
        description="R2 S3 endpoint, e.g. https://<account_id>.r2.cloudflarestorage.com",
    )
    r2_auto_upload: bool = Field(
        default=True,
        description="Upload each demo to R2 after generation when credentials are set",
    )
    demo_upload_mode: str = Field(
        default="auto",
        description="auto | netlify | r2 | ftp | local — where to publish demo HTML",
    )
    demo_host_strategy: str = Field(
        default="priority",
        description=(
            "auto mode only: priority = Hostinger sites → Cloudflare R2; "
            "random = shuffle Hostinger sites per demo, then R2"
        ),
    )
    demo_skip_netlify: bool = Field(
        default=True,
        description="If true, Netlify is never used (Hostinger + R2 only)",
    )
    netlify_auth_token: str = Field(
        default="",
        description="Netlify personal access token (Site deploy scope)",
    )
    netlify_site_id: str = Field(
        default="",
        description="Netlify site UUID (from site settings → Site information)",
    )
    netlify_accounts_file: str = Field(
        default="",
        description=(
            "Optional JSON list of extra Netlify sites "
            "(ignored when NETLIFY_ENV_ONLY=true)"
        ),
    )
    netlify_env_only: bool = Field(
        default=True,
        description="If true, demo deploys use only .env NETLIFY_* (not netlify_accounts.json)",
    )
    netlify_skip_primary: bool = Field(
        default=False,
        description="Skip .env primary Netlify site (e.g. clientdemosites out of credits)",
    )
    netlify_credits_min_remaining: int = Field(
        default=50,
        description="Do not deploy if team credits remaining <= this (keep buffer for site to work)",
    )
    netlify_credits_reserve: int = Field(
        default=50,
        description="Reserved credits not used for deploys (250/300 usable ≈ remaining > 50)",
    )
    netlify_deploy_credit_cost: int = Field(
        default=15,
        description="Estimated credits per production deploy (Netlify credit plan)",
    )
    demo_prefer_r2: bool = Field(
        default=False,
        description="If true, R2 runs before Hostinger in auto mode",
    )
    hostinger_sites_file: str = Field(
        default="",
        description="JSON list of Hostinger demo subdomains (data/hostinger_sites.example.json)",
    )
    ftp_host: str = Field(default="", description="FTP host, e.g. ftp.hostinger.com")
    ftp_port: int = Field(default=21, description="FTP port (21 plain, 990 implicit TLS)")
    ftp_user: str = Field(default="", description="FTP username")
    ftp_password: str = Field(default="", description="FTP password")
    ftp_use_tls: bool = Field(
        default=False,
        description="Use explicit FTPS (FTP_TLS). Try false first on Hostinger.",
    )
    ftp_remote_base: str = Field(
        default="public_html/demos",
        description="Remote folder under FTP root for demo sites",
    )
    strict_spam_check: bool = Field(
        default=False,
        description="Block Instantly push when spam_words.txt phrases are found",
    )
    demo_generation_mode: str = Field(
        default="hybrid",
        description=(
            "Demo HTML strategy: hybrid (unique AI site, shell fallback), "
            "creative (AI only), safe (premium shell only)"
        ),
    )
    smtp_provider: str = Field(
        default="custom",
        description="Preset: zoho | google_workspace | microsoft365 | hostinger | namecheap | custom",
    )
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(
        default="",
        description="Login email, e.g. hello@gauravxd.dev",
    )
    smtp_password: str = Field(
        default="",
        description="Mailbox password or app-specific password (not your personal Gmail)",
    )
    smtp_from_email: str = Field(
        default="",
        description="From address in outreach (defaults to smtp_user), e.g. hello@gauravxd.dev",
    )
    smtp_from_name: str = Field(
        default="",
        description="Display name in inbox (defaults to your_name), e.g. Gaurav",
    )
    smtp_reply_to: str = Field(
        default="",
        description="Optional Reply-To (defaults to smtp_from_email)",
    )
    smtp_use_ssl: bool = Field(
        default=False,
        description="True for port 465 (SMTP_SSL); False for 587 + STARTTLS",
    )
    smtp_bcc_self: bool = Field(
        default=True,
        description="BCC sender so a copy appears in Hostinger Inbox (webmail Sent is empty for API sends)",
    )
    smtp_save_to_sent: bool = Field(
        default=True,
        description="After SMTP send, append message to IMAP Sent folder (shows in Hostinger webmail)",
    )
    smtp_imap_host: str = Field(
        default="",
        description="IMAP host for Sent copy (empty = auto from SMTP_PROVIDER, e.g. imap.hostinger.com)",
    )
    m02_sparse_fallback: bool = Field(
        default=True,
        description="If M02 finds 0 outdated sites but OSM returned businesses, use weakest design scores",
    )

    # Instantly.ai — warmed mailboxes on your domain (recommended if you use Instantly)
    instantly_api_key: str = Field(default="", description="Instantly API v2 key (Bearer)")
    instantly_campaign_id: str = Field(
        default="",
        description="UUID of Instantly campaign with 3-step sequence + variables",
    )
    instantly_auto_prepare: bool = Field(
        default=True,
        description=(
            "Before pushing leads: resume paused campaign, resume paused sending "
            "accounts, enable paused warmup (Instantly API)"
        ),
    )
    instantly_reply_sync_limit: int = Field(
        default=50,
        description="Max Instantly Unibox emails to scan per reply-sync run",
    )
    reply_alert_on_unknown: bool = Field(
        default=False,
        description="Telegram alert for replies that are not clearly hot/unsub/not_now",
    )
    instantly_webhook_secret: str = Field(
        default="",
        description="Optional shared secret for POST /webhooks/instantly (set in Instantly UI)",
    )
    reply_sync_interval_minutes: int = Field(
        default=15,
        description="Default interval for run_reply_daemon.py",
    )
    outreach_domains_file: str = Field(
        default="",
        description=(
            "JSON list of domains for rotation (copy outreach_domains.example.json). "
            "Leave empty to use single DEMO_SITE_BASE_URL / SMTP / Instantly only."
        ),
    )
    email_send_mode: str = Field(
        default="draft",
        description=(
            "draft | smtp | instantly | auto | hybrid "
            "(hybrid = random Instantly/SMTP per lead + fallback if one fails)"
        ),
    )

    # ══════════════════════════════════════════
    # VALIDATORS
    # ══════════════════════════════════════════
    @field_validator("agent_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"agent_env must be one of {allowed}, got: {v}")
        return v

    @field_validator("agent_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got: {v}")
        return v_upper

    @field_validator("max_emails_per_day")
    @classmethod
    def validate_email_limit(cls, v: int) -> int:
        if v > 400:
            raise ValueError("max_emails_per_day cannot exceed 400 (hard safety limit)")
        return v

    # ══════════════════════════════════════════
    # COMPUTED PROPERTIES
    # ══════════════════════════════════════════
    @property
    def is_production(self) -> bool:
        return self.agent_env == "production"

    @property
    def is_development(self) -> bool:
        return self.agent_env == "development"

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def has_groq(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def has_gmail(self) -> bool:
        return bool(self.gmail_client_id and self.gmail_refresh_token)

    @property
    def has_razorpay(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def has_binance(self) -> bool:
        return bool(self.binance_api_key and self.binance_secret)

    @property
    def has_telegram(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def telegram_webhook_enabled(self) -> bool:
        import os

        if not self.has_telegram:
            return False
        if (self.telegram_webhook_url or "").strip():
            return True
        if self.telegram_use_webhook:
            return True
        if (os.environ.get("TELEGRAM_USE_WEBHOOK") or "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return True
        return bool(os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip())

    def resolved_telegram_webhook_url(self) -> str:
        import os
        from urllib.parse import urljoin

        explicit = (self.telegram_webhook_url or "").strip().rstrip("/")
        if explicit:
            return explicit
        domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if not domain:
            return ""
        path = (self.telegram_webhook_path or "telegram/webhook").strip("/")
        base = f"https://{domain}/"
        return urljoin(base, path).rstrip("/")

    @property
    def has_smtp(self) -> bool:
        cfg = self.get_smtp_config()
        return bool(cfg.get("host") and cfg.get("user") and cfg.get("password"))

    @property
    def has_instantly(self) -> bool:
        return bool(self.instantly_api_key and self.instantly_campaign_id)

    def _smtp_preset_host_port(self) -> tuple[str, int]:
        from utils.smtp_profiles import SMTP_PRESETS

        key = (self.smtp_provider or "custom").lower().strip()
        preset = SMTP_PRESETS.get(key)
        if not preset:
            return self.smtp_host, self.smtp_port
        if self.smtp_use_ssl:
            return str(preset["host"]), int(preset.get("ssl_port", preset["port"]))
        return str(preset["host"]), int(preset["port"])

    @property
    def r2_endpoint(self) -> str:
        if self.r2_endpoint_url:
            return self.r2_endpoint_url.rstrip("/")
        if self.r2_account_id:
            return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"
        return ""

    @property
    def has_r2(self) -> bool:
        return bool(
            self.r2_access_key_id
            and self.r2_secret_access_key
            and self.r2_bucket_name
            and self.r2_endpoint
            and self.demo_site_base_url
        )

    @property
    def has_netlify(self) -> bool:
        return bool(
            self.netlify_auth_token
            and self.netlify_site_id
            and self.demo_site_base_url
        )

    def get_smtp_config(self) -> dict[str, str | int | bool]:
        host, port = self._smtp_preset_host_port()
        if (self.smtp_provider or "custom").lower().strip() == "custom":
            host = self.smtp_host or host
            port = self.smtp_port if self.smtp_host else port
        from_email = (self.smtp_from_email or self.smtp_user or self.your_email).strip()
        from_name = (self.smtp_from_name or self.your_name).strip()
        reply_to = (self.smtp_reply_to or from_email).strip()
        return {
            "host": host,
            "port": port,
            "user": self.smtp_user,
            "password": self.smtp_password,
            "from_email": from_email,
            "from_name": from_name,
            "reply_to": reply_to,
            "use_ssl": self.smtp_use_ssl,
            "bcc_self": self.smtp_bcc_self,
            "save_to_sent": self.smtp_save_to_sent,
            "imap_host": self.smtp_imap_host,
            "provider": self.smtp_provider,
        }

    def get_enabled_features(self) -> dict:
        """Returns a dict of which features are enabled based on configured keys."""
        return {
            "llm_gemini": self.has_gemini,
            "llm_groq": self.has_groq,
            "email_outreach": self.has_gmail,
            "payment_razorpay": self.has_razorpay,
            "payment_binance": self.has_binance,
            "telegram_alerts": self.has_telegram,
            "lead_google_maps": bool(self.google_places_api_key),
            "lead_osm_free": True,
            "lead_apollo": bool(self.apollo_api_key),
            "lead_outdated_site": True,
            "lead_low_reviews": bool(self.google_places_api_key),
            "lead_reddit": bool(self.reddit_client_id),
            "lead_twitter": bool(self.twitter_bearer_token),
            "image_generation": bool(self.replicate_api_token),
            "email_enrichment": bool(self.hunter_api_key),
            "email_instantly": self.has_instantly,
            "email_smtp": self.has_smtp,
            "email_mailbox_rotation": bool(self.outreach_domains_file),
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Use this everywhere instead of instantiating Settings directly.
    
    Usage:
        from config import get_settings
        settings = get_settings()
    """
    return Settings()
