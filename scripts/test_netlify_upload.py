"""
Test Netlify demo deploy — run after setting NETLIFY_* in .env

  python scripts/test_netlify_upload.py
  python scripts/test_netlify_upload.py outputs/demos/austin-precision-plumbing.html
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.hosting.netlify_deployer import NetlifyDemoDeployer


async def main() -> None:
    settings = get_settings()
    if not settings.has_netlify:
        print("Missing Netlify config in .env:")
        print("  DEMO_UPLOAD_MODE=netlify")
        print("  DEMO_SITE_BASE_URL=https://YOUR-SITE.netlify.app")
        print("  NETLIFY_AUTH_TOKEN=...")
        print("  NETLIFY_SITE_ID=...")
        print("\nSee docs/NETLIFY_DEMO_SETUP.md")
        sys.exit(1)

    demos = sorted((ROOT / "outputs" / "demos").glob("*.html"))
    if len(sys.argv) > 1:
        demo_path = Path(sys.argv[1])
    elif demos:
        demo_path = demos[-1]
    else:
        print("No HTML in outputs/demos/ — run a campaign first or pass a file path")
        sys.exit(1)

    deployer = NetlifyDemoDeployer(settings)
    slug = demo_path.stem
    print(f"Uploading {demo_path.name} → Netlify site {settings.netlify_site_id[:8]}...")
    url = await deployer.upload_demo(demo_path, slug=slug)
    if url:
        print(f"\nOK: {url}")
        print("Open that URL in your browser.")
    else:
        print("\nUpload failed — check logs above")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
