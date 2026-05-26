"""
Upload generated demo HTML to Cloudflare R2 (S3-compatible API).
Public URLs use your domain + business slug (trustworthy preview links).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from loguru import logger

try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]
    Config = None  # type: ignore[assignment,misc]
    BotoCoreError = ClientError = Exception  # type: ignore[misc,assignment]


class R2DemoDeployer:
    """
    Upload as {slug}/index.html. Public R2 dev URLs must include index.html
    (folder URLs 404 on pub-*.r2.dev):
      https://pub-xxx.r2.dev/austin-precision-plumbing/index.html
    """

    def __init__(self, settings: Any) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        return bool(
            boto3
            and self.settings.r2_access_key_id
            and self.settings.r2_secret_access_key
            and self.settings.r2_bucket_name
            and self.settings.r2_endpoint
            and self.settings.demo_site_base_url
        )

    def _client(self):
        if not boto3:
            raise RuntimeError("boto3 is required for R2 uploads. Run: pip install boto3")
        return boto3.client(
            "s3",
            endpoint_url=self.settings.r2_endpoint,
            aws_access_key_id=self.settings.r2_access_key_id,
            aws_secret_access_key=self.settings.r2_secret_access_key,
            region_name="auto",
            config=Config(signature_version="s3v4"),
        )

    def public_url_for_slug(self, slug: str, demo_base_url: str | None = None) -> str:
        base = (demo_base_url or self.settings.demo_site_base_url or "").rstrip("/")
        slug = slug.strip("/")
        # R2 public dev endpoints do not serve directory indexes; object key is {slug}/index.html
        return f"{base}/{slug}/index.html"

    def _upload_sync(self, local_path: Path, slug: str, demo_base_url: str | None = None) -> str:
        key = f"{slug}/index.html"
        client = self._client()
        client.upload_file(
            str(local_path),
            self.settings.r2_bucket_name,
            key,
            ExtraArgs={"ContentType": "text/html; charset=utf-8"},
        )
        url = self.public_url_for_slug(slug, demo_base_url=demo_base_url)
        logger.success(f"[R2] Uploaded demo: {url}")
        return url

    async def upload_demo(
        self,
        local_path: str | Path,
        slug: str | None = None,
        demo_base_url: str | None = None,
    ) -> str | None:
        """
        Upload HTML to R2. Returns public HTTPS URL or None on failure.
        slug defaults to local filename without .html
        """
        path = Path(local_path)
        if not path.is_file():
            logger.warning(f"[R2] Demo file not found: {path}")
            return None
        if not self.is_configured:
            logger.debug("[R2] Not configured — skip upload")
            return None

        object_slug = slug or path.stem
        try:
            return await asyncio.to_thread(
                self._upload_sync, path, object_slug, demo_base_url
            )
        except (BotoCoreError, ClientError, OSError) as e:
            logger.error(f"[R2] Upload failed for {object_slug}: {e}")
            return None
