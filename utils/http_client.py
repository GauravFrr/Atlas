"""
Async HTTP Client — httpx with retry, timeout, and caching.
All outbound HTTP requests go through this client.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from exceptions import ServiceUnavailableError, RateLimitError


class AsyncHTTPClient:
    """
    Shared async HTTP client with:
    - Connection pooling
    - Automatic retry with exponential backoff
    - Response caching (optional)
    - Rate limit detection
    - Timeout configuration
    
    Usage:
        client = AsyncHTTPClient()
        data = await client.get("https://api.example.com/endpoint")
        result = await client.post("https://api.example.com/data", json={"key": "value"})
    """

    def __init__(
        self,
        timeout: float = 30.0,
        cache_ttl_minutes: int = 0,  # 0 = no caching
    ):
        self._timeout = httpx.Timeout(timeout)
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes) if cache_ttl_minutes else None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily creates and returns the shared client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/html, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        use_cache: bool = False,
    ) -> dict | str:
        """GET request with optional caching."""
        cache_key = self._make_cache_key(url, params)

        if use_cache and self._cache_ttl:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        client = await self._get_client()

        try:
            response = await client.get(url, params=params, headers=headers)
            self._handle_error_status(response, url)
            result = self._parse_response(response)

            if use_cache and self._cache_ttl:
                self._set_cached(cache_key, result)

            return result

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"HTTP GET failed ({url}): {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True,
    )
    async def post(
        self,
        url: str,
        json: dict | None = None,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> dict | str:
        """POST request with retry."""
        client = await self._get_client()

        try:
            response = await client.post(url, json=json, data=data, headers=headers)
            self._handle_error_status(response, url)
            return self._parse_response(response)

        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"HTTP POST failed ({url}): {e}")
            raise

    def _handle_error_status(self, response: httpx.Response, url: str) -> None:
        """Handles HTTP error status codes."""
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise RateLimitError("http", retry_after=retry_after)

        if response.status_code >= 500:
            raise ServiceUnavailableError("http", f"Server error {response.status_code}: {url}")

        if response.status_code == 401:
            from exceptions import AuthenticationError
            raise AuthenticationError("http", f"Authentication failed for {url}")

        response.raise_for_status()

    def _parse_response(self, response: httpx.Response) -> dict | str:
        """Parse response as JSON if possible, otherwise return text."""
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def _make_cache_key(self, url: str, params: dict | None) -> str:
        raw = f"{url}:{json.dumps(params, sort_keys=True) if params else ''}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _get_cached(self, key: str) -> Any | None:
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.now() < expires_at:
                return value
            del self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any) -> None:
        if self._cache_ttl:
            self._cache[key] = (value, datetime.now() + self._cache_ttl)

    async def close(self) -> None:
        """Close the underlying client."""
        if self._client:
            await self._client.aclose()
