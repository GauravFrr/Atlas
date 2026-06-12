"""JSON-serializable helpers for enrichment_data / Postgres JSON columns."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Convert dataclasses and nested structures to JSON-safe values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return {k: to_jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return str(value)
