"""
Demo site design system — unique premium layouts per lead.
Muted, matte palettes only. No bright yellows, neon, or generic templates.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class DemoDesignVariant:
    """One visual direction for a generated demo site."""
    id: str
    layout_id: str
    palette_name: str
    layout_name: str
    colors: dict[str, str]
    fonts: dict[str, str]
    layout_notes: str
    hero_style: str
    forbidden: str


# Matte / premium palettes — hex values for inline CSS (Tailwind CDN optional)
PALETTES: list[dict[str, str]] = [
    {
        "name": "Slate & Stone",
        "bg": "#f7f6f4",
        "surface": "#ffffff",
        "text": "#1c1917",
        "muted": "#57534e",
        "primary": "#334155",
        "accent": "#64748b",
        "cta_bg": "#3f4f5f",
        "cta_text": "#f8fafc",
        "border": "#e7e5e4",
    },
    {
        "name": "Charcoal & Sand",
        "bg": "#f5f3ef",
        "surface": "#fffcf8",
        "text": "#1a1814",
        "muted": "#6b6560",
        "primary": "#2c2825",
        "accent": "#a8957d",
        "cta_bg": "#3d3832",
        "cta_text": "#faf8f5",
        "border": "#e8e2d9",
    },
    {
        "name": "Muted Navy",
        "bg": "#f4f6f8",
        "surface": "#ffffff",
        "text": "#0f172a",
        "muted": "#64748b",
        "primary": "#1e293b",
        "accent": "#94a3b8",
        "cta_bg": "#273549",
        "cta_text": "#f1f5f9",
        "border": "#e2e8f0",
    },
    {
        "name": "Sage Professional",
        "bg": "#f6f7f5",
        "surface": "#ffffff",
        "text": "#1a2118",
        "muted": "#5c6658",
        "primary": "#3d4a3a",
        "accent": "#7d8f78",
        "cta_bg": "#4a5c47",
        "cta_text": "#f4f6f3",
        "border": "#e2e6df",
    },
    {
        "name": "Warm Taupe",
        "bg": "#faf9f7",
        "surface": "#ffffff",
        "text": "#292524",
        "muted": "#78716c",
        "primary": "#44403c",
        "accent": "#a8a29e",
        "cta_bg": "#57534e",
        "cta_text": "#fafaf9",
        "border": "#e7e5e4",
    },
    {
        "name": "Deep Forest",
        "bg": "#f3f5f2",
        "surface": "#fafbf9",
        "text": "#141a16",
        "muted": "#5f6b63",
        "primary": "#1c2520",
        "accent": "#8fa396",
        "cta_bg": "#2a3530",
        "cta_text": "#f0f4f1",
        "border": "#dfe5e0",
    },
    {
        "name": "Graphite & Clay",
        "bg": "#f8f7f6",
        "surface": "#ffffff",
        "text": "#18181b",
        "muted": "#71717a",
        "primary": "#27272a",
        "accent": "#a8a29e",
        "cta_bg": "#3f3f46",
        "cta_text": "#fafafa",
        "border": "#e4e4e7",
    },
    {
        "name": "Dusty Blue-Gray",
        "bg": "#f5f7f9",
        "surface": "#ffffff",
        "text": "#1e2428",
        "muted": "#6b7280",
        "primary": "#374151",
        "accent": "#9ca3af",
        "cta_bg": "#4b5563",
        "cta_text": "#f9fafb",
        "border": "#e5e7eb",
    },
]

LAYOUTS: list[dict[str, str]] = [
    {
        "id": "split_hero",
        "name": "Split Hero",
        "notes": (
            "Two-column hero: left = large headline + CTA, right = subtle gradient panel "
            "or abstract geometric shape (CSS only, no stock photos). Services as horizontal cards."
        ),
        "hero": "asymmetric split, 55/45, no full-width photo banner",
    },
    {
        "id": "editorial",
        "name": "Editorial Minimal",
        "notes": (
            "Oversized serif headline, lots of whitespace, thin dividers. "
            "Services in a 2-column editorial grid with numbers 01, 02, 03."
        ),
        "hero": "centered typographic hero, minimal decoration",
    },
    {
        "id": "dark_band",
        "name": "Dark Band Hero",
        "notes": (
            "Top nav on light bg, then a full-width dark matte band for hero (not pure black). "
            "Services on light surface below. Testimonial in a bordered card."
        ),
        "hero": "contained dark hero band with soft edges",
    },
    {
        "id": "bento",
        "name": "Bento Grid",
        "notes": (
            "Hero as one large bento cell + two smaller cells (stats or trust badges). "
            "Services in uneven bento grid — different card sizes."
        ),
        "hero": "CSS grid bento layout, no carousel",
    },
    {
        "id": "sidebar_accent",
        "name": "Sidebar Accent",
        "notes": (
            "Hero content centered in container (max ~720px). Optional 4px left border on hero card only — "
            "NO full-height viewport stripe. Services: 3-column grid on desktop. Footer two columns."
        ),
        "hero": "centered hero card with subtle left border accent, full container width",
    },
    {
        "id": "stacked_cards",
        "name": "Stacked Cards",
        "notes": (
            "Compact hero, then 3 service cards in a horizontal grid on desktop (no negative margins, "
            "no overlapping cards). Single testimonial with subtle CSS quote mark."
        ),
        "hero": "short centered hero, services grid below with even spacing",
    },
]

FONT_PAIRINGS: list[dict[str, str]] = [
    {
        "heading": "Fraunces",
        "body": "Source Sans 3",
        "url": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap",
    },
    {
        "heading": "Libre Baskerville",
        "body": "DM Sans",
        "url": "https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@400;700&family=DM+Sans:wght@400;500;600&display=swap",
    },
    {
        "heading": "Cormorant Garamond",
        "body": "Nunito Sans",
        "url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Nunito+Sans:wght@400;500;600&display=swap",
    },
    {
        "heading": "Playfair Display",
        "body": "Work Sans",
        "url": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Work+Sans:wght@400;500;600&display=swap",
    },
    {
        "heading": "Instrument Serif",
        "body": "Inter",
        "url": "https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Inter:wght@400;500;600&display=swap",
    },
    {
        "heading": "Lora",
        "body": "Karla",
        "url": "https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=Karla:wght@400;500;600&display=swap",
    },
]

FORBIDDEN_RULES = (
    "Do NOT use: bright yellow (#facc15, yellow-400), neon green, electric blue, "
    "purple gradients, default Bootstrap look, emoji as service icons, "
    "loremflickr or random stock photo URLs, Inter-only generic startup template, "
    "identical layout to a typical Tailwind landing page clone."
)


def pick_design_variant(unique_per_run: bool = True) -> DemoDesignVariant:
    """Pick a random premium design direction. New call = new look."""
    if unique_per_run:
        rng = random.Random()
    else:
        rng = random.Random(42)

    palette = rng.choice(PALETTES)
    layout = rng.choice(LAYOUTS)
    fonts = rng.choice(FONT_PAIRINGS)

    return DemoDesignVariant(
        id=f"{layout['id']}_{palette['name'].lower().replace(' ', '_')}",
        layout_id=layout["id"],
        palette_name=palette["name"],
        layout_name=layout["name"],
        colors=palette,
        fonts=fonts,
        layout_notes=layout["notes"],
        hero_style=layout["hero"],
        forbidden=FORBIDDEN_RULES,
    )


def build_copy_prompt(business_name: str, niche: str, city: str) -> str:
    """Small JSON-only prompt — LLM writes copy, template renders HTML."""
    return f"""
