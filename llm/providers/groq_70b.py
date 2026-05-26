"""
Groq Llama 3.3 70B Provider — Ultra-fast fallback.
Use for: when Gemini is rate-limited or down.
Free tier: 14,400 requests/day at 6000 tokens/min.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator

from llm.base import BaseLLM, LLMResponse
from constants import LLMModel
from exceptions import LLMRateLimitError, LLMResponseError

# Only resolved at type-check time — gives Pylance full method signatures
# without requiring groq to be installed for the import to succeed at runtime.
if TYPE_CHECKING:
    from groq import AsyncGroq


class Groq70B(BaseLLM):
    """Groq Llama 3.3 70B — Ultra-fast fallback with strong quality."""

    # Class-level annotation lets Pylance resolve .chat.completions.create()
    _client: "AsyncGroq"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        try:
            from groq import AsyncGroq  # noqa: F811  (shadows TYPE_CHECKING import intentionally)
            self._client = AsyncGroq(api_key=api_key, timeout=30.0)
        except ImportError as exc:
            raise ImportError("groq not installed. Run: pip install groq") from exc

    @property
    def model_id(self) -> str:
        return LLMModel.GROQ_70B

    @property
    def provider_name(self) -> str:
        return "Groq Llama 3.3 70B"

    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        try:
            messages: list[Any] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content: str = response.choices[0].message.content or ""
            if not content:
                raise LLMResponseError(self.model_id, "Empty response from Groq")

            tokens: int = response.usage.total_tokens if response.usage else 0

            return LLMResponse(
                content=content,
                model=self.model_id,
                tokens_used=tokens,
                provider=self.provider_name,
            )

        except (LLMRateLimitError, LLMResponseError):
            raise  # Never re-wrap our own exceptions
        except Exception as exc:
            msg = str(exc).lower()
            if "rate" in msg or "429" in msg or "too many" in msg:
                raise LLMRateLimitError(self.model_id) from exc
            raise LLMResponseError(self.model_id, str(exc)) from exc

    async def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream via create(stream=True) — AsyncStream supports async for."""
        try:
            messages: list[Any] = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            stream = await self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except (LLMRateLimitError, LLMResponseError):
            raise
        except Exception as exc:
            msg = str(exc).lower()
            if "rate" in msg or "429" in msg:
                raise LLMRateLimitError(self.model_id) from exc
            raise LLMResponseError(self.model_id, str(exc)) from exc

    def is_available(self) -> bool:
        return bool(self._api_key)
