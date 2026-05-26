# 🤖 AUTONOMOUS AI EARNING AGENT
## Ultimate Production-Grade Blueprint v3.0
### Advanced Architecture | Full Stack | Enterprise Level
#### Owner: Mikey (gauravstack) | Started: May 2026

---

> **Vision:** A fully autonomous, self-improving AI agent that discovers clients, delivers premium services, processes payments, and compounds its own earnings — running 24/7 with enterprise-grade reliability, zero downtime, and minimal human intervention.

---

# 📋 MASTER TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [System Philosophy](#2-system-philosophy)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Full Tech Stack](#4-full-tech-stack)
5. [Advanced Folder Structure](#5-advanced-folder-structure)
6. [Core Brain Architecture](#6-core-brain-architecture)
7. [LLM Strategy](#7-llm-strategy)
8. [All Earning Modules](#8-all-earning-modules)
9. [Customer Acquisition System](#9-customer-acquisition-system)
10. [Quality Control System](#10-quality-control-system)
11. [Payment Infrastructure](#11-payment-infrastructure)
12. [Database Architecture](#12-database-architecture)
13. [API Integration Layer](#13-api-integration-layer)
14. [Security Architecture](#14-security-architecture)
15. [Scheduler & Job System](#15-scheduler--job-system)
16. [Dashboard & Monitoring](#16-dashboard--monitoring)
17. [Self-Improvement Engine](#17-self-improvement-engine)
18. [Error Handling & Recovery](#18-error-handling--recovery)
19. [Deployment Architecture](#19-deployment-architecture)
20. [Earning Methods (Complete)](#20-earning-methods-complete)
21. [Pricing Strategy](#21-pricing-strategy)
22. [Payment Flow (Complete)](#22-payment-flow-complete)
23. [Environment & Setup](#23-environment--setup)
24. [Build Order & Timeline](#24-build-order--timeline)
25. [Accounts Required](#25-accounts-required)
26. [Income Projections](#26-income-projections)
27. [Risk Management](#27-risk-management)
28. [Agent Constitution & Rules](#28-agent-constitution--rules)
29. [Prompt Engineering Strategy](#29-prompt-engineering-strategy)
30. [Complete Checklist](#30-complete-checklist)

---

# 1. EXECUTIVE SUMMARY

## What We're Building

A **production-grade autonomous AI agent** that operates as a full digital business. It does not just automate tasks — it runs an entire freelancing operation end-to-end.

## Core Capabilities

```
🔍 DISCOVER  → Finds clients across 10+ platforms autonomously
📧 OUTREACH  → Sends personalized, context-aware cold emails
🏗️ BUILD     → Generates websites, chatbots, content, designs
💰 EARN      → Processes payments via 4 methods automatically
📈 IMPROVE   → Analyzes performance and upgrades its own strategy
🔄 SCALE     → Compounds earnings by doing more of what works
```

## What Makes This Production-Grade

```
✅ Clean Architecture (not spaghetti code)
✅ Repository Pattern (no raw SQL in business logic)
✅ Dependency Injection (testable, swappable components)
✅ Async-first (non-blocking, handles multiple tasks)
✅ Circuit Breakers (fails gracefully, recovers automatically)
✅ Rate Limiting (never gets banned from any platform)
✅ Full Test Coverage (unit + integration tests)
✅ Structured Logging (every action traceable)
✅ Webhook-based payments (real-time, not polling)
✅ Self-healing (detects + recovers from its own errors)
✅ Versioned Prompts (every LLM prompt tracked like code)
✅ Hot-reloadable Config (change settings without restart)
```

## Cost to Run

```
Infrastructure:    $0 (Railway free tier)
LLM Inference:     $0 (Gemini + Groq free tiers)
Database:          $0 (SQLite local)
Email Sending:     $0 (Gmail API free)
Scraping:          $0 (Playwright + httpx)
Design Gen:        $0 (Replicate free credits)

TOTAL MONTHLY COST: $0
```

---

# 2. SYSTEM PHILOSOPHY

## Core Principles

### 1. Earn First, Scale Later
```
Agent doesn't try to do everything at once.
It focuses on what makes money fastest first.
Then reinvests time into passive/scaling methods.
```

### 2. Quality Over Volume
```
Agent sends 20 perfect emails > 200 generic ones.
Every deliverable is reviewed 3 times before delivery.
One happy client = 3 referrals.
```

### 3. Human In The Loop (For What Matters)
```
Agent handles: finding, generating, quality checking
Human handles: deal closing, final approval, strategy

Agent never: sends money, commits code, makes promises
Human always: approves payments, reviews edge cases
```

### 4. Data-Driven Everything
```
Every action is logged.
Every result is measured.
Every week the agent analyzes what worked.
Every month strategy is updated based on data.
```

### 5. Fail Safe, Not Fail Hard
```
API down? → Use fallback API
LLM hallucinating? → Retry with different prompt
Email bounced? → Mark lead, move on
Payment failed? → Alert human, wait
Rate limited? → Back off, continue later
```

---

# 3. HIGH-LEVEL ARCHITECTURE

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS AGENT SYSTEM                       │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      CORE BRAIN LAYER                        │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │    │
│  │  │  Agent   │  │ Decision │  │ Planner  │  │  State   │   │    │
│  │  │ Manager  │  │ Engine   │  │          │  │ Machine  │   │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │    │
│  └───────┼─────────────┼─────────────┼──────────────┼──────────┘    │
│          └─────────────┴─────────────┴──────────────┘               │
│                                  │                                    │
│  ┌───────────────────────────────▼─────────────────────────────┐    │
│  │                      LLM ROUTER LAYER                        │    │
│  │   Gemini 2.5 Pro │ Gemini 2.0 Flash │ Groq Llama 3.3        │    │
│  │   (Complex tasks)│ (Fast bulk tasks) │ (Simple/fallback)     │    │
│  └───────────────────────────────┬─────────────────────────────┘    │
│                                  │                                    │
│  ┌───────────────────────────────▼─────────────────────────────┐    │
│  │                      MODULE LAYER                             │    │
│  │  Lead    │ Outreach │ Website │ Chatbot │ Content │ Design   │    │
│  │  Finder  │ Engine   │ Builder │ Builder │ Writer  │ Engine   │    │
│  │          │          │         │         │         │          │    │
│  │  Service │ Social   │ Payment │ Report  │ Digital │ White    │    │
│  │  Delivery│ Manager  │ Handler │ Engine  │ Products│ Label    │    │
│  └───────────────────────────────┬─────────────────────────────┘    │
│                                  │                                    │
│  ┌───────────────────────────────▼─────────────────────────────┐    │
│  │                    QUALITY CONTROL LAYER                      │    │
│  │         3-Pass Review → Auto-Fix → Score → Flag/Deliver      │    │
│  └───────────────────────────────┬─────────────────────────────┘    │
│                                  │                                    │
│  ┌──────────────┬────────────────▼───────────────┬──────────────┐   │
│  │  INTEGRATION │      DATA LAYER                │  SECURITY    │   │
│  │  LAYER       │   SQLite + Repositories        │  LAYER       │   │
│  │  Gmail       │   Leads | Orders | Payments    │  Auth        │   │
│  │  Razorpay    │   Content | Performance        │  Audit Log   │   │
│  │  Binance     │   Clients | Emails             │  Rate Guard  │   │
│  │  Gemini API  │                                │  Sandbox     │   │
│  └──────────────┴────────────────────────────────┴──────────────┘   │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                   MONITORING LAYER                            │    │
│  │   FastAPI Dashboard │ Telegram Alerts │ Structured Logs      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## The Agent Loop (Detailed)

```
STARTUP
    │
    ▼
LOAD CONFIGURATION
→ Read .env
→ Validate all API keys
→ Check DB connection
→ Register all modules
→ Start scheduler
    │
    ▼
HEALTH CHECK
→ Ping all external APIs
→ Verify Gmail connected
→ Verify DB accessible
→ Alert if anything down
    │
    ▼
━━━━━━━━━━━━━━━━━━ MAIN LOOP (every 30 mins) ━━━━━━━━━━━━━━━━━━
    │
    ▼
READ AGENT STATE
→ Current balance/earnings
→ Pending orders count
→ Unread email replies
→ Leads in pipeline
→ Content scheduled
    │
    ▼
DECISION ENGINE
Priority 1: New Fiverr orders? → Handle immediately
Priority 2: Email replies? → Draft responses
Priority 3: Pending deliverables? → Complete them
Priority 4: Follow-ups due? → Send sequences
Priority 5: Leads to contact? → Send cold emails
Priority 6: Content to post? → Write + publish
Priority 7: New leads needed? → Hunt platforms
Priority 8: Nothing urgent → Self-improve + plan
    │
    ▼
EXECUTE SELECTED TASK
    │
    ├── Call module manager
    ├── Module calls LLM router (if needed)
    ├── LLM router picks model based on task
    ├── Module calls integrations (if needed)
    ├── Quality control checks output
    ├── Repository saves results to DB
    └── Logger records everything
    │
    ▼
POST-EXECUTION
→ Update task status in DB
→ Send Telegram alert if human needed
→ Log performance metric
→ Update agent memory
    │
    ▼
SLEEP UNTIL NEXT TICK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# 4. FULL TECH STACK

## Language & Runtime

| Component | Choice | Version | Why |
|---|---|---|---|
| Language | Python | 3.11+ | Best AI/automation ecosystem |
| Package Manager | uv | Latest | 10x faster than pip |
| Virtual Env | uv venv | Latest | Isolated dependencies |
| Type Checking | mypy | Latest | Catch bugs before runtime |
| Formatting | ruff | Latest | Fast linting + formatting |

## Agent Framework

| Component | Choice | Why |
|---|---|---|
| Agent Orchestration | LangGraph | Production-grade stateful agents |
| Tool Management | LangChain Tools | Structured tool definitions |
| Memory | Custom SQLite | Full control, no cost |
| State Management | Custom StateStore | Persists across restarts |

## LLM Layer

| Model | Provider | Use Case | Cost |
|---|---|---|---|
| Gemini 2.5 Pro | Google AI Studio | Complex reasoning, quality work | Free tier |
| Gemini 2.0 Flash | Google AI Studio | Fast bulk tasks, emails | Free tier |
| Gemini 2.0 Flash-Lite | Google AI Studio | Simple classifications | Free tier |
| Llama 3.3 70B | Groq | Ultra-fast fallback | Free tier |
| Llama 3.1 8B | Groq | Simple/fast tasks | Free tier |

## Web & Scraping

| Component | Choice | Why |
|---|---|---|
| Browser Automation | Playwright (async) | Faster than Selenium, modern |
| HTML Parsing | BeautifulSoup4 | Industry standard |
| HTTP Client | httpx (async) | Async, retry built-in |
| JavaScript Sites | Playwright | Handles SPAs |
| Rate Limiting | slowapi + custom | Per-platform limits |
| Proxy Rotation | rotating-proxies | Avoid IP bans |

## Data Layer

| Component | Choice | Why |
|---|---|---|
| Database | SQLite | Zero cost, zero config, sufficient |
| ORM | SQLAlchemy 2.0 | Modern async ORM |
| Migrations | Alembic | Production DB migrations |
| Cache | diskcache | Fast local caching |
| File Storage | Local + GitHub | Free, versioned |
| Backup | GitHub Actions | Automated daily backup |

## API & Server

| Component | Choice | Why |
|---|---|---|
| Web Framework | FastAPI | Async, fast, auto-docs |
| ASGI Server | uvicorn | Production ASGI |
| WebSockets | FastAPI WS | Real-time dashboard |
| Background Tasks | APScheduler | Production scheduling |
| Process Manager | supervisord | Keeps agent alive |

## Notifications

| Component | Choice | Why |
|---|---|---|
| Real-time Alerts | Telegram Bot API | Instant, free, mobile |
| Email Alerts | Gmail API | Backup notifications |
| Dashboard | FastAPI + Chart.js | Visual monitoring |
| Logs | Loguru | Beautiful structured logs |

## Design & Media

| Component | Choice | Why |
|---|---|---|
| AI Image Gen | Replicate (SDXL) | Free credits, high quality |
| Image Processing | Pillow | Standard Python imaging |
| SVG Handling | cairosvg | Vector graphics |
| PDF Generation | reportlab | Invoice + report PDFs |
| HTML to PDF | weasyprint | Website previews as PDF |

## Payments

| Provider | Use Case | Fee | API |
|---|---|---|---|
| Razorpay | Indian clients | 2% | Full API + webhooks |
| Binance Pay | Crypto clients | 0.1% | Official API |
| Wise | International | ~1% | Manual (share details) |
| Fiverr | Gig marketplace | 20% | Official API |
| UPI Direct | Small Indian | Free | QR code sharing |

## Deployment

| Component | Choice | Cost |
|---|---|---|
| Primary Host | Railway.app | Free tier |
| Backup Host | Render.com | Free tier |
| Code Storage | GitHub | Free |
| CI/CD | GitHub Actions | Free |
| SSL | Cloudflare | Free |
| Uptime Monitor | UptimeRobot | Free |
| Cron Keepalive | cron-job.org | Free |

---

# 5. ADVANCED FOLDER STRUCTURE

```
autonomous-agent/
│
├── 📄 main.py                              ← Master bootstrap + startup sequence
├── 📄 config.py                            ← Pydantic settings (validates all env vars)
├── 📄 constants.py                         ← App-wide constants (no magic strings/numbers)
├── 📄 exceptions.py                        ← Custom exception hierarchy
├── 📄 dependencies.py                      ← Shared dependency injection container
│
├── 📄 .env                                 ← All secrets (gitignored always)
├── 📄 .env.example                         ← Fully documented env template
├── 📄 .env.test                            ← Test environment (fake API keys)
├── 📄 .env.staging                         ← Staging environment
│
├── 📄 pyproject.toml                       ← Project metadata + all tool configs
├── 📄 requirements.txt                     ← Pinned production deps
├── 📄 requirements-dev.txt                 ← Dev deps (pytest, mypy, ruff)
├── 📄 Makefile                             ← make run | make test | make deploy | make lint
├── 📄 Dockerfile                           ← Multi-stage optimized build
├── 📄 docker-compose.yml                   ← Local dev stack
├── 📄 docker-compose.prod.yml              ← Production overrides
├── 📄 railway.toml                         ← Railway deployment
├── 📄 render.yaml                          ← Render.com backup deployment
├── 📄 .dockerignore
├── 📄 .gitignore
├── 📄 README.md
├── 📄 CHANGELOG.md                         ← Version history
│
│
├── 🧠 core/                                ← AGENT BRAIN
│   ├── __init__.py
│   ├── agent.py                            ← Master Agent class
│   │                                          → Lifecycle: startup/run/shutdown
│   │                                          → Registers all modules
│   │                                          → Handles global exceptions
│   │                                          → Manages agent state
│   │
│   ├── loop.py                             ← Main execution loop
│   │                                          → Runs every 30 minutes
│   │                                          → Calls decision engine
│   │                                          → Executes selected task
│   │                                          → Handles tick errors gracefully
│   │
│   ├── decision_engine.py                  ← Task priority + routing
│   │                                          → Reads current agent state
│   │                                          → Applies priority rules
│   │                                          → Returns next task + module
│   │                                          → Dynamic priority based on time of day
│   │
│   ├── planner.py                          ← Strategic daily/weekly planner
│   │                                          → Sets daily targets (leads, emails, content)
│   │                                          → Adjusts targets based on performance
│   │                                          → Generates weekly strategy via Gemini
│   │
│   ├── context_builder.py                  ← Builds LLM context per task
│   │                                          → Loads relevant memory
│   │                                          → Includes performance history
│   │                                          → Adds task-specific info
│   │
│   ├── memory_manager.py                   ← Agent long-term memory
│   │                                          → What worked this week
│   │                                          → Best performing email subjects
│   │                                          → Best lead sources
│   │                                          → Client preferences learned
│   │
│   ├── state_machine.py                    ← Agent state management
│   │                                          States: STARTING | IDLE | WORKING
│   │                                          → PAUSED | ERROR | SLEEPING | SHUTDOWN
│   │                                          → State transitions with validation
│   │                                          → State persisted to DB (survives restart)
│   │
│   ├── tool_registry.py                    ← All tools registered here
│   │                                          → Tool name, description, module
│   │                                          → Input/output schemas
│   │                                          → Rate limits per tool
│   │
│   ├── health_monitor.py                   ← System health checks
│   │                                          → Pings all external APIs
│   │                                          → Checks DB connection
│   │                                          → Monitors memory usage
│   │                                          → Alerts if anything degraded
│   │
│   ├── self_improvement.py                 ← Weekly self-analysis
│   │                                          → Analyzes all performance data
│   │                                          → Identifies top/bottom performers
│   │                                          → Updates strategy via Gemini
│   │                                          → Rewrites underperforming prompts
│   │
│   └── constitution.py                     ← Immutable agent rules
│                                              → What agent CAN do
│                                              → What agent CANNOT do (ever)
│                                              → Ethical guidelines
│                                              → Human override triggers
│
│
├── 🤖 llm/                                 ← LLM ABSTRACTION LAYER
│   ├── __init__.py
│   ├── base.py                             ← Abstract LLM interface
│   │                                          → complete(prompt) → response
│   │                                          → stream(prompt) → generator
│   │                                          → embed(text) → vector
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── gemini_pro.py                   ← Gemini 2.5 Pro (complex tasks)
│   │   ├── gemini_flash.py                 ← Gemini 2.0 Flash (fast tasks)
│   │   ├── gemini_flash_lite.py            ← Gemini Flash Lite (simple tasks)
│   │   ├── groq_70b.py                     ← Groq Llama 3.3 70B (fallback)
│   │   └── groq_8b.py                      ← Groq Llama 3.1 8B (simple)
│   │
│   ├── router.py                           ← Smart model selector
│   │                                          Task complexity → Model selection:
│   │                                          CRITICAL  → gemini_pro
│   │                                          STANDARD  → gemini_flash
│   │                                          SIMPLE    → gemini_flash_lite
│   │                                          FALLBACK  → groq_70b
│   │                                          FASTEST   → groq_8b
│   │
│   ├── prompt_manager.py                   ← Loads + renders prompt templates
│   │                                          → Jinja2 template rendering
│   │                                          → Variable injection
│   │                                          → Version tracking
│   │                                          → A/B prompt testing
│   │
│   ├── response_parser.py                  ← Validates + parses LLM output
│   │                                          → JSON extraction
│   │                                          → Schema validation (Pydantic)
│   │                                          → Hallucination detection
│   │                                          → Auto-retry if invalid
│   │
│   ├── token_tracker.py                    ← Usage monitoring
│   │                                          → Tokens per model per day
│   │                                          → Cost estimation (even if free)
│   │                                          → Rate limit tracking
│   │                                          → Alert if near limit
│   │
│   ├── cache.py                            ← LLM response caching
│   │                                          → Cache identical prompts 1hr
│   │                                          → Skip LLM for repeated work
│   │                                          → Massive speed improvement
│   │
│   └── fallback_chain.py                   ← Automatic fallback logic
│                                              → Try Gemini Pro → Flash → Groq 70B → Groq 8B
│                                              → Log which fallback used + why
│                                              → Alert if all fail
│
│
├── 📦 modules/                             ← ALL EARNING MODULES
│   │
│   ├── lead_finder/                        ← MULTI-PLATFORM LEAD DISCOVERY
│   │   ├── __init__.py
│   │   ├── manager.py                      ← Orchestrates all sources
│   │   │                                      → Runs sources in parallel (asyncio)
│   │   │                                      → Deduplicates across sources
│   │   │                                      → Scores + saves qualified leads
│   │   │
│   │   ├── scorer.py                       ← Lead quality scoring engine
│   │   │                                      → 12-point scoring system
│   │   │                                      → Weights by source quality
│   │   │                                      → Gemini-assisted problem detection
│   │   │
│   │   ├── deduplicator.py                 ← Prevents duplicate contacts
│   │   │                                      → Email hash matching
│   │   │                                      → Domain matching
│   │   │                                      → Business name fuzzy match
│   │   │
│   │   ├── enricher.py                     ← Lead data enrichment
│   │   │                                      → Website quality score
│   │   │                                      → Social media presence check
│   │   │                                      → Google Maps rating
│   │   │                                      → Estimated business size
│   │   │
│   │   ├── contact_finder.py               ← Email discovery
│   │   │                                      → Website footer/contact scrape
│   │   │                                      → Hunter.io API (free tier)
│   │   │                                      → LinkedIn profile scrape
│   │   │                                      → WHOIS lookup
│   │   │
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── base_source.py              ← Abstract source interface
│   │       ├── google_maps.py              ← Google Places API
│   │       │                                  → Niche + city combinations
│   │       │                                  → Filter: no website OR bad rating
│   │       │                                  → Extract: name, phone, address, site
│   │       │
│   │       ├── reddit.py                   ← PRAW Reddit monitor
│   │       │                                  → Subreddits: forhire, entrepreneur,
│   │       │                                    smallbusiness, startups, marketing
│   │       │                                  → Keywords: need developer, need website,
│   │       │                                    looking for, hire someone
│   │       │
│   │       ├── twitter.py                  ← Tweepy Twitter/X
│   │       │                                  → Search: "need a website" "looking for developer"
│   │       │                                  → Monitor: founder complaints, tool requests
│   │       │
│   │       ├── linkedin.py                 ← LinkedIn scraper
│   │       │                                  → Search: decision makers in target niches
│   │       │                                  → Careful: strict rate limits applied
│   │       │
│   │       ├── craigslist.py               ← Craigslist scanner
│   │       │                                  → Services wanted section
│   │       │                                  → Web services, computer help
│   │       │
│   │       ├── producthunt.py              ← ProductHunt daily launches
│   │       │                                  → New startups without good sites
│   │       │                                  → Makers needing tech help
│   │       │
│   │       ├── indiehackers.py             ← Indie Hackers forum
│   │       │                                  → Forum posts requesting help
│   │       │                                  → Milestone posts (growing = needs help)
│   │       │
│   │       ├── yelp.py                     ← Yelp scraper
│   │       │                                  → Businesses with <4 star reviews
│   │       │                                  → Reviews mentioning "no website" or "hard to find"
│   │       │
│   │       ├── facebook_groups.py          ← Facebook group monitor
│   │       │                                  → Business owner groups
│   │       │                                  → Entrepreneur communities
│   │       │
│   │       └── nextdoor.py                 ← Nextdoor local businesses
│   │                                          → Hyper-local targeting
│   │                                          → Neighborhood businesses
│   │
│   │
│   ├── outreach/                           ← COLD EMAIL + FOLLOW-UP ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py                      ← Full outreach orchestrator
│   │   │                                      → Pulls leads ready to contact
│   │   │                                      → Manages daily send limits (400/day)
│   │   │                                      → Tracks all sequences
│   │   │                                      → Handles replies
│   │   │
│   │   ├── email_generator.py              ← Personalized email writer
│   │   │                                      → Scrapes lead's website first
│   │   │                                      → Identifies their specific problem
│   │   │                                      → Writes email mentioning exact problem
│   │   │                                      → Under 150 words always
│   │   │                                      → Human-sounding, no AI tells
│   │   │
│   │   ├── subject_optimizer.py            ← Subject line A/B testing
│   │   │                                      → Generates 3 subject variants
│   │   │                                      → Tracks open rates per variant
│   │   │                                      → Auto-promotes winner after 50 sends
│   │   │
│   │   ├── sequence_engine.py              ← 5-touch follow-up manager
│   │   │                                      Touch 1: Hook + mockup (Day 1)
│   │   │                                      Touch 2: Value add tip (Day 4)
│   │   │                                      Touch 3: Social proof (Day 8)
│   │   │                                      Touch 4: Different angle (Day 14)
│   │   │                                      Touch 5: Breakup email (Day 21)
│   │   │
│   │   ├── reply_classifier.py             ← Classifies incoming replies
│   │   │                                      Categories: interested / not_interested /
│   │   │                                      too_expensive / wrong_person /
│   │   │                                      needs_info / referral / schedule_call
│   │   │
│   │   ├── reply_drafter.py                ← Drafts reply based on classification
│   │   │                                      → Loads reply template for category
│   │   │                                      → Personalizes with Gemini
│   │   │                                      → Flags for human review before send
│   │   │
│   │   ├── mockup_generator.py             ← Auto-generates preview mockups
│   │   │                                      → Website screenshot mockup for web leads
│   │   │                                      → Email sequence preview for marketing leads
│   │   │                                      → Chatbot demo link for tech leads
│   │   │
│   │   ├── quality_checker.py              ← Pre-send email quality gate
│   │   │                                      → Spam score check
│   │   │                                      → Personalization score
│   │   │                                      → Length check (under 150 words)
│   │   │                                      → Single CTA check
│   │   │                                      → Human tone score
│   │   │
│   │   ├── spam_guard.py                   ← Spam prevention
│   │   │                                      → Check against spam word list
│   │   │                                      → Verify SPF/DKIM configured
│   │   │                                      → Monitor bounce rate
│   │   │                                      → Auto-pause if bounce >5%
│   │   │
│   │   ├── open_tracker.py                 ← Email open/click tracking
│   │   │                                      → 1x1 pixel injection
│   │   │                                      → Click tracking via redirect
│   │   │                                      → Webhook endpoint for events
│   │   │
│   │   ├── unsubscribe_handler.py          ← Handles opt-outs immediately
│   │   │                                      → One-click unsubscribe link
│   │   │                                      → Removes from all sequences instantly
│   │   │                                      → Blacklists domain forever
│   │   │
│   │   └── providers/
│   │       ├── gmail.py                    ← Gmail API (primary sender)
│   │       └── smtp.py                     ← SMTP fallback
│   │
│   │
│   ├── website_builder/                    ← AUTO WEBSITE GENERATION ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py                      ← Full build pipeline orchestrator
│   │   │
│   │   ├── template_selector.py            ← Industry → template mapping
│   │   │                                      → Analyzes client's niche
│   │   │                                      → Selects best template match
│   │   │                                      → Considers their brand colors
│   │   │
│   │   ├── content_generator.py            ← Page copy writer (Gemini 2.5 Pro)
│   │   │                                      → Homepage hero + features
│   │   │                                      → About page story
│   │   │                                      → Services with pricing
│   │   │                                      → Testimonials (placeholder)
│   │   │                                      → FAQ section
│   │   │                                      → CTA sections
│   │   │
│   │   ├── seo_optimizer.py                ← On-page SEO layer
│   │   │                                      → Title tags (60 chars)
│   │   │                                      → Meta descriptions (160 chars)
│   │   │                                      → H1/H2/H3 hierarchy
│   │   │                                      → Alt text for images
│   │   │                                      → Schema markup (LocalBusiness)
│   │   │                                      → Sitemap.xml generation
│   │   │
│   │   ├── branding_engine.py              ← Client branding extraction
│   │   │                                      → Extract colors from logo/site
│   │   │                                      → Match Google Fonts
│   │   │                                      → Generate CSS variables
│   │   │                                      → Apply consistently to template
│   │   │
│   │   ├── image_sourcer.py                ← Professional image acquisition
│   │   │                                      → Unsplash API (free, no attribution needed)
│   │   │                                      → Pexels API (backup)
│   │   │                                      → AI-generated via Replicate
│   │   │                                      → Compressed + optimized
│   │   │
│   │   ├── performance_optimizer.py        ← Website performance
│   │   │                                      → Image lazy loading
│   │   │                                      → CSS minification
│   │   │                                      → JS deferring
│   │   │                                      → Target: 90+ PageSpeed score
│   │   │
│   │   ├── form_builder.py                 ← Contact forms
│   │   │                                      → HTML form + validation
│   │   │                                      → Formspree.io backend (free)
│   │   │                                      → Success/error states
│   │   │
│   │   ├── analytics_injector.py           ← Tracking setup
│   │   │                                      → Google Analytics 4 code
│   │   │                                      → Google Search Console meta tag
│   │   │                                      → Facebook Pixel (if requested)
│   │   │
│   │   ├── quality_scorer.py               ← Pre-delivery quality gate
│   │   │                                      → Design score (Gemini vision)
│   │   │                                      → Copy quality score
│   │   │                                      → SEO completeness score
│   │   │                                      → Mobile responsiveness check
│   │   │                                      → Link validation
│   │   │                                      → Auto-fix issues below 7/10
│   │   │
│   │   ├── exporter.py                     ← Package for delivery
│   │   │                                      → Zip all files
│   │   │                                      → Include setup instructions
│   │   │                                      → Generate hosting guide PDF
│   │   │                                      → Save to outputs/websites/
│   │   │
│   │   └── templates/                      ← 12 Industry Templates
│   │       ├── _base/                      ← Shared base template
│   │       │   ├── index.html
│   │       │   ├── style.css
│   │       │   ├── main.js
│   │       │   └── assets/
│   │       ├── restaurant/
│   │       ├── real_estate/
│   │       ├── salon_spa/
│   │       ├── fitness_gym/
│   │       ├── medical_clinic/
│   │       ├── lawyer_consultant/
│   │       ├── ecommerce_simple/
│   │       ├── portfolio_freelancer/
│   │       ├── startup_saas/
│   │       ├── coaching/
│   │       ├── local_service/
│   │       └── photography/
│   │
│   │
│   ├── chatbot_builder/                    ← AI CHATBOT CREATION ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   │
│   │   ├── faq_extractor.py                ← Scrapes client's site for FAQs
│   │   │                                      → Contact page questions
│   │   │                                      → FAQ page content
│   │   │                                      → Product/service pages
│   │   │                                      → Google Reviews analysis
│   │   │
│   │   ├── knowledge_builder.py            ← Structures FAQ into KB
│   │   │                                      → Q&A pairs extracted
│   │   │                                      → Categories organized
│   │   │                                      → Confidence scores assigned
│   │   │                                      → Fallback responses written
│   │   │
│   │   ├── personality_engine.py           ← Brand voice matching
│   │   │                                      → Analyzes client's existing copy
│   │   │                                      → Extracts tone (formal/casual/friendly)
│   │   │                                      → Configures bot personality
│   │   │                                      → Writes welcome message
│   │   │
│   │   ├── widget_generator.py             ← Embeddable chat widget
│   │   │                                      → Vanilla JS widget (no dependencies)
│   │   │                                      → Customizable colors/position
│   │   │                                      → Mobile responsive
│   │   │                                      → One-line embed code
│   │   │
│   │   ├── backend_generator.py            ← Chatbot API backend
│   │   │                                      → FastAPI endpoint per client
│   │   │                                      → Gemini Flash for responses
│   │   │                                      → Session management
│   │   │                                      → Rate limiting per user
│   │   │
│   │   ├── whatsapp_integrator.py          ← WhatsApp Business API
│   │   │                                      → Twilio WhatsApp integration
│   │   │                                      → Same knowledge base
│   │   │                                      → Business hours handling
│   │   │
│   │   ├── analytics_builder.py            ← Chat analytics dashboard
│   │   │                                      → Most asked questions
│   │   │                                      → Unanswered questions
│   │   │                                      → Satisfaction scores
│   │   │                                      → Monthly PDF report
│   │   │
│   │   ├── tester.py                       ← Automated chatbot testing
│   │   │                                      → Runs 20 sample questions
│   │   │                                      → Checks response accuracy
│   │   │                                      → Checks escalation works
│   │   │                                      → Passes/fails quality gate
│   │   │
│   │   └── quality_scorer.py
│   │
│   │
│   ├── service_delivery/                   ← ORDER FULFILLMENT ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py                      ← Main order orchestrator
│   │   │                                      → Poll Fiverr every 30 mins
│   │   │                                      → Parse requirements
│   │   │                                      → Route to generator
│   │   │                                      → Quality check
│   │   │                                      → Alert human
│   │   │
│   │   ├── fiverr_monitor.py               ← Fiverr order polling
│   │   │                                      → New order detection
│   │   │                                      → Order status tracking
│   │   │                                      → Revision request handling
│   │   │                                      → Delivery confirmation
│   │   │
│   │   ├── order_parser.py                 ← Requirements extraction
│   │   │                                      → Natural language → structured data
│   │   │                                      → Missing info detection
│   │   │                                      → Clarification question generation
│   │   │
│   │   ├── requirement_validator.py        ← Checks requirements are clear
│   │   │                                      → Completeness check
│   │   │                                      → Ambiguity detection
│   │   │                                      → Auto-ask client if unclear
│   │   │
│   │   ├── delivery_packager.py            ← Final package assembly
│   │   │                                      → Bundles all deliverable files
│   │   │                                      → Writes delivery message
│   │   │                                      → Adds usage instructions
│   │   │                                      → Creates zip package
│   │   │
│   │   ├── revision_handler.py             ← Handles revision requests
│   │   │                                      → Parses what needs changing
│   │   │                                      → Routes to original generator
│   │   │                                      → Applies specific changes only
│   │   │
│   │   └── generators/                     ← SERVICE-SPECIFIC GENERATORS
│   │       ├── __init__.py
│   │       ├── blog_post.py                ← SEO blog posts (1500-2500 words)
│   │       │                                  → Keyword research first
│   │       │                                  → Proper H1/H2/H3 structure
│   │       │                                  → Internal linking suggestions
│   │       │                                  → Meta description included
│   │       │
│   │       ├── email_sequence.py           ← Cold email campaigns
│   │       │                                  → 3-5 email sequences
│   │       │                                  → Subject line variants
│   │       │                                  → Reply scripts included
│   │       │                                  → A/B testing notes
│   │       │
│   │       ├── social_pack.py              ← Social media content packs
│   │       │                                  → 30 posts per pack
│   │       │                                  → Platform-specific formatting
│   │       │                                  → Hashtag research included
│   │       │                                  → Content calendar template
│   │       │
│   │       ├── ad_copy.py                  ← Paid ad copy
│   │       │                                  → Facebook/Instagram ads
│   │       │                                  → Headlines + body + CTA variants
│   │       │                                  → Multiple angles per ad
│   │       │
│   │       ├── youtube_script.py           ← YouTube video scripts
│   │       │                                  → Hook (first 30 seconds)
│   │       │                                  → Full script with timestamps
│   │       │                                  → Title + description + tags
│   │       │                                  → Thumbnail concept description
│   │       │
│   │       ├── podcast_notes.py            ← Podcast show notes
│   │       │                                  → Episode summary
│   │       │                                  → Key takeaways
│   │       │                                  → Guest bio (if applicable)
│   │       │                                  → Timestamps + chapters
│   │       │
│   │       ├── case_study.py               ← Client case studies
│   │       │                                  → Problem → Solution → Results format
│   │       │                                  → Metrics and data emphasis
│   │       │                                  → Pull quotes generated
│   │       │
│   │       ├── pitch_deck.py               ← Pitch deck content
│   │       │                                  → Slide-by-slide content
│   │       │                                  → 10-slide standard format
│   │       │                                  → Investor-ready language
│   │       │
│   │       ├── linkedin_profile.py         ← LinkedIn profile optimization
│   │       │                                  → Headline rewrite
│   │       │                                  → About section
│   │       │                                  → Experience descriptions
│   │       │
│   │       └── press_release.py            ← Press releases
│   │                                          → News-ready format
│   │                                          → Distribution-ready copy
│   │
│   │
│   ├── design_generator/                   ← DESIGN & VISUAL ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   │
│   │   ├── logo_generator.py               ← AI logo creation
│   │   │                                      → Replicate SDXL API
│   │   │                                      → Multiple concept variations
│   │   │                                      → Light + dark versions
│   │   │                                      → PNG + SVG export
│   │   │
│   │   ├── thumbnail_creator.py            ← YouTube thumbnails
│   │   │                                      → High contrast design
│   │   │                                      → Text overlay generation
│   │   │                                      → Face + background composition
│   │   │                                      → 1280x720px standard
│   │   │
│   │   ├── ad_creative_builder.py          ← Social ad creatives
│   │   │                                      → Facebook (1200x628)
│   │   │                                      → Instagram square (1080x1080)
│   │   │                                      → Instagram story (1080x1920)
│   │   │                                      → Multiple text variations
│   │   │
│   │   ├── brand_kit_compiler.py           ← Complete brand kit
│   │   │                                      → Logo (all versions)
│   │   │                                      → Color palette (hex codes)
│   │   │                                      → Typography guide
│   │   │                                      → Business card design
│   │   │                                      → Email signature
│   │   │                                      → Compiled into PDF guide
│   │   │
│   │   ├── color_extractor.py              ← Brand color analysis
│   │   │                                      → Extract from logo image
│   │   │                                      → Generate complementary palette
│   │   │                                      → Accessibility check (contrast)
│   │   │
│   │   ├── font_matcher.py                 ← Typography pairing
│   │   │                                      → Brand personality → font style
│   │   │                                      → Google Fonts only (free)
│   │   │                                      → Heading + body combinations
│   │   │
│   │   ├── quality_scorer.py               ← Visual quality assessment
│   │   │                                      → Gemini Vision API
│   │   │                                      → Professional appearance score
│   │   │                                      → Brand consistency check
│   │   │
│   │   └── exporters/
│   │       ├── png_exporter.py             ← PNG at multiple resolutions
│   │       ├── svg_exporter.py             ← Vector SVG
│   │       ├── pdf_exporter.py             ← Print-ready PDF
│   │       └── zip_packager.py             ← All formats in one zip
│   │
│   │
│   ├── content_writer/                     ← SEO & AFFILIATE CONTENT ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   │
│   │   ├── topic_researcher.py             ← Content opportunity finder
│   │   │                                      → Google Trends API
│   │   │                                      → Reddit trending topics
│   │   │                                      → Competitor content gaps
│   │   │                                      → Affiliate product trends
│   │   │
│   │   ├── keyword_analyzer.py             ← SEO keyword research
│   │   │                                      → Search volume estimation
│   │   │                                      → Competition scoring
│   │   │                                      → Long-tail opportunity finder
│   │   │                                      → Keyword clustering
│   │   │
│   │   ├── article_generator.py            ← Full article writer
│   │   │                                      → Gemini 2.5 Pro for quality
│   │   │                                      → 1500-2500 word target
│   │   │                                      → Proper structure (intro/body/CTA)
│   │   │                                      → Natural language, human-sounding
│   │   │                                      → Internal + external linking
│   │   │
│   │   ├── affiliate_linker.py             ← Affiliate link embedding
│   │   │                                      → Product recommendation extraction
│   │   │                                      → Natural link placement
│   │   │                                      → Disclosure statement auto-added
│   │   │                                      → Link tracking parameters
│   │   │
│   │   ├── seo_finalizer.py                ← Final SEO pass
│   │   │                                      → Keyword density check
│   │   │                                      → Readability score (Flesch)
│   │   │                                      → Meta description generation
│   │   │                                      → Title optimization
│   │   │
│   │   ├── uniqueness_checker.py           ← Originality verification
│   │   │                                      → Perplexity API check
│   │   │                                      → Rewrite if similarity >20%
│   │   │
│   │   ├── performance_tracker.py          ← Content performance monitoring
│   │   │                                      → Medium stats API
│   │   │                                      → Affiliate click tracking
│   │   │                                      → Revenue per article
│   │   │                                      → Update strategy based on winners
│   │   │
│   │   └── publishers/
│   │       ├── medium.py                   ← Medium API publisher
│   │       ├── substack.py                 ← Substack publisher
│   │       ├── wordpress.py                ← WordPress REST API
│   │       └── dev_to.py                   ← Dev.to (tech audience)
│   │
│   │
│   ├── social_manager/                     ← SOCIAL MEDIA AUTOMATION
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   │
│   │   ├── post_generator.py               ← Platform-specific post writer
│   │   │                                      → LinkedIn: professional, 1300 chars
│   │   │                                      → Twitter: punchy, under 280
│   │   │                                      → Instagram: visual-first captions
│   │   │
│   │   ├── hashtag_researcher.py           ← Trending hashtag finder
│   │   │                                      → Platform-specific research
│   │   │                                      → Volume + competition balance
│   │   │                                      → Niche-specific hashtag sets
│   │   │
│   │   ├── content_calendar.py             ← Monthly content planning
│   │   │                                      → 30-day calendar generation
│   │   │                                      → Topic variety enforcement
│   │   │                                      → Best posting times per platform
│   │   │
│   │   ├── scheduler.py                    ← Buffer API integration
│   │   │                                      → Schedule posts at optimal times
│   │   │                                      → Queue management
│   │   │                                      → Failed post retry
│   │   │
│   │   ├── engagement_tracker.py           ← Performance monitoring
│   │   │                                      → Likes, shares, comments
│   │   │                                      → Follower growth
│   │   │                                      → Best performing content types
│   │   │
│   │   ├── monthly_reporter.py             ← Client monthly reports
│   │   │                                      → PDF report auto-generated
│   │   │                                      → Growth metrics
│   │   │                                      → Top performing posts
│   │   │                                      → Next month recommendations
│   │   │
│   │   └── platforms/
│   │       ├── linkedin.py
│   │       ├── twitter.py
│   │       └── instagram.py
│   │
│   │
│   ├── payment_handler/                    ← PAYMENT PROCESSING ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py                      ← Routes to correct provider
│   │   │                                      → Decides method based on client location
│   │   │                                      → Generates payment instructions
│   │   │                                      → Monitors for confirmation
│   │   │                                      → Logs all transactions
│   │   │
│   │   ├── invoice_generator.py            ← Professional invoice creation
│   │   │                                      → PDF invoice with your branding
│   │   │                                      → GST-ready format
│   │   │                                      → Invoice number tracking
│   │   │                                      → Due date + payment terms
│   │   │
│   │   ├── payment_tracker.py              ← All payment monitoring
│   │   │                                      → Real-time status tracking
│   │   │                                      → Overdue payment alerts
│   │   │                                      → Payment reconciliation
│   │   │
│   │   ├── currency_converter.py           ← Live FX rates
│   │   │                                      → USD ↔ INR conversion
│   │   │                                      → Always store INR equivalent
│   │   │                                      → Free ExchangeRate API
│   │   │
│   │   ├── earnings_reporter.py            ← Financial reporting
│   │   │                                      → Daily earnings summary
│   │   │                                      → Weekly revenue breakdown
│   │   │                                      → Monthly P&L statement
│   │   │                                      → Per-service profitability
│   │   │
│   │   └── providers/
│   │       ├── base_provider.py            ← Abstract payment interface
│   │       ├── razorpay.py                 ← Razorpay full integration
│   │       │                                  → Create payment links
│   │       │                                  → Webhook verification
│   │       │                                  → Refund handling
│   │       │                                  → Settlement tracking
│   │       │
│   │       ├── binance.py                  ← Binance Pay + wallet monitor
│   │       │                                  → Binance Pay ID sharing
│   │       │                                  → USDT TRC20 monitoring
│   │       │                                  → P2P conversion guidance
│   │       │                                  → Transaction confirmation
│   │       │
│   │       ├── wise.py                     ← Wise international payments
│   │       │                                  → Account details sharing
│   │       │                                  → Transfer confirmation tracking
│   │       │                                  → Currency conversion logging
│   │       │
│   │       └── fiverr.py                   ← Fiverr earnings tracking
│   │                                          → Balance monitoring
│   │                                          → Withdrawal scheduling
│   │                                          → Revenue reporting
│   │
│   │
│   ├── digital_products/                   ← PASSIVE INCOME ENGINE
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── prompt_pack_creator.py          ← AI prompt pack generator
│   │   ├── template_pack_creator.py        ← Website template packs
│   │   ├── swipe_file_creator.py           ← Email swipe files
│   │   ├── ebook_creator.py                ← Short ebook generator
│   │   ├── gumroad_publisher.py            ← Auto-publish to Gumroad
│   │   └── sales_tracker.py                ← Track product sales
│   │
│   │
│   └── white_label/                        ← WHITE LABEL AGENCY MODULE
│       ├── __init__.py
│       ├── manager.py
│       ├── partner_manager.py              ← Partner agency tracking
│       ├── white_label_delivery.py         ← Deliver under partner brand
│       ├── partner_reporter.py             ← Monthly reports for partners
│       └── billing_manager.py              ← Partner invoicing
│
│
├── 🔌 integrations/                        ← ALL THIRD-PARTY API WRAPPERS
│   ├── __init__.py
│   ├── base_integration.py                 ← Abstract integration interface
│   │                                          → Rate limiting built-in
│   │                                          → Retry logic built-in
│   │                                          → Error logging built-in
│   │
│   ├── google/
│   │   ├── __init__.py
│   │   ├── gmail.py                        ← Gmail API (send, read, labels)
│   │   ├── places.py                       ← Google Places API
│   │   ├── trends.py                       ← Google Trends
│   │   ├── analytics.py                    ← Google Analytics 4
│   │   └── search_console.py               ← Search Console data
│   │
│   ├── social/
│   │   ├── __init__.py
│   │   ├── reddit.py                       ← PRAW Reddit
│   │   ├── twitter.py                      ← Tweepy v2
│   │   ├── linkedin.py                     ← LinkedIn scraper
│   │   └── buffer.py                       ← Buffer scheduling
│   │
│   ├── publishing/
│   │   ├── __init__.py
│   │   ├── medium.py
│   │   ├── substack.py
│   │   ├── wordpress.py
│   │   ├── dev_to.py
│   │   └── gumroad.py
│   │
│   ├── design/
│   │   ├── __init__.py
│   │   ├── replicate.py                    ← Replicate AI (SDXL)
│   │   ├── canva.py                        ← Canva API
│   │   ├── unsplash.py                     ← Unsplash free images
│   │   └── pexels.py                       ← Pexels free images
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── hunter.py                       ← Hunter.io email finder
│   │   ├── clearbit.py                     ← Company enrichment (free tier)
│   │   └── exchangerate.py                 ← Live FX rates
│   │
│   ├── communication/
│   │   ├── __init__.py
│   │   ├── telegram.py                     ← Telegram Bot API
│   │   └── twilio.py                       ← WhatsApp + SMS
│   │
│   └── freelance/
│       ├── __init__.py
│       └── fiverr.py                       ← Fiverr API
│
│
├── 💾 database/                            ← COMPLETE DATA LAYER
│   ├── __init__.py
│   ├── connection.py                       ← SQLAlchemy async engine
│   │                                          → Connection pooling
│   │                                          → Health check on startup
│   │                                          → Auto-reconnect on failure
│   │
│   ├── base.py                             ← Base model + mixins
│   │                                          → Timestamps mixin (created_at, updated_at)
│   │                                          → SoftDelete mixin
│   │                                          → UUID primary keys
│   │
│   ├── session.py                          ← Session management
│   │                                          → Context manager
│   │                                          → Transaction handling
│   │                                          → Rollback on error
│   │
│   ├── migrations/                         ← Alembic migrations
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 001_initial_schema.py
│   │       ├── 002_add_performance_table.py
│   │       └── 003_add_white_label.py
│   │
│   ├── models/                             ← ALL ORM MODELS
│   │   ├── __init__.py
│   │   ├── lead.py                         ← Lead model (full schema)
│   │   ├── email.py                        ← Email send/receive model
│   │   ├── order.py                        ← Order model
│   │   ├── payment.py                      ← Payment model
│   │   ├── content.py                      ← Published content model
│   │   ├── client.py                       ← Repeat client model
│   │   ├── performance.py                  ← Performance metrics
│   │   ├── agent_log.py                    ← Agent activity log
│   │   ├── prompt_version.py               ← Prompt A/B test tracking
│   │   ├── digital_product.py              ← Digital product sales
│   │   └── white_label_partner.py          ← Partner tracking
│   │
│   └── repositories/                       ← DATA ACCESS LAYER
│       ├── __init__.py
│       ├── base_repository.py              ← Generic async CRUD
│       │                                      → get_by_id, get_all, create
│       │                                      → update, delete, paginate
│       │                                      → filter_by, search
│       │
│       ├── lead_repository.py              ← Lead-specific queries
│       │                                      → get_uncontacted(score_min=7)
│       │                                      → get_in_sequence()
│       │                                      → get_by_source()
│       │                                      → mark_contacted()
│       │
│       ├── email_repository.py             ← Email queries
│       │                                      → get_pending_followups()
│       │                                      → get_open_rates_by_subject()
│       │                                      → get_reply_rate_by_template()
│       │
│       ├── order_repository.py             ← Order queries
│       │                                      → get_pending_orders()
│       │                                      → get_revenue_by_service()
│       │                                      → get_client_orders()
│       │
│       ├── payment_repository.py           ← Payment queries
│       │                                      → get_daily_revenue()
│       │                                      → get_monthly_breakdown()
│       │                                      → get_pending_payments()
│       │
│       └── content_repository.py          ← Content queries
│                                              → get_top_performing()
│                                              → get_affiliate_earnings()
│                                              → get_by_platform()
│
│
├── 📊 dashboard/                           ← FASTAPI MONITORING DASHBOARD
│   ├── __init__.py
│   ├── app.py                              ← FastAPI app factory
│   │                                          → CORS middleware
│   │                                          → Auth middleware
│   │                                          → Rate limiting
│   │                                          → Exception handlers
│   │                                          → WebSocket support
│   │
│   ├── middleware/
│   │   ├── auth.py                         ← Simple token auth
│   │   ├── rate_limit.py                   ← Request rate limiting
│   │   └── logging.py                      ← Request logging
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── overview.py                     ← GET / → today summary
│   │   ├── leads.py                        ← GET /leads + filters
│   │   ├── emails.py                       ← GET /emails + stats
│   │   ├── orders.py                       ← GET /orders + status
│   │   ├── earnings.py                     ← GET /earnings + charts
│   │   ├── content.py                      ← GET /content + performance
│   │   ├── alerts.py                       ← GET /alerts → human actions needed
│   │   ├── logs.py                         ← GET /logs → streamed via WebSocket
│   │   ├── control.py                      ← POST /control → pause/resume/stop
│   │   └── webhooks/
│   │       ├── razorpay.py                 ← POST /webhooks/razorpay
│   │       ├── fiverr.py                   ← POST /webhooks/fiverr
│   │       └── email_events.py             ← POST /webhooks/email (opens/clicks)
│   │
│   ├── schemas/                            ← Pydantic response models
│   │   ├── __init__.py
│   │   ├── lead_schema.py
│   │   ├── order_schema.py
│   │   ├── earnings_schema.py
│   │   ├── alert_schema.py
│   │   └── control_schema.py
│   │
│   └── static/
│       ├── index.html                      ← Single page dashboard
│       ├── css/
│       │   └── dashboard.css               ← Clean dark theme UI
│       └── js/
│           ├── dashboard.js                ← Main dashboard logic
│           ├── charts.js                   ← Chart.js visualizations
│           ├── realtime.js                 ← WebSocket live logs
│           └── alerts.js                   ← Alert management
│
│
├── ⚙️ scheduler/                           ← JOB SCHEDULING SYSTEM
│   ├── __init__.py
│   ├── scheduler.py                        ← APScheduler setup
│   │                                          → Persistent job store (SQLite)
│   │                                          → Survives restarts
│   │                                          → Timezone-aware (IST)
│   │                                          → Job error handling
│   │
│   ├── job_store.py                        ← Persistent storage for jobs
│   │
│   └── jobs/
│       ├── __init__.py
│       ├── lead_hunting.py                 ← Daily 9AM IST
│       │                                      → Run all lead sources
│       │                                      → Score + save qualified leads
│       │
│       ├── email_sending.py                ← Daily 11AM + 3PM IST
│       │                                      → Send cold emails (batch)
│       │                                      → Respect daily limit (400)
│       │
│       ├── followup_check.py               ← Every 6 hours
│       │                                      → Check sequence schedule
│       │                                      → Send due follow-ups
│       │
│       ├── fiverr_monitor.py               ← Every 30 minutes
│       │                                      → Check new orders
│       │                                      → Handle pending deliveries
│       │
│       ├── payment_monitor.py              ← Every 15 minutes
│       │                                      → Check Razorpay webhook queue
│       │                                      → Monitor Binance for USDT
│       │
│       ├── content_publishing.py           ← Daily 7PM IST
│       │                                      → Publish scheduled articles
│       │                                      → Post scheduled social content
│       │
│       ├── reply_checker.py                ← Every 2 hours
│       │                                      → Check Gmail for new replies
│       │                                      → Classify + draft responses
│       │                                      → Alert human if needed
│       │
│       ├── performance_review.py           ← Every Sunday 10PM IST
│       │                                      → Analyze full week data
│       │                                      → Update strategy
│       │                                      → Optimize prompts
│       │                                      → Send weekly report to Telegram
│       │
│       ├── db_backup.py                    ← Daily 2AM IST
│       │                                      → Backup SQLite to GitHub
│       │                                      → Compress + timestamp
│       │                                      → Keep last 30 backups
│       │
│       └── health_check.py                 ← Every 1 hour
│                                              → Check all API connections
│                                              → Alert if anything degraded
│                                              → Log system health metrics
│
│
├── 🔐 security/                            ← SECURITY LAYER
│   ├── __init__.py
│   ├── auth.py                             ← Dashboard authentication
│   │                                          → Token-based auth
│   │                                          → Brute force protection
│   │                                          → Session management
│   │
│   ├── api_key_manager.py                  ← API key validation + rotation
│   │                                          → Validates all keys on startup
│   │                                          → Alerts before keys expire
│   │
│   ├── webhook_verifier.py                 ← Payment webhook security
│   │                                          → Razorpay signature verification
│   │                                          → Replay attack prevention
│   │
│   ├── rate_guard.py                       ← Anti-spam protection
│   │                                          → Per-platform daily limits
│   │                                          → Automatic back-off
│   │                                          → Emergency pause trigger
│   │
│   ├── sandbox.py                          ← Agent capability sandbox
│   │                                          → File system restrictions
│   │                                          → Network restrictions
│   │                                          → Action whitelist enforcement
│   │
│   ├── encryption.py                       ← Sensitive data encryption
│   │                                          → Fernet symmetric encryption
│   │                                          → Encrypt sensitive DB fields
│   │
│   └── audit_log.py                        ← Immutable audit trail
│                                              → Every agent action logged
│                                              → Cannot be modified/deleted
│                                              → Append-only file
│
│
├── 🔧 utils/                               ← SHARED UTILITIES
│   ├── __init__.py
│   ├── logger.py                           ← Loguru structured logging
│   │                                          → JSON format for prod
│   │                                          → Human format for dev
│   │                                          → Auto-rotation + compression
│   │
│   ├── notifier.py                         ← Alert dispatcher
│   │                                          → Telegram (primary)
│   │                                          → Email (backup)
│   │                                          → Priority levels: INFO/WARN/URGENT
│   │
│   ├── scraper.py                          ← Playwright async helpers
│   │                                          → Anti-detection headers
│   │                                          → Screenshot capture
│   │                                          → JS rendering wait
│   │
│   ├── http_client.py                      ← httpx async client
│   │                                          → Retry with exponential backoff
│   │                                          → Timeout configuration
│   │                                          → Response caching
│   │
│   ├── rate_limiter.py                     ← Per-API rate limiting
│   │                                          → Token bucket algorithm
│   │                                          → Per-platform configs
│   │
│   ├── retry.py                            ← Retry decorator
│   │                                          → @retry(max_attempts=3, backoff=2)
│   │                                          → Circuit breaker pattern
│   │
│   ├── validators.py                       ← Input validation
│   │                                          → Email format validator
│   │                                          → URL validator
│   │                                          → Phone number validator
│   │                                          → Amount validator
│   │
│   ├── formatters.py                       ← Output formatting
│   │                                          → Currency (INR/USD)
│   │                                          → Date/time (IST)
│   │                                          → Text truncation
│   │
│   ├── file_handler.py                     ← File operations
│   │                                          → Safe read/write
│   │                                          → Zip creation
│   │                                          → Temp file management
│   │                                          → Auto-cleanup
│   │
│   ├── crypto_utils.py                     ← Encryption utilities
│   │                                          → Fernet encryption
│   │                                          → Hash generation
│   │
│   ├── ip_rotator.py                       ← Proxy management
│   │                                          → Free proxy list rotation
│   │                                          → Health check per proxy
│   │
│   └── health_checker.py                   ← API health verification
│                                              → Check all integrations
│                                              → Return health status dict
│                                              → Called on startup + hourly
│
│
├── 📝 prompts/                             ← ALL LLM PROMPTS (versioned)
│   ├── system/
│   │   ├── agent_identity.txt              ← Who the agent is
│   │   ├── decision_making.txt             ← How it prioritizes
│   │   └── quality_standards.txt           ← What good looks like
│   │
│   ├── lead_finder/
│   │   ├── score_lead.txt                  ← Lead quality scoring prompt
│   │   ├── identify_problem.txt            ← Business problem detection
│   │   └── enrich_lead.txt                 ← Lead data enrichment
│   │
│   ├── outreach/
│   │   ├── write_cold_email.txt            ← Main cold email writer
│   │   ├── write_followup_1.txt            ← Follow-up 1 (value add)
│   │   ├── write_followup_2.txt            ← Follow-up 2 (social proof)
│   │   ├── write_followup_3.txt            ← Follow-up 3 (different angle)
│   │   ├── write_breakup.txt               ← Breakup email
│   │   ├── optimize_subject.txt            ← Subject line generator
│   │   ├── classify_reply.txt              ← Reply classification
│   │   └── draft_reply.txt                 ← Response drafter
│   │
│   ├── website_builder/
│   │   ├── generate_hero.txt
│   │   ├── generate_about.txt
│   │   ├── generate_services.txt
│   │   ├── generate_faq.txt
│   │   ├── generate_cta.txt
│   │   └── score_website.txt
│   │
│   ├── content_writer/
│   │   ├── research_topic.txt
│   │   ├── write_article_outline.txt
│   │   ├── write_article_full.txt
│   │   ├── embed_affiliate_links.txt
│   │   ├── optimize_seo.txt
│   │   └── write_social_teaser.txt
│   │
│   ├── service_delivery/
│   │   ├── write_blog_post.txt
│   │   ├── write_email_sequence.txt
│   │   ├── write_social_pack.txt
│   │   ├── write_ad_copy.txt
│   │   ├── write_youtube_script.txt
│   │   └── write_case_study.txt
│   │
│   ├── quality_control/
│   │   ├── review_email.txt
│   │   ├── review_website.txt
│   │   ├── review_article.txt
│   │   └── review_chatbot.txt
│   │
│   └── self_improvement/
│       ├── analyze_weekly_performance.txt
│       ├── identify_improvements.txt
│       └── update_strategy.txt
│
│
├── 🧪 tests/                               ← FULL TEST SUITE
│   ├── __init__.py
│   ├── conftest.py                         ← Global fixtures + test DB
│   │
│   ├── unit/                               ← Unit tests (mocked dependencies)
│   │   ├── test_decision_engine.py
│   │   ├── test_lead_scorer.py
│   │   ├── test_email_generator.py
│   │   ├── test_subject_optimizer.py
│   │   ├── test_reply_classifier.py
│   │   ├── test_website_builder.py
│   │   ├── test_quality_scorer.py
│   │   ├── test_payment_handler.py
│   │   ├── test_article_generator.py
│   │   └── test_token_tracker.py
│   │
│   ├── integration/                        ← Integration tests (real DB, mocked APIs)
│   │   ├── test_lead_to_email_flow.py
│   │   ├── test_order_to_delivery_flow.py
│   │   ├── test_payment_webhook_flow.py
│   │   ├── test_content_publish_flow.py
│   │   └── test_full_agent_cycle.py
│   │
│   ├── e2e/                                ← End-to-end (full system)
│   │   └── test_full_business_cycle.py
│   │
│   └── mocks/
│       ├── mock_gemini.py
│       ├── mock_gmail.py
│       ├── mock_razorpay.py
│       ├── mock_fiverr.py
│       └── mock_binance.py
│
│
├── 📁 outputs/                             ← ALL GENERATED DELIVERABLES
│   ├── websites/
│   │   └── {client_id}_{date}/
│   ├── chatbots/
│   │   └── {client_id}_{date}/
│   ├── designs/
│   │   └── {client_id}_{date}/
│   ├── content/
│   │   └── {date}_{slug}/
│   ├── reports/
│   │   └── {year}_{month}/
│   └── invoices/
│       └── INV-{number}.pdf
│
│
├── 📁 data/                                ← STATIC REFERENCE DATA
│   ├── niches.json                         ← Target niches + keywords
│   ├── cities.json                         ← Target cities (India + global)
│   ├── email_blacklist.txt                 ← Never email these domains
│   ├── spam_words.txt                      ← Avoid in emails
│   ├── affiliate_programs.json             ← All programs + commission rates
│   ├── pricing_tiers.json                  ← Current service pricing
│   ├── lead_sources_config.json            ← Source weights + limits
│   └── industry_keywords.json             ← Per-industry search terms
│
│
├── 📁 scripts/                             ← UTILITY SCRIPTS
│   ├── setup.py                            ← First-time setup wizard
│   ├── init_db.py                          ← Initialize + migrate DB
│   ├── backup_db.py                        ← Manual backup
│   ├── test_all_apis.py                    ← Verify all API keys work
│   ├── seed_test_data.py                   ← Seed dev data
│   ├── generate_invoice.py                 ← Manual invoice generator
│   └── export_earnings.py                  ← Export earnings to CSV
│
│
├── 📁 logs/                                ← RUNTIME LOGS (gitignored)
│   ├── agent.log
│   ├── errors.log
│   ├── emails.log
│   ├── payments.log
│   ├── leads.log
│   └── performance.log
│
│
└── 📁 docs/                                ← PROJECT DOCUMENTATION
    ├── BLUEPRINT.md                        ← This master file
    ├── STRUCTURE.md                        ← Folder structure guide
    ├── API_KEYS.md                         ← How to get every key
    ├── DEPLOYMENT.md                       ← Deploy guide
    ├── MODULES.md                          ← Module documentation
    ├── PROMPTS.md                          ← Prompt engineering guide
    ├── PAYMENTS.md                         ← Payment setup guide
    ├── SECURITY.md                         ← Security guidelines
    └── TROUBLESHOOTING.md                  ← Common errors + fixes
```

---

# 6. CORE BRAIN ARCHITECTURE

## Agent States

```
STARTING → validates config, connects APIs, runs health check
    ↓
IDLE → waiting for next scheduled tick
    ↓
WORKING → actively executing a task
    ↓
PAUSED → manually paused by human via dashboard
    ↓
ERROR → encountered unrecoverable error, alerting human
    ↓
SLEEPING → all tasks complete, nothing urgent, conserving
    ↓
SHUTDOWN → graceful shutdown initiated
```

## Decision Priority Matrix

```
PRIORITY 1 (Immediate):
→ New Fiverr order received
→ Payment webhook received
→ Client replied to email

PRIORITY 2 (Within 1 hour):
→ Follow-up emails due
→ Pending deliverables to complete
→ Overdue orders

PRIORITY 3 (Same day):
→ New leads to contact
→ Content to publish
→ Social posts to schedule

PRIORITY 4 (When idle):
→ Hunt for new leads
→ Write new content
→ Research new topics

PRIORITY 5 (Weekly):
→ Performance analysis
→ Strategy update
→ Prompt optimization
```

---

# 7. LLM STRATEGY

## Model Selection Rules

```
TASK TYPE                    → MODEL              → REASON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complex reasoning/planning   → Gemini 2.5 Pro     → Best reasoning
Quality content writing      → Gemini 2.5 Pro     → Best output quality
Website copy generation      → Gemini 2.5 Pro     → Needs to be good
Chatbot personality design   → Gemini 2.5 Pro     → Nuanced task
Strategy/self-improvement    → Gemini 2.5 Pro     → High stakes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cold email generation        → Gemini 2.0 Flash   → Fast + good enough
Social media posts           → Gemini 2.0 Flash   → Speed matters
Reply drafting               → Gemini 2.0 Flash   → Fast turnaround
Lead scoring                 → Gemini 2.0 Flash   → Bulk operation
Subject line generation      → Gemini 2.0 Flash   → Many variations needed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email classification         → Flash Lite         → Simple task
Spam word detection          → Flash Lite         → Yes/No answer
URL validation               → Flash Lite         → Simple check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gemini down/rate limited     → Groq Llama 3.3 70B → Strong fallback
Simple/ultra-fast needed     → Groq Llama 3.1 8B  → Fastest option
```

## Prompt Versioning

Every prompt is stored as a .txt file and versioned:
```
prompts/outreach/write_cold_email.txt  ← current version
→ Tracked in git
→ Version number in DB
→ A/B tested against previous version
→ Performance data drives which wins
```

---

# 8. ALL EARNING MODULES

## Complete Service Menu

### Active Services (Agent Delivers)

| # | Service | Generator Module | LLM Used | Delivery Time |
|---|---|---|---|---|
| 1 | Cold Email Sequence (3-5 emails) | generators/email_sequence.py | Flash | 30 mins |
| 2 | SEO Blog Post (1500-2500 words) | generators/blog_post.py | Pro | 45 mins |
| 3 | Landing Page (full HTML) | website_builder/ | Pro | 2 hours |
| 4 | AI Chatbot + Widget | chatbot_builder/ | Flash | 3 hours |
| 5 | Social Media Pack (30 posts) | generators/social_pack.py | Flash | 1 hour |
| 6 | Facebook/Instagram Ad Copy | generators/ad_copy.py | Flash | 30 mins |
| 7 | YouTube Script | generators/youtube_script.py | Pro | 45 mins |
| 8 | Brand Kit (Logo+Colors+Fonts) | design_generator/ | Pro | 2 hours |
| 9 | Podcast Show Notes | generators/podcast_notes.py | Flash | 20 mins |
| 10 | LinkedIn Profile Optimization | generators/linkedin_profile.py | Pro | 45 mins |
| 11 | Case Study | generators/case_study.py | Pro | 1 hour |
| 12 | Pitch Deck Content | generators/pitch_deck.py | Pro | 1 hour |
| 13 | Press Release | generators/press_release.py | Flash | 30 mins |
| 14 | WhatsApp Chatbot Setup | chatbot_builder/whatsapp | Flash | 3 hours |
| 15 | Full Website (5 pages) | website_builder/ | Pro | 4 hours |

### Passive Services (Agent Handles + Recurring)

| # | Service | Module | Revenue Type |
|---|---|---|---|
| 16 | Social Media Management | social_manager/ | Monthly retainer |
| 17 | Chatbot Maintenance | chatbot_builder/ | Monthly retainer |
| 18 | Content Writing Retainer | content_writer/ | Monthly retainer |
| 19 | Lead Gen Service | lead_finder/ | Per list + retainer |
| 20 | White Label Delivery | white_label/ | Monthly recurring |

### Passive Income (Agent Runs Autonomously)

| # | Service | Module | Revenue Type |
|---|---|---|---|
| 21 | Medium Affiliate Articles | content_writer/ | Per read + affiliate |
| 22 | Gumroad Prompt Packs | digital_products/ | Per sale |
| 23 | Gumroad Template Packs | digital_products/ | Per sale |
| 24 | Gumroad Email Swipe Files | digital_products/ | Per sale |
| 25 | Newsletter Sponsorships | content_writer/ | Per edition |

---

# 9. CUSTOMER ACQUISITION SYSTEM

## Lead Scoring (12-Point System)

```
POSITIVE SCORES:
+3 → No website OR website looks pre-2018
+2 → Has Google Maps listing but low rating (<3.8)
+2 → Reviews mention "hard to find" or "no online booking"
+1 → Active on Google Maps (recent updates)
+1 → Phone visible and callable (real business)
+1 → Niche matches our best-converting niches
+1 → Located in Tier 1/2 city (more spending power)
+1 → Business exists 1-5 years (established but growing)

NEGATIVE SCORES:
-2 → Already has professional website with good SEO
-2 → Enterprise/chain (too big for our prices)
-1 → Very new business (<6 months, tight budget)
-1 → Niche we've had poor conversion with
-1 → Outside our target geography

SCORE THRESHOLDS:
9-12 → HOT LEAD → Contact same day, personalized email + mockup
6-8  → WARM LEAD → Contact in batch, personalized email
3-5  → COLD LEAD → Contact only when hot leads exhausted
0-2  → SKIP → Not worth contacting
```

## Cold Email Quality Gates

```
Email MUST pass all before sending:
✅ Under 150 words
✅ Mentions their specific business/problem (personalization score >7/10)
✅ Subject line is curiosity-driven (not salesy)
✅ Single clear CTA (not multiple asks)
✅ Spam score below 3/10
✅ No spam trigger words
✅ Human tone score >8/10
✅ No "I hope this email finds you well"
✅ Plain text format (not HTML)
✅ Unsubscribe link included
```

---

# 10. QUALITY CONTROL SYSTEM

## 3-Pass Review Process

```
PASS 1 — TECHNICAL (automated)
→ Does it meet word count / page count requirements?
→ Are all sections present?
→ Are there broken links or missing images?
→ Does code work (for websites)?
→ RESULT: Pass/Fail (auto-fix if fail)

PASS 2 — QUALITY (Gemini Vision/Pro review)
→ Score 1-10 on primary quality metric
→ Does it look/sound professional?
→ Would a paying client be satisfied?
→ Specific improvement suggestions
→ RESULT: Auto-fix if <7, flag if 7-8, approve if 9+

PASS 3 — CONTEXT (Gemini Pro)
→ Does it match the client's industry?
→ Does the tone match their brand?
→ Is all client-specific info accurate?
→ Does it solve the stated problem?
→ RESULT: Ready to deliver OR needs human review
```

## Quality Score Thresholds

```
9-10 → Auto-approve → Ready for delivery
7-8  → Flag for human review → 2-minute check
5-6  → Auto-fix attempt → Re-score → If still <7 → human
<5   → Discard + regenerate → Max 3 attempts → Human if still failing
```

---

# 11. PAYMENT INFRASTRUCTURE

## Complete Payment Flow

```
INDIAN CLIENT (INR):
Client agrees → Agent creates Razorpay link → Client pays UPI/Card
→ Webhook fires → Agent confirms → Work starts → Bank in 2 days

INTERNATIONAL CLIENT (USD):
Client agrees → Agent shares Wise details → Client sends USD
→ Wise converts → INR lands in bank → Agent confirms → Work starts

CRYPTO CLIENT (USDT):
Client agrees → Agent shares Binance Pay ID or USDT address
→ Client sends → Agent monitors Binance API → Confirms
→ Work starts → You P2P to INR when ready

FIVERR:
Client orders → Fiverr holds payment → Agent detects order
→ Delivers → Client accepts → Fiverr releases → Withdraw to Wise
```

## Invoice System

Every direct client gets a professional PDF invoice:
```
Invoice #INV-2026-001
Date: [date]
Due: [date + 7 days]
From: [Your Name / Business]
To: [Client Name]
Service: [Service description]
Amount: ₹X,XXX or $XXX
Payment methods: [Razorpay link / Crypto / Wise]
GST: [If applicable]
```

---

# 12. DATABASE ARCHITECTURE

## Complete Schema

```sql
-- LEADS TABLE
leads (
    id UUID PRIMARY KEY,
    source VARCHAR,              -- google_maps|reddit|twitter|etc
    business_name VARCHAR,
    contact_name VARCHAR,
    email VARCHAR UNIQUE,
    phone VARCHAR,
    website VARCHAR,
    location VARCHAR,
    niche VARCHAR,
    problem_detected TEXT,       -- Gemini-identified problem
    score INTEGER,               -- 0-12 quality score
    score_breakdown JSON,        -- detailed scoring
    status VARCHAR,              -- new|contacted|replied|client|rejected|unsubscribed
    enrichment_data JSON,        -- social presence, website quality etc
    created_at TIMESTAMP,
    last_contacted TIMESTAMP,
    next_followup TIMESTAMP,
    sequence_step INTEGER        -- 0-5
)

-- EMAILS TABLE
emails (
    id UUID PRIMARY KEY,
    lead_id UUID → leads.id,
    direction VARCHAR,           -- sent|received
    subject VARCHAR,
    body TEXT,
    template_id VARCHAR,         -- which prompt template used
    personalization_score FLOAT, -- 0-10
    spam_score FLOAT,            -- 0-10
    quality_score FLOAT,         -- 0-10
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    sequence_step INTEGER,
    status VARCHAR,              -- sent|opened|clicked|replied|bounced
    metadata JSON                -- email provider response
)

-- ORDERS TABLE
orders (
    id UUID PRIMARY KEY,
    source VARCHAR,              -- fiverr|razorpay|direct|crypto
    external_id VARCHAR,         -- Fiverr order ID / Razorpay order ID
    client_id UUID → clients.id,
    service_type VARCHAR,
    requirements TEXT,
    parsed_requirements JSON,
    amount REAL,
    currency VARCHAR,
    inr_amount REAL,
    payment_method VARCHAR,
    payment_status VARCHAR,      -- pending|paid|refunded
    order_status VARCHAR,        -- new|clarifying|in_progress|quality_check|ready|delivered|revision
    quality_score REAL,
    deliverable_path VARCHAR,
    revision_count INTEGER,
    created_at TIMESTAMP,
    delivered_at TIMESTAMP,
    notes TEXT
)

-- PAYMENTS TABLE
payments (
    id UUID PRIMARY KEY,
    order_id UUID → orders.id,
    provider VARCHAR,            -- razorpay|binance|wise|fiverr
    external_payment_id VARCHAR,
    amount REAL,
    currency VARCHAR,
    inr_amount REAL,
    fx_rate REAL,
    status VARCHAR,              -- pending|confirmed|failed|refunded
    provider_response JSON,
    received_at TIMESTAMP,
    settled_at TIMESTAMP,
    notes TEXT
)

-- CLIENTS TABLE
clients (
    id UUID PRIMARY KEY,
    name VARCHAR,
    email VARCHAR UNIQUE,
    phone VARCHAR,
    company VARCHAR,
    location VARCHAR,
    niche VARCHAR,
    total_orders INTEGER,
    total_spent_inr REAL,
    preferred_payment VARCHAR,
    satisfaction_score REAL,     -- average review score
    is_retainer BOOLEAN,
    retainer_amount REAL,
    retainer_next_billing TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP,
    last_order_at TIMESTAMP
)

-- CONTENT TABLE
content (
    id UUID PRIMARY KEY,
    type VARCHAR,                -- article|social_post|newsletter
    platform VARCHAR,            -- medium|substack|linkedin|twitter
    title VARCHAR,
    slug VARCHAR,
    url VARCHAR,
    word_count INTEGER,
    keywords JSON,
    affiliate_links JSON,
    seo_score REAL,
    views INTEGER,
    clicks INTEGER,
    affiliate_earnings REAL,
    medium_earnings REAL,
    published_at TIMESTAMP,
    last_stats_update TIMESTAMP
)

-- PERFORMANCE TABLE
performance (
    id UUID PRIMARY KEY,
    metric_type VARCHAR,         -- email_open_rate|lead_source_cvr|service_satisfaction
    metric_value REAL,
    context JSON,                -- what conditions (source, template, service type)
    period VARCHAR,              -- daily|weekly|monthly
    recorded_at TIMESTAMP
)

-- AGENT LOGS TABLE
agent_logs (
    id UUID PRIMARY KEY,
    module VARCHAR,
    action VARCHAR,
    result VARCHAR,              -- success|failed|partial|skipped
    duration_ms INTEGER,
    details JSON,
    error_message TEXT,
    created_at TIMESTAMP
)

-- PROMPT VERSIONS TABLE
prompt_versions (
    id UUID PRIMARY KEY,
    prompt_name VARCHAR,
    version INTEGER,
    content TEXT,
    performance_score REAL,
    uses INTEGER,
    is_active BOOLEAN,
    created_at TIMESTAMP
)

-- DIGITAL PRODUCTS TABLE
digital_products (
    id UUID PRIMARY KEY,
    name VARCHAR,
    type VARCHAR,                -- prompt_pack|template|swipe_file|ebook
    gumroad_id VARCHAR,
    price_usd REAL,
    total_sales INTEGER,
    total_revenue_usd REAL,
    created_at TIMESTAMP,
    last_sale_at TIMESTAMP
)
```

---

# 13. API INTEGRATION LAYER

## All APIs Used

### Free APIs (No Credit Card)

| API | Purpose | Daily Free Limit |
|---|---|---|
| Google Gemini 2.5 Pro | Primary LLM | 500 req/day |
| Google Gemini 2.0 Flash | Fast LLM | 1500 req/day |
| Groq Llama 3.3 70B | Fallback LLM | 14,400 req/day |
| Gmail API | Email sending | 500 emails/day |
| Google Places API | Lead discovery | $200 credit/month |
| Google Trends | Topic research | Unlimited |
| Reddit API (PRAW) | Lead monitoring | 60 req/min |
| Twitter API v2 | Lead monitoring | 500K tweets/month |
| Medium API | Content publish | Unlimited |
| Buffer API | Social schedule | 10 posts free |
| Unsplash API | Free images | 50 req/hr |
| Replicate API | Logo/image gen | $5 free credit |
| ExchangeRate API | FX rates | 1500 req/month |
| Hunter.io | Email finding | 25 searches/month |
| Telegram Bot API | Alerts | Unlimited |

### Paid APIs (Transaction-Based, No Monthly Fee)

| API | Purpose | Cost |
|---|---|---|
| Razorpay | Indian payments | 2% per transaction |
| Binance API | Crypto monitoring | Free |
| Twilio | WhatsApp (optional) | Pay-per-message |

---

# 14. SECURITY ARCHITECTURE

## What Agent CAN Do

```
✅ Read/write files in /outputs and /data
✅ Make HTTP requests to whitelisted APIs only
✅ Query and update its own database
✅ Send emails from configured Gmail account
✅ Post content to connected platforms
✅ Generate Razorpay payment links
✅ Monitor Binance for incoming payments
✅ Send Telegram alerts
✅ Read and classify incoming emails
✅ Schedule its own jobs
```

## What Agent CANNOT Do

```
❌ Move, transfer, or withdraw any money
❌ Confirm or approve any payments
❌ Deliver orders without setting human_review=True
❌ Modify its own constitution.py file
❌ Delete any database records
❌ Access files outside project directory
❌ Make API calls to non-whitelisted domains
❌ Send more than 400 emails per day (hard limit)
❌ Contact same lead more than once per 3 days
❌ Execute arbitrary code
❌ Install new packages without human approval
```

## Security Layers

```
Layer 1: .env validation on startup (fail if missing keys)
Layer 2: API key whitelist (only approved endpoints callable)
Layer 3: File system sandbox (chroot-like path restrictions)
Layer 4: Rate guard (hard limits per platform, auto-pause)
Layer 5: Webhook signature verification (Razorpay)
Layer 6: Audit log (every action recorded, append-only)
Layer 7: Human approval gates (payments, deliveries)
Layer 8: Circuit breakers (auto-stop on anomaly detection)
```

---

# 15. SCHEDULER & JOB SYSTEM

## Complete Job Schedule (IST)

```
TIME          FREQUENCY    JOB                    MODULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
06:00         Daily        health_check           core/
08:00         Daily        lead_hunting           lead_finder/
09:00         Daily        content_publishing     content_writer/
11:00         Daily        email_sending (AM)     outreach/
14:00         Daily        email_sending (PM)     outreach/
19:00         Daily        social_scheduling      social_manager/
21:00         Daily        performance_log        core/
23:00         Daily        db_backup              scripts/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Every 15min               payment_monitor        payment_handler/
Every 30min               fiverr_monitor         service_delivery/
Every 2hrs                reply_checker          outreach/
Every 6hrs                followup_check         outreach/
Every 1hr                 health_check           core/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sunday 22:00  Weekly       performance_review     core/
1st of month  Monthly      earnings_report        payment_handler/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# 16. DASHBOARD & MONITORING

## Dashboard Pages

### Overview Page (/)
```
📊 TODAY'S SUMMARY
  New leads found: 47          Emails sent: 23
  Email opens: 8 (35%)         Replies: 2 🔥
  Orders completed: 1          Revenue today: ₹4,999

🔴 NEEDS YOUR ATTENTION (3 items)
  → Fiverr order #1234 ready to deliver [REVIEW]
  → Hot reply from Sharma's Kitchen [DRAFT READY]
  → Payment of ₹8,999 received from Priya S. [CONFIRM WORK]

📈 THIS WEEK
  Revenue: ₹18,450 | Leads: 312 | Emails: 156 | Replies: 11
```

### Earnings Page (/earnings)
```
💰 REVENUE BREAKDOWN
  [Chart: Daily revenue last 30 days]
  [Chart: Revenue by service type]
  [Chart: Revenue by payment method]

  Fiverr gigs:          ₹8,200
  Direct websites:      ₹14,999
  Chatbot retainers:    ₹5,997
  Affiliate content:    ₹1,240
  TOTAL THIS MONTH:     ₹30,436
```

## Telegram Alert Format

```
🔴 URGENT ALERT
━━━━━━━━━━━━━━━━━━
New Fiverr Order Received
Order #: FVR-128493
Service: Landing Page
Budget: $80
Requirements: Restaurant website for Mumbai client
Estimated delivery: 24hrs

Deliverable ready in: ~2 hours
Action needed: Review + deliver
━━━━━━━━━━━━━━━━━━
[View in Dashboard]

🟡 HOT REPLY
━━━━━━━━━━━━━━━━━━
From: rajesh@sharmaskitchen.com
Subject: Re: Quick question about Sharma's Kitchen

Reply content: "Yes, please send the mockup!"

Draft reply prepared and waiting for your review.
━━━━━━━━━━━━━━━━━━
[Review Draft]

🟢 PAYMENT RECEIVED
━━━━━━━━━━━━━━━━━━
₹12,999 via Razorpay
Client: Priya Sharma
Service: Full website + chatbot
Payment ID: pay_abc123xyz
━━━━━━━━━━━━━━━━━━
Agent starting work now.

📊 DAILY SUMMARY (9 PM IST)
━━━━━━━━━━━━━━━━━━
Leads discovered: 47
Emails sent: 23 (daily limit: 400)
Open rate today: 34.8%
Replies: 2
Orders delivered: 1
Revenue today: ₹4,999
Running total (month): ₹18,450
━━━━━━━━━━━━━━━━━━
```

---

# 17. SELF-IMPROVEMENT ENGINE

## Weekly Analysis (Every Sunday)

```
Agent analyzes past 7 days:

EMAIL PERFORMANCE:
→ Which subject lines got highest open rates?
→ Which email templates got most replies?
→ Which niches responded best?
→ What time of day had best reply rates?

LEAD PERFORMANCE:
→ Which sources produced converting leads?
→ Which niches converted to paying clients?
→ What lead score threshold was most accurate?

SERVICE PERFORMANCE:
→ Which services got best client satisfaction?
→ Which services had most revisions?
→ Which services are most profitable per hour?

CONTENT PERFORMANCE:
→ Which articles got most views?
→ Which affiliate products got most clicks?
→ Which topics to write more about?

→ Updates strategy configuration
→ Rewrites underperforming prompts (with Gemini's help)
→ Adjusts lead source weights
→ Changes daily schedule if needed
→ Sends full report to Telegram
```

---

# 18. ERROR HANDLING & RECOVERY

## Circuit Breaker Pattern

```python
# If Gemini API fails 3 times in a row:
→ Switch to Groq fallback automatically
→ Alert human via Telegram
→ Continue with Groq until Gemini recovers
→ Auto-switch back when Gemini responds

# If Gmail bounce rate exceeds 5%:
→ PAUSE all email sending immediately
→ Alert human urgently
→ Wait for human to investigate + resume

# If Razorpay webhook fails:
→ Retry 3 times with exponential backoff
→ Log failed webhook payload
→ Alert human to manually verify payment
→ Do NOT start work until confirmed

# If database unavailable:
→ Log to local file temporarily
→ Retry connection every 60 seconds
→ Alert human after 5 failed attempts
→ Pause all DB-dependent operations
```

## Error Categories

```
FATAL (stops agent, alerts immediately):
→ Database unrecoverable
→ All LLMs down
→ Unauthorized access attempt

CRITICAL (alerts human, degrades gracefully):
→ Primary LLM down (switch to fallback)
→ Gmail bounce rate too high (pause emails)
→ Razorpay webhook validation failing

WARNING (logs, continues):
→ Single API request failed (retry)
→ Lead source rate limited (back off)
→ Single email bounced (mark, move on)

INFO (logs only):
→ Task completed successfully
→ Lead scored and saved
→ Scheduled job ran
```

---

# 19. DEPLOYMENT ARCHITECTURE

## Railway.app Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login + create project
railway login
railway new autonomous-agent

# Set all environment variables
railway variables set GEMINI_API_KEY=xxx
railway variables set GMAIL_CLIENT_ID=xxx
# ... (all env vars)

# Deploy
git push && railway up

# Monitor
railway logs --follow
```

## Dockerfile (Multi-Stage)

```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder
WORKDIR /build
RUN pip install uv
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime
WORKDIR /app

# Install Playwright + Chromium
RUN apt-get update && apt-get install -y \
    chromium chromium-driver \
    fonts-liberation libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app
COPY . .
RUN playwright install chromium

# Non-root user for security
RUN useradd -m agent
USER agent

CMD ["python", "main.py"]
```

## Keep-Alive Setup

```
1. Deploy to Railway
2. Get your Railway public URL
3. Go to cron-job.org (free)
4. Create job: GET https://your-app.railway.app/health
5. Frequency: Every 5 minutes
6. This prevents Railway free tier from sleeping
```

## Zero-Downtime Updates

```
git add .
git commit -m "feat: improved email templates"
git push origin main
→ GitHub Actions runs tests
→ If tests pass → Railway auto-deploys
→ Old version stays up until new is healthy
→ Zero downtime deployment
```

---

# 20. EARNING METHODS (COMPLETE)

## Tier 1: Active (Fast Cash)

### Fiverr Gigs

| Gig | Intro Price | Growth Price | Authority Price |
|---|---|---|---|
| AI Chatbot Setup | $30 | $60 | $120 |
| Landing Page | $50 | $90 | $180 |
| Cold Email Sequence | $30 | $60 | $100 |
| SEO Blog Post | $15 | $30 | $60 |
| Brand Kit | $50 | $80 | $150 |
| YouTube Thumbnail (5) | $20 | $35 | $60 |
| Social Media Pack (30) | $30 | $60 | $100 |
| Ad Copy Set | $25 | $50 | $80 |
| YouTube Script | $25 | $50 | $80 |
| LinkedIn Profile Rewrite | $30 | $60 | $100 |

### Direct Clients (INR)

| Service | Intro | Growth | Authority |
|---|---|---|---|
| Basic Website (3 pages) | ₹3,999 | ₹6,999 | ₹12,999 |
| Full Website (5 pages + SEO) | ₹7,999 | ₹14,999 | ₹24,999 |
| AI Chatbot (website) | ₹4,999 | ₹8,999 | ₹16,999 |
| AI Chatbot + WhatsApp | ₹7,999 | ₹13,999 | ₹24,999 |
| Cold Email System Setup | ₹6,999 | ₹12,999 | ₹22,999 |
| Brand Kit | ₹3,499 | ₹5,999 | ₹9,999 |
| Social Media Pack | ₹1,999 | ₹3,499 | ₹5,999 |

## Tier 2: Recurring (Stable Income)

| Service | Intro/month | Growth/month | Authority/month |
|---|---|---|---|
| Social Media Management | ₹2,999 | ₹5,999 | ₹9,999 |
| Chatbot Maintenance | ₹1,999 | ₹3,499 | ₹5,999 |
| Content Writing (4 articles) | ₹3,999 | ₹6,999 | ₹11,999 |
| Lead Gen Service | ₹4,999 | ₹8,999 | ₹14,999 |
| White Label Partner | ₹8,999 | ₹15,999 | ₹24,999 |

## Tier 3: High Ticket (Big Deals)

| Service | Price Range |
|---|---|
| Full AI Business Integration | ₹24,999 - ₹99,999 |
| Complete Digital Presence Setup | ₹14,999 - ₹49,999 |
| AI Audit + Implementation | ₹12,999 - ₹39,999 |
| Custom SaaS MVP | ₹49,999 - ₹1,99,999 |

## Tier 4: Passive (While Sleeping)

| Source | Month 1 | Month 3 | Month 6 |
|---|---|---|---|
| Medium Partner + Affiliate | ₹500 | ₹3,000 | ₹12,000 |
| Gumroad Digital Products | ₹0 | ₹1,000 | ₹5,000 |
| Newsletter Sponsorships | ₹0 | ₹0 | ₹3,000 |
| Substack Paid Tier | ₹0 | ₹0 | ₹2,000 |

---

# 21. PRICING STRATEGY

## Phase 1: New Account (Month 1-2)
```
Goal: Get 10 reviews FAST
Strategy: Price 40-50% below market
Result: Lots of orders → lots of reviews → algorithm boost
```

## Phase 2: Established (Month 3-4)
```
Goal: Raise prices, keep volume
Strategy: 20% price increase per month
Filter: Keep clients who pay new price, let budget ones go
```

## Phase 3: Authority (Month 5+)
```
Goal: Premium positioning
Strategy: Highest prices in niche + best reviews combo
Filter: Only take high-quality, high-budget clients
```

## Upsell Ladder

```
Client buys blog post ($20)
    → Upsell: social media pack for this post ($30)
    → Upsell: monthly content package ($80/month)

Client buys landing page ($80)
    → Upsell: AI chatbot for the page ($60)
    → Upsell: monthly maintenance ($40/month)
    → Upsell: SEO optimization ($50)

Client buys chatbot ($100)
    → Upsell: WhatsApp integration ($80)
    → Upsell: monthly maintenance ($50/month)
    → Upsell: analytics dashboard ($40)

Client buys cold email system ($150)
    → Upsell: we manage it monthly ($80/month)
    → Upsell: lead list + CRM setup ($100)
```

---

# 22. PAYMENT FLOW (COMPLETE)

## Decision Logic

```python
def decide_payment_method(client):
    if client.location == "India":
        if client.amount < 500:  # INR
            return "UPI_DIRECT"
        else:
            return "RAZORPAY"
    elif client.prefers_crypto:
        return "BINANCE_USDT"
    elif client.location in INTERNATIONAL_COUNTRIES:
        return "WISE"
    elif client.platform == "fiverr":
        return "FIVERR_HANDLES"
    else:
        return "WISE"  # default international
```

## Razorpay Complete Flow

```
1. Agent creates payment link via Razorpay API
   → Amount, description, client name
   → Expiry: 7 days
   → Accepts: UPI, Cards, NetBanking, Wallets

2. Agent sends link to client in email

3. Client pays

4. Razorpay fires webhook to /webhooks/razorpay

5. Agent verifies webhook signature (security)

6. Agent confirms payment in DB

7. Agent starts work

8. Razorpay settles to your bank (T+2 working days)
```

## Binance/Crypto Complete Flow

```
1. Client wants to pay crypto

2. Agent determines best method:
   → Binance Pay ID (for Binance users)
   → USDT TRC20 address (for wallet users)
   → USDT ERC20 address (backup, higher fees)

3. Agent sends payment details with exact amount

4. Agent polls Binance API every 5 minutes for incoming

5. Payment detected → confirmed → logged

6. Work starts

7. When ready to cash out:
   → Binance P2P → sell USDT → buyer sends UPI
   → Money in bank within 30 mins
```

## Wise Complete Flow

```
1. International client confirmed

2. Agent shares Wise account details:
   → Account holder name
   → IBAN (for Europe/UK)
   → Sort code + account number (UK)
   → Routing number (US)

3. Client sends in their currency (USD/EUR/GBP)

4. Wise auto-converts at near-market rate

5. INR lands in your Wise balance

6. Transfer to Indian bank manually (when amount builds up)

7. Fee: ~1% total (much better than PayPal's 4%)
```

---

# 23. ENVIRONMENT & SETUP

## Complete .env File

```bash
# ═══════════════════════════════
# AGENT CONFIGURATION
# ═══════════════════════════════
AGENT_NAME=Atlas
AGENT_ENV=production               # development|staging|production
AGENT_LOG_LEVEL=INFO               # DEBUG|INFO|WARNING|ERROR
DASHBOARD_PASSWORD=your_strong_password
DASHBOARD_PORT=8000

# ═══════════════════════════════
# LLM APIS
# ═══════════════════════════════
GEMINI_API_KEY=                    # aistudio.google.com
GROQ_API_KEY=                      # console.groq.com

# ═══════════════════════════════
# GOOGLE APIS
# ═══════════════════════════════
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_SENDER_ADDRESS=your@gmail.com
GOOGLE_PLACES_API_KEY=
GOOGLE_ANALYTICS_ID=

# ═══════════════════════════════
# SOCIAL MEDIA
# ═══════════════════════════════
REDDIT_CLIENT_ID=
REDDIT_SECRET=
REDDIT_USERNAME=
TWITTER_BEARER_TOKEN=
TWITTER_API_KEY=
TWITTER_API_SECRET=
BUFFER_ACCESS_TOKEN=
MEDIUM_INTEGRATION_TOKEN=

# ═══════════════════════════════
# PAYMENTS
# ═══════════════════════════════
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
BINANCE_API_KEY=
BINANCE_SECRET=
BINANCE_PAY_ID=                    # Your Binance Pay ID
USDT_TRC20_ADDRESS=                # Your USDT wallet address

# ═══════════════════════════════
# DESIGN APIS
# ═══════════════════════════════
REPLICATE_API_TOKEN=
CANVA_API_KEY=
UNSPLASH_ACCESS_KEY=
PEXELS_API_KEY=

# ═══════════════════════════════
# FREELANCE PLATFORMS
# ═══════════════════════════════
FIVERR_API_KEY=
FIVERR_USERNAME=gauravstack
GUMROAD_ACCESS_TOKEN=

# ═══════════════════════════════
# COMMUNICATION
# ═══════════════════════════════
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TWILIO_ACCOUNT_SID=                # Optional, for WhatsApp
TWILIO_AUTH_TOKEN=                 # Optional

# ═══════════════════════════════
# DATA ENRICHMENT
# ═══════════════════════════════
HUNTER_API_KEY=
EXCHANGERATE_API_KEY=

# ═══════════════════════════════
# LIMITS & SAFETY
# ═══════════════════════════════
MAX_EMAILS_PER_DAY=400
MAX_LEADS_PER_DAY=200
MIN_LEAD_SCORE=6
EMAIL_COOLDOWN_DAYS=3
MAX_REVISIONS_PER_ORDER=2
QUALITY_SCORE_THRESHOLD=7.0

# ═══════════════════════════════
# YOUR INFO (for invoices)
# ═══════════════════════════════
YOUR_NAME=Mikey
YOUR_BUSINESS_NAME=
YOUR_EMAIL=
YOUR_UPI_ID=
YOUR_BANK_ACCOUNT=
YOUR_WISE_EMAIL=
```

## First-Time Setup Commands

```bash
# 1. Clone project
git clone https://github.com/yourusername/autonomous-agent.git
cd autonomous-agent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install uv
uv pip install -r requirements.txt
playwright install chromium

# 4. Setup environment
cp .env.example .env
# Fill in all values in .env

# 5. Validate all API connections
python scripts/test_all_apis.py

# 6. Initialize database
python scripts/init_db.py

# 7. Run first test cycle
python main.py --test --verbose

# 8. Deploy to Railway
railway login
railway up
```

---

# 24. BUILD ORDER & TIMELINE

## Week 1: Foundation

```
Day 1:
  □ Project setup + virtual env
  □ Install all dependencies
  □ Create .env with all keys
  □ Run test_all_apis.py (verify everything connects)
  □ Initialize database + migrations

Day 2:
  □ core/agent.py → master agent class
  □ core/state_machine.py → agent states
  □ core/constitution.py → agent rules
  □ llm/providers/ → Gemini + Groq clients
  □ llm/router.py → smart model selector

Day 3:
  □ utils/logger.py → structured logging
  □ utils/notifier.py → Telegram alerts
  □ utils/http_client.py → async httpx
  □ utils/rate_limiter.py → per-API limits
  □ database/connection.py → SQLAlchemy setup

Day 4:
  □ database/models/ → all ORM models
  □ database/repositories/ → all repositories
  □ Run migrations → verify DB structure
  □ Test: create/read/update lead in DB

Day 5:
  □ core/loop.py → main execution loop
  □ core/decision_engine.py → task prioritization
  □ scheduler/scheduler.py → APScheduler setup
  □ Test: agent starts, runs one cycle, logs output

Day 6-7:
  □ modules/lead_finder/sources/google_maps.py
  □ modules/lead_finder/scorer.py
  □ modules/lead_finder/deduplicator.py
  □ Test: find + score 10 real leads
  □ Verify leads saved to DB correctly
```

## Week 2: Outreach Engine

```
Day 1-2:
  □ integrations/google/gmail.py
  □ modules/outreach/email_generator.py
  □ modules/outreach/quality_checker.py
  □ modules/outreach/spam_guard.py
  □ Test: generate + quality-check 5 emails (don't send yet)

Day 3:
  □ modules/outreach/sequence_engine.py
  □ modules/outreach/reply_classifier.py
  □ modules/outreach/reply_drafter.py
  □ scheduler/jobs/email_sending.py
  □ Test: send 3 real test emails to yourself

Day 4-5:
  □ modules/outreach/subject_optimizer.py
  □ modules/outreach/open_tracker.py
  □ modules/outreach/unsubscribe_handler.py
  □ Test: full outreach sequence on 5 real leads

Day 6-7:
  □ modules/payment_handler/providers/razorpay.py
  □ modules/payment_handler/invoice_generator.py
  □ dashboard/routers/webhooks/razorpay.py
  □ modules/payment_handler/providers/binance.py
  □ Test: create Razorpay link, complete test payment
```

## Week 3: Service Delivery

```
Day 1-2:
  □ modules/website_builder/ (full module)
  □ All 12 website templates (HTML/CSS)
  □ Test: build complete restaurant website

Day 3:
  □ modules/service_delivery/fiverr_monitor.py
  □ modules/service_delivery/order_parser.py
  □ modules/service_delivery/generators/ (all generators)
  □ Test: simulate Fiverr order, generate + package deliverable

Day 4:
  □ modules/chatbot_builder/ (full module)
  □ Test: build chatbot for a real website URL

Day 5:
  □ modules/design_generator/ (full module)
  □ Test: generate logo + brand kit

Day 6-7:
  □ dashboard/ (full FastAPI dashboard)
  □ Test: access dashboard, see all data
  □ Deploy to Railway
  □ Set up cron keepalive
```

## Week 4: Content + Polish

```
Day 1-2:
  □ modules/content_writer/ (full module)
  □ Test: research topic, write article, post to Medium

Day 3:
  □ modules/social_manager/ (full module)
  □ modules/digital_products/ (basic version)
  □ Test: generate social pack, schedule via Buffer

Day 4:
  □ core/self_improvement.py
  □ scheduler/jobs/performance_review.py
  □ Test: run weekly review, see strategy output

Day 5-7:
  □ Full system test (all modules together)
  □ Fix all bugs found
  □ Launch Fiverr gigs
  □ Start first real cold email campaign (50 leads)
  □ Publish first Medium article
  □ Monitor dashboard + Telegram alerts
```

## Month 2+: Scale

```
  → Analyze first month data
  → Double down on what's working
  → Add more lead sources
  → Expand to more website templates
  → Launch more Fiverr gigs
  → Start retainer conversations
  → Build white label partnerships
  → Grow affiliate content library
  → Launch digital products on Gumroad
```

---

# 25. ACCOUNTS REQUIRED

## Day 1 (Before Writing Code)

```
Priority  Platform              URL                        Purpose
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴        Google AI Studio      aistudio.google.com        Gemini API key
🔴        Groq Console          console.groq.com           Fallback LLM
🔴        GitHub                github.com                 Code hosting
🔴        Railway.app           railway.app                Free hosting
🔴        Gmail (dedicated)     gmail.com                  Agent email sender
🔴        Razorpay              razorpay.com               Indian payments
🔴        Binance               binance.com                Crypto payments
🔴        Wise                  wise.com                   International
🔴        Telegram              t.me/BotFather             Alerts bot
🔴        Fiverr                fiverr.com/gauravstack      Already have ✅
```

## Week 1 (During Development)

```
🟡        Google Cloud Console  console.cloud.google.com   Gmail + Places API
🟡        Reddit Dev            reddit.com/prefs/apps      Reddit API
🟡        Twitter Dev           developer.twitter.com      Twitter API
🟡        Medium                medium.com                 Content publishing
🟡        Buffer                buffer.com                 Social scheduling
🟡        Unsplash Dev          unsplash.com/developers    Free images API
🟡        Replicate             replicate.com              Logo/image gen
🟡        Hunter.io             hunter.io                  Email finder (free)
🟡        ExchangeRate API      exchangerate-api.com       Currency rates
```

## Month 1 (After Launch)

```
🟢        Gumroad               gumroad.com                Digital products
🟢        Canva API             canva.com/developers       Design templates
🟢        AppSumo Affiliate     affiliate.appsumo.com      Affiliate income
🟢        Fiverr Affiliate      fiverr.com/affiliate       Affiliate income
🟢        Amazon Associates     affiliate-program.amazon   Affiliate income
🟢        Semrush Affiliate     semrush.com/affiliates     $200/referral
🟢        Hostinger Affiliate   hostinger.com/affiliates   60% commission
🟢        Pexels API            pexels.com/api             Backup free images
🟢        Clearbit              clearbit.com               Company enrichment
🟢        UptimeRobot           uptimerobot.com            Uptime monitoring
```

---

# 26. INCOME PROJECTIONS

## Conservative Path

```
MONTH 1 (Building + Testing):
  Fiverr gigs (5 orders):      ₹6,000
  Direct clients (1):           ₹4,999
  TOTAL:                        ₹10,999

MONTH 2 (System Running):
  Fiverr gigs (12 orders):     ₹15,000
  Direct clients (2):           ₹12,999
  Retainers (1):                ₹2,999
  Affiliate starts:             ₹500
  TOTAL:                        ₹31,498

MONTH 3 (Gaining Traction):
  Fiverr gigs (20 orders):     ₹26,000
  Direct clients (3):           ₹22,999
  Retainers (3):                ₹8,997
  Affiliate:                    ₹2,000
  TOTAL:                        ₹59,996

MONTH 6 (Scaled):
  Fiverr gigs:                 ₹40,000
  Direct clients (5):           ₹49,999
  Retainers (7):                ₹20,993
  White label (2):              ₹17,998
  Affiliate + passive:          ₹8,000
  TOTAL:                        ₹1,36,990

MONTH 12 (Mature System):
  All above growing             ₹2,50,000 - ₹5,00,000
```

## Revenue Mix at Scale

```
Active income (40%):     Client work, Fiverr
Recurring income (35%):  Retainers, white label, maintenance
Passive income (25%):    Affiliate, digital products, newsletter
```

---

# 27. RISK MANAGEMENT

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Gmail banned for spam | Medium | High | Dedicated Gmail, warm-up slowly, 400/day hard limit |
| Gemini rate limit hit | Low | Medium | Groq fallback, response caching |
| Railway goes down | Low | High | Render.com backup, auto-redeploy |
| Fiverr gig removed | Low | Medium | Multiple gigs, diversify services |
| Low reply rate (<2%) | Medium | Medium | A/B test constantly, improve targeting |
| Razorpay webhook failure | Low | High | Retry logic, human alert, manual verify |
| Client unhappy | Low | High | 3-pass quality, revisions policy |
| Scraping blocked | Medium | Medium | Official APIs preferred, proxy rotation |
| DB corruption | Very Low | High | Daily backup to GitHub |
| Crypto price volatility | Low | Low | Convert to INR immediately via P2P |
| Platform API changes | Medium | Medium | Abstract integration layer (easy swap) |

## Emergency Procedures

```
Email spam complaint received:
→ Immediately pause all sending
→ Alert human
→ Review complaint, remove lead
→ Check bounce rate
→ Human resumes when resolved

Unexpected charge/payment issue:
→ Agent CANNOT spend money
→ All payments are incoming only
→ If payment issue: alert human immediately

API key compromised:
→ Rotate key immediately via platform
→ Update .env
→ Restart agent
→ Review audit log for unauthorized use
```

---

# 28. AGENT CONSTITUTION & RULES

## Immutable Rules (Cannot Be Changed)

```python
# constitution.py — NEVER MODIFY THIS FILE

ALLOWED_ACTIONS = [
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
    "log_own_activity"
]

FORBIDDEN_ACTIONS = [
    "transfer_any_money",
    "approve_any_payment",
    "deliver_without_human_review_flag",
    "modify_constitution_file",
    "delete_database_records",
    "access_files_outside_project",
    "call_non_whitelisted_urls",
    "send_more_than_400_emails_per_day",
    "contact_same_lead_within_3_days",
    "execute_arbitrary_code",
    "install_packages_automatically"
]

HUMAN_REQUIRED_FOR = [
    "any_payment_confirmation",
    "final_order_delivery",
    "strategy_major_changes",
    "new_api_key_addition",
    "budget_decisions"
]
```

---

# 29. PROMPT ENGINEERING STRATEGY

## Prompt Template Format

```
# prompts/outreach/write_cold_email.txt
# Version: 3
# Last updated: 2026-05
# Performance: 34% open rate, 8.2% reply rate

SYSTEM:
You are an expert cold email copywriter. You write short, 
human-sounding emails that get replies. You never sound salesy.

RULES:
- Under 150 words total
- First line must mention their specific situation
- Single clear CTA only
- No "I hope this email finds you well"
- Plain text, no formatting
- Must sound like a human wrote it at 2pm on a Tuesday

INPUT:
Business: {{business_name}}
Contact: {{contact_name}}
Their website: {{website_url}}
Problem detected: {{problem_detected}}
Our service: {{service_to_pitch}}
Our proof: {{social_proof}}

OUTPUT FORMAT:
Subject: [subject line here]

[email body here]

---
Generate the email now. Under 150 words.
```

## A/B Testing Prompts

```
Every prompt has a version number.
New version tested against old version on 50 emails each.
Winner (higher reply rate) becomes active.
Old version archived, not deleted.
Performance tracked in prompt_versions table.
```

---

# 30. COMPLETE CHECKLIST

## Pre-Launch Checklist

```
ACCOUNTS:
□ Google AI Studio account + Gemini API key obtained
□ Groq account + API key obtained
□ GitHub account + repo created
□ Railway.app account created
□ Dedicated Gmail created + API configured
□ Razorpay account created + verified
□ Binance account created + KYC completed
□ Wise account created
□ Telegram bot created via @BotFather
□ Reddit dev app created
□ Twitter dev account approved
□ Medium account created
□ Buffer account created
□ Replicate account + credits obtained
□ Fiverr gigs updated/optimized

DEVELOPMENT:
□ All code written + tested
□ All API connections verified (test_all_apis.py passes)
□ Database initialized + migrations run
□ All environment variables set
□ Dashboard accessible + secured
□ Telegram alerts working
□ First test cycle ran successfully (no errors)
□ Lead finder tested (finds 10+ real leads)
□ Email generator tested (quality score 8+)
□ Website builder tested (builds complete site)
□ Payment flow tested (Razorpay link created + paid)
□ Fiverr monitor tested (detects test order)

DEPLOYMENT:
□ Docker build succeeds
□ Railway deployment successful
□ Public URL accessible
□ Cron-job.org keepalive set up
□ UptimeRobot monitoring set up
□ GitHub Actions CI/CD working

LAUNCH:
□ First 50 leads loaded in database
□ First cold email campaign scheduled
□ First Medium article written + ready
□ Fiverr gigs published + optimized
□ Dashboard checked and working
□ Telegram alerts arriving on phone
□ Daily summary scheduled for 9PM IST
□ Weekly review scheduled for Sunday

POST-LAUNCH (Week 1):
□ Monitor email delivery rates daily
□ Check bounce rate (must stay <5%)
□ Review first replies + approve drafts
□ Check Fiverr for any orders
□ Review dashboard metrics daily
□ Adjust lead targeting if needed

MONTH 1 GOALS:
□ 10+ Fiverr orders completed
□ 5+ direct client conversations
□ 1-2 paying direct clients
□ 500+ emails sent
□ 5+ articles published
□ First ₹10,000 earned
□ First retainer client signed
```

---

## 🎯 NORTH STAR METRICS

```
WEEK 1:   System live, first emails sent
WEEK 2:   First reply received, first order delivered
MONTH 1:  ₹10,000 earned, 10 Fiverr reviews
MONTH 3:  ₹50,000/month, 3+ retainers
MONTH 6:  ₹1,00,000/month, system mostly autonomous
MONTH 12: ₹2,50,000+/month, passive income growing
```

---

## 💡 FINAL NOTES

```
This is not just a script. This is a business.
Build it seriously. Monitor it daily (5 mins).
The agent handles 95% of the work automatically.
Your role: strategy, deal closing, final approvals.

The first month is the hardest.
The system compounds. Be patient.
Every improvement you make runs forever.

Build it right once.
Then let it run.
```

---

*Blueprint Version: 3.0 — Ultimate Production Grade*
*Total Files in Project: ~260+*
*Total Earning Methods: 25+*
*Architecture: Clean Architecture + Repository Pattern + Circuit Breakers*
*Target: ₹1,00,000+/month by Month 6*
*Owner: Mikey (gauravstack)*
*Status: Ready to Build*
*Created: May 2026*

---
