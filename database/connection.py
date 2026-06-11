"""
Database Connection — SQLAlchemy 2.0 async engine.
SQLite (local / Railway volume) or managed Postgres (Neon, Supabase, Railway).

All services (webhooks, Telegram, Atlas) must use the same DATABASE_URL.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from loguru import logger
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None
_resolved_database_url: str | None = None

DEFAULT_SQLITE = "sqlite+aiosqlite:///agent.db"
RAILWAY_DATA_DIR = Path("/app/data")


def _sqlite_file_url(path: Path) -> str:
    p = path.resolve().as_posix()
    return f"sqlite+aiosqlite:///{p}"


def normalize_database_url(url: str) -> str:
    """
    Neon/Supabase/Railway often provide postgresql:// — SQLAlchemy async needs asyncpg.
    Strips ?pgbouncer=true (Prisma hint) — asyncpg rejects it as a connect() kwarg.
    """
    u = url.strip().strip('"').strip("'")
    if u.startswith("postgres://"):
        u = "postgresql+asyncpg://" + u[len("postgres://") :]
    elif u.startswith("postgresql://") and "+asyncpg" not in u:
        u = "postgresql+asyncpg://" + u[len("postgresql://") :]
    try:
        parsed = make_url(u)
        if parsed.drivername.startswith("postgresql"):
            u = str(parsed.difference_update_query(["pgbouncer"]))
    except Exception:
        import re

        u = re.sub(r"([?&])pgbouncer=[^&]*&?", r"\1", u, flags=re.I)
        u = re.sub(r"\?&", "?", u).rstrip("?&")
    return u


def _ensure_sqlite_parent(url: str) -> None:
    try:
        parsed = make_url(url)
    except Exception:
        return
    if not parsed.drivername.startswith("sqlite"):
        return
    db_file = parsed.database
    if not db_file or db_file == ":memory:":
        return
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)


def resolve_database_url() -> str:
    """
    Priority:
      1. DATABASE_URL env
      2. Settings.database_url from .env
      3. /app/data/agent.db when Railway volume is mounted
      4. ./agent.db (local default)
    """
    explicit = (os.environ.get("DATABASE_URL") or "").strip()
    if not explicit:
        try:
            from config import get_settings

            explicit = str(get_settings().database_url or "").strip()
        except Exception:
            explicit = ""

    if explicit:
        url = normalize_database_url(explicit)
    elif RAILWAY_DATA_DIR.is_dir():
        url = _sqlite_file_url(RAILWAY_DATA_DIR / "agent.db")
    else:
        url = DEFAULT_SQLITE

    _ensure_sqlite_parent(url)
    return url


def get_database_url() -> str:
    global _resolved_database_url
    if _resolved_database_url is None:
        _resolved_database_url = resolve_database_url()
    return _resolved_database_url


def database_url_for_log(url: str | None = None) -> str:
    """Hide credentials in logs."""
    try:
        return make_url(url or get_database_url()).render_as_string(hide_password=True)
    except Exception:
        return "database"


def __getattr__(name: str):
    if name == "DATABASE_URL":
        return get_database_url()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def _is_sqlite(url: str) -> bool:
    try:
        return make_url(url).drivername.startswith("sqlite")
    except Exception:
        return url.startswith("sqlite")


def _is_postgres(url: str) -> bool:
    try:
        return make_url(url).drivername.startswith("postgresql")
    except Exception:
        return "postgresql" in url


def _uses_supabase_pooler(url: str) -> bool:
    """Transaction pooler (port 6543 / pooler host) — disable prepared statements."""
    lower = url.lower()
    return ":6543" in lower or "pooler.supabase.com" in lower


def _postgres_engine_kwargs(database_url: str) -> dict:
    kwargs: dict = {"echo": False, "pool_pre_ping": True}
    if _uses_supabase_pooler(database_url):
        # Supavisor/pgbouncer transaction mode — see docs/DATABASE.md
        kwargs["poolclass"] = NullPool
        kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
        }
    else:
        kwargs["pool_size"] = 5
        kwargs["max_overflow"] = 10
    return kwargs


async def init_db() -> None:
    """
    Initialize the database engine and create all tables.
    Called once on startup.
    """
    global _engine, _session_factory

    database_url = get_database_url()
    engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
    if _is_sqlite(database_url):
        engine_kwargs["connect_args"] = {
            "check_same_thread": False,
            "timeout": 60,
        }
    elif _is_postgres(database_url):
        engine_kwargs.update(_postgres_engine_kwargs(database_url))

    _engine = create_async_engine(database_url, **engine_kwargs)

    if _is_sqlite(database_url):

        @event.listens_for(_engine.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _connection_record) -> None:
            """WAL + busy timeout — allows backfill/scripts while agent holds DB."""
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=60000")
            cursor.close()

    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async with _engine.begin() as conn:
        import database.models  # noqa: F401 — register all ORM models
        from database.base import Base

        await conn.run_sync(Base.metadata.create_all)

    from database.migrations import run_migrations

    await run_migrations(_engine)

    await health_check()
    backend = "Postgres" if _is_postgres(database_url) else "SQLite"
    logger.success(f"Database initialized ({backend}): {database_url_for_log(database_url)}")


async def health_check() -> bool:
    """Returns True if database is accessible."""
    if not _engine:
        return False
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_engine() -> AsyncEngine:
    """Returns the database engine (initializes if needed)."""
    if not _engine:
        await init_db()
    assert _engine is not None, "init_db() failed to initialize the database engine"
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Returns the session factory."""
    if not _session_factory:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory
