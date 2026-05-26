"""
Scan outreach copy against data/spam_words.txt before sending.
"""

from __future__ import annotations

import re
from pathlib import Path

_SPAM_PATH = Path(__file__).resolve().parents[1] / "data" / "spam_words.txt"


def load_spam_words(path: Path | None = None) -> list[str]:
    p = path or _SPAM_PATH
    if not p.is_file():
        return []
    words: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        w = line.strip().lower()
        if w and not w.startswith("#"):
            words.append(w)
    return words


def find_spam_hits(text: str, words: list[str] | None = None) -> list[str]:
    """Return spam phrases found in text (case-insensitive)."""
    if not text:
        return []
    vocab = words if words is not None else load_spam_words()
    low = text.lower()
    hits: list[str] = []
    for phrase in vocab:
        if len(phrase) < 3:
            continue
        if phrase in low:
            hits.append(phrase)
    return hits


def check_outreach_copy(
    subject: str,
    body: str,
    *,
    words: list[str] | None = None,
) -> tuple[bool, list[str]]:
    """
    Returns (ok, hits). ok=False if any spam phrase found in subject or body.
    """
    combined = f"{subject}\n{body}"
    hits = find_spam_hits(combined, words)
    return (len(hits) == 0, hits)
