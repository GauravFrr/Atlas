"""
Method 10 â€” Local Business Directory Scanner (PRIMARY METHOD)
TARGET:  US/UK/AU local businesses on Google Maps with no website
EARN:    $300â€“1,200 per website
VOLUME:  Every US city Ã— every niche = unlimited leads
LOGIC:   Scan Maps â†’ flag no-website businesses â†’ build demo â†’ pitch

This is one of the HIGHEST PRIORITY methods â€” Google Maps gives us
unlimited warm leads of businesses actively looking for web presence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import asyncio
import httpx
from pathlib import Path
from loguru import logger

from modules.lead_finder.demo_designer import build_demo_prompt, pick_design_variant
from modules.lead_finder.demo_premium_renderer import fetch_demo_copy, render_premium_demo


# Priority niches to scan â€” every local business type that needs a website or automation.
# Extend without code changes: HUNT_EXTRA_NICHES=med spa,boat repair in .env
PRIORITY_NICHES = [
    # Trades / home services
    "plumber", "electrician", "HVAC", "roofer", "landscaper",
    "pest control", "locksmith", "cleaning service", "painter",
    "carpenter", "handyman", "flooring contractor", "fencing contractor",
    "garage door repair", "gutter cleaning", "pressure washing",
    "tree service", "pool service", "appliance repair",
    "window installation", "solar installer", "moving company",
    "junk removal", "paving contractor", "masonry contractor",
    "general contractor", "home remodeling", "kitchen remodeling",
    "bathroom remodeling", "interior designer",
    # Health & medical
    "dentist", "chiropractor", "optometrist", "physical therapy",
    "dermatologist", "veterinarian", "orthodontist", "med spa",
    "acupuncture clinic", "massage therapist", "home health care",
    "urgent care clinic", "physiotherapy clinic", "dental clinic",
    # Food & hospitality
    "restaurant", "cafe", "bakery", "food truck", "pizza restaurant",
    "catering service", "juice bar", "ice cream shop", "coffee shop",
    "bar and grill", "banquet hall",
    # Professional services
    "lawyer", "accountant", "insurance agent", "financial advisor",
    "tax preparation service", "bookkeeping service", "mortgage broker",
    "travel agency", "staffing agency", "security service",
    "immigration consultant", "notary public",
    # Beauty & personal care
    "hair salon", "nail salon", "barber", "spa", "tattoo studio",
    "lash studio", "makeup artist", "beauty parlour",
    # Fitness & wellness
    "gym", "personal trainer", "yoga studio", "pilates studio",
    "martial arts school", "dance studio", "crossfit gym", "swim school",
    # Property
    "real estate agent", "property management", "home inspector",
    "self storage", "interior decorator", "packers and movers",
    # Auto
    "auto repair", "mechanic", "car wash", "auto detailing",
    "tire shop", "auto body shop", "towing service", "driving school",
    "car dealership", "bike repair shop",
    # Events / pets / education / misc
    "photographer", "wedding planner", "event venue", "florist",
    "dog groomer", "pet boarding", "daycare center", "tutoring center",
    "music school", "dry cleaner", "tailor", "computer repair",
    "laundromat", "courier service", "printing service", "sign shop",
    "coaching institute", "play school",
]

# Cities to scan â€” richest English-speaking markets first, then India + global hubs.
# Extend without code changes: HUNT_EXTRA_CITIES=Berlin DE,Amsterdam NL in .env
TARGET_CITIES = [
    # USA â€” major metros
    "New York NY", "Los Angeles CA", "Chicago IL", "Houston TX",
    "Phoenix AZ", "Philadelphia PA", "San Antonio TX", "San Diego CA",
    "Dallas TX", "San Jose CA", "Austin TX", "Jacksonville FL",
    "Fort Worth TX", "Columbus OH", "Charlotte NC", "Indianapolis IN",
    "San Francisco CA", "Seattle WA", "Denver CO", "Nashville TN",
    "Boston MA", "Portland OR", "Las Vegas NV", "Detroit MI",
    "Memphis TN", "Louisville KY", "Baltimore MD", "Milwaukee WI",
    "Albuquerque NM", "Tucson AZ", "Fresno CA", "Sacramento CA",
    "Kansas City MO", "Mesa AZ", "Atlanta GA", "Omaha NE",
    "Colorado Springs CO", "Raleigh NC", "Miami FL", "Long Beach CA",
    "Virginia Beach VA", "Oakland CA", "Minneapolis MN", "Tulsa OK",
    "Tampa FL", "Arlington TX", "New Orleans LA", "Wichita KS",
    "Cleveland OH", "Bakersfield CA", "Honolulu HI", "Anaheim CA",
    "Riverside CA", "Corpus Christi TX", "Lexington KY", "St. Louis MO",
    "Pittsburgh PA", "Cincinnati OH", "Salt Lake City UT", "Orlando FL",
    "Boise ID", "Richmond VA", "Scottsdale AZ", "Fort Lauderdale FL",
    "Charleston SC", "Savannah GA", "Oklahoma City OK", "El Paso TX",
    # UK & Ireland
    "London UK", "Manchester UK", "Birmingham UK", "Leeds UK",
    "Glasgow UK", "Liverpool UK", "Bristol UK", "Edinburgh UK",
    "Sheffield UK", "Nottingham UK", "Dublin Ireland",
    # Australia & New Zealand
    "Sydney AU", "Melbourne AU", "Brisbane AU", "Perth AU",
    "Adelaide AU", "Gold Coast AU", "Canberra AU",
    "Auckland NZ", "Wellington NZ", "Christchurch NZ",
    # Canada
    "Toronto CA", "Vancouver CA", "Montreal CA", "Calgary CA",
    "Ottawa CA", "Edmonton CA", "Mississauga CA",
    # India â€” major metros + tier-2
    "Mumbai India", "Delhi India", "Bangalore India", "Hyderabad India",
    "Chennai India", "Pune India", "Kolkata India", "Ahmedabad India",
    "Jaipur India", "Gurgaon India", "Noida India", "Chandigarh India",
    "Indore India", "Lucknow India", "Kochi India", "Surat India",
    "Nagpur India", "Coimbatore India", "Bhopal India", "Vadodara India",
    # Middle East / Asia / Africa hubs (English-friendly)
    "Dubai UAE", "Abu Dhabi UAE", "Sharjah UAE", "Doha Qatar",
    "Singapore", "Kuala Lumpur Malaysia",
    "Cape Town South Africa", "Johannesburg South Africa", "Durban South Africa",
]


@dataclass
class MapsScanResult:
    place_id: str
    business_name: str
    niche: str
    city: str
    country: str
    address: str
    phone: str | None
    email: str | None
    has_website: bool
    website_url: str | None
    rating: float | None
    review_count: int
    demo_site_path: str | None = None   # Path to pre-generated HTML demo
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_no_website_target(self) -> bool:
        return not self.has_website

    @property
    def is_outdated_website_target(self) -> bool:
        return self.has_website and self.website_url is not None


class GoogleMapsScanner:
    """
    Method 10 â€” Scans Google Maps for businesses with no website.
    One of the highest-priority methods â€” unlimited warm leads.

    Usage:
        scanner = GoogleMapsScanner(settings, llm_router)
        leads = await scanner.scan(niche="plumber", city="Austin TX", limit=50)
    """

    def __init__(self, settings: Any, llm_router: Any | None = None) -> None:
        self.settings = settings
        self.llm = llm_router

    async def scan(
        self,
        niche: str,
        city: str,
        limit: int = 50,
        no_website_only: bool = True,
    ) -> list[MapsScanResult]:
        """
        Scan Google Maps for local businesses matching niche + city.
        Uses Google Places Text Search and Details API.
        """
        api_key = getattr(self.settings, "google_places_api_key", None)
        if not api_key:
            logger.warning("[M10] Missing google_places_api_key in settings. Skipping scan.")
            return []

        logger.info(f"[M10] Google Maps Scanner: niche={niche}, city={city}, limit={limit}")
        query = f"{niche} in {city}"
        search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        leads: list[MapsScanResult] = []
        seen_ids: set[str] = set()
        async with httpx.AsyncClient(timeout=45.0) as client:
            places: list[dict[str, Any]] = []
            next_token: str | None = None
            pages = 0
            while len(places) < limit and pages < 3:
                # Page 2+ must use pagetoken ONLY (query + pagetoken = INVALID_REQUEST).
                if next_token:
                    await asyncio.sleep(2.0)
                    params = {"pagetoken": next_token, "key": api_key}
                else:
                    params = {"query": query, "key": api_key}
                search_resp = await client.get(search_url, params=params)
                if search_resp.status_code != 200:
                    logger.error(f"[M10] Places API HTTP {search_resp.status_code}: {search_resp.text[:300]}")
                    break
                data = search_resp.json()
                status = str(data.get("status") or "")
                if status not in ("OK", "ZERO_RESULTS"):
                    if places:
                        logger.warning(
                            f"[M10] Places pagination stopped ({status}) — "
                            f"using {len(places)} result(s) from first page"
                        )
                    else:
                        logger.error(
                            f"[M10] Places text search failed status={status} "
                            f"error={data.get('error_message', '')} query={query!r}"
                        )
                    break
                batch = data.get("results") or []
                for row in batch:
                    pid = row.get("place_id")
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        places.append(row)
                pages += 1
                next_token = data.get("next_page_token")
                if not next_token or not batch:
                    break

            if not places:
                logger.info(f"[M10] No places found for '{query}' (status OK but empty)")
                return leads

            logger.info(f"[M10] Text search returned {len(places)} place(s) for '{query}'")

            # 2. Get Details for each place
            details_url = "https://maps.googleapis.com/maps/api/place/details/json"
            for place in places:
                if len(leads) >= limit:
                    break
                place_id = place.get("place_id")
                if not place_id:
                    continue
                
                det_resp = await client.get(
                    details_url, 
                    params={
                        "place_id": place_id, 
                        "fields": "name,website,formatted_phone_number,formatted_address,rating,user_ratings_total", 
                        "key": api_key
                    }
                )
                if det_resp.status_code != 200:
                    continue
                
                det_data = det_resp.json().get("result", {})
                
                has_website = "website" in det_data
                if no_website_only and has_website:
                    continue
                    
                lead = MapsScanResult(
                    place_id=place_id,
                    business_name=det_data.get("name", place.get("name", "Local Business")),
                    niche=niche,
                    city=city,
                    country="", # Could extract from address
                    address=det_data.get("formatted_address", place.get("formatted_address", "")),
                    phone=det_data.get("formatted_phone_number"),
                    email=None, # Hunter.io lookup would happen later in the pipeline
                    has_website=has_website,
                    website_url=det_data.get("website"),
                    rating=det_data.get("rating"),
                    review_count=det_data.get("user_ratings_total", 0),
                    raw=det_data
                )
                leads.append(lead)

        if no_website_only and places and not leads:
            logger.warning(
                f"[M10] {len(places)} places found but 0 without website for '{query}'. "
                "Use hunt mode m02_outdated (most US/UK businesses have a site)."
            )
        logger.info(
            f"[M10] Found {len(leads)} leads for '{query}' "
            f"(no_website_only={no_website_only}, scanned={len(places)} places)"
        )
        return leads

    async def scan_bulk(
        self,
        niches: list[str] | None = None,
        cities: list[str] | None = None,
        limit_per_combo: int = 20,
    ) -> list[MapsScanResult]:
        """
        Run scan across multiple niche x city combinations in parallel.
        This is the main production scan loop.
        """
        import asyncio
        niches = niches or PRIORITY_NICHES[:5]
        cities = cities or TARGET_CITIES[:5]

        tasks = [
            self.scan(niche=n, city=c, limit=limit_per_combo)
            for n in niches
            for c in cities
        ]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)
        results: list[MapsScanResult] = []
        for r in results_nested:
            if isinstance(r, list):
                results.extend(r)
        logger.info(f"[M10] Bulk scan complete: {len(results)} total leads")
        return results

    async def _generate_complete_html(self, prompt: str, max_attempts: int = 2) -> str:
        """Call LLM for full HTML with retry if output is truncated."""
        system = (
            "You are an award-winning web designer for premium local businesses. "
            "Output one complete HTML document with matte muted colors and refined CSS. "
            "Never stop mid-file — always close </style>, </body>, and </html>. "
            "No bright yellow CTAs, no emoji icons, no stock image URLs."
        )
        last_text = ""

        for attempt in range(1, max_attempts + 1):
            try:
                response = await self.llm.complete(
                    prompt=prompt,
                    task_type="generate_demo_site",
                    system=system,
                    temperature=0.82 if attempt == 1 else 0.7,
                    max_tokens=16384,
                )
                last_text = _sanitize_demo_html(response.content)
            except Exception as e:
                logger.error(f"[M10] LLM generation failed (attempt {attempt}): {e}")
                continue

            if _is_html_complete(last_text):
                return last_text

            logger.warning(
                f"[M10] HTML incomplete ({len(last_text)} chars), "
                f"retrying ({attempt}/{max_attempts})..."
            )
            prompt = (
                prompt
                + "\n\nCRITICAL: Your previous output was CUT OFF. "
                "Regenerate the ENTIRE page from scratch. Must end with </html>."
            )

        if last_text and not _is_html_complete(last_text):
            logger.error(
                f"[M10] HTML still incomplete after {max_attempts} attempts "
                f"({len(last_text)} chars)"
            )
        return last_text

    def _demo_mode(self) -> str:
        mode = getattr(self.settings, "demo_generation_mode", "hybrid")
        return str(mode).lower().strip()

    async def _build_safe_demo(self, result: MapsScanResult, variant) -> str:
        """Premium shell — same polished layout, AI copy, variant palette."""
        copy = await fetch_demo_copy(
            self.llm,
            business_name=result.business_name,
            niche=result.niche,
            city=result.city,
        )
        html = render_premium_demo(
            business_name=result.business_name,
            niche=result.niche,
            city=result.city,
            phone=result.phone or "(555) 555-0199",
            address=result.address or result.city,
            variant=variant,
            copy=copy,
        )
        return _inject_layout_guards(html)

    async def _build_creative_demo(self, result: MapsScanResult, variant) -> str:
        """Full unique HTML from scratch — premium prompt + layout guards."""
        if not self.llm:
            logger.warning("[M10] No LLM — cannot run creative demo mode")
            return ""

        prompt = build_demo_prompt(
            business_name=result.business_name,
            niche=result.niche,
            city=result.city,
            phone=result.phone or "(555) 555-0199",
            address=result.address or result.city,
            variant=variant,
        )
        html = await self._generate_complete_html(prompt)
        if not html or not _is_html_complete(html):
            return ""
        return _inject_layout_guards(html)

    def _write_demo_file(self, result: MapsScanResult, html_text: str) -> str:
        from utils.demo_slug import local_demo_filename, trusted_demo_slug

        out_dir = Path("outputs/demos")
        out_dir.mkdir(parents=True, exist_ok=True)
        slug = trusted_demo_slug(result.business_name, result.city, result.place_id)
        file_path = out_dir / local_demo_filename(slug)
        file_path.write_text(html_text, encoding="utf-8")
        result.demo_site_path = str(file_path)
        return str(file_path)

    async def generate_demo_site(self, result: MapsScanResult) -> str:
        """
        Hybrid demo generation (default):
          1. Creative — full premium HTML from scratch (unique layout)
          2. Fallback — premium shell if API fails or output incomplete
        """
        mode = self._demo_mode()
        variant = pick_design_variant(unique_per_run=True)
        logger.info(
            f"[M10] Demo for {result.business_name} | mode={mode} | "
            f"layout={variant.layout_name} | palette={variant.palette_name}"
        )

        html_text = ""
        source = ""

        if mode in ("creative", "hybrid"):
            html_text = await self._build_creative_demo(result, variant)
            if html_text:
                source = "creative"

        if not html_text and mode in ("hybrid", "safe"):
            if mode == "hybrid":
                logger.warning(
                    f"[M10] Creative demo unavailable for {result.business_name} "
                    "→ using premium shell fallback"
                )
            html_text = await self._build_safe_demo(result, variant)
            source = "safe"

        if not html_text:
            logger.error(f"[M10] Demo generation failed for {result.business_name}")
            return ""

        file_path = self._write_demo_file(result, html_text)
        logger.success(f"[M10] Generated demo ({source}): {file_path}")
        return file_path

    def build_pitch_context(self, result: MapsScanResult) -> dict[str, Any]:
        return {
            "method": "google_maps_no_website",
            "business_name": result.business_name,
            "niche": result.niche,
            "city": result.city,
            "has_demo": result.demo_site_path is not None,
        }


# Separate stylesheet injected last in <head> — overrides LLM layout bugs on desktop.
_LAYOUT_GUARDS_CSS = """
/* Atlas layout guards v2 */
html { scroll-padding-top: 5rem; }
body { margin: 0; overflow-x: hidden; min-height: 100vh; width: 100%; }
section, main { overflow: visible !important; }
[id] { scroll-margin-top: 5rem; }
.container {
  width: 100% !important;
  max-width: 1140px !important;
  margin-left: auto !important;
  margin-right: auto !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
}
#services, .services, section#services {
  margin-top: 0 !important;
  overflow: visible !important;
}
.service-card {
  overflow: visible !important;
  max-width: none !important;
  margin-top: 0 !important;
}
.service-card:not(:first-child) { margin-top: 0 !important; }
.service-card:hover { transform: translateY(-4px) !important; }
.hero::before, .hero::after, #hero::before, #hero::after {
  width: 6px !important;
  max-width: 6px !important;
}
@media (min-width: 768px) {
  header, .header, #header {
    display: block !important;
    width: 100% !important;
    text-align: left !important;
  }
  header .container, header > .container, .header .container, .header-inner {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    justify-content: space-between !important;
    align-items: center !important;
    gap: 1.5rem !important;
    text-align: left !important;
  }
  header nav, .header nav {
    display: flex !important;
    align-items: center !important;
    margin-left: auto !important;
    flex-shrink: 0 !important;
  }
  header nav ul, nav ul, .nav-links, .nav-list, .navigation ul {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 1.75rem !important;
    list-style: none !important;
    margin: 0 !important;
    padding: 0 !important;
    align-items: center !important;
  }
  header nav ul li, nav ul li, .nav-links li, .nav-list li {
    display: block !important;
    margin: 0 !important;
  }
  .logo, .site-logo, header .logo, header a.logo {
    flex-shrink: 0 !important;
    white-space: nowrap !important;
  }
  .hero, #hero, section.hero {
    padding: 3.5rem 0 !important;
    min-height: unset !important;
    overflow: visible !important;
  }
  .hero-content, .hero .hero-content, .hero-inner {
    max-width: 800px !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
  }
  .services-grid, .service-grid, .service-cards, .services-cards,
  #services .service-grid, #services .services-grid, #services .service-cards {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 1.75rem !important;
    align-items: stretch !important;
    overflow: visible !important;
  }
}
@media (max-width: 767px) {
  .header, header {
    position: relative !important;
  }
  header .container, .header .container {
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    justify-content: space-between !important;
    text-align: left !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    gap: 0.5rem !important;
  }
  .logo, header .logo, header a.logo {
    font-size: 1rem !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    flex: 1 !important;
    min-width: 0 !important;
  }
  header nav, .header nav {
    display: none !important;
  }
  .header-call, a.header-call {
    display: inline-block !important;
  }
  html { scroll-padding-top: 0.5rem !important; }
  .services-grid, .service-grid, .service-cards, .services-cards {
    grid-template-columns: 1fr !important;
  }
}
"""

_GUARD_STYLE_ID = "atlas-layout-guards"


def _inject_layout_guards(html: str) -> str:
    """Inject a final stylesheet in <head> so desktop layout always wins."""
    import re

    html = re.sub(
        rf"<style[^>]*\s+id=[\"']{_GUARD_STYLE_ID}[\"'][^>]*>.*?</style>",
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    guard_tag = (
        f'<style id="{_GUARD_STYLE_ID}">\n{_LAYOUT_GUARDS_CSS}\n</style>\n'
    )
    lower = html.lower()
    if "</head>" in lower:
        idx = lower.find("</head>")
        return html[:idx] + guard_tag + html[idx:]
    if "</html>" in lower:
        idx = lower.rfind("</html>")
        return html[:idx] + guard_tag + html[idx:]
    return html + guard_tag


def _repair_truncated_html(text: str) -> str:
    """Close common missing tags when the model hits token limits."""
    lower = text.lower().strip()
    if lower.endswith("</html>"):
        return text
    if "</body>" in lower and len(text) > 8000:
        if "</html>" not in lower[-200:]:
            return text.rstrip() + "\n</html>"
    if len(text) > 12000 and "<body" in lower and "</body>" not in lower:
        return text.rstrip() + "\n</body>\n</html>"
    return text


def _sanitize_demo_html(html_text: str) -> str:
    """Strip markdown fences and ensure HTML document boundaries."""
    text = html_text.strip()
    if text.startswith("```html"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    if "<!DOCTYPE" in text.upper():
        start = text.upper().find("<!DOCTYPE")
        text = text[start:]
    elif "<html" in text.lower():
        start = text.lower().find("<html")
        text = text[start:]
    text = _repair_truncated_html(text)
    return _inject_layout_guards(text)


def _is_html_complete(html: str) -> bool:
    """True if the LLM returned a full page, not a truncated fragment."""
    lower = html.lower()
    if len(html) < 2500:
        return False
    if not lower.strip().endswith("</html>") or "</body>" not in lower:
        return False
    if "<style" in lower and "</style>" not in lower:
        return False
    return True
