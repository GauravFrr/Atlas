"""
Database Session — Async session management with transaction handling.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.
    Automatically commits on success, rolls back on error.
    
    Usage:
        async with get_session() as session:
            lead = await session.get(Lead, lead_id)
    """
    factory = get_session_factory()
    session: AsyncSession = factory()

    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Session rolled back due to error: {e}")
        raise
    finally:
        await session.close()
