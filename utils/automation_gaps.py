"""
Detect missing automation on business websites — AI chat, booking, ordering, scheduling.

Used by M24/M27/M28 hunters and website_pitch.py to pitch the right offer
(AI chatbot vs booking vs online orders vs custom SaaS) per niche.
"""

from __future__ import annotations

from typing import Any

# Tool/widget signatures grouped by automation type.
AUTOMATION_SIGNATURES: dict[str, tuple[str, ...]] = {
    "ai_chat": (
        "intercom",
        "drift.com",
        "tawk.to",
        "tidio",
        "crisp.chat",
        "livechat",
        "zendesk",
        "chatbot",
        "botpress",
        "voiceflow",
        "manychat",
        "landbot",
        "chatbase",
        "customgpt",
        "dialogflow",
        "freshchat",
        "hubspot.com/chat",
        "olark",
        "smartsupp",
    ),
    "booking": (
        "calendly.com",
        "acuityscheduling",
        "setmore.com",
        "booksy.com",
        "vagaro.com",
        "squareup.com/appointments",
        "simplybook",
        "schedulicity",
        "fresha.com",
        "mindbodyonline",
        "mindbody.io",
        "appointlet",
        "booker.com",
        "schedulista",
    ),
    "ordering": (
        "toasttab",
        "chownow",
        "doordash",
        "ubereats",
        "grubhub",
        "clover.com/online",
        "order online",
        "online ordering",
        "order now",
        "add to cart",
        "woocommerce",
        "shopify.com",
        "square.site",
        "menufy",
        "slice",
    ),
    "scheduling": (
        "cal.com",
        "doodle.com",
        "when2meet",
        "youcanbook",
        "schedule appointment",
        "book appointment",
        "book online",
    ),
    "whatsapp": (
        "wa.me/",
        "api.whatsapp.com",
        "whatsapp.com/send",
    ),
    "crm_followup": (
        "hubspot",
        "mailchimp",
        "activecampaign",
        "pipedrive",
        "salesforce",
        "zapier",
        "make.com",
        "convertkit",
        "klaviyo",
    ),
    "intake_forms": (
        "typeform.com",
        "jotform",
        "google.com/forms",
        "formspree",
        "contact-form-7",
        "wpforms",
        "gravityforms",
    ),
    "customer_support": (
        "zendesk",
        "zdassets.com",
        "freshdesk",
        "helpscout",
        "help scout",
        "gorgias",
        "kayako",
        "liveagent",
        "happyfox",
        "desk.zoho",
        "zoho.com/desk",
        "servicenow",
        "ada.support",
        "forethought.ai",
        "ultimate.ai",
        "kustomer",
        "help center",
        "knowledge base",
        "support ticket",
        "customer support",
        "/support",
        "faq widget",
        "support chat",
    ),
}

# What each niche type should have — gaps become pitch targets.
NICHE_AUTOMATION_NEEDS: dict[str, tuple[str, ...]] = {
  # Food & ordering
    "restaurant": ("ordering", "booking", "customer_support", "ai_chat"),
    "cafe": ("ordering", "customer_support", "ai_chat"),
    "bakery": ("ordering", "ai_chat"),
    "pizza": ("ordering", "ai_chat"),
    "food truck": ("ordering", "ai_chat"),
    "catering": ("ordering", "booking", "ai_chat"),
    # Beauty & wellness — booking first
    "hair salon": ("booking", "ai_chat"),
    "nail salon": ("booking", "ai_chat"),
    "barber": ("booking", "ai_chat"),
    "spa": ("booking", "ai_chat"),
    "massage": ("booking", "ai_chat"),
    "beauty salon": ("booking", "ai_chat"),
    # Health — booking + intake
    "dentist": ("booking", "ai_chat", "intake_forms"),
    "chiropractor": ("booking", "ai_chat"),
    "optometrist": ("booking", "ai_chat"),
    "physical therapy": ("booking", "ai_chat"),
    "veterinarian": ("booking", "ai_chat"),
    "doctor": ("booking", "ai_chat", "intake_forms"),
    "clinic": ("booking", "ai_chat", "intake_forms"),
    # Professional services
    "lawyer": ("ai_chat", "intake_forms", "booking"),
    "accountant": ("booking", "intake_forms", "ai_chat"),
    "insurance agent": ("customer_support", "ai_chat", "intake_forms"),
    "real estate": ("customer_support", "ai_chat", "crm_followup", "booking"),
    "realtor": ("customer_support", "ai_chat", "crm_followup", "booking"),
    "ecommerce": ("customer_support", "ordering", "ai_chat"),
    "retail": ("customer_support", "ordering", "ai_chat"),
    "store": ("customer_support", "ordering", "ai_chat"),
    # Trades — service calls + chat
    "plumber": ("ai_chat", "booking", "scheduling"),
    "electrician": ("ai_chat", "booking", "scheduling"),
    "hvac": ("ai_chat", "booking", "scheduling"),
    "roofer": ("ai_chat", "booking"),
    "landscaper": ("ai_chat", "booking"),
    "pest control": ("ai_chat", "booking"),
    "locksmith": ("ai_chat", "booking"),
    "cleaning": ("ai_chat", "booking"),
    # Fitness
    "gym": ("booking", "ai_chat"),
    "personal trainer": ("booking", "ai_chat"),
    "yoga studio": ("booking", "ai_chat"),
    # Auto
    "auto repair": ("booking", "ai_chat"),
    "car wash": ("booking", "ai_chat"),
    # Default local service
    "default": ("customer_support", "ai_chat", "booking", "scheduling"),
}

