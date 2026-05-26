"""
Load and route Mikey universal reply scripts (data/close_templates/universal_reply_scripts.md).

Golden rules (from doc):
- No price before qualifying questions (script 2, not a number dump in script 1)
- End with a question when possible
- Payment / order link only on close script — separate from first interested reply
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from database.models.lead import Lead

SCRIPT_MD = (
    Path(__file__).resolve().parents[2] / "data" / "close_templates" / "universal_reply_scripts.md"
)
WEBSITE_SCRIPT_1 = (
    Path(__file__).resolve().parents[2] / "data" / "close_templates" / "script_1_website.txt"
)

ScriptId = Literal[
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "close",
    "ghost_1",
    "ghost_2",
    "ghost_3",
    "obj_works",
    "obj_no_time",
    "obj_call",
    "obj_testimonial",
]

# Section headers in universal_reply_scripts.md → script id
_SECTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"# SCRIPT 1\b", re.I), "1"),
    (re.compile(r"# SCRIPT 2\b", re.I), "2"),
    (re.compile(r"# SCRIPT 3\b", re.I), "3"),
    (re.compile(r"# SCRIPT 4\b", re.I), "4"),
    (re.compile(r"# SCRIPT 5\b", re.I), "5"),
    (re.compile(r"# SCRIPT 6\b", re.I), "6"),
    (re.compile(r"# SCRIPT 7\b", re.I), "7"),
    (re.compile(r"# SCRIPT 8\b", re.I), "8"),
    (re.compile(r"# CLOSING SCRIPT", re.I), "close"),
    (re.compile(r"## Ghost 1\b", re.I), "ghost_1"),
    (re.compile(r"## Ghost 2\b", re.I), "ghost_2"),
    (re.compile(r"## Ghost 3\b", re.I), "ghost_3"),
    (re.compile(r'## "How do I know', re.I), "obj_works"),
    (re.compile(r'## "I don\'t have time', re.I), "obj_no_time"),
    (re.compile(r'## "Can we get on a call', re.I), "obj_call"),
    (re.compile(r'## "Do you have any reviews', re.I), "obj_testimonial"),
]

_SCRIPTS_CACHE: dict[str, str] | None = None

_PRICING = re.compile(
    r"\b(how\s+much|what'?s\s+the\s+(cost|price)|pricing|quote|budget|"
    r"what\s+do\s+you\s+charge|rate|fees?)\b",
    re.I,
)
_WHAT_BUILD = re.compile(
    r"\b(what\s+exactly|what\s+do\s+you\s+build|what\s+is\s+this|"
    r"what\s+are\s+you\s+offering|how\s+does\s+it\s+work)\b",
    re.I,
)
_PORTFOLIO = re.compile(
    r"\b(examples?|portfolio|case\s+stud|show\s+me|proof|previous\s+work)\b",
    re.I,
)
_HAS_TOOL = re.compile(
    r"\b(already\s+use|we\s+have\s+a|our\s+crm|chatbot|hubspot|zapier|"
    r"already\s+got|existing\s+tool)\b",
    re.I,
)
_NOT_INTERESTED = re.compile(
    r"\b(not\s+interested|no\s+thanks|we'?re\s+good|pass|don'?t\s+need)\b",
    re.I,
)
_MAYBE_LATER = re.compile(
    r"\b(maybe\s+later|not\s+right\s+now|not\s+now|circle\s+back|"
    r"reach\s+out\s+later|busy\s+right\s+now)\b",
    re.I,
)
_MORE_INFO = re.compile(
    r"\b(send\s+me\s+more|more\s+info|proposal|details|overview|"
    r"brochure|pdf|deck)\b",
    re.I,
)
_READY_CLOSE = re.compile(
    r"\b(ready\s+to\s+pay|let'?s\s+do\s+it|move\s+forward|send\s+the\s+link|"
    r"invoice|let'?s\s+start|sign\s+me\s+up|i'?m\s+in)\b",
    re.I,
)
_CALL = re.compile(
    r"\b(quick\s+call|get\s+on\s+a\s+call|schedule\s+a\s+call|zoom|"
    r"phone\s+call|meet)\b",
    re.I,
)
_TESTIMONIAL = re.compile(
    r"\b(reviews?|testimonials?|references?|clients\s+you'?ve)\b",
    re.I,
)
_WORKS = re.compile(
    r"\b(will\s+this\s+work|actually\s+work|prove|guarantee)\b",
    re.I,
)
_NO_TIME = re.compile(
    r"\b(don'?t\s+have\s+time|too\s+busy|no\s+time\s+for)\b",
    re.I,
)
_INTERESTED = re.compile(
    r"\b(yes|interested|tell\s+me\s+more|sounds\s+good|sounds\s+interesting|"
    r"let'?s\s+talk|open\s+to\s+it|sure)\b",
    re.I,
)


def _strip_script_body(block: str) -> str:
    lines: list[str] = []
    for line in block.splitlines():
        if line.strip().startswith("#"):
            continue
        if line.strip() == "---":
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def load_scripts() -> dict[str, str]:
    global _SCRIPTS_CACHE
    if _SCRIPTS_CACHE is not None:
        return _SCRIPTS_CACHE

    if not SCRIPT_MD.is_file():
        _SCRIPTS_CACHE = {}
        return _SCRIPTS_CACHE

    text = SCRIPT_MD.read_text(encoding="utf-8")
    markers: list[tuple[int, str]] = []
    for pattern, sid in _SECTION_PATTERNS:
        m = pattern.search(text)
        if m:
            markers.append((m.start(), sid))
    markers.sort(key=lambda x: x[0])

    out: dict[str, str] = {}
    for i, (start, sid) in enumerate(markers):
        end = markers[i + 1][0] if i + 1 < len(markers) else len(text)
        body = _strip_script_body(text[start:end])
        if body:
            out[sid] = body
    _SCRIPTS_CACHE = out
    return out


def detect_reply_script(
    subject: str,
    body: str,
    *,
    classification: str = "unknown",
) -> str:
    """
    Pick script id from reply text (see quick reference table in universal_reply_scripts.md).
  """
    text = f"{subject}\n{body}".strip()

    if classification == "not_now":
        if _MAYBE_LATER.search(text):
            return "7"
        if _NOT_INTERESTED.search(text):
            return "6"
        return "7"

    if _READY_CLOSE.search(text):
        return "close"
    if _PRICING.search(text):
        return "2"
    if _WHAT_BUILD.search(text):
        return "3"
    if _PORTFOLIO.search(text):
        return "4"
    if _HAS_TOOL.search(text):
        return "5"
    if _NOT_INTERESTED.search(text):
        return "6"
    if _MAYBE_LATER.search(text):
        return "7"
    if _MORE_INFO.search(text):
        return "8"
    if _CALL.search(text):
        return "obj_call"
    if _TESTIMONIAL.search(text):
        return "obj_testimonial"
    if _WORKS.search(text):
        return "obj_works"
    if _NO_TIME.search(text):
        return "obj_no_time"
    if classification == "interested" or _INTERESTED.search(text):
        return "1"
    if classification == "unknown":
        return "1"
    return "1"


def lead_pitch_service(lead: Lead) -> str:
    """website | automation | youtube — matches cold email offer."""
    from core.lead_maps import lead_to_maps_scan
    from modules.outreach.website_pitch import ServiceOffer, resolve_pitch_plan

    plan = resolve_pitch_plan(lead_to_maps_scan(lead))
    if plan.service == ServiceOffer.WEBSITE:
        return "website"
    if plan.service == ServiceOffer.YOUTUBE:
        return "youtube"
    return "automation"


def pick_script_id(
    lead: Lead,
    subject: str,
    body: str,
    *,
    classification: str = "unknown",
) -> str:
    """Route to script 1_website when lead was pitched a website build."""
    sid = detect_reply_script(subject, body, classification=classification)
    if sid == "1" and lead_pitch_service(lead) == "website":
        return "1_website"
    return sid


def script_label(script_id: str) -> str:
    labels = {
        "1": "Yes / sounds interesting",
        "1_website": "Yes / sounds interesting (website pitch)",
        "2": "How much does it cost",
        "3": "What do you build",
        "4": "Examples / portfolio",
        "5": "Already have a tool",
        "6": "Not interested",
        "7": "Maybe later",
        "8": "Send more info / proposal",
        "close": "Ready to move forward",
        "ghost_1": "Ghost follow-up 1",
        "ghost_2": "Ghost follow-up 2",
        "ghost_3": "Ghost follow-up 3",
        "obj_works": "Will this work?",
        "obj_no_time": "No time right now",
        "obj_call": "Request a call",
        "obj_testimonial": "Reviews / testimonials",
    }
    return labels.get(script_id, script_id)


def _reply_subject_for_lead(lead: Lead) -> str:
    data = dict(lead.enrichment_data or {})
    last = data.get("last_reply") or {}
    if last.get("subject"):
        sub = str(last["subject"]).strip()
        return sub if sub.lower().startswith("re:") else f"Re: {sub}"
    pitch = (lead.pitch_subject or "").strip()
    if pitch:
        return pitch if pitch.lower().startswith("re:") else f"Re: {pitch}"
    company = (lead.business_name or "your business")[:40]
    return f"Re: {company}"


def _first_name(lead: Lead) -> str:
    data = dict(lead.enrichment_data or {})
    raw = data.get("raw") or {}
    if isinstance(raw, dict):
        for key in ("contact_first_name", "first_name"):
            v = str(raw.get(key) or "").strip()
            if v:
                return v.split()[0]
    for key in ("contact_first_name", "first_name"):
        v = str(data.get(key) or "").strip()
        if v:
            return v.split()[0]
    if lead.contact_name:
        return lead.contact_name.split()[0]
    return "there"


def render_script(
    script_id: str,
    lead: Lead,
    settings: object,
    *,
    payment_url: str = "",
    amount_inr: int | None = None,
) -> dict[str, str]:
    """Fill {{firstName}}, {{companyName}}, sender; optional payment for close follow-up."""
    if script_id == "1" and lead_pitch_service(lead) == "website":
        script_id = "1_website"

    scripts = load_scripts()
    if script_id == "1_website" and WEBSITE_SCRIPT_1.is_file():
        body_tpl = WEBSITE_SCRIPT_1.read_text(encoding="utf-8")
    else:
        body_tpl = scripts.get(script_id) or scripts.get("1", "")
    if not body_tpl:
        body_tpl = (
            "Hey {{firstName}},\n\n"
            "Really glad this landed at a good time.\n\n"
            "Quick question — where are most of your leads coming in right now?\n\n"
            "— {{sender_name}}"
        )

    sender = getattr(settings, "your_name", None) or "Gaurav"
    company = (lead.business_name or "your business").strip()
    first = _first_name(lead)
    niche = (lead.niche or "local").replace("_", " ")

    body = (
        body_tpl.replace("{{firstName}}", first)
        .replace("{{companyName}}", company)
        .replace("{{first_name}}", first)
        .replace("{{company_name}}", company)
        .replace("{{niche}}", niche)
        .replace("— Mikey", f"— {sender}")
        .replace("— Gaurav", f"— {sender}")
    )
    if "— " in body and not body.rstrip().endswith(sender):
        pass
    if not body.rstrip().endswith(sender) and "—" not in body[-40:]:
        body = f"{body.rstrip()}\n\n— {sender}"

    # Close script mentions Fiverr in source doc — payment is always a separate email
    if script_id == "close" and "Fiverr" in body:
        body = body.replace(
            "order link through Fiverr so the payment's protected and everything's official on both sides.",
            "secure payment link once you confirm scope (I'll send it in a follow-up email).",
        )

    subj = _reply_subject_for_lead(lead)

    return {
        "subject": subj,
        "body": body.strip(),
        "script_id": script_id,
        "script_label": script_label(script_id),
    }
