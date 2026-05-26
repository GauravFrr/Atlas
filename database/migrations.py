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


async def run_migrations(engine: AsyncEngine) -> None:
    """Apply additive column migrations for existing SQLite databases."""
    async with engine.connect() as conn:
        for table, column, sql_type in COLUMN_MIGRATIONS:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}")
                )
                await conn.commit()
                logger.info(f"Migration: added {table}.{column}")
            except Exception as e:
                err = str(e).lower()
                if "duplicate column" in err or "already exists" in err:
                    continue
                if "no such table" in err:
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
            logger.debug(f"place_id index migration: {e}")
