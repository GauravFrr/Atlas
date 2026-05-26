"""
Agent-Earns: Autonomous AI Earning System
Application-wide constants — no magic strings or numbers anywhere in the code.
"""

# ══════════════════════════════════════════════
# APPLICATION
# ══════════════════════════════════════════════
APP_NAME = "Agent-Earns"
APP_VERSION = "1.0.0"
AGENT_DEFAULT_NAME = "Atlas"

# ══════════════════════════════════════════════
# AGENT STATES
# ══════════════════════════════════════════════
class AgentState:
    STARTING = "STARTING"
    IDLE = "IDLE"
    WORKING = "WORKING"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    SLEEPING = "SLEEPING"
    SHUTDOWN = "SHUTDOWN"

# ══════════════════════════════════════════════
# TASK PRIORITIES
# ══════════════════════════════════════════════
class Priority:
    IMMEDIATE = 1   # New Fiverr order, payment webhook, client reply
    URGENT = 2      # Follow-ups due, pending deliverables
    STANDARD = 3    # New leads to contact, content to publish
    LOW = 4         # Hunt for new leads, write content
    WEEKLY = 5      # Performance analysis, strategy update

# ══════════════════════════════════════════════
# LLM MODELS
# ══════════════════════════════════════════════
class LLMModel:
    GEMINI_PRO = "gemini-2.5-pro"
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_FLASH_LITE = "gemini-2.5-flash"
    GROQ_70B = "llama-3.3-70b-versatile"
    GROQ_8B = "llama-3.1-8b-instant"


# ══════════════════════════════════════════════
# LLM TASK COMPLEXITY LEVELS
# ══════════════════════════════════════════════
class TaskComplexity:
    CRITICAL = "CRITICAL"    # → Gemini Pro
    STANDARD = "STANDARD"    # → Gemini Flash
    SIMPLE = "SIMPLE"        # → Gemini Flash Lite
    FALLBACK = "FALLBACK"    # → Groq 70B
    FASTEST = "FASTEST"      # → Groq 8B

# ══════════════════════════════════════════════
# LEAD STATUS
# ══════════════════════════════════════════════
class LeadStatus:
    NEW = "new"
    DRAFT_READY = "draft_ready"       # Demo + email draft saved, not sent
    PENDING_EMAIL = "pending_email"   # No email found — demo/draft only
    CONTACTED = "contacted"
    REPLIED = "replied"
    CLIENT = "client"
    REJECTED = "rejected"
    UNSUBSCRIBED = "unsubscribed"
    SKIPPED = "skipped"               # Duplicate or filtered out

# ══════════════════════════════════════════════
# LEAD SCORING THRESHOLDS
# ══════════════════════════════════════════════
LEAD_SCORE_HOT = 9       # Contact same day + mockup
LEAD_SCORE_WARM = 6      # Contact in batch
LEAD_SCORE_COLD = 3      # Contact only when hot exhausted
LEAD_SCORE_SKIP = 0      # Not worth contacting

# ══════════════════════════════════════════════
# EMAIL SEQUENCE STEPS (0-indexed)
# ══════════════════════════════════════════════
class EmailSequenceStep:
    COLD_OUTREACH = 0    # Day 0: Hook + mockup
    FOLLOW_UP_1 = 1      # Day 4: Value add tip
    FOLLOW_UP_2 = 2      # Day 8: Social proof
    FOLLOW_UP_3 = 3      # Day 14: Different angle
    BREAKUP = 4          # Day 21: Breakup email

EMAIL_SEQUENCE_DAYS = [0, 4, 8, 14, 21]  # Days for each step

# ══════════════════════════════════════════════
# EMAIL QUALITY THRESHOLDS
# ══════════════════════════════════════════════
EMAIL_MAX_WORDS = 150
EMAIL_MIN_PERSONALIZATION_SCORE = 7.0
EMAIL_MAX_SPAM_SCORE = 3.0
EMAIL_MIN_HUMAN_TONE_SCORE = 8.0
EMAIL_MAX_BOUNCE_RATE = 0.05  # 5% — pause if exceeded

# ══════════════════════════════════════════════
# ORDER STATUS
# ══════════════════════════════════════════════
class OrderStatus:
    NEW = "new"
    CLARIFYING = "clarifying"
    IN_PROGRESS = "in_progress"
    QUALITY_CHECK = "quality_check"
    READY = "ready"
    DELIVERED = "delivered"
    REVISION = "revision"
    COMPLETED = "completed"

# ══════════════════════════════════════════════
# PAYMENT STATUS
# ══════════════════════════════════════════════
class PaymentStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"

# ══════════════════════════════════════════════
# PAYMENT PROVIDERS
# ══════════════════════════════════════════════
class PaymentProvider:
    RAZORPAY = "razorpay"
    BINANCE = "binance"
    WISE = "wise"
    FIVERR = "fiverr"
    UPI_DIRECT = "upi_direct"

