"""Warn when scripts run with wrong Python (Telegram/httpx mismatch)."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_project_venv() -> None:
    root = Path(__file__).resolve().parents[1]
    venv_py = root / "venv" / "Scripts" / "python.exe"
    here = Path(sys.executable).resolve()
    if venv_py.exists() and here != venv_py.resolve():
        print(
            "Use the project venv (system Python breaks Telegram):\n"
            f"  {venv_py} {' '.join(sys.argv)}",
            file=sys.stderr,
        )
        sys.exit(1)


def check_telegram_import() -> None:
    try:
        from telegram import Bot  # noqa: F401
    except TypeError as e:
        if "proxies" in str(e):
            print(
                "Telegram library incompatible with installed httpx.\n"
                "Fix: .\\venv\\Scripts\\pip install -r requirements.txt\n"
                "Then: .\\venv\\Scripts\\python.exe " + " ".join(sys.argv),
                file=sys.stderr,
            )
            sys.exit(1)
        raise
