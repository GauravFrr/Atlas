import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from llm.router import LLMRouter
from modules.lead_finder.scanners.google_maps import GoogleMapsScanner, MapsScanResult


def parse_args():
    p = argparse.ArgumentParser(description="Test Maps scanner + demo generation")
    p.add_argument(
        "--safe-demo",
        action="store_true",
        help="Force premium shell only (skip creative AI HTML)",
    )
    p.add_argument(
        "--creative",
        action="store_true",
        help="Force full AI HTML only (no shell fallback)",
    )
    return p.parse_args()


async def main():
    args = parse_args()
    settings = get_settings()
    if args.safe_demo:
        settings.demo_generation_mode = "safe"
    elif args.creative:
        settings.demo_generation_mode = "creative"
    llm_router = LLMRouter(settings)
    scanner = GoogleMapsScanner(settings, llm_router)

    print("========================================")
    print(" TESTING GOOGLE MAPS SCANNER")
    print(f" Demo mode: {settings.demo_generation_mode}")
    print("========================================")
    
    # 1. Test Demo Generation directly (no API key needed)
    print("\n[1] Testing Demo Generation...")
    dummy_result = MapsScanResult(
        place_id="ChIJtest123",
        business_name="Austin Precision Plumbing",
        niche="plumber",
        city="Austin TX",
        country="USA",
        address="123 Main St, Austin, TX",
        phone="(512) 555-0198",
        email=None,
        has_website=False,
        website_url=None,
        rating=4.8,
        review_count=14
    )
    
    demo_path = await scanner.generate_demo_site(dummy_result)
    print(f"-> Generated Demo Path: {demo_path}")
    if demo_path and Path(demo_path).exists():
        print("-> Demo HTML file successfully created!")
        print(f"-> File size: {Path(demo_path).stat().st_size} bytes")
    else:
        print("-> FAILED to create Demo HTML file.")

    # 2. Test API Call if Key is present
    print("\n[2] Testing Maps API Call...")
    if not settings.google_places_api_key:
        print("-> Skipping: 'GOOGLE_PLACES_API_KEY' not found in .env")
    else:
        print("-> Key found! Scanning for plumbers in Austin TX...")
        leads = await scanner.scan(niche="plumber", city="Austin TX", limit=2)
        print(f"-> Found {len(leads)} leads.")
        for lead in leads:
            print(f"   - {lead.business_name} | Website: {lead.website_url}")

if __name__ == "__main__":
    asyncio.run(main())
