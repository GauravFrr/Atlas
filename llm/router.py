"""
LLM Router — Smart model selector with automatic fallback chain.

Task complexity → Model selection:
  CRITICAL  → Gemini 2.5 Pro
  STANDARD  → Gemini 2.0 Flash
  SIMPLE    → Gemini 2.0 Flash Lite
  FALLBACK  → Groq Llama 3.3 70B
  FASTEST   → Groq Llama 3.1 8B

If primary model fails → auto-fallback to next in chain.
"""

from loguru import logger

from llm.base import BaseLLM, LLMResponse
from constants import LLMModel, TaskComplexity
from config import Settings
from exceptions import LLMAllFailedError, LLMRateLimitError


# Task type → complexity mapping
TASK_COMPLEXITY_MAP: dict[str, str] = {
    # CRITICAL — Gemini Pro
    "write_website_copy": TaskComplexity.CRITICAL,
    "write_about_page": TaskComplexity.CRITICAL,
    "generate_hero_section": TaskComplexity.CRITICAL,
    "strategy_update": TaskComplexity.CRITICAL,
    "weekly_self_improvement": TaskComplexity.CRITICAL,
    "score_design_quality": TaskComplexity.CRITICAL,
    "write_chatbot_personality": TaskComplexity.CRITICAL,
    "write_case_study": TaskComplexity.CRITICAL,
    "write_pitch_deck": TaskComplexity.CRITICAL,
    "write_linkedin_profile": TaskComplexity.CRITICAL,
    "write_youtube_script": TaskComplexity.CRITICAL,
    "write_full_article": TaskComplexity.CRITICAL,
    "generate_demo_site": TaskComplexity.CRITICAL,
    "generate_demo_copy": TaskComplexity.STANDARD,

    # STANDARD — Gemini Flash
    "write_followup_email": TaskComplexity.STANDARD,
    "draft_reply": TaskComplexity.STANDARD,
    "score_lead": TaskComplexity.STANDARD,
    "write_social_posts": TaskComplexity.STANDARD,
    "write_ad_copy": TaskComplexity.STANDARD,
    "write_blog_post": TaskComplexity.STANDARD,
    "generate_subject_lines": TaskComplexity.STANDARD,
    "extract_faq": TaskComplexity.STANDARD,
    "generate_email_sequence": TaskComplexity.STANDARD,

    # SIMPLE — Flash Lite
    "classify_reply": TaskComplexity.SIMPLE,
    "check_spam_score": TaskComplexity.SIMPLE,
    "detect_business_problem": TaskComplexity.SIMPLE,
    "validate_email_quality": TaskComplexity.SIMPLE,
    "classify_niche": TaskComplexity.SIMPLE,

    # FALLBACK / FASTEST — Groq Llama 3.3 70B
    "write_cold_email": TaskComplexity.FALLBACK,
}


class LLMRouter:
    """
    Routes tasks to the appropriate LLM model.
    Handles rate limiting with automatic fallback.
    
    Usage:
        router = LLMRouter(settings)
        response = await router.complete(
            task_type="write_cold_email",
            prompt="Write an email for...",
            system="You are..."
        )
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._providers: dict[str, BaseLLM] = {}
        self._circuit_breakers: dict[str, int] = {}  # model -> consecutive failures
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize all available LLM providers."""
        if self.settings.has_gemini:
            try:
                from llm.providers.gemini_pro import GeminiPro
                from llm.providers.gemini_flash import GeminiFlash
                self._providers[TaskComplexity.CRITICAL] = GeminiPro(self.settings.gemini_api_key)
                self._providers[TaskComplexity.STANDARD] = GeminiFlash(self.settings.gemini_api_key)
                self._providers[TaskComplexity.SIMPLE] = GeminiFlash(self.settings.gemini_api_key)
                logger.info("Gemini providers initialized (Pro + Flash)")
            except ImportError:
                logger.warning("google-generativeai not installed. Run: pip install google-generativeai")

        if self.settings.has_groq:
            try:
                from llm.providers.groq_70b import Groq70B
                self._providers[TaskComplexity.FALLBACK] = Groq70B(self.settings.groq_api_key)
                logger.info("Groq provider initialized (Llama 3.3 70B)")
            except ImportError:
                logger.warning("groq not installed. Run: pip install groq")

        if not self._providers:
            logger.error("NO LLM PROVIDERS AVAILABLE. Set GEMINI_API_KEY or GROQ_API_KEY")

    def get_complexity(self, task_type: str) -> str:
        """Determine complexity level for a task type."""
        return TASK_COMPLEXITY_MAP.get(task_type, TaskComplexity.STANDARD)

    def _get_fallback_chain(self, complexity: str) -> list[str]:
        """Returns ordered list of complexity levels to try."""
        chains = {
            TaskComplexity.CRITICAL: [TaskComplexity.CRITICAL, TaskComplexity.STANDARD, TaskComplexity.FALLBACK],
            TaskComplexity.STANDARD: [TaskComplexity.STANDARD, TaskComplexity.CRITICAL, TaskComplexity.FALLBACK],
            TaskComplexity.SIMPLE:   [TaskComplexity.SIMPLE, TaskComplexity.STANDARD, TaskComplexity.FALLBACK],
            TaskComplexity.FALLBACK: [TaskComplexity.FALLBACK],
            TaskComplexity.FASTEST:  [TaskComplexity.FALLBACK],
        }
        return chains.get(complexity, [TaskComplexity.STANDARD, TaskComplexity.FALLBACK])

    async def complete(
        self,
        prompt: str,
        task_type: str = "generic",
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Route task to appropriate model, with automatic fallback.
        
        Args:
            prompt: The prompt to complete
            task_type: Task identifier for routing (see TASK_COMPLEXITY_MAP)
            system: System instructions
            temperature: Creativity level
            max_tokens: Max response tokens
        """
        complexity = self.get_complexity(task_type)
        fallback_chain = self._get_fallback_chain(complexity)
        last_error = None

        for level in fallback_chain:
            provider = self._providers.get(level)
            if not provider:
                continue

            # Skip if circuit breaker tripped (3+ consecutive failures)
            if self._circuit_breakers.get(level, 0) >= 3:
                logger.warning(f"Circuit breaker open for {level}, skipping")
                continue

            try:
                logger.debug(f"LLM call: task={task_type} model={provider.model_id}")
                response = await provider.complete(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Reset circuit breaker on success
                self._circuit_breakers[level] = 0

                if level != self.get_complexity(task_type):
                    logger.info(f"Used fallback provider: {provider.provider_name}")

                return response

            except LLMRateLimitError as e:
                logger.warning(f"{provider.provider_name} rate limited. Trying fallback...")
                self._circuit_breakers[level] = self._circuit_breakers.get(level, 0) + 1
                last_error = e
                continue

            except Exception as e:
                logger.error(f"{provider.provider_name} failed: {e}")
                self._circuit_breakers[level] = self._circuit_breakers.get(level, 0) + 1
                last_error = e
                continue

        raise LLMAllFailedError(
            f"All LLM providers failed for task '{task_type}'. Last error: {last_error}"
        )

    def get_provider_status(self) -> dict:
        """Returns status of all providers (for health check)."""
        return {
            level: {
                "provider": provider.provider_name,
                "model": provider.model_id,
                "circuit_breaker_failures": self._circuit_breakers.get(level, 0),
                "available": self._circuit_breakers.get(level, 0) < 3,
            }
            for level, provider in self._providers.items()
        }
