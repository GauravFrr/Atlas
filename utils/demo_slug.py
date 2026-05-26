"""
Trustworthy demo URLs: business-name slugs on your own domain (e.g. demos.gauravxd.dev).

Local file:  outputs/demos/austin-precision-plumbing.html
Public URL:  https://pub-xxx.r2.dev/austin-precision-plumbing/index.html
R2 object:   austin-precision-plumbing/index.html
"""

from __future__ import annotations

import hashlib
import re

_LEGAL_SUFFIXES = re.compile(r"\b(llc|inc|co|corp|ltd|pllc)\b", re.I)


def slugify_business(name: str) -> str:
    name = _LEGAL_SUFFIXES.sub("", name)
    name = name.lower().replace("&", " and ")
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-")


def trusted_demo_slug(business_name: str, city: str, place_id: str) -> str:
    """
    Human-readable slug so the link feels made for that business.

    Examples:
      Austin Precision Plumbing → austin-precision-plumbing
      Capitol City Plumbing Co  → capitol-city-plumbing
    """
    slug = slugify_business(business_name)
    if not slug:
        slug = "preview-site"

    slug = slug[:52].rstrip("-")

    city_word = ""
    if city:
        city_word = re.sub(r"[^a-z0-9]", "", city.split(",")[0].split()[0].lower())
    if city_word and len(city_word) >= 3 and city_word not in slug and len(slug) < 44:
        slug = f"{slug}-{city_word}"

    # Real Maps place_id: rare collision guard (short suffix, not a random blob URL)
    is_mock = place_id.startswith("ChIJmock") or bool(re.search(r"_\d{3,4}$", place_id))
    if not is_mock and place_id.startswith("ChIJ"):
        tail = hashlib.sha256(place_id.encode("utf-8")).hexdigest()[:4]
        slug = f"{slug}-{tail}"

    return slug


def local_demo_filename(slug: str) -> str:
    return f"{slug}.html"
