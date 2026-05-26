"""
Renders complete demo HTML from design variant + copy.
Jinja2 templates always output a full document (no LLM truncation).
"""

from __future__ import annotations

import json
import re
from typing import Any

from jinja2 import Template

from modules.lead_finder.demo_designer import DemoDesignVariant


def parse_demo_copy(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    data = json.loads(text)
    services = list(data.get("services", []))
    while len(services) < 3:
        services.append(
            {"title": "Professional Service", "description": "Quality local service you can trust."}
        )
    return {
        "hero_subtitle": data.get("hero_subtitle", "Trusted local professionals."),
        "services": services[:3],
        "testimonial_quote": data.get("testimonial_quote", "Professional and reliable."),
        "testimonial_author": data.get("testimonial_author", "Local Customer"),
    }


def default_copy(niche: str, city: str) -> dict[str, Any]:
    return {
        "hero_subtitle": f"Reliable {niche} services in {city}.",
        "services": [
            {"title": "Emergency Service", "description": "Fast response when it matters most."},
            {"title": "Installations", "description": "Clean installs done right the first time."},
            {"title": "Maintenance", "description": "Ongoing care to prevent costly repairs."},
        ],
        "testimonial_quote": f"Best {niche} experience we've had in {city}.",
        "testimonial_author": "Homeowner",
    }


def render_demo_html(
    variant: DemoDesignVariant,
    business_name: str,
    niche: str,
    city: str,
    phone: str,
    address: str,
    copy: dict[str, Any],
) -> str:
    fn = _RENDERERS.get(variant.layout_id, _render_split_hero)
    return fn(variant, business_name, niche, city, phone, address, copy)


def _ctx(v, bn, ni, ci, ph, ad, co) -> dict[str, Any]:
    return {
        "business_name": bn,
        "niche": ni,
        "city": ci,
        "phone": ph,
        "address": ad,
        "copy": co,
        "c": v.colors,
        "font_url": v.fonts["url"],
        "font_heading": v.fonts["heading"],
        "font_body": v.fonts["body"],
    }


def _render_split_hero(v, bn, ni, ci, ph, ad, co) -> str:
    return Template(_SPLIT_HERO).render(**_ctx(v, bn, ni, ci, ph, ad, co))


def _render_editorial(v, bn, ni, ci, ph, ad, co) -> str:
    return Template(_EDITORIAL).render(**_ctx(v, bn, ni, ci, ph, ad, co))


def _render_dark_band(v, bn, ni, ci, ph, ad, co) -> str:
    return Template(_DARK_BAND).render(**_ctx(v, bn, ni, ci, ph, ad, co))


def _render_bento(v, bn, ni, ci, ph, ad, co) -> str:
    return Template(_BENTO).render(**_ctx(v, bn, ni, ci, ph, ad, co))


_RENDERERS = {
    "split_hero": _render_split_hero,
    "editorial": _render_editorial,
    "dark_band": _render_dark_band,
    "bento": _render_bento,
    "sidebar_accent": _render_dark_band,
    "stacked_cards": _render_editorial,
}

_BASE_CSS = """
:root {
  --bg: {{ c.bg }}; --surface: {{ c.surface }}; --text: {{ c.text }};
  --muted: {{ c.muted }}; --primary: {{ c.primary }}; --accent: {{ c.accent }};
  --cta-bg: {{ c.cta_bg }}; --cta-text: {{ c.cta_text }}; --border: {{ c.border }};
  --fh: '{{ font_heading }}', Georgia, serif;
  --fb: '{{ font_body }}', system-ui, sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--fb);background:var(--bg);color:var(--text);line-height:1.65}
.btn{display:inline-block;background:var(--cta-bg);color:var(--cta-text);padding:.8rem 1.4rem;border-radius:3px;font-weight:600;font-size:.92rem;text-decoration:none}
.btn:hover{opacity:.9}
"""

_SPLIT_HERO = (
    "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>{{ business_name }}</title><link href=\"{{ font_url }}\" rel=\"stylesheet\"><style>"
    + _BASE_CSS
    + """
nav{display:flex;justify-content:space-between;align-items:center;padding:1.1rem 6%;border-bottom:1px solid var(--border)}
.logo{font-family:var(--fh);font-weight:600}
.hero{display:grid;grid-template-columns:1fr 1fr;min-height:68vh}
.hero-copy{padding:3.5rem 6%;display:flex;flex-direction:column;justify-content:center}
.hero-copy h1{font-family:var(--fh);font-size:clamp(1.9rem,4vw,2.75rem);line-height:1.15;margin-bottom:1rem}
.hero-copy p{color:var(--muted);max-width:24rem;margin-bottom:1.5rem}
.hero-panel{background:linear-gradient(155deg,var(--primary),var(--accent));min-height:240px}
.services{padding:3.5rem 6%}
.services h2{font-family:var(--fh);margin-bottom:1.5rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:1.1rem}
.card{background:var(--surface);border:1px solid var(--border);padding:1.4rem;border-radius:3px}
.card h3{font-family:var(--fh);font-size:1rem;margin-bottom:.45rem}
.card p{color:var(--muted);font-size:.9rem}
.quote{margin:0 6% 3rem;padding:1.75rem;background:var(--surface);border-left:3px solid var(--accent)}
.quote p{font-family:var(--fh);font-style:italic;margin-bottom:.5rem}
.quote span{color:var(--muted);font-size:.85rem}
footer{background:var(--primary);color:var(--cta-text);padding:1.75rem 6%;display:flex;justify-content:space-between;flex-wrap:wrap;gap:.75rem;font-size:.85rem}
@media(max-width:768px){.hero{grid-template-columns:1fr}}
</style></head><body>
<nav><span class=\"logo\">{{ business_name }}</span><a class=\"btn\" href=\"tel:{{ phone }}\">Call</a></nav>
<section class=\"hero\"><div class=\"hero-copy\"><h1>{{ business_name }}</h1><p>{{ copy.hero_subtitle }}</p>
<a class=\"btn\" href=\"tel:{{ phone }}\">{{ phone }}</a></div><div class=\"hero-panel\"></div></section>
<section class=\"services\"><h2>Our Services</h2><div class=\"grid\">
{% for s in copy.services %}<article class=\"card\"><h3>{{ s.title }}</h3><p>{{ s.description }}</p></article>{% endfor %}
</div></section>
<blockquote class=\"quote\"><p>\"{{ copy.testimonial_quote }}\"</p><span>— {{ copy.testimonial_author }}, {{ city }}</span></blockquote>
<footer><div><strong>{{ business_name }}</strong><br>{{ address }}</div><div>{{ phone }}</div></footer>
</body></html>"""
)

_EDITORIAL = (
    "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>{{ business_name }}</title><link href=\"{{ font_url }}\" rel=\"stylesheet\"><style>"
    + _BASE_CSS
    + """
.wrap{max-width:920px;margin:0 auto;padding:0 1.5rem}
header{padding:2.5rem 0 3rem;text-align:center;border-bottom:1px solid var(--border)}
header h1{font-family:var(--fh);font-size:clamp(2.2rem,5vw,3.2rem);letter-spacing:-.02em;margin-bottom:.75rem}
header p{color:var(--muted);max-width:32rem;margin:0 auto 1.5rem}
.svc{padding:3rem 0}
.svc-item{display:grid;grid-template-columns:3rem 1fr;gap:1rem;padding:1.5rem 0;border-bottom:1px solid var(--border)}
.svc-item:last-child{border:none}
.num{font-family:var(--fh);color:var(--accent);font-size:1.1rem}
.svc-item h3{font-family:var(--fh);margin-bottom:.35rem}
.svc-item p{color:var(--muted);font-size:.92rem}
.tst{margin:2rem 0 3rem;padding:2rem;text-align:center;background:var(--surface);border:1px solid var(--border)}
.tst p{font-family:var(--fh);font-size:1.2rem;font-style:italic;margin-bottom:.5rem}
.tst span{color:var(--muted);font-size:.85rem}
footer{padding:2rem 0;border-top:1px solid var(--border);display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;font-size:.88rem}
</style></head><body><div class=\"wrap\">
<header><h1>{{ business_name }}</h1><p>{{ copy.hero_subtitle }}</p><a class=\"btn\" href=\"tel:{{ phone }}\">{{ phone }}</a></header>
<section class=\"svc\">{% for s in copy.services %}<article class=\"svc-item\"><span class=\"num\">0{{ loop.index }}</span><div><h3>{{ s.title }}</h3><p>{{ s.description }}</p></div></article>{% endfor %}</section>
<div class=\"tst\"><p>\"{{ copy.testimonial_quote }}\"</p><span>— {{ copy.testimonial_author }}</span></div>
<footer><div>{{ address }}</div><div>{{ phone }}</div></footer>
</div></body></html>"""
)

_DARK_BAND = (
    "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>{{ business_name }}</title><link href=\"{{ font_url }}\" rel=\"stylesheet\"><style>"
    + _BASE_CSS
    + """
.top{display:flex;justify-content:space-between;align-items:center;padding:1rem 6%}
.band{background:var(--primary);color:var(--cta-text);padding:4rem 6%;margin-bottom:2.5rem}
.band h1{font-family:var(--fh);font-size:clamp(2rem,4vw,2.6rem);max-width:18ch;margin-bottom:1rem}
.band p{opacity:.85;max-width:36ch;margin-bottom:1.5rem}
.main{padding:0 6% 3rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2.5rem}
.cards article{background:var(--surface);border:1px solid var(--border);padding:1.25rem}
.cards h3{font-family:var(--fh);font-size:.98rem;margin-bottom:.4rem}
.cards p{color:var(--muted);font-size:.88rem}
.tst{border:1px solid var(--border);padding:1.5rem;background:var(--surface);margin-bottom:2rem}
.tst p{font-style:italic;margin-bottom:.4rem}
footer{padding:1.5rem 6%;background:var(--surface);border-top:1px solid var(--border);font-size:.85rem;display:flex;justify-content:space-between}
</style></head><body>
<div class=\"top\"><strong style=\"font-family:var(--fh)\">{{ business_name }}</strong><a class=\"btn\" href=\"tel:{{ phone }}\">Call</a></div>
<section class=\"band\"><h1>{{ business_name }}</h1><p>{{ copy.hero_subtitle }}</p><a class=\"btn\" href=\"tel:{{ phone }}\">{{ phone }}</a></section>
<div class=\"main\"><div class=\"cards\">{% for s in copy.services %}<article><h3>{{ s.title }}</h3><p>{{ s.description }}</p></article>{% endfor %}</div>
<div class=\"tst\"><p>\"{{ copy.testimonial_quote }}\"</p><span style=\"color:var(--muted)\">— {{ copy.testimonial_author }}, {{ city }}</span></div></div>
<footer><span>{{ address }}</span><span>{{ phone }}</span></footer>
</body></html>"""
)

_BENTO = (
    "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>{{ business_name }}</title><link href=\"{{ font_url }}\" rel=\"stylesheet\"><style>"
    + _BASE_CSS
    + """
.pad{padding:1.25rem 5% 3rem}
.bento{display:grid;grid-template-columns:2fr 1fr;grid-template-rows:auto auto;gap:1rem;margin:1.5rem 0 2.5rem}
.cell{background:var(--surface);border:1px solid var(--border);padding:1.5rem;border-radius:4px}
.cell-hero{grid-row:span 2;background:linear-gradient(145deg,var(--primary),var(--accent));color:var(--cta-text);display:flex;flex-direction:column;justify-content:flex-end;min-height:280px}
.cell-hero h1{font-family:var(--fh);font-size:1.85rem;margin-bottom:.5rem}
.cell-hero p{opacity:.9;font-size:.95rem;margin-bottom:1rem}
.stat{font-family:var(--fh);font-size:1.4rem;color:var(--primary)}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
.grid3 h3{font-family:var(--fh);font-size:.95rem;margin-bottom:.35rem}
.grid3 p{color:var(--muted);font-size:.85rem}
.tst{margin-top:1rem;padding:1.25rem;border-left:3px solid var(--accent);background:var(--surface)}
footer{margin-top:2rem;padding-top:1rem;border-top:1px solid var(--border);display:flex;justify-content:space-between;font-size:.85rem}
@media(max-width:768px){.bento{grid-template-columns:1fr}.cell-hero{grid-row:auto;min-height:200px}.grid3{grid-template-columns:1fr}}
</style></head><body><div class=\"pad\">
<nav style=\"display:flex;justify-content:space-between;align-items:center\"><span style=\"font-family:var(--fh);font-weight:600\">{{ business_name }}</span><a class=\"btn\" href=\"tel:{{ phone }}\">Call</a></nav>
<div class=\"bento\"><div class=\"cell cell-hero\"><h1>{{ business_name }}</h1><p>{{ copy.hero_subtitle }}</p><a class=\"btn\" href=\"tel:{{ phone }}\">{{ phone }}</a></div>
<div class=\"cell\"><span class=\"stat\">24/7</span><p style=\"color:var(--muted);font-size:.85rem\">Emergency availability</p></div>
<div class=\"cell\"><span class=\"stat\">{{ city }}</span><p style=\"color:var(--muted);font-size:.85rem\">Locally trusted</p></div></div>
<div class=\"grid3\">{% for s in copy.services %}<article class=\"cell\"><h3>{{ s.title }}</h3><p>{{ s.description }}</p></article>{% endfor %}</div>
<div class=\"tst\"><p>\"{{ copy.testimonial_quote }}\"</p></div>
<footer><span>{{ address }}</span><span>{{ phone }}</span></footer>
</div></body></html>"""
)
