"""
Agent Constitution — Immutable rules.
This file defines what the agent CAN and CANNOT do, forever.
DO NOT MODIFY THIS FILE without explicit human approval.

The constitution is loaded once at startup and enforced at every action.
Any attempt to perform a FORBIDDEN action raises ConstitutionViolationError.
"""

from exceptions import ConstitutionViolationError
from loguru import logger


# ══════════════════════════════════════════════════════════════
# IMMUTABLE ALLOWED ACTIONS
# ══════════════════════════════════════════════════════════════

ALLOWED_ACTIONS: frozenset[str] = frozenset([
    "read_files_in_project_directory",
    "write_files_to_outputs",
    "call_whitelisted_apis",
    "query_own_database",
    "send_emails_from_configured_account",
    "post_content_to_connected_platforms",
    "generate_payment_links",
    "monitor_incoming_payments",
    "send_telegram_alerts",
    "schedule_own_jobs",
    "log_own_activity",
    "read_lead_sources",
    "scrape_public_websites",
    "generate_content_with_llm",
    "create_website_files",
    "create_chatbot_widget",
    "generate_images_via_api",
    "create_invoices",
    "classify_email_replies",
    "draft_email_replies",           # Draft only — human approves sends
    "analyze_own_performance",
    "update_strategy_config",
    "run_quality_checks",
])

# ══════════════════════════════════════════════════════════════
# IMMUTABLE FORBIDDEN ACTIONS
# ══════════════════════════════════════════════════════════════

FORBIDDEN_ACTIONS: frozenset[str] = frozenset([
    "transfer_any_money",
    "approve_any_payment",
    "withdraw_from_any_account",
    "deliver_without_human_review_flag",
    "modify_constitution_file",
    "delete_database_records",
    "access_files_outside_project",
    "call_non_whitelisted_urls",
    "send_more_than_400_emails_per_day",
    "contact_same_lead_within_3_days",
    "execute_arbitrary_code",
    "install_packages_automatically",
    "modify_agent_core_code",
    "bypass_quality_gates",
    "send_email_without_unsubscribe",
    "store_payment_card_data",
    "access_user_passwords",
])

# ══════════════════════════════════════════════════════════════
# HUMAN APPROVAL REQUIRED
# ══════════════════════════════════════════════════════════════

HUMAN_REQUIRED_FOR: frozenset[str] = frozenset([
    "any_payment_confirmation",
    "final_order_delivery",
    "strategy_major_changes",
    "new_api_key_addition",
    "budget_decisions",
    "sending_reply_to_hot_lead",
    "removing_lead_from_blacklist",
    "increasing_daily_email_limit",
    "deploying_to_production",
])

# ══════════════════════════════════════════════════════════════
# WHITELISTED API DOMAINS
# ══════════════════════════════════════════════════════════════

WHITELISTED_DOMAINS: frozenset[str] = frozenset([
    "generativelanguage.googleapis.com",   # Gemini
    "api.groq.com",                         # Groq
    "gmail.googleapis.com",                 # Gmail
    "maps.googleapis.com",                  # Google Maps
    "nominatim.openstreetmap.org",          # OSM geocode (free leads)
    "overpass-api.de",                      # OSM Overpass (free leads)
    "photon.komoot.io",                     # OSM geocode fallback (free)
    "api.razorpay.com",                     # Razorpay
    "api.binance.com",                      # Binance
    "api.telegram.org",                     # Telegram
    "api.twitter.com",                      # Twitter
    "oauth.reddit.com",                     # Reddit
    "api.praw.rocks",                       # Reddit PRAW
    "api.medium.com",                       # Medium
    "api.bufferapp.com",                    # Buffer
    "api.unsplash.com",                     # Unsplash
    "api.pexels.com",                       # Pexels
    "api.replicate.com",                    # Replicate
    "api.hunter.io",                        # Hunter.io
    "api.apollo.io",                        # Apollo lead search
    "www.googleapis.com",                     # YouTube Data API
    "itunes.apple.com",                     # App Store search
    "rss.indeed.com",                       # Job board RSS
    "www.reddit.com",                       # Reddit public JSON
    "api.stackexchange.com",                # Forum questions
    "www.etsy.com",                         # Etsy listings
    "www.producthunt.com",                  # ProductHunt feed
    "listen-api.listennotes.com",           # Podcast search
    "v6.exchangerate-api.com",              # Exchange rates
    "api.gumroad.com",                      # Gumroad
    "api.fiverr.com",                       # Fiverr
    "api.wise.com",                         # Wise
])


class AgentConstitution:
    """
    Enforces the agent's immutable rules.
    Use check_action() before any significant agent action.
    """

    def check_action(self, action: str) -> None:
        """
        Validates that an action is allowed.
        Raises ConstitutionViolationError if the action is forbidden.
        """
        if action in FORBIDDEN_ACTIONS:
            logger.critical(f"CONSTITUTION VIOLATION BLOCKED: {action}")
            raise ConstitutionViolationError(action)

        if action not in ALLOWED_ACTIONS:
            # Unknown action — log warning but don't block (allow extension)
            logger.warning(f"Unknown action attempted (not in whitelist): {action}")

    def requires_human_approval(self, action: str) -> bool:
        """Returns True if this action requires a human to approve it."""
        return action in HUMAN_REQUIRED_FOR

    def is_domain_whitelisted(self, domain: str) -> bool:
        """Returns True if the domain is on the API whitelist."""
        return any(domain.endswith(allowed) for allowed in WHITELISTED_DOMAINS)

    def get_summary(self) -> dict:
        return {
            "allowed_actions": len(ALLOWED_ACTIONS),
            "forbidden_actions": len(FORBIDDEN_ACTIONS),
            "human_required_actions": len(HUMAN_REQUIRED_FOR),
            "whitelisted_domains": len(WHITELISTED_DOMAINS),
        }
