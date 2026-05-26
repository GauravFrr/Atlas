"""
Import leads from CSV (e.g. batch icebreaker exports) — no Google Places API.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path

from modules.lead_finder.scanners.google_maps import MapsScanResult

# Map common header variants (lowercase key -> canonical)
_HEADER_ALIASES: dict[str, str] = {
    "email": "email",
    "e-mail": "email",
    "work email": "email",
    "first name": "first_name",
    "firstname": "first_name",
    "last name": "last_name",
    "lastname": "last_name",
    "company": "company",
    "company name": "company",
    "business": "company",
    "business name": "company",
    "title": "title",
    "website": "website",
    "url": "website",
    "linkedin": "linkedin",
    "city": "city",
    "niche": "niche",
    "industry": "niche",
    "phone": "phone",
    "icebreaker": "icebreaker",
    "opening": "icebreaker",
    "country": "country",
}


def _norm_header(h: str) -> str:
    key = re.sub(r"\s+", " ", h.strip().lower())
    return _HEADER_ALIASES.get(key, key.replace(" ", "_"))


def _norm_row(raw: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in raw.items():
        if k is None:
            continue
        nk = _norm_header(str(k))
        val = (v or "").strip()
        if val:
            out[nk] = val
    return out


def _place_id_from_email(email: str) -> str:
    digest = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
    return f"csv_{digest}"


def load_csv_leads(
    path: str | Path,
    *,
    default_niche: str = "local_service",
    default_city: str = "US",
    default_country: str = "US",
    limit: int | None = None,
) -> list[MapsScanResult]:
    """
    Load leads from CSV. Required column: email (or Email).
    Company defaults to email local-part if missing.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV not found: {path}")

    leads: list[MapsScanResult] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header row: {path}")

        for row in reader:
            if limit is not None and len(leads) >= limit:
                break
            data = _norm_row({k: (v or "") for k, v in row.items() if k})
            email = data.get("email", "").strip().lower()
            if not email or "@" not in email:
                continue

            company = data.get("company") or email.split("@")[0]
            website = data.get("website", "").strip() or None
            if website and not website.startswith(("http://", "https://")):
                website = f"https://{website}"

            city = data.get("city") or default_city
            niche = data.get("niche") or default_niche
            country = data.get("country") or default_country

            first = data.get("first_name", "")
            last = data.get("last_name", "")
            if first and not company.startswith(first):
                business_name = f"{company}" if company else f"{first} {last}".strip()
            else:
                business_name = company

            extra: dict = {"from_csv": "1"}
            if data.get("icebreaker"):
                extra["icebreaker"] = data["icebreaker"]
            if first:
                extra["first_name"] = first
            if last:
                extra["last_name"] = last
            if data.get("title"):
                extra["title"] = data["title"]

            leads.append(
                MapsScanResult(
                    place_id=_place_id_from_email(email),
                    business_name=business_name,
                    niche=niche,
                    city=city,
                    country=country,
                    address=data.get("address", city),
                    phone=data.get("phone") or None,
                    email=email,
                    has_website=bool(website),
                    website_url=website,
                    rating=None,
                    review_count=0,
                    raw=extra,
                )
            )

    if not leads:
        raise ValueError(f"No valid rows with email in {path}")
    return leads