# Human labels for pitches / Instantly variables
AUTOMATION_PITCH_LABELS: dict[str, str] = {
    "ai_chat": "custom AI chatbot for your website (24/7 answers + lead capture)",
    "booking": "online appointment booking (no more phone tag)",
    "ordering": "online ordering so customers can place orders without calling",
    "scheduling": "self-serve scheduling for service calls and visits",
    "whatsapp": "WhatsApp AI assistant for enquiries and follow-up",
    "crm_followup": "automated lead follow-up so no enquiry goes cold",
    "intake_forms": "smart intake forms that qualify leads before you talk to them",
    "custom_saas": "custom software / SaaS tool built for your workflow",
    "customer_support": (
        "AI customer support — answers FAQs, handles tickets, escalates to you 24/7"
    ),
}

# Priority when multiple gaps exist (pitch the highest-value one first)
_GAP_PRIORITY = (
    "ordering",
    "booking",
    "customer_support",
    "ai_chat",
    "scheduling",
    "whatsapp",
    "intake_forms",
    "crm_followup",
)


def _niche_key(niche: str) -> str:
    n = (niche or "").lower().strip().replace("_", " ")
    if not n:
        return "default"
    for key in NICHE_AUTOMATION_NEEDS:
        if key == "default":
            continue
        if key in n or n in key:
            return key
    return "default"


def niche_automation_needs(niche: str) -> tuple[str, ...]:
    return NICHE_AUTOMATION_NEEDS.get(_niche_key(niche), NICHE_AUTOMATION_NEEDS["default"])


def detect_present_automation(html: str) -> set[str]:
    low = (html or "").lower()
    present: set[str] = set()
    for category, sigs in AUTOMATION_SIGNATURES.items():
        if any(sig in low for sig in sigs):
            present.add(category)
    return present


def detect_automation_gaps(html: str, niche: str) -> dict[str, Any]:
    """
    Return which automation types are missing for this niche + primary pitch target.
    """
    present = detect_present_automation(html)
    needed = niche_automation_needs(niche)
    missing = [cat for cat in needed if cat not in present]
    primary = _pick_primary_gap(missing)
    return {
        "automation_present": sorted(present),
        "automation_missing": missing,
        "automation_primary": primary,
        "automation_pitch": AUTOMATION_PITCH_LABELS.get(primary, AUTOMATION_PITCH_LABELS["ai_chat"]),
    }


def _pick_primary_gap(missing: list[str]) -> str:
    if not missing:
        return "ai_chat"
    for cat in _GAP_PRIORITY:
        if cat in missing:
            return cat
    return missing[0]


def has_any_automation(html: str) -> bool:
    return bool(detect_present_automation(html))


def missing_category(html: str, category: str) -> bool:
    return category not in detect_present_automation(html)


def problem_line_for_gaps(gaps: dict[str, Any], niche: str) -> str:
    primary = gaps.get("automation_primary") or "ai_chat"
    n = (niche or "local business").replace("_", " ")
    labels = {
        "ai_chat": f"no AI chatbot — {n} visitors who have questions after hours just leave",
        "booking": f"no online booking — customers still have to call to schedule",
        "ordering": f"no online ordering — hungry customers can't place orders from the site",
        "scheduling": f"no self-serve scheduling — every appointment starts with phone tag",
        "whatsapp": f"no WhatsApp automation — enquiries on mobile go unanswered",
        "intake_forms": f"no smart intake — you can't qualify leads before a call",
        "crm_followup": f"no automated follow-up — warm leads go cold",
        "customer_support": (
            f"no AI customer support — {n} visitors with questions wait for email or phone callbacks"
        ),
    }
    return labels.get(primary, labels["ai_chat"])
