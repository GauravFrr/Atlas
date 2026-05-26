"""
Gemini 2.5 Pro Provider — For complex tasks requiring best reasoning.
Uses the new google-genai SDK (google.generativeai is deprecated).
Use for: website copy, strategy, self-improvement, quality work.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

from llm.base import BaseLLM, LLMResponse
from constants import LLMModel
from exceptions import LLMRateLimitError, LLMResponseError

if TYPE_CHECKING:
    from google import genai as genai_types


class GeminiPro(BaseLLM):
    """
    Google Gemini 2.5 Pro — Best for complex reasoning and quality output.
    Free tier: 500 requests/day via Google AI Studio.
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
        return LLMModel.GEMINI_PRO

    @property
    def provider_name(self) -> str:
        return "Google Gemini 2.5 Pro"

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Generate a completion using Gemini 2.5 Pro."""
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
                raise LLMResponseError(self.model_id, "Empty response from Gemini Pro")

            # Token usage from new SDK
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
        """Stream Gemini Pro response via new SDK."""
        try:
            client = self._get_client()
            config = self._make_config(system, temperature, max_tokens=8192)

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
