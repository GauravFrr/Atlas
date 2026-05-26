"""
Upload demo HTML to Netlify via API (file-digest deploy).

No Cloudflare, no Landingsite file manager. Use:
  - https://your-site.netlify.app/slug/index.html
  - or custom subdomain demos.gauravxd.dev (CNAME in Landingsite DNS only)

Setup: docs/NETLIFY_DEMO_SETUP.md
Multi-site: data/netlify_accounts.json (see docs/DEMO_HOSTING.md)
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from pathlib import Path
from typing import Any

import httpx
from loguru import logger


class NetlifyDemoDeployer:
    API_BASE = "https://api.netlify.com/api/v1"

    def __init__(self, settings: Any) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        from utils.netlify_pool import NetlifyAccountPool

        pool = NetlifyAccountPool(self.settings)
        return pool.enabled

    def _normalize_base(self, base: str) -> str:
        base = base.strip().rstrip("/")
        if base and not base.startswith(("http://", "https://")):
            base = f"https://{base}"
        return base

    def public_url_for_slug(
        self, slug: str, demo_base_url: str | None = None
    ) -> str:
        base = self._normalize_base(
            demo_base_url or self.settings.demo_site_base_url or ""
        )
        return f"{base}/{slug.strip('/')}/index.html"

    def _deploy_sync(
        self,
        remote_path: str,
        content: bytes,
        *,
        site_id: str,
        auth_token: str,
        demo_base_url: str,
        account_name: str = "netlify",
    ) -> str:
        remote_path = remote_path.lstrip("/")
        digest = hashlib.sha1(content).hexdigest()
        files_manifest = {remote_path: digest}
        headers = {"Authorization": f"Bearer {auth_token.strip()}"}

        with httpx.Client(timeout=120.0) as client:
            create = client.post(
                f"{self.API_BASE}/sites/{site_id.strip()}/deploys",
                headers=headers,
                json={"files": files_manifest},
            )
            if create.status_code not in (200, 201):
                raise RuntimeError(
                    f"Netlify create deploy failed ({create.status_code}): "
                    f"{create.text[:400]}"
                )

            deploy_id = create.json()["id"]

            upload = client.put(
                f"{self.API_BASE}/deploys/{deploy_id}/files/{remote_path}",
                headers={
                    **headers,
                    "Content-Type": "application/octet-stream",
                },
                content=content,
            )
            if upload.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"Netlify file upload failed ({upload.status_code}): "
                    f"{upload.text[:400]}"
                )

            for _ in range(45):
                status_resp = client.get(
                    f"{self.API_BASE}/deploys/{deploy_id}",
                    headers=headers,
                )
                if status_resp.status_code == 200:
                    state = status_resp.json().get("state", "")
                    if state in ("ready", "published"):
                        break
                    if state in ("error", "failed"):
                        raise RuntimeError(
                            f"Netlify deploy {deploy_id} failed: state={state}"
                        )
                time.sleep(2)

        slug = remote_path.split("/")[0]
        url = f"{self._normalize_base(demo_base_url)}/{slug}/index.html"
        logger.success(f"[Netlify/{account_name}] Deployed demo: {url}")
        return url

    async def upload_demo(
        self,
        local_path: str | Path,
        slug: str | None = None,
        demo_base_url: str | None = None,
        *,
        site_id: str | None = None,
        auth_token: str | None = None,
        account_name: str = "netlify",
    ) -> str | None:
        path = Path(local_path)
        if not path.is_file():
            logger.warning(f"[Netlify] Demo file not found: {path}")
            return None

        sid = site_id or getattr(self.settings, "netlify_site_id", "")
        token = auth_token or getattr(self.settings, "netlify_auth_token", "")
        base = demo_base_url or getattr(self.settings, "demo_site_base_url", "")
        if not (sid and token and base):
            logger.debug("[Netlify] Not configured — skip upload")
            return None

        object_slug = slug or path.stem
        remote_path = f"{object_slug}/index.html"
        content = path.read_bytes()

        try:
            return await asyncio.to_thread(
                self._deploy_sync,
                remote_path,
                content,
                site_id=sid,
                auth_token=token,
                demo_base_url=base,
                account_name=account_name,
            )
        except Exception as e:
            err = str(e).lower()
            if any(
                x in err
                for x in ("credit", "quota", "limit", "402", "usage exceeded", "blocked")
            ):
                from utils.netlify_credits import invalidate_cache

                invalidate_cache(token)
                logger.error(
                    f"[Netlify/{account_name}] Upload failed (credits?): {e} — "
                    "account skipped until credits renew"
                )
            else:
                logger.error(
                    f"[Netlify/{account_name}] Upload failed for {object_slug}: {e}"
                )
            return None
