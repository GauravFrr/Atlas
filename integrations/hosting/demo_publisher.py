"""
Publish demos: Hostinger (FTP) first, Cloudflare R2 fallback.
Netlify is opt-in only via demo_upload_mode=netlify and demo_skip_netlify=false.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from integrations.hosting.ftp_deployer import FtpDemoDeployer
from integrations.hosting.netlify_deployer import NetlifyDemoDeployer
from integrations.hosting.r2_deployer import R2DemoDeployer
from loguru import logger
from utils.hostinger_pool import HostingerDemoPool, HostingerDemoSite
from utils.netlify_pool import NetlifyAccountPool


@dataclass(frozen=True)
class _PublishTarget:
    kind: Literal["hostinger", "netlify"]
    label: str
    site: HostingerDemoSite | None = None


class DemoPublisher:
    """
    demo_upload_mode:
      auto     — Hostinger pool, then R2 (see demo_host_strategy)
      ftp      — Hostinger only
      r2       — R2 only
      netlify  — Netlify only (disabled when demo_skip_netlify=true)
      local    — No upload

    demo_host_strategy (auto only):
      random   — shuffle Hostinger sites each demo, then R2
      priority — all Hostinger sites in order, then R2
    """

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.netlify = NetlifyDemoDeployer(settings)
        self.netlify_pool = NetlifyAccountPool(settings)
        self.hostinger_pool = HostingerDemoPool(settings)
        self.r2 = R2DemoDeployer(settings)
        self.ftp = FtpDemoDeployer(settings)
        self.mode = (getattr(settings, "demo_upload_mode", "auto") or "auto").lower()
        self.host_strategy = (
            getattr(settings, "demo_host_strategy", "random") or "random"
        ).lower()
        self.prefer_r2 = bool(getattr(settings, "demo_prefer_r2", False))
        self.skip_netlify = bool(getattr(settings, "demo_skip_netlify", True))

    def _netlify_allowed(self) -> bool:
        return not self.skip_netlify and self.mode == "netlify"

    def _effective_mode(self) -> str:
        m = self.mode
        if m == "netlify" and self.skip_netlify:
            logger.warning("[Demo] Netlify disabled (demo_skip_netlify) — using auto")
            m = "auto"
        if m != "auto":
            return m
        if self.prefer_r2 and self.r2.is_configured:
            return "r2"
        if self.hostinger_pool.enabled:
            return "auto"
        if self.r2.is_configured:
            return "r2"
        return "local"

    def _random_targets(self) -> list[_PublishTarget]:
        targets: list[_PublishTarget] = []
        for site in self.hostinger_pool.sites:
            targets.append(
                _PublishTarget(
                    kind="hostinger",
                    label=site.demo_base_url or site.name,
                    site=site,
                )
            )
        random.shuffle(targets)
        return targets

    async def _try_netlify_accounts(
        self,
        path: Path,
        slug: str,
        demo_base_url: str | None,
        *,
        accounts: list | None = None,
    ) -> str | None:
        order = list(accounts or self.netlify_pool.usable_accounts())
        if not order:
            return None
        for account in order:
            url = await self.netlify.upload_demo(
                path,
                slug=slug,
                demo_base_url=account.demo_base_url,
                site_id=account.site_id,
                auth_token=account.auth_token,
                account_name=account.name,
            )
            if url:
                return url
            logger.warning(
                f"[Demo] Netlify '{account.name}' failed — trying next"
            )
        return None

    async def _try_hostinger_site(
        self,
        path: Path,
        slug: str,
        demo_base_url: str | None,
        site: HostingerDemoSite,
    ) -> str | None:
        return await self.ftp.upload_demo(
            path,
            slug=slug,
            demo_base_url=site.demo_base_url or demo_base_url,
            ftp_remote_base=site.ftp_remote_base,
            site_name=site.name,
            ftp_host=site.resolved_host(self.settings),
            ftp_user=site.resolved_user(self.settings),
        )

    async def _try_netlify_pool(
        self, path: Path, slug: str, demo_base_url: str | None
    ) -> str | None:
        return await self._try_netlify_accounts(
            path, slug, demo_base_url, accounts=self.netlify_pool.ordered_for_fallback(slug)
        )

    async def _try_hostinger_pool(
        self, path: Path, slug: str, demo_base_url: str | None
    ) -> str | None:
        if not self.hostinger_pool.enabled:
            return None
        for site in self.hostinger_pool.sites:
            url = await self._try_hostinger_site(path, slug, demo_base_url, site)
            if url:
                return url
            logger.warning(f"[Demo] Hostinger '{site.name}' failed — trying next")
        return None

    async def _try_r2(
        self, path: Path, slug: str, demo_base_url: str | None
    ) -> str | None:
        if not self.r2.is_configured:
            return None
        url = await self.r2.upload_demo(path, slug=slug, demo_base_url=demo_base_url)
        if url:
            logger.info("[Demo] Published via Cloudflare R2 (fallback)")
        return url

    async def _publish_random(
        self, path: Path, slug: str, demo_base_url: str | None
    ) -> str | None:
        """Shuffle Hostinger sites per demo; try each; then Cloudflare R2."""
        targets = self._random_targets()
        if not targets:
            return await self._try_r2(path, slug, demo_base_url)

        labels = [t.label for t in targets]
        logger.info(f"[Demo] Random host order: {labels}")

        for target in targets:
            if target.kind != "hostinger" or not target.site:
                continue
            url = await self._try_hostinger_site(
                path, slug, demo_base_url, target.site
            )
            if url:
                logger.info(f"[Demo] Published via {target.label}")
                return url
            logger.warning(f"[Demo] {target.label} failed — trying next host")

        return await self._try_r2(path, slug, demo_base_url)

    async def _publish_priority(
        self, path: Path, slug: str, demo_base_url: str | None
    ) -> str | None:
        """Hostinger → Cloudflare R2."""
        url = await self._try_hostinger_pool(path, slug, demo_base_url)
        if url:
            return url
        return await self._try_r2(path, slug, demo_base_url)

    def public_url_for_slug(self, slug: str, demo_base_url: str | None = None) -> str | None:
        base = demo_base_url or getattr(self.settings, "demo_site_base_url", None)
        if not base:
            return None
        mode = self._effective_mode()
        if mode == "netlify" and self._netlify_allowed():
            acct = self.netlify_pool.pick(slug)
            if acct:
                return self.netlify.public_url_for_slug(
                    slug, demo_base_url=acct.demo_base_url
                )
        if mode == "ftp" and self.hostinger_pool.sites:
            return self.ftp.public_url_for_slug(
                slug, demo_base_url=self.hostinger_pool.sites[0].demo_base_url
            )
        if self.hostinger_pool.sites:
            site = random.choice(self.hostinger_pool.sites)
            return self.ftp.public_url_for_slug(slug, demo_base_url=site.demo_base_url)
        return self.ftp.public_url_for_slug(slug, demo_base_url=base)

    async def publish(
        self,
        local_path: str | Path,
        slug: str,
        demo_base_url: str | None = None,
    ) -> str | None:
        path = Path(local_path)
        if not path.is_file():
            return None

        mode = self._effective_mode()
        strategy = self.host_strategy
        logger.debug(f"[Demo] Publish mode={mode} strategy={strategy} slug={slug}")

        if mode == "netlify" and self._netlify_allowed():
            return await self._try_netlify_pool(path, slug, demo_base_url)
        if mode == "ftp":
            return await self._try_hostinger_pool(path, slug, demo_base_url)
        if mode == "r2":
            return await self._try_r2(path, slug, demo_base_url)
        if mode == "local":
            return self.public_url_for_slug(slug, demo_base_url=demo_base_url)
        if mode == "auto":
            if self.prefer_r2 and self.r2.is_configured:
                url = await self._try_r2(path, slug, demo_base_url)
                if url:
                    return url
            if strategy == "priority":
                return await self._publish_priority(path, slug, demo_base_url)
            return await self._publish_random(path, slug, demo_base_url)

        return self.public_url_for_slug(slug, demo_base_url=demo_base_url)
