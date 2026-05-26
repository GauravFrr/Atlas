"""
Test script for the Cold Email Engine (Method 17).
Demonstrates the full flow: Mock Lead -> LLM Draft -> Local Save (Dry Run).
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from config import Settings
from llm.router import LLMRouter
from modules.outreach.cold_email import ColdEmailEngine
from modules.lead_finder.scanners.google_maps import MapsScanResult

async def main():
    settings = Settings()
    
    # Initialize the LLM Router
    try:
        router = LLMRouter(settings)
    except Exception as e:
        logger.error(f"Failed to init LLMRouter: {e}")
        return

    engine = ColdEmailEngine(settings=settings, llm_router=router)

    # 1. Create a mock lead (as if it just came from the Google Maps Scanner)
    dummy_lead = MapsScanResult(
        place_id="ChIJtest123",
        business_name="Austin Precision Plumbing",
        niche="plumber",
        city="Austin TX",
        country="US",
        address="123 Main St, Austin, TX",
        phone="(512) 555-0198",
        email="owner@austinprecisionplumbing.com", # Mocking a found email
        has_website=False,
        website_url=None,
        rating=4.8,
        review_count=120,
        demo_site_path="outputs/demos/demo_austin_precision_plumbing_ChIJtest123.html"
    )

    print("\n" + "="*40)
    print(" TESTING COLD EMAIL ENGINE (M17)")
    print("="*40 + "\n")

    # 2. Draft the personalized pitch
    print("[1] Drafting Pitch via LLM...")
    draft = await engine.draft_pitch(
        lead=dummy_lead, 
        your_name=settings.your_name, 
        your_business=settings.your_business_name or "Digital Agency"
    )
    
    # Encode and decode to handle emojis in Windows terminal safely
    safe_body = draft['body'].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
    
    print(f"\n-> Subject: {draft['subject']}")
    print(f"-> Body:\n{safe_body}\n")

    # 3. Simulate sending the email
    print("[2] Simulating Email Send (Dry Run)...")
    success = engine.send_email(
        to_email=dummy_lead.email or "test@example.com",
        subject=draft['subject'],
        body=draft['body'],
        dry_run=True  # Ensure it doesn't actually try to connect to SMTP
    )
    
    if success:
        print("-> Success! Email draft saved to outputs/emails/")
    else:
        print("-> Failed to process email.")

if __name__ == "__main__":
    asyncio.run(main())
