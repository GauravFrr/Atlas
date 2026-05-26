"""
Classify cold-email replies: interested, not_now, unsubscribe, auto_reply, unknown.
Keyword-first; optional LLM when configured and ambiguous.
"""

from __future__ import annotations

import re
from typing import Any, Literal

ReplyClass = Literal[
    "interested", "not_now", "unsubscribe", "auto_reply", "unknown"
]

_UNSUB = re.compile(
    r"\b(unsubscribe|opt\s*out|remove\s+me|stop\s+emailing|don'?t\s+contact)\b",
    re.I,
)
_NOT_INTERESTED = re.compile(
    r"\b(not\s+interested|we'?re\s+good|pass\s+on|no\s+thanks)\b",
    re.I,
)
_NOT_NOW = re.compile(
    r"\b(maybe\s+later|not\s+right\s+now|not\s+now|circle\s+back)\b",
    re.I,
)
_INTERESTED = re.compile(
    r"\b(yes|interested|tell\s+me\s+more|how\s+much|pricing|schedule|"
    r"call\s+me|sounds\s+good|let'?s\s+talk|book\s+a|demo)\b",
    re.I,
)
_AUTO = re.compile(
    r"\b(out\s+of\s+office|automatic\s+reply|auto[\s-]?reply|away\s+from)\b",
    re.I,
)


def classify_reply(subject: str, body: str) -> ReplyClass:
    """Fast keyword classification (no API call)."""
    text = f"{subject}\n{body}".strip()
    if not text:
        return "unknown"
    if _AUTO.search(text):
        return "auto_reply"
    if _UNSUB.search(text):
        return "unsubscribe"
    if _NOT_INTERESTED.search(text):
        return "not_now"
    if _NOT_NOW.search(text):
        return "not_now"
    if _INTERESTED.search(text):
        return "interested"
    return "unknown"


async def classify_reply_async(
    subject: str,
    body: str,
    llm: Any | None = None,
) -> ReplyClass:
    """Keyword pass; LLM only when still unknown and router available."""
    base = classify_reply(subject, body)
    if base != "unknown" or not llm:
        return base

    prompt = (
        "Classify this cold-email reply with ONE word only:\n"
        "interested | not_now | unsubscribe | auto_reply | unknown\n\n"
        f"Subject: {subject[:200]}\n\nBody:\n{body[:1500]}"
    )
    try:
        raw = await llm.complete(
            prompt,
            task_type="classify_reply",
            max_tokens=20,
        )
        word = (raw or "").strip().lower().split()[0] if raw else "unknown"
        for label in ("interested", "not_now", "unsubscribe", "auto_reply"):
            if label in word:
                return label  # type: ignore[return-value]
    except Exception:
        pass
    return "unknown"
