"""Listen Notes — Podcast discovery API (Method 16)."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger


class ListenNotesClient:
    BASE_URL = "https://listen-api.listennotes.com/api/v2"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def search_podcasts(self, query: str, language: str = "English", limit: int = 20) -> list[dict[str, Any]]:
        if not self.api_key:
            return []
        headers = {"X-ListenAPI-Key": self.api_key}
        params = {"q": query, "type": "podcast", "language": language, "page_size": min(limit, 10)}
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/search",
                    params=params,
                    headers=headers,
                )
                if resp.status_code != 200:
                    logger.warning(f"[ListenNotes] {resp.status_code}: {resp.text[:200]}")
                    return []
                return resp.json().get("results", []) or []
        except Exception as e:
            logger.error(f"[ListenNotes] {e}")
            return []