Write marketing copy for a local {niche} business website.

Business: {business_name}
City: {city}

Return ONLY valid JSON (no markdown):
{{
  "hero_headline": "short powerful headline",
  "hero_subtitle": "one professional sentence",
  "services_heading": "Our Expert [niche] Services",
  "services": [
    {{"title": "service name", "description": "two short sentences"}},
    {{"title": "...", "description": "..."}},
    {{"title": "...", "description": "..."}}
  ],
  "testimonial_quote": "realistic 1-2 sentence review",
  "testimonial_author": "first name + last initial"
}}
"""


def build_demo_prompt(
    business_name: str,
    niche: str,
    city: str,
    phone: str,
    address: str,
    variant: DemoDesignVariant,
) -> str:
    """LLM generates the full HTML page — unique design each run, no fill-in template."""
    c = variant.colors
    f = variant.fonts

    return f"""
You are an award-winning web designer for high-end local businesses.
Build ONE complete, unique, PREMIUM single-page website in raw HTML — different layout every time.

PREMIUM RULES (non-negotiable)
- Matte, muted palettes only — use the exact hex values below. NO bright yellow, neon, or cheap startup look.
- Elegant serif + clean sans font pairing from the Google Fonts URL below.
- Polished embedded CSS (~150-280 lines): subtle shadows, refined spacing, professional typography.
- Inline SVG icons for services (not emoji). NO stock photos, NO loremflickr.
- Must feel like a $2k+ agency site — not a generic Tailwind clone or Bootstrap template.

