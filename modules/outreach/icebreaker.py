"""
Email 1 opening — Mikey / blueprint style.

Icebreaker only (no pitch). Service (website vs automation) decided in website_pitch.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from modules.lead_finder.scanners.google_maps import MapsScanResult
    from modules.outreach.website_pitch import PitchPlan
else:
    MapsScanResult = Any
    PitchPlan = Any

_FEWSHOT_PATH = Path(__file__).resolve().parents[2] / "data" / "icebreaker_fewshot.txt"
_LEGAL_SUFFIXES = re.compile(
    r"\b(llc|inc|co|corp|ltd|pllc|llp)\.?$", re.I
)


def first_name_from_lead(lead: MapsScanResult) -> str:
    """Use utils.contact_greeting — never guess from business name."""
    from utils.contact_greeting import first_name_from_lead as _greeting_name

    return _greeting_name(lead)


def company_name(lead: MapsScanResult) -> str:
    return lead.business_name.split(",")[0].strip()


_GEO_TAIL_WORDS = frozenset({
    "london", "austin", "chicago", "houston", "dallas", "boston", "miami",
    "atlanta", "denver", "seattle", "phoenix", "portland", "nashville",
    "charlotte", "orlando", "tampa", "vegas", "diego", "francisco", "york",
    "angeles", "uk", "usa",
})


def company_cta_name(lead: MapsScanResult) -> str:
    name = company_name(lead)
    name = _LEGAL_SUFFIXES.sub("", name).strip()
    parts = name.split()
    if len(parts) == 2 and parts[1].lower() in _GEO_TAIL_WORDS:
        return parts[0]
    return name


def icebreaker_subject(lead: MapsScanResult) -> str:
    from utils.platform_domains import is_platform_url
    from utils.youtube_channel import is_youtube_lead

    if is_youtube_lead(lead):
        return company_name(lead)
    if lead.website_url and not is_platform_url(lead.website_url):
        return (
            lead.website_url.replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
            .replace("www.", "")
        )
    return company_name(lead)


def _load_fewshot_examples(max_lines: int = 5) -> str:
    if not _FEWSHOT_PATH.exists():
        return ""
    lines = [
        ln.strip()
        for ln in _FEWSHOT_PATH.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    if not lines:
        return ""
    return "\n".join(f"- {ex}" for ex in lines[:max_lines])


def fallback_icebreaker(
    lead: MapsScanResult,
    demo_url: str | None = None,
    plan: PitchPlan | None = None,
) -> str:
    _ = demo_url
    from modules.outreach.website_pitch import (
        cache_pitch_on_lead,
        fallback_icebreaker_for_plan,
    )

    p = plan or cache_pitch_on_lead(lead)
    return fallback_icebreaker_for_plan(lead, p)


def build_icebreaker_prompt(
    lead: MapsScanResult,
    demo_url: str | None = None,
    plan: PitchPlan | None = None,
) -> str:
    _ = demo_url
    from modules.outreach.website_pitch import (
        ServiceOffer,
        cache_pitch_on_lead,
    )

    p = plan or cache_pitch_on_lead(lead)
    biz = company_name(lead)
    site = icebreaker_subject(lead)
    examples = _load_fewshot_examples()
    examples_block = f"\nExamples:\n{examples}\n" if examples else ""

    if p.service == ServiceOffer.YOUTUBE:
        angle = (
            "YouTube CREATOR / channel. Gap = channel SEO, thumbnails, description, "
            "no landing page for off-platform leads. Do NOT mention plumbing, "
            "outdated business website, or youtube.com as their site."
        )
    elif p.service == ServiceOffer.WEBSITE and p.tier.value == "no_site":
        angle = "NO website. Gap = phone-only, nothing online after hours. Do NOT praise a site."
    elif p.service == ServiceOffer.WEBSITE:
        angle = (
            "OUTDATED website (old, not mobile, or not HTTPS). "
            "Do NOT call it professional. Gap = visitors leave without enquiring."
        )
    else:
        angle = (
            "They have a MODERN site already. Do NOT offer a new website. "
            "Gap = no AI chat, no online booking, no automated follow-up."
        )

    return f"""
Write the OPENING for a cold email (1–2 sentences, max 50 words).{examples_block}
Format:
- Start with "Saw …"
- {angle}
- Then "But noticed …" or "But …" — the gap only
- No URLs, no "I build", no pitch, no "impressive/professional website"
- Reference "{biz}" or "{site}"

service_to_pitch={p.service.value}
problem_detected={p.problem_detected}
Return ONLY the opening sentences.
"""


def _valid_opening(line: str) -> bool:
    low = line.lower()
    if any(b in low for b in ("r2.dev", "pub-", "http://", "https://")):
        return False
    banned = (
        "professional website",
        "impressive",
        "i build",
        "i offer",
        "plumbing",
        "youtube.com",
        "mobile-friendly site",
    )
    if any(b in low for b in banned):
        return False
    return low.startswith("saw ") or low.startswith("i checked out")


def preset_icebreaker(lead: MapsScanResult) -> str | None:
    line = (getattr(lead, "raw", None) or {}).get("icebreaker", "").strip()
    return line or None


async def generate_icebreaker(
    lead: MapsScanResult,
    demo_url: str | None = None,
    llm: Any | None = None,
    plan: PitchPlan | None = None,
) -> str:
    from modules.outreach.website_pitch import cache_pitch_on_lead

    p = plan or cache_pitch_on_lead(lead)
    preset = preset_icebreaker(lead)
    if preset:
        return preset
    if llm:
        try:
            response = await llm.complete(
                prompt=build_icebreaker_prompt(lead, demo_url, plan=p),
                task_type="write_cold_email",
                temperature=0.7,
                max_tokens=150,
            )
            line = response.content.strip().strip('"').strip()
            if _valid_opening(line):
                return line
        except Exception:
            pass
    return fallback_icebreaker(lead, demo_url, plan=p)
