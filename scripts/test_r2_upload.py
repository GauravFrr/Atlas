"""
Test R2 demo upload (one file).

  pip install boto3
  # Add R2_* and DEMO_SITE_BASE_URL to .env first
  python scripts/test_r2_upload.py
  python scripts/test_r2_upload.py outputs/demos/demo_austin_precision_plumbing_ChIJtest123.html
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.hosting.r2_deployer import R2DemoDeployer


async def main() -> None:
    settings = get_settings()
    deployer = R2DemoDeployer(settings)

    if not settings.has_r2:
        print("R2 not configured. Set in .env:")
        print("  DEMO_SITE_BASE_URL=https://pub-xxxxx.r2.dev")
        print("  R2_ACCOUNT_ID=...")
        print("  R2_ACCESS_KEY_ID=...")
        print("  R2_SECRET_ACCESS_KEY=...")
        print("  R2_BUCKET_NAME=agent-demos")
        print("  R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com")
        sys.exit(1)

    if len(sys.argv) > 1:
        demo = Path(sys.argv[1])
    else:
        demos = sorted((ROOT / "outputs" / "demos").glob("*.html"))
        if not demos:
            print("No HTML files in outputs/demos/")
            sys.exit(1)
        demo = demos[-1]

    slug = demo.stem
    print(f"Uploading: {demo.name} → slug /{slug}/")
    url = await deployer.upload_demo(demo, slug=slug)
    if url:
        print(f"OK: {url}")
        print("Open that URL in your browser to confirm.")
    else:
        print("Upload failed — check logs.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
