"""
Premium demo renderer — same layout/quality as the approved reference demo.
AI writes JSON copy only; HTML/CSS structure stays consistent and polished.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass

from loguru import logger

from modules.lead_finder.demo_designer import DemoDesignVariant, build_copy_prompt

# Minimal inline SVGs (niche-neutral)
SERVICE_ICONS = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 2c-4 0-7 2.5-7 6v8c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V8c0-3.5-3-6-7-6zm0 2c2.8 0 5 1.7 5 4v1H7V8c0-2.3 2.2-4 5-4z"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 14H8v-2h4v2zm0-4H8v-2h4v2zm0-4H8V7h4v2zm6 8h-4v-2h4v2zm0-4h-4v-2h4v2zm0-4h-4V7h4v2z"/></svg>',
]

NICHE_DEFAULTS: dict[str, dict] = {
    "plumber": {
        "hero_headline": "Reliable Plumbing Solutions for Your Home",
        "hero_subtitle": "Expert repairs, drain cleaning, and water heater service — done right by licensed local plumbers.",
        "services_heading": "Our Expert Plumbing Services",
        "services": [
            ("Leak Detection & Repair", "Fast diagnosis and lasting fixes for leaks and burst pipes before costly damage spreads."),
            ("Water Heater Services", "Installation, repair, and maintenance for tank and tankless systems."),
            ("Drain Cleaning & Clog Removal", "Clear stubborn clogs and restore full flow throughout your plumbing system."),
        ],
    },
    "default": {
        "hero_headline": "Professional Service You Can Trust",
        "hero_subtitle": "Quality work, clear communication, and results that earn repeat customers in your neighborhood.",
        "services_heading": "Our Professional Services",
        "services": [
            ("Core Services", "Comprehensive solutions tailored to your needs with attention to detail on every job."),
            ("Emergency Support", "Responsive help when timing matters most — we show up prepared and professional."),
            ("Maintenance Plans", "Proactive care that prevents problems and keeps everything running smoothly."),
        ],
    },
}


@dataclass
class DemoCopy:
    hero_headline: str
    hero_subtitle: str
    services_heading: str
    services: list[tuple[str, str]]
    testimonial_quote: str
    testimonial_author: str


def _phone_href(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return f"tel:+{digits}" if digits else "tel:+15555550199"


def _guess_email(business_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", business_name.lower())[:32] or "contact"
    return f"info@{slug}.com"


def default_copy(niche: str, city: str) -> DemoCopy:
    key = niche.lower().strip()
    data = NICHE_DEFAULTS.get(key, NICHE_DEFAULTS["default"])
    return DemoCopy(
        hero_headline=data["hero_headline"],
        hero_subtitle=data["hero_subtitle"].replace("your neighborhood", city),
        services_heading=data["services_heading"],
        services=list(data["services"]),
        testimonial_quote=(
            f"Outstanding service — professional, on time, and fairly priced. "
            f"Would recommend to anyone in {city}."
        ),
        testimonial_author="Sarah L.",
    )


def parse_copy_json(raw: str, niche: str, city: str) -> DemoCopy | None:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            return None

    services_raw = data.get("services") or []
    services: list[tuple[str, str]] = []
    for item in services_raw[:3]:
        if isinstance(item, dict):
            services.append((str(item.get("title", "Service")), str(item.get("description", ""))))

    if len(services) < 3:
        return None

    headline = data.get("hero_headline") or data.get("hero_title")
    subtitle = data.get("hero_subtitle") or data.get("hero_description")
    if not headline or not subtitle:
        return None

    return DemoCopy(
        hero_headline=str(headline),
        hero_subtitle=str(subtitle),
        services_heading=str(data.get("services_heading") or "Our Expert Services"),
        services=services,
        testimonial_quote=str(data.get("testimonial_quote", "")),
        testimonial_author=str(data.get("testimonial_author", "A satisfied customer")),
    )


async def fetch_demo_copy(llm, business_name: str, niche: str, city: str) -> DemoCopy:
    """LLM writes short JSON copy; falls back to niche defaults if API fails."""
    fallback = default_copy(niche, city)
    if not llm:
        return fallback

    prompt = build_copy_prompt(business_name, niche, city)
    prompt += (
        '\nAlso include: "hero_headline": "short powerful headline", '
        '"services_heading": "section title for services"\n'
    )

    try:
        response = await llm.complete(
            prompt=prompt,
            task_type="generate_demo_copy",
            system="Return only valid JSON. No markdown.",
            temperature=0.75,
            max_tokens=1024,
        )
        parsed = parse_copy_json(response.content, niche, city)
        if parsed and parsed.testimonial_quote:
            return parsed
        if parsed:
            parsed.testimonial_quote = fallback.testimonial_quote
            parsed.testimonial_author = fallback.testimonial_author
            return parsed
    except Exception as e:
        logger.warning(f"[M10] Demo copy LLM failed, using defaults: {e}")

    return fallback


def render_premium_demo(
    *,
    business_name: str,
    niche: str,
    city: str,
    phone: str,
    address: str,
    variant: DemoDesignVariant,
    copy: DemoCopy,
) -> str:
    """Render the approved premium layout with variant palette/fonts."""
    c = variant.colors
    f = variant.fonts
    esc = html.escape
    tel = _phone_href(phone)
    email = _guess_email(business_name)
    display_phone = esc(phone)
    services_html = ""
    for i, (title, desc) in enumerate(copy.services[:3]):
        icon = SERVICE_ICONS[i % len(SERVICE_ICONS)]
        services_html += f"""
                    <article class="service-card">
                        {icon}
                        <h3>{esc(title)}</h3>
                        <p>{esc(desc)}</p>
                    </article>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(business_name)} — {esc(city)}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{f['url']}" rel="stylesheet">
    <style>
        :root {{
            --bg: {c['bg']};
            --surface: {c['surface']};
            --text: {c['text']};
            --muted: {c['muted']};
            --primary: {c['primary']};
            --accent: {c['accent']};
            --cta: {c['cta_bg']};
            --ctaText: {c['cta_text']};
            --border: {c['border']};
            --font-heading: '{f['heading']}', serif;
            --font-body: '{f['body']}', sans-serif;
        }}
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        html {{ scroll-behavior: smooth; scroll-padding-top: 4.5rem; }}
        body {{
            font-family: var(--font-body);
            color: var(--text);
            background: var(--bg);
            line-height: 1.6;
        }}
        h1, h2, h3 {{ font-family: var(--font-heading); color: var(--primary); line-height: 1.2; }}
        a {{ color: inherit; text-decoration: none; }}
        .container {{
            width: 100%;
            max-width: 1140px;
            margin: 0 auto;
            padding: 0 1.5rem;
        }}
        .header {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .header .container {{
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            padding-top: 0.85rem;
            padding-bottom: 0.85rem;
        }}
        .logo {{
            font-family: var(--font-heading);
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1.15;
        }}
        .header nav {{ flex-shrink: 0; }}
        .nav-links {{
            display: flex;
            flex-direction: row;
            gap: 1.25rem;
            list-style: none;
            align-items: center;
        }}
        .nav-links a {{ font-weight: 500; font-size: 0.95rem; }}
        .nav-links a:hover {{ color: var(--accent); }}
        .header-call {{ display: none; }}
        .hero {{
            padding: 3.5rem 0;
            text-align: center;
            background: linear-gradient(180deg, var(--surface) 0%, var(--bg) 100%);
        }}
        .hero-content {{ max-width: 800px; margin: 0 auto; }}
        .hero h1 {{ font-size: clamp(2.25rem, 5vw, 3.5rem); margin-bottom: 1rem; }}
        .hero p {{ font-size: 1.15rem; color: var(--muted); margin-bottom: 2rem; }}
        .cta-button {{
            display: inline-block;
            background: var(--cta);
            color: var(--ctaText);
            padding: 1rem 2.25rem;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.2s, background 0.2s;
        }}
        .cta-button:hover {{ background: var(--primary); transform: translateY(-2px); }}
        .services {{ padding: 4rem 0; }}
        .services h2 {{ text-align: center; font-size: 2.5rem; margin-bottom: 2.5rem; }}
        .service-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.75rem;
        }}
        .service-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06);
            text-align: center;
            transition: transform 0.25s, box-shadow 0.25s;
        }}
        .service-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.1);
        }}
        .service-card svg {{
            width: 48px;
            height: 48px;
            fill: var(--cta);
            margin-bottom: 1rem;
        }}
        .service-card h3 {{ font-size: 1.5rem; margin-bottom: 0.75rem; }}
        .service-card p {{ color: var(--muted); font-size: 0.95rem; }}
        .testimonial {{
            background: var(--primary);
            color: var(--ctaText);
            padding: 4rem 0;
            text-align: center;
        }}
        .testimonial blockquote {{
            font-family: var(--font-heading);
            font-size: clamp(1.25rem, 2.5vw, 1.75rem);
            font-style: italic;
            max-width: 800px;
            margin: 0 auto 1rem;
            line-height: 1.5;
        }}
        .testimonial cite {{ font-style: normal; color: var(--accent); }}
        .footer {{
            background: var(--primary);
            color: var(--ctaText);
            padding: 3rem 0;
        }}
        .footer .container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
        }}
        .footer h3 {{
            font-family: var(--font-heading);
            color: var(--ctaText);
            margin-bottom: 1rem;
            font-size: 1.35rem;
        }}
        .footer p, .footer a {{ color: var(--accent); margin-bottom: 0.35rem; }}
        .footer a:hover {{ color: var(--ctaText); }}
        @media (max-width: 767px) {{
            html {{ scroll-padding-top: 0.5rem; }}
            .header {{ position: relative; box-shadow: none; }}
            .header .container {{
                padding-top: 0.5rem;
                padding-bottom: 0.5rem;
            }}
            .logo {{
                font-size: 1rem;
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            .header nav {{ display: none; }}
            .header-call {{
                display: inline-block;
                background: var(--cta);
                color: var(--ctaText);
                font-size: 0.8rem;
                font-weight: 600;
                padding: 0.45rem 0.75rem;
                border-radius: 6px;
            }}
            .hero {{ padding: 2rem 0 2.5rem; }}
            .hero h1 {{ font-size: 1.85rem; }}
            .service-grid {{ grid-template-columns: 1fr; }}
            .footer .container {{ grid-template-columns: 1fr; text-align: center; }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <a href="#" class="logo">{esc(business_name)}</a>
            <a href="{tel}" class="header-call">Call</a>
            <nav aria-label="Main">
                <ul class="nav-links">
                    <li><a href="#services">Services</a></li>
                    <li><a href="#testimonials">Reviews</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <main>
        <section class="hero">
            <div class="hero-content">
                <h1>{esc(copy.hero_headline)}</h1>
                <p>{esc(copy.hero_subtitle)}</p>
                <a href="{tel}" class="cta-button">Call Us Today: {display_phone}</a>
            </div>
        </section>
        <section id="services" class="services">
            <div class="container">
                <h2>{esc(copy.services_heading)}</h2>
                <div class="service-grid">{services_html}
                </div>
            </div>
        </section>
        <section id="testimonials" class="testimonial">
            <div class="container">
                <blockquote>&ldquo;{esc(copy.testimonial_quote)}&rdquo;</blockquote>
                <cite>&mdash; {esc(copy.testimonial_author)}</cite>
            </div>
        </section>
    </main>
    <footer id="contact" class="footer">
        <div class="container">
            <div>
                <h3>Contact Us</h3>
                <p>Phone: <a href="{tel}">{display_phone}</a></p>
                <p>Email: <a href="mailto:{esc(email)}">{esc(email)}</a></p>
            </div>
            <div>
                <h3>Our Location</h3>
                <p>{esc(address or city)}</p>
                <p>Serving {esc(city)} and surrounding areas.</p>
            </div>
        </div>
    </footer>
</body>
</html>
"""
