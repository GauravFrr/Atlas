"""
Gaurav-style cold email sequence — matches the founder's manual outreach tone.
Email 1: curiosity + no-website hook + demo offer (campaign default).
Emails 2–3: light follow-ups for future sequence_engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from modules.lead_finder.scanners.google_maps import MapsScanResult
else:
    MapsScanResult = Any  # duck-typed: business_name, niche, city

# How they get leads without a site — one line per niche
NICHE_LEAD_QUESTIONS: dict[str, str] = {
    "plumber": "how you're currently handling emergency calls and booked jobs in {city}",
    "electrician": "how new customers are finding you for jobs in {city}",
    "hvac": "how you're booking service calls in {city} right now",
    "roofer": "how homeowners are reaching you for quotes in {city}",
    "landscaper": "how you're lining up new jobs in {city}",
    "dentist": "how new patients are booking with you in {city}",
    "chiropractor": "how patients are finding you in {city}",
    "restaurant": "how people are discovering you and placing orders in {city}",
    "cafe": "how foot traffic and online orders are working in {city}",
    "lawyer": "how potential clients are reaching your firm in {city}",
    "accountant": "how new clients are finding you in {city}",
}

DEFAULT_LEAD_QUESTION = "how you're currently handling local leads in {city}"


def _lead_question(niche: str, city: str) -> str:
    key = niche.lower().strip()
    template = NICHE_LEAD_QUESTIONS.get(key, DEFAULT_LEAD_QUESTION)
    return template.format(city=city)


def build_email_1(
    lead: MapsScanResult,
    your_name: str,
    demo_url: str | None = None,
) -> dict[str, str]:
    """
    First-touch email — same structure as Gaurav's manual sequence.
    Blank line between each beat (readable in inbox).
    """
    city = lead.city
    biz = lead.business_name
    question = _lead_question(lead.niche, city)

    if demo_url:
        demo_block = (
            f"I actually put together a quick custom demo site for {biz} — "
            f"wanted to show you what it could look like before you commit to anything."
        )
        cta = (
            f"Preview I put together for {biz}:\n{demo_url}\n\n"
            f"No pressure either way 👍"
        )
    else:
        demo_block = (
            f"I actually built a quick custom demo site for {biz} "
            f"just to show you what it could look like."
        )
        cta = "Happy to send over the link if you're open to taking a look 👍"

    body = (
        f"Hey {biz},\n\n"
        f"Noticed you don't have a website up yet — not sure if that's intentional "
        f"or just something you haven't had time to sort yet.\n\n"
        f"Curious {question}?\n\n"
        f"{demo_block}\n\n"
        f"{cta}\n\n"
        f"— {your_name}"
    )

    # Casual subject — not salesy
    short_name = biz.split(",")[0].strip()
    if len(short_name) > 40:
        short_name = short_name[:40].rsplit(" ", 1)[0]
    subject = f"quick question — {short_name}"

    return {"subject": subject, "body": body, "sequence_step": 1}


def build_email_2(lead: MapsScanResult, your_name: str) -> dict[str, str]:
    """Follow-up #1 — bump, same casual tone."""
    biz = lead.business_name
    body = (
        f"Hey {biz},\n\n"
        f"Just bumping this in case it got buried.\n\n"
        f"Still happy to send that demo link if you want to see what a simple site "
        f"could look like for {biz}.\n\n"
        f"Either way, no worries 👍\n\n"
        f"— {your_name}"
    )
    return {
        "subject": f"re: quick question — {biz.split(',')[0].strip()[:30]}",
        "body": body,
        "sequence_step": 2,
    }


def build_email_3(lead: MapsScanResult, your_name: str) -> dict[str, str]:
    """Follow-up #2 — last touch, breakup style."""
    biz = lead.business_name
    body = (
        f"Hey {biz},\n\n"
        f"Last note from me — I mocked up a clean site for {biz} a while back "
        f"and can send it over if it's ever useful.\n\n"
        f"If not, I'll leave you be.\n\n"
        f"— {your_name}"
    )
    return {
        "subject": f"last one — {biz.split(',')[0].strip()[:30]}",
        "body": body,
        "sequence_step": 3,
    }


def build_sequence(
    lead: MapsScanResult,
    your_name: str,
    demo_url: str | None = None,
    steps: int = 3,
) -> list[dict[str, str]]:
    """Full 3-email sequence for export or future sequence_engine."""
    emails = [build_email_1(lead, your_name, demo_url)]
    if steps >= 2:
        emails.append(build_email_2(lead, your_name))
    if steps >= 3:
        emails.append(build_email_3(lead, your_name))
    return emails


def format_sequence_export(emails: list[dict[str, str]]) -> str:
    """Human-readable file with all touchpoints (manual send / pending leads)."""
    blocks: list[str] = []
    for e in emails:
        step = e.get("sequence_step", 1)
        blocks.append(f"--- EMAIL {step} ---\nSUBJECT: {e['subject']}\n\n{e['body']}")
    return "\n\n".join(blocks)
