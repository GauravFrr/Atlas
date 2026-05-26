"""
List FTP directories after login (find where files actually land).

  python scripts/test_ftp_list.py
"""

from __future__ import annotations

import sys
from ftplib import FTP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings
from utils.hostinger_pool import HostingerDemoPool


def list_tree(ftp: FTP, path: str = "", depth: int = 0, max_depth: int = 3) -> None:
    if depth > max_depth:
        return
    try:
        ftp.cwd(path or "/")
    except Exception as e:
        print(f"{'  ' * depth}Cannot cwd {path!r}: {e}")
        return
    pwd = ftp.pwd()
    print(f"{'  ' * depth}[{pwd}]")
    try:
        items = []
        ftp.retrlines("LIST", items.append)
    except Exception as e:
        print(f"{'  ' * depth}LIST failed: {e}")
        return
    for line in items[:30]:
        print(f"{'  ' * depth}{line}")
    # Try common subdirs
    if depth < max_depth:
        for sub in ("public_html", "ftp-connection-test", "domains"):
            try:
                ftp.cwd(pwd)
                ftp.cwd(sub)
                list_tree(ftp, ftp.pwd(), depth + 1, max_depth)
            except Exception:
                pass


def main() -> None:
    settings = get_settings()
    pool = HostingerDemoPool(settings)
    if not pool.enabled:
        print("Configure FTP_PASSWORD + hostinger_sites.json")
        sys.exit(1)

    for site in pool.sites:
        host = site.resolved_host(settings)
        user = site.resolved_user(settings)
        print(f"\n=== {site.name} ({user} @ {host}) ===")
        ftp = FTP(host, timeout=60)
        try:
            ftp.login(user, settings.ftp_password)
            ftp.set_pasv(True)
            print(f"PWD after login: {ftp.pwd()}")
            list_tree(ftp)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            try:
                ftp.quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
