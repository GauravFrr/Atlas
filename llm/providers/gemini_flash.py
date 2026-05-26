"""
Gemini 2.0 Flash Provider — For fast bulk tasks.
Uses the new google-genai SDK (google.generativeai is deprecated).
Use for: cold emails, social posts, reply drafting, lead scoring.
"""

from __future__ import annotations

from typing import AsyncGenerator

from llm.base import BaseLLM, LLMResponse
from constants import LLMModel
from exceptions import LLMRateLimitError, LLMResponseError


class GeminiFlash(BaseLLM):
    """
    Google Gemini 2.0 Flash — Fast and capable for bulk operations.
    Free tier: 1500 requests/day via Google AI Studio.
    Uses new google-genai SDK (client.aio.models.generate_content).
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        try:
            from google import genai  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "google-genai not installed. Run: pip install google-genai"
            ) from exc

    def _get_client(self):  # type: ignore[return]
        from google import genai
        return genai.Client(api_key=self._api_key)

    def _make_config(self, system: str, temperature: float, max_tokens: int):  # type: ignore[return]
        from google.genai import types
        return types.GenerateContentConfig(
            system_instruction=system if system else None,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    @property
    def model_id(self) -> str:
        return LLMModel.GEMINI_FLASH

    @property
    def provider_name(self) -> str:
        return "Google Gemini 2.0 Flash"

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        try:
            client = self._get_client()
            config = self._make_config(system, temperature, max_tokens)

            response = await client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=config,
            )

            try:
                text: str = response.text or ""
            except (ValueError, AttributeError) as ve:
                raise LLMResponseError(
                    self.model_id, f"Safety filter blocked response: {ve}"
                ) from ve

            if not text:
                raise LLMResponseError(self.model_id, "Empty response from Gemini Flash")

            usage = getattr(response, "usage_metadata", None)
            total_tokens: int = 0
            if usage:
                total_tokens = (
                    getattr(usage, "total_token_count", None)
                    or getattr(usage, "candidates_token_count", 0)
                    + getattr(usage, "prompt_token_count", 0)
                )

            return LLMResponse(
                content=text,
                model=self.model_id,
                tokens_used=total_tokens,
                provider=self.provider_name,
            )

        except (LLMRateLimitError, LLMResponseError):
            raise
        except Exception as exc:
            msg = str(exc).lower()
            if "rate" in msg or "429" in msg or "quota" in msg or "resource_exhausted" in msg:
                raise LLMRateLimitError(self.model_id) from exc
            raise LLMResponseError(self.model_id, str(exc)) from exc

    async def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream Flash response via new SDK."""
        try:
            client = self._get_client()
            config = self._make_config(system, temperature, max_tokens=4096)

            async for chunk in await client.aio.models.generate_content_stream(
                model=self.model_id,
                contents=prompt,
                config=config,
            ):
                try:
                    chunk_text = chunk.text
                    if chunk_text:
                        yield chunk_text
                except (ValueError, AttributeError):
                    continue

        except (LLMRateLimitError, LLMResponseError):
            raise
        except Exception as exc:
            msg = str(exc).lower()
            if "rate" in msg or "429" in msg or "quota" in msg or "resource_exhausted" in msg:
                raise LLMRateLimitError(self.model_id) from exc
            raise LLMResponseError(self.model_id, str(exc)) from exc

    def is_available(self) -> bool:
        return bool(self._api_key)