BUSINESS
- Name: {business_name}
- Niche: {niche}
- City: {city}
- Phone: {phone}
- Address: {address or city}

DESIGN (must look different every time — follow this direction)
- Layout: {variant.layout_name} — {variant.layout_notes}
- Hero: {variant.hero_style}
- Palette "{variant.palette_name}" — matte, muted, premium. Use ONLY these hex values:
  bg={c['bg']} surface={c['surface']} text={c['text']} muted={c['muted']}
  primary={c['primary']} accent={c['accent']} cta={c['cta_bg']} ctaText={c['cta_text']} border={c['border']}
- Fonts: headings="{f['heading']}", body="{f['body']}" via {f['url']}

REQUIRED HTML STRUCTURE (include these elements; layout/CSS must still be unique)
<header class="header">
  <div class="container">
    <a class="logo">Business Name</a>
    <a href="tel:..." class="header-call">Call</a>
    <nav><ul class="nav-links"><li><a href="#services">Services</a></li>...</ul></nav>
  </div>
</header>
<section class="hero"><div class="hero-content">...</div></section>
<section id="services" class="services"><div class="container"><h2>...</h2><div class="service-grid">3x .service-card</div></div></section>

PAGE STRUCTURE (include ALL sections with real copy)
1. Sticky header — logo LEFT, nav links RIGHT on same row (never stack nav vertically on desktop)
2. Hero: large headline, subtitle, matte CTA button (tel link), padding ~3.5rem vertical max
3. Services: div.service-grid with 3x .service-card, inline SVG icons, hover lift shadow
4. Testimonial: quoted review from a customer in {city}
5. Footer: two columns — contact/phone + address

DESKTOP LAYOUT (critical at 100% zoom on 1280px+ screens)
- .container max-width 1140px centered — page must NOT look like a narrow phone column on desktop
- Do NOT set flex-direction:column on header or header .container without a @media (max-width:767px) wrapper
- Services grid: display:grid; grid-template-columns: repeat(3,1fr) on screens 768px+
- NO negative margins on #services or .service-card; NO overlapping stacked cards
- Hero padding max 4rem top/bottom; NO min-height: 100vh on hero
- NO full-height side stripes; NO overflow:hidden on hero

QUALITY BAR
- Rich embedded CSS in <head> (~150-250 lines CSS is fine)
- Professional US local business tone
- CSS gradients or shapes for hero — NO stock photo URLs, NO loremflickr
- Mobile (max-width 767px): ONE slim row — logo left + tel Call button right. Hide nav menu on mobile (no vertical link stack). position:relative on header (not sticky). Max ~52px header height.
- Must end with </body></html> — do not stop mid-CSS

FORBIDDEN: bright yellow/orange CTAs, neon blue, emoji icons, generic identical layouts, Tailwind-only clones.
{variant.forbidden}

OUTPUT: Raw HTML only. Start with <!DOCTYPE html>. End with </html>. No markdown fences.
"""
