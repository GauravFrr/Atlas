"""
Upload demo HTML via FTP (Hostinger, etc.) — no Cloudflare nameserver change.

Typical Hostinger setup:
  FTP → public_html/{slug}/index.html
  Public URL: https://demos.example.com/{slug}/index.html
"""

from __future__ import annotations

import asyncio
from ftplib import FTP, FTP_TLS
from pathlib import Path
from typing import Any

from loguru import logger


class FtpDemoDeployer:
    def __init__(self, settings: Any) -> None:
        self.settings = settings

    @property
    def is_configured(self) -> bool:
        if not getattr(self.settings, "ftp_password", ""):
            return False
        if getattr(self.settings, "ftp_host", "") and getattr(
            self.settings, "ftp_user", ""
        ):
            return True
        from utils.hostinger_pool import HostingerDemoPool

        return HostingerDemoPool(self.settings).enabled

    def public_url_for_slug(self, slug: str, demo_base_url: str | None = None) -> str:
        base = (demo_base_url or self.settings.demo_site_base_url or "").rstrip("/")
        return f"{base}/{slug.strip('/')}/index.html"

    @staticmethod
    def _folder_name(slug: str) -> str:
        clean = slug.strip().replace("\\", "/")
        parts = [p for p in clean.split("/") if p and p not in (".", "..")]
        return parts[-1] if parts else "demo"

    @staticmethod
    def _normalize_host(host: str) -> str:
        h = host.strip()
        for prefix in ("ftp://", "http://", "https://"):
            if h.lower().startswith(prefix):
                h = h[len(prefix) :]
        return h.rstrip("/")

    @staticmethod
    def _host_candidates(host: str) -> list[str]:
        h = FtpDemoDeployer._normalize_host(host)
        if not h:
            return []
        out = [h]
        if h.replace(".", "").isdigit():
            out.append("ftp.hostinger.com")
        return out

    @staticmethod
    def _build_attempts(hosts: list[str], use_tls: bool) -> list[tuple[str, bool, bool]]:
        """plain passive → FTPS passive → plain active → FTPS active per host."""
        attempts: list[tuple[str, bool, bool]] = []
        for h in hosts:
            if use_tls:
                attempts.extend([(h, True, True), (h, False, True)])
            else:
                attempts.extend(
                    [
                        (h, True, False),
                        (h, True, True),
                        (h, False, False),
                        (h, False, True),
                    ]
                )
        return attempts

    def _remote_segments(self, ftp: FTP, slug: str) -> list[str]:
        folder = self._folder_name(slug)
        pwd = (ftp.pwd() or "").replace("\\", "/").rstrip("/") or "/"
        if pwd == "/public_html" or pwd.endswith("/public_html"):
            return [folder]
        if pwd in ("/", ""):
            return ["public_html", folder]
        return ["public_html", folder]

    def _cwd_mkdir(self, ftp: FTP, segments: list[str]) -> None:
        for seg in segments:
            if not seg or seg == ".":
                continue
            try:
                ftp.cwd(seg)
            except Exception:
                ftp.mkd(seg)
                ftp.cwd(seg)

    def _connect(
        self,
        host: str,
        user: str,
        password: str,
        *,
        port: int,
        timeout: int,
        passive: bool,
        use_tls: bool,
    ) -> FTP:
        client: FTP = FTP_TLS() if use_tls else FTP()
        client.connect(host, port, timeout=timeout)
        client.login(user, password)
        if isinstance(client, FTP_TLS):
            client.prot_p()
        client.set_pasv(passive)
        return client

    def _stor_index(self, ftp: FTP, local_path: Path, slug: str, site_name: str) -> None:
        remote_segments = self._remote_segments(ftp, slug)
        self._cwd_mkdir(ftp, remote_segments)
        final_dir = ftp.pwd()
        folder = self._folder_name(slug)
        logger.info(
            f"[FTP/{site_name}] upload {final_dir}/index.html (folder={folder})"
        )
        with local_path.open("rb") as f:
            ftp.storbinary("STOR index.html", f)

    def _upload_sync(
        self,
        local_path: Path,
        slug: str,
        *,
        remote_base: str | None = None,
        demo_base_url: str | None = None,
        site_name: str = "ftp",
        ftp_host: str | None = None,
        ftp_user: str | None = None,
    ) -> str:
        del remote_base
        user = (ftp_user or self.settings.ftp_user or "").strip()
        password = self.settings.ftp_password
        port = int(getattr(self.settings, "ftp_port", 21) or 21)
        use_tls = bool(getattr(self.settings, "ftp_use_tls", False))
        timeout = 60

        hosts = self._host_candidates(ftp_host or self.settings.ftp_host or "")
        if not hosts or not user or not password:
            raise ValueError("FTP host, user, or password missing")

        attempts = self._build_attempts(hosts, use_tls)
        errors: list[str] = []

        for host, passive, tls in attempts:
            mode = "passive" if passive else "active"
            enc = "ftps" if tls else "ftp"
            label = f"{enc}/{mode}@{host}:{port}"
            ftp: FTP | None = None
            try:
                ftp = self._connect(
                    host,
                    user,
                    password,
                    port=port,
                    timeout=timeout,
                    passive=passive,
                    use_tls=tls,
                )
                self._stor_index(ftp, local_path, slug, site_name)
                logger.info(f"[FTP/{site_name}] OK via {label}")
                url = self.public_url_for_slug(
                    self._folder_name(slug), demo_base_url=demo_base_url
                )
                logger.success(f"[FTP/{site_name}] Uploaded demo: {url}")
                return url
            except Exception as e:
                errors.append(f"{label}: {e}")
                logger.debug(f"[FTP/{site_name}] {label} failed: {e}")
            finally:
                if ftp is not None:
                    try:
                        ftp.quit()
                    except Exception:
                        pass

        raise ConnectionError(
            f"FTP failed after {len(attempts)} attempts — " + "; ".join(errors[-3:])
        )

    async def upload_demo(
        self,
        local_path: str | Path,
        slug: str | None = None,
        demo_base_url: str | None = None,
        *,
        ftp_remote_base: str | None = None,
        site_name: str = "ftp",
        ftp_host: str | None = None,
        ftp_user: str | None = None,
    ) -> str | None:
        path = Path(local_path)
        if not path.is_file():
            logger.warning(f"[FTP] Demo file not found: {path}")
            return None
        password = str(getattr(self.settings, "ftp_password", "") or "")
        host = (ftp_host or getattr(self.settings, "ftp_host", "") or "").strip()
        user = (ftp_user or getattr(self.settings, "ftp_user", "") or "").strip()
        if not password or not host or not user:
            logger.warning(
                f"[FTP/{site_name}] Missing host, user, or FTP_PASSWORD in .env"
            )
            return None
        object_slug = self._folder_name(slug or path.stem)
        try:
            return await asyncio.to_thread(
                self._upload_sync,
                path,
                object_slug,
                remote_base=ftp_remote_base,
                demo_base_url=demo_base_url,
                site_name=site_name,
                ftp_host=ftp_host,
                ftp_user=ftp_user,
            )
        except Exception as e:
            err = str(e)
            hint = ""
            if "10061" in err or "actively refused" in err.lower():
                hint = " — passive FTP may be blocked; client retries active + FTPS"
            logger.error(
                f"[FTP/{site_name}] Upload failed for {object_slug}: {e}{hint}"
            )
            return None
