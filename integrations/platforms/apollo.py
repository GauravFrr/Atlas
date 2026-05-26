"""Apollo.io — Lead sourcing API (Method 17)."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger


class ApolloClient:
    BASE_URL = "https://api.apollo.io/v1"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def search_people(
        self,
        niche: str,
        location: str,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        payload = {
            "q_keywords": niche,
            "person_locations": [location],
            "page": 1,
            "per_page": min(max(limit, 1), 25),
            "contact_email_status": ["verified", "guessed"],
        }
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/mixed_people/search",
                    json=payload,
                    headers=headers,
                )
        except Exception as e:
            logger.error(f"[Apollo] request failed: {e}")
            return []

        if resp.status_code != 200:
            logger.warning(f"[Apollo] HTTP {resp.status_code}: {resp.text[:300]}")
            return []

        data = resp.json()
        people = data.get("people") or data.get("contacts") or []
        logger.info(f"[Apollo] API returned {len(people)} people for {niche} @ {location}")
        return people[:limit]
