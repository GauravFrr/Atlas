"""
Test Supabase DATABASE_URL — run before Railway deploy.

  set DATABASE_URL=postgresql://postgres.REF:PASSWORD@...pooler.supabase.com:6543/postgres?sslmode=require
  python scripts/test_supabase_db.py
"""

from __future__ import annotations

import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


async def main() -> None:
    from sqlalchemy import text
    from sqlalchemy.engine import make_url

    from database.connection import database_url_for_log, get_database_url, init_db

    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if not raw:
        print("Set DATABASE_URL first.")
        sys.exit(1)

    url = get_database_url()
    parsed = make_url(url)
    print(f"Host:     {parsed.host}:{parsed.port}")
    print(f"User:     {parsed.username}")
    print(f"Password: {'set' if parsed.password else 'MISSING'}")
    print(f"URL:      {database_url_for_log(url)}")

    if parsed.password in ("***", "%2A%2A%2A"):
        print("ERROR: password was mangled to *** — fix normalize_database_url")
        sys.exit(1)

    await init_db()
    from database.connection import get_engine

    engine = await get_engine()
    async with engine.connect() as conn:
        one = await conn.scalar(text("SELECT 1"))
    print(f"OK - SELECT 1 = {one}")


if __name__ == "__main__":
    asyncio.run(main())
