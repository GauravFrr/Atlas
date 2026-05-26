"""
Deprecated — use the single entry point:

  python start_agent.py

Reply sync and outreach run inside each autonomous cycle.
Optional dashboard: python scripts/run_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    print("Use one command for full autopilot:\n")
    print(f"  cd {ROOT}")
    print("  python start_agent.py\n")
    print("Optional: python scripts/run_dashboard.py\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