# ══════════════════════════════════════════════
# QUALITY CONTROL
# ══════════════════════════════════════════════
QUALITY_SCORE_AUTO_APPROVE = 9.0
QUALITY_SCORE_HUMAN_REVIEW = 7.0
QUALITY_SCORE_AUTO_FIX = 5.0
QUALITY_MAX_REGEN_ATTEMPTS = 3

# ══════════════════════════════════════════════
# LEAD SOURCES
# ══════════════════════════════════════════════
class LeadSource:
    GOOGLE_MAPS = "google_maps"
    REDDIT = "reddit"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    CRAIGSLIST = "craigslist"
    PRODUCT_HUNT = "producthunt"
    INDIE_HACKERS = "indiehackers"
    YELP = "yelp"
    FACEBOOK = "facebook"
    NEXTDOOR = "nextdoor"

# ══════════════════════════════════════════════
# REPLY CLASSIFICATIONS
# ══════════════════════════════════════════════
class ReplyCategory:
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    TOO_EXPENSIVE = "too_expensive"
    WRONG_PERSON = "wrong_person"
    NEEDS_INFO = "needs_info"
    REFERRAL = "referral"
    SCHEDULE_CALL = "schedule_call"

# ══════════════════════════════════════════════
# SERVICE TYPES
# ══════════════════════════════════════════════
class ServiceType:
    COLD_EMAIL_SEQUENCE = "cold_email_sequence"
    SEO_BLOG_POST = "seo_blog_post"
    LANDING_PAGE = "landing_page"
    AI_CHATBOT = "ai_chatbot"
    SOCIAL_MEDIA_PACK = "social_media_pack"
    AD_COPY = "ad_copy"
    YOUTUBE_SCRIPT = "youtube_script"
    BRAND_KIT = "brand_kit"
    PODCAST_NOTES = "podcast_notes"
    LINKEDIN_PROFILE = "linkedin_profile"
    CASE_STUDY = "case_study"
    PITCH_DECK = "pitch_deck"
    PRESS_RELEASE = "press_release"
    WHATSAPP_CHATBOT = "whatsapp_chatbot"
    FULL_WEBSITE = "full_website"
    # Recurring
    SOCIAL_MEDIA_MGMT = "social_media_management"
    CHATBOT_MAINTENANCE = "chatbot_maintenance"
    CONTENT_RETAINER = "content_retainer"
    LEAD_GEN_SERVICE = "lead_gen_service"
    WHITE_LABEL = "white_label"

# ══════════════════════════════════════════════
# EARNING METHODS (All 40 Methods)
# ══════════════════════════════════════════════
class EarningMethod:
    # Category A: Lead Hunting & Outreach
    BROKEN_LINK_OUTREACH = "m01_broken_link"
    OUTDATED_WEBSITE = "m02_outdated_website"
    REDDIT_LEAD_MINING = "m03_reddit_mining"
    GOOGLE_REVIEWS = "m04_google_reviews"
    JOB_BOARD_SCRAPER = "m05_job_board"
    YOUTUBE_AUDITOR = "m06_youtube_auditor"
    APP_REVIEW_MINER = "m07_app_review_miner"
    ETSY_AMAZON_OPTIMIZER = "m08_etsy_amazon"
    COLD_DM_SOCIAL = "m09_cold_dm"
    GOOGLE_MAPS_SCANNER = "m10_google_maps"
    LINKEDIN_JOB_MONITOR = "m11_linkedin_jobs"
    PRODUCTHUNT_MONITOR = "m12_producthunt"
    FORUM_ANSWER_MARKETING = "m13_forum_answers"
    SAAS_CHURN_EMAIL = "m14_saas_churn"
    SHOPIFY_AUDITOR = "m15_shopify_auditor"
    PODCAST_OUTREACH = "m16_podcast_outreach"
    COLD_EMAIL_CORE = "m17_cold_email_core"

    # Category B: Content & Passive Income
    NICHE_BLOG = "m18_niche_blog"
    NEWSLETTER_SPONSOR = "m19_newsletter"
    TWITTER_GHOSTWRITING = "m20_twitter_ghostwriting"
    MEDIUM_SUBSTACK = "m21_medium_substack"
    GITHUB_SPONSORS = "m22_github_sponsors"
    YOUTUBE_SCRIPTS = "m23_youtube_scripts"

    # Category C: Service Delivery
    AI_CHATBOT_BUILDER = "m24_chatbot_builder"
    WEBSITE_BUILDER = "m25_website_builder"
    LEAD_GEN_SERVICE = "m26_lead_gen_service"
    CONTENT_RETAINER = "m27_content_retainer"
    SEO_AUDIT = "m28_seo_audit"
    EMAIL_SEQUENCE = "m29_email_sequence"
    AUTOMATION_SETUP = "m30_automation_setup"

    # Category D: Digital Products & Arbitrage
    PROMPT_PACKS = "m31_prompt_packs"
    NOTION_TEMPLATES = "m32_notion_templates"
    EBOOK_SELLER = "m33_ebook_seller"
    DOMAIN_FLIPPING = "m34_domain_flipping"
    WHITE_LABEL = "m35_white_label"

    # Category E: Platform & Marketplace
    FIVERR_AUTO_FULFILLMENT = "m36_fiverr"
    UPWORK_AUTO_BIDDING = "m37_upwork"
    FREELANCER_MONITOR = "m38_freelancer"
    MICRO_SAAS = "m39_micro_saas"
    APPSUMO_LAUNCH = "m40_appsumo"

