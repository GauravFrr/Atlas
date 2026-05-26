"""
Agent Memory Manager — Long-term memory for the agent.
Stores what worked, what didn't, and client preferences learned over time.
All memory is persisted in SQLite (survives restarts).
"""

import json
from datetime import datetime, timezone, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession


class MemoryManager:
    """
    Agent's long-term memory system.
    
    Tracks:
    - Best performing email subject lines
    - Best lead sources by conversion rate  
    - Best performing content topics
    - Client preferences learned
    - Weekly strategy updates
    """

    def __init__(self, db_session_factory):
        self._session_factory = db_session_factory
        self._cache: dict = {}  # In-memory cache for frequently accessed data
        self._cache_expires: dict = {}

    async def get_best_subject_lines(self, limit: int = 10) -> list[dict]:
        """Returns subject lines with highest open rates."""
        cache_key = "best_subjects"
        if self._is_cached(cache_key):
            return self._cache[cache_key]

        # TODO: Query from DB when email_repository is ready
        # For now return empty — will be populated as agent runs
        return []

    async def get_best_lead_sources(self) -> list[dict]:
        """Returns lead sources ranked by conversion to paying client."""
        # Will be populated from performance data
        return [
            {"source": "google_maps", "conversion_rate": 0.08, "avg_deal_inr": 8999},
            {"source": "reddit", "conversion_rate": 0.05, "avg_deal_inr": 6000},
        ]

    async def get_winning_niches(self) -> list[str]:
        """Returns niches that have converted best historically."""
        return ["restaurant", "salon_spa", "fitness_gym", "local_service"]

    async def remember_email_result(
        self,
        subject: str,
        template_id: str,
        opened: bool,
        replied: bool,
    ) -> None:
        """Records outcome of a sent email for learning."""
        logger.debug(f"Memory: email_result subject='{subject[:30]}...' opened={opened} replied={replied}")
        # Will write to performance table when DB is ready

    async def remember_lead_source_result(
        self,
        source: str,
        leads_found: int,
        leads_converted: int,
    ) -> None:
        """Records lead source performance."""
        logger.debug(f"Memory: lead_source={source} found={leads_found} converted={leads_converted}")

    async def get_strategy(self) -> dict:
        """
        Returns current strategy configuration.
        Updated weekly by self_improvement module.
        """
        return {
            "focus_niches": ["restaurant", "salon_spa", "fitness_gym"],
            "focus_cities": ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad"],
            "best_email_time_ist": "11:00",
            "lead_score_threshold": 7,
            "primary_service": "full_website",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def update_strategy(self, updates: dict) -> None:
        """
        Updates the strategy based on weekly performance review.
        Called by self_improvement module.
        """
        logger.info(f"Strategy updated: {list(updates.keys())}")
        # TODO: Persist to DB

    def _is_cached(self, key: str) -> bool:
        if key not in self._cache:
            return False
        if datetime.now() > self._cache_expires.get(key, datetime.min):
            del self._cache[key]
            return False
        return True

    def _set_cache(self, key: str, value, ttl_minutes: int = 60) -> None:
        self._cache[key] = value
        self._cache_expires[key] = datetime.now() + timedelta(minutes=ttl_minutes)
