"""
Shared dependency injection container.
All shared singletons are created once here and injected where needed.
This makes the entire system testable — swap any dependency in tests.
"""

from functools import lru_cache
from config import Settings, get_settings


# ══════════════════════════════════════════════
# Settings (always available)
# ══════════════════════════════════════════════

def get_config() -> Settings:
    """FastAPI dependency for settings."""
    return get_settings()


# ══════════════════════════════════════════════
# Database Session
# ══════════════════════════════════════════════

async def get_db_session():
    """
    FastAPI dependency for async database sessions.
    Usage in route:
        async def my_route(db: AsyncSession = Depends(get_db_session)):
    """
    from database.session import get_session
    async with get_session() as session:
        yield session


# ══════════════════════════════════════════════
# LLM Router
# ══════════════════════════════════════════════

@lru_cache()
def get_llm_router():
    """Returns the singleton LLM router instance."""
    from llm.router import LLMRouter
    return LLMRouter(settings=get_settings())


# ══════════════════════════════════════════════
# Notifier (Telegram + Email alerts)
# ══════════════════════════════════════════════

@lru_cache()
def get_notifier():
    """Returns the singleton notifier instance."""
    from utils.notifier import Notifier
    return Notifier(settings=get_settings())


# ══════════════════════════════════════════════
# HTTP Client
# ══════════════════════════════════════════════

@lru_cache()
def get_http_client():
    """Returns the shared async HTTP client."""
    from utils.http_client import AsyncHTTPClient
    return AsyncHTTPClient()


# ══════════════════════════════════════════════
# Rate Limiter
# ══════════════════════════════════════════════

@lru_cache()
def get_rate_limiter():
    """Returns the shared rate limiter."""
    from utils.rate_limiter import RateLimiter
    return RateLimiter()
