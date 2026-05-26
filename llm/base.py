"""
LLM Base — Abstract interface all LLM providers must implement.
Swapping providers = just changing which class you inject.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: str
    model: str
    tokens_used: int
    cached: bool = False
    provider: str = ""

    def __bool__(self) -> bool:
        return bool(self.content)


class BaseLLM(ABC):
    """
    Abstract base for all LLM providers.
    Every provider (Gemini, Groq) must implement these methods.
    """

    @property
    @abstractmethod
    def model_id(self) -> str:
        """The model identifier string."""
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The user prompt
            system: System instructions (optional)
            temperature: 0.0 = deterministic, 1.0 = creative
            max_tokens: Maximum tokens in response
            
        Returns:
            LLMResponse with content, model, and token usage
        """
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion token by token.
        Used for real-time dashboard output.

        NOTE: Must be implemented as an async generator (use 'yield').
        The yield below is intentional — it makes Python treat this base method
        as an async generator function so its type matches all subclass overrides.
        """
        raise NotImplementedError("stream() must be implemented by subclass")
        yield  # unreachable — exists only to set the async generator type

    def is_available(self) -> bool:
        """Returns True if the provider is configured and available."""
        return True
