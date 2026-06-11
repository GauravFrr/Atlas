"""
Lightweight SQLite migrations — adds new columns to existing databases.
Safe to run on every startup (ignores columns that already exist).
"""

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


# (table, column, sql_type)
COLUMN_MIGRATIONS: list[tuple[str, str, str]] = [
    ("leads", "place_id", "VARCHAR(255)"),
    ("leads", "campaign_run_id", "VARCHAR(36)"),
    ("leads", "demo_site_path", "VARCHAR(500)"),
    ("leads", "pitch_subject", "VARCHAR(500)"),
    ("leads", "pitch_body", "TEXT"),
]


def _column_exists_err(err: str) -> bool:
    e = err.lower()
    return (
        "duplicate column" in e
        or "already exists" in e
        or "duplicate column name" in e
    )


async def run_migrations(engine: AsyncEngine) -> None:
    """Apply additive column migrations for existing SQLite / Postgres databases."""
    async with engine.connect() as conn:
        for table, column, sql_type in COLUMN_MIGRATIONS:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
                )
                await conn.commit()
                logger.info(f"Migration: added {table}.{column}")
            except Exception as e:
                await conn.rollback()
                err = str(e).lower()
                if _column_exists_err(err):
                    continue
                if "no such table" in err or "does not exist" in err:
                    continue
                logger.warning(f"Migration skipped {table}.{column}: {e}")

        # Unique index on place_id (ignore if exists)
        try:
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_leads_place_id "
                    "ON leads (place_id) WHERE place_id IS NOT NULL"
                )
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            logger.debug(f"place_id index migration: {e}")
