"""
Test Netlify accounts: credits + site API + test deploy.

  python scripts/test_netlify_accounts.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from integrations.hosting.netlify_deployer import NetlifyDemoDeployer
from utils.netlify_credits import fetch_credit_status
from utils.netlify_pool import NetlifyAccountPool

API = "https://api.netlify.com/api/v1"
TEST_HTML = b"<html><body><h1>Agent-Earns account test</h1></body></html>"
TEST_SLUG = "agent-earns-pool-check"


def check_site_access(account) -> tuple[bool, str]:
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                f"{API}/sites/{account.site_id}",
                headers={"Authorization": f"Bearer {account.auth_token}"},
            )
        if r.status_code == 200:
            name = r.json().get("name", "")
            url = r.json().get("ssl_url") or r.json().get("url", "")
            return True, f"site OK ({name}, {url})"
        return False, f"site API {r.status_code}: {r.text[:120]}"
    except Exception as e:
        return False, str(e)


async def check_deploy(account) -> tuple[bool, str]:
    deployer = NetlifyDemoDeployer(get_settings())
    remote = f"{TEST_SLUG}-{account.name}/index.html"
    try:
        url = await asyncio.to_thread(
            deployer._deploy_sync,
            remote,
            TEST_HTML,
            site_id=account.site_id,
            auth_token=account.auth_token,
            demo_base_url=account.demo_base_url,
            account_name=account.name,
        )
        return True, url
    except Exception as e:
        return False, str(e)[:200]


async def main() -> None:
    settings = get_settings()
    pool = NetlifyAccountPool(settings)
    if not pool.accounts:
        print("No Netlify accounts configured.")
        sys.exit(1)

    min_rem = settings.netlify_credits_min_remaining
    print(f"Credit rule: skip if remaining <= {min_rem} (reserve {settings.netlify_credits_reserve})\n")
    print(f"{'Account':<16} {'Credits':<18} {'Usable':<8} {'Site':<6} {'Deploy':<8} Details")
    print("-" * 90)

    failed = 0
    for acct in pool.accounts:
        label = "primary (.env)" if acct.name == "env-primary" else acct.name
        st = acct.credit_status or fetch_credit_status(
            acct.auth_token, pool_name=acct.name, settings=settings, use_cache=False
        )
        cred_col = f"{st.remaining}/{st.included} left"
        use_col = "YES" if st.usable else "NO"

        if not st.usable:
            print(f"{label:<16} {cred_col:<18} {use_col:<8} {'—':<6} {'—':<8} SKIP: {st.reason}")
            failed += 1
            continue

        site_ok, site_msg = check_site_access(acct)
        if not site_ok:
            deploy_ok, deploy_msg = False, "skipped (site API failed)"
        else:
            deploy_ok, deploy_msg = await check_deploy(acct)
            time.sleep(1)

        if not site_ok or not deploy_ok:
            failed += 1

        site_col = "PASS" if site_ok else "FAIL"
        dep_col = "PASS" if deploy_ok else "FAIL"
        detail = deploy_msg if deploy_ok else (site_msg if not site_ok else deploy_msg)
        print(f"{label:<16} {cred_col:<18} {use_col:<8} {site_col:<6} {dep_col:<6} {detail}")

    usable = pool.usable_accounts()
    print("-" * 90)
    print(f"Usable for campaigns: {[a.name for a in usable]}")
    if not usable:
        print("No Netlify accounts pass credit check — demos will use Hostinger + R2 only.")
        sys.exit(1)
    if failed:
        print(f"\n{failed} account(s) skipped or failed.")
    else:
        print("\nAll usable accounts passed.")
    sys.exit(0 if usable else 1)


if __name__ == "__main__":
    asyncio.run(main())