# ══════════════════════════════════════════════
# NOTIFICATION PRIORITY
# ══════════════════════════════════════════════
class NotifyPriority:
    INFO = "info"
    WARN = "warn"
    URGENT = "urgent"

# ══════════════════════════════════════════════
# ERROR CATEGORIES
# ══════════════════════════════════════════════
class ErrorCategory:
    FATAL = "FATAL"       # Stop agent, alert immediately
    CRITICAL = "CRITICAL" # Alert human, degrade gracefully
    WARNING = "WARNING"   # Log, continue
    INFO = "INFO"         # Log only

# ══════════════════════════════════════════════
# SCHEDULER TIMINGS (IST - UTC+5:30)
# ══════════════════════════════════════════════
SCHEDULER_TIMEZONE = "Asia/Kolkata"

class JobSchedule:
    HEALTH_CHECK_STARTUP = "06:00"
    LEAD_HUNTING = "08:00"
    CONTENT_PUBLISHING = "09:00"
    EMAIL_SENDING_AM = "11:00"
    EMAIL_SENDING_PM = "14:00"
    SOCIAL_SCHEDULING = "19:00"
    PERFORMANCE_LOG = "21:00"
    DB_BACKUP = "23:00"
    PAYMENT_MONITOR_INTERVAL_MINS = 15
    FIVERR_MONITOR_INTERVAL_MINS = 30
    REPLY_CHECKER_INTERVAL_HRS = 2
    FOLLOWUP_CHECK_INTERVAL_HRS = 6
    HEALTH_CHECK_INTERVAL_HRS = 1
    PERFORMANCE_REVIEW_DAY = "sunday"
    PERFORMANCE_REVIEW_TIME = "22:00"

# ══════════════════════════════════════════════
# CIRCUIT BREAKER
# ══════════════════════════════════════════════
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3
CIRCUIT_BREAKER_TIMEOUT_SECONDS = 60
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 300

# ══════════════════════════════════════════════
# RATE LIMITS (per platform)
# ══════════════════════════════════════════════
RATE_LIMITS = {
    "gmail": {"daily": 400, "per_minute": 10},
    "google_places": {"per_minute": 10, "daily": 1000},
    "reddit": {"per_minute": 60},
    "twitter": {"per_15min": 15},
    "linkedin": {"per_hour": 30},
    "replicate": {"per_minute": 5},
    "hunter": {"daily": 25},
    "gemini_pro": {"per_minute": 30, "daily": 500},
    "gemini_flash": {"per_minute": 60, "daily": 1500},
    "groq_70b": {"per_minute": 30, "daily": 14400},
}

# ══════════════════════════════════════════════
# CONTENT
# ══════════════════════════════════════════════
BLOG_POST_MIN_WORDS = 1500
BLOG_POST_MAX_WORDS = 2500
SOCIAL_PACK_POST_COUNT = 30
SEO_TITLE_MAX_CHARS = 60
SEO_META_MAX_CHARS = 160

# ══════════════════════════════════════════════
# FILE PATHS
# ══════════════════════════════════════════════
OUTPUTS_DIR = "outputs"
LOGS_DIR = "logs"
DATA_DIR = "data"
PROMPTS_DIR = "prompts"
TEMPLATES_DIR = "modules/website_builder/templates"

# ══════════════════════════════════════════════
# CURRENCY
# ══════════════════════════════════════════════
# PRIMARY: USD (foreign clients — US, UK, AU, CA, UAE)
# SECONDARY: INR (Indian clients — fallback only)
DEFAULT_CURRENCY = "USD"
SUPPORTED_CURRENCIES = ["USD", "GBP", "AUD", "CAD", "EUR", "USDT", "INR"]

# ══════════════════════════════════════════════
# TARGET MARKETS (in priority order)
# ══════════════════════════════════════════════
# Foreign clients pay 5-10x more than local Indian clients.
# Always exhaust foreign pipeline before targeting India.
TARGET_MARKETS_PRIORITY = [
    "usa_primary",       # Biggest market, most businesses, best pay
    "uk_primary",        # Strong pound, high quality expectations
    "australia_primary", # AUD strong, small businesses underserved
    "canada_primary",    # CAD solid, similar culture to USA
    "uae_primary",       # No tax, high spenders
    "singapore",         # Very high per-capita income
    "new_zealand",       # Similar to AU, less competition
    "india_tier1",       # Only if foreign pipeline < 50 leads
    "india_tier2",       # Last resort
]
