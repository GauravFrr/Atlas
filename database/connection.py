"""
Database Connection — SQLAlchemy 2.0 async engine.
Connection pooling, health check on startup, auto-reconnect on failure.
"""

import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event, text

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None
DATABASE_URL = "sqlite+aiosqlite:///agent.db"


async def init_db() -> None:
    """
    Initialize the database engine and create all tables.
    Called once on startup.
    """
    global _engine, _session_factory

    _engine = create_async_engine(
        DATABASE_URL,
        echo=False,           # Set to True to see SQL queries in logs
        pool_pre_ping=True,   # Verify connections before using them
        connect_args={
            "check_same_thread": False,
            "timeout": 60,
        },
    )

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
        expire_on_commit=False,  # Don't expire objects after commit
        autoflush=False,
        autocommit=False,
    )

    # Create tables
    async with _engine.begin() as conn:
        import database.models  # noqa: F401 — register all ORM models
        from database.base import Base
        await conn.run_sync(Base.metadata.create_all)

    from database.migrations import run_migrations
    await run_migrations(_engine)

    # Verify connection
    await health_check()
    logger.success(f"Database initialized: {DATABASE_URL}")


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
