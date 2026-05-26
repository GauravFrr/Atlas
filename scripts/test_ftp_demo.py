"""
Upload a tiny test HTML file via Hostinger FTP (all sites in hostinger_sites.json).

  python scripts/test_ftp_demo.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.hosting.ftp_deployer import FtpDemoDeployer
from utils.hostinger_pool import HostingerDemoPool


async def main() -> None:
    settings = get_settings()
    pool = HostingerDemoPool(settings)
    if not pool.enabled:
        print("FTP not configured. Set FTP_PASSWORD in .env + hostinger_sites.json")
        sys.exit(1)

    if not settings.ftp_password:
        print("FIX: Set FTP_PASSWORD in .env (FTP password from hPanel, not email password)")
        sys.exit(1)

    test_file = Path("outputs/demos/ftp_connection_test.html")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(
        "<html><body><h1>Agent-Earns FTP OK</h1></body></html>",
        encoding="utf-8",
    )

    deployer = FtpDemoDeployer(settings)
    ok_any = False
    for site in pool.sites:
        host = site.resolved_host(settings)
        user = site.resolved_user(settings)
        print(f"Testing {site.name}")
        print(f"  host:   {host}")
        print(f"  user:   {user}")
        print(f"  target: public_html/ftp-connection-test/index.html")
        print(f"  url:    {site.demo_base_url}/ftp-connection-test/index.html")

        url = await deployer.upload_demo(
            test_file,
            slug="ftp-connection-test",
            demo_base_url=site.demo_base_url,
            ftp_remote_base=site.ftp_remote_base,
            site_name=site.name,
            ftp_host=host,
            ftp_user=user,
        )
        if url:
            print(f"  SUCCESS: {url}\n")
            ok_any = True
        else:
            print("  FAIL — see error above\n")

    if not ok_any:
        print("Tips:")
        print("  1. hPanel -> FTP Accounts -> confirm host (try ftp.hostinger.com)")
        print("  2. Reset password for u709319479.demos.* -> FTP_PASSWORD in .env")
        print("  3. WinError 10061 on upload = passive FTP blocked; code retries active mode")
        print("  4. Allow FileZilla through Windows Firewall, or test from phone hotspot")
        print("  5. ftp_remote_base stays empty (files go to public_html/{slug}/)")
    sys.exit(0 if ok_any else 1)


if __name__ == "__main__":
    asyncio.run(main())
