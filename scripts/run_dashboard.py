"""Start dashboard only."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import uvicorn
from config import get_settings


def main() -> None:
    port = get_settings().dashboard_port
    print(f"Dashboard: http://localhost:{port}  (user: admin, password: DASHBOARD_PASSWORD)")
    uvicorn.run(
        "dashboard.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
