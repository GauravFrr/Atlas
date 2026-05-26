"""
Custom exception hierarchy for Agent-Earns.
All exceptions trace back here — never use bare Exception.
"""


# ══════════════════════════════════════════════
# BASE
# ══════════════════════════════════════════════

class AgentBaseError(Exception):
    """Root exception for all Agent-Earns errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ══════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════

class ConfigurationError(AgentBaseError):
    """Missing or invalid configuration (env vars, API keys)."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """A required API key is not set."""
    def __init__(self, key_name: str):
        super().__init__(f"Required API key not set: {key_name}", {"key": key_name})


# ══════════════════════════════════════════════
# LLM ERRORS
# ══════════════════════════════════════════════

class LLMError(AgentBaseError):
    """Base LLM error."""
    pass


class LLMRateLimitError(LLMError):
    """LLM rate limit hit — triggers fallback."""
    def __init__(self, model: str, retry_after: int = 60):
        super().__init__(
            f"Rate limit hit for {model}. Retry after {retry_after}s",
            {"model": model, "retry_after": retry_after}
        )
        self.retry_after = retry_after


class LLMResponseError(LLMError):
    """LLM returned an invalid or unparseable response."""
    def __init__(self, model: str, reason: str):
        super().__init__(
            f"Invalid response from {model}: {reason}",
            {"model": model, "reason": reason}
        )


class LLMAllFailedError(LLMError):
    """All LLM providers failed — FATAL."""
    pass


class LLMHallucinationError(LLMError):
    """LLM response failed validation checks."""
    pass


# ══════════════════════════════════════════════
# DATABASE ERRORS
# ══════════════════════════════════════════════

class DatabaseError(AgentBaseError):
    """Base database error."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Cannot connect to database — triggers retry loop."""
    pass


class RecordNotFoundError(DatabaseError):
    """Requested record does not exist."""
    def __init__(self, model: str, record_id: str):
        super().__init__(
            f"{model} with id={record_id} not found",
            {"model": model, "id": record_id}
        )


class DuplicateRecordError(DatabaseError):
    """Record already exists (unique constraint)."""
    pass


# ══════════════════════════════════════════════
# INTEGRATION ERRORS
# ══════════════════════════════════════════════

class IntegrationError(AgentBaseError):
    """Base error for third-party API integrations."""
    def __init__(self, service: str, message: str, status_code: int | None = None):
        super().__init__(
            f"[{service}] {message}",
            {"service": service, "status_code": status_code}
        )
        self.service = service
        self.status_code = status_code


class RateLimitError(IntegrationError):
    """API rate limit hit — triggers back-off."""
    def __init__(self, service: str, retry_after: int = 60):
        super().__init__(service, f"Rate limited. Retry after {retry_after}s")
        self.retry_after = retry_after


class AuthenticationError(IntegrationError):
    """API authentication failed — API key invalid/expired."""
    pass


class ServiceUnavailableError(IntegrationError):
    """External service is down — triggers circuit breaker."""
    pass


# ══════════════════════════════════════════════
# EMAIL ERRORS
# ══════════════════════════════════════════════

class EmailError(AgentBaseError):
    """Base email error."""
    pass


class EmailQualityGateError(EmailError):
    """Email failed quality gate checks before sending."""
    def __init__(self, reason: str, scores: dict):
        super().__init__(f"Email quality gate failed: {reason}", {"scores": scores})


class EmailSendError(EmailError):
    """Failed to send email via provider."""
    pass


class EmailBounceRateError(EmailError):
    """Bounce rate exceeded threshold — CRITICAL, pause sending."""
    def __init__(self, current_rate: float, threshold: float):
        super().__init__(
            f"Bounce rate {current_rate:.1%} exceeds threshold {threshold:.1%}",
            {"current_rate": current_rate, "threshold": threshold}
        )


# ══════════════════════════════════════════════
# PAYMENT ERRORS
# ══════════════════════════════════════════════

class PaymentError(AgentBaseError):
    """Base payment error."""
    pass


class PaymentWebhookError(PaymentError):
    """Webhook validation failed — CRITICAL."""
    pass


class PaymentVerificationError(PaymentError):
    """Payment could not be verified — alert human."""
    pass


# ══════════════════════════════════════════════
# QUALITY CONTROL ERRORS
# ══════════════════════════════════════════════

class QualityError(AgentBaseError):
    """Base quality control error."""
    pass


class QualityScoreTooLowError(QualityError):
    """Deliverable quality score too low after max regeneration attempts."""
    def __init__(self, score: float, threshold: float, attempts: int):
        super().__init__(
            f"Quality score {score:.1f} below {threshold:.1f} after {attempts} attempts",
            {"score": score, "threshold": threshold, "attempts": attempts}
        )


# ══════════════════════════════════════════════
# SCRAPING ERRORS
# ══════════════════════════════════════════════

class ScrapingError(AgentBaseError):
    """Base scraping/web automation error."""
    pass


class ScrapingBlockedError(ScrapingError):
    """IP/bot was blocked by target site."""
    pass


# ══════════════════════════════════════════════
# LEAD FINDER ERRORS
# ══════════════════════════════════════════════

class LeadFinderError(AgentBaseError):
    """Base lead finder error."""
    pass


class NoLeadsFoundError(LeadFinderError):
    """Lead source returned no results."""
    pass


# ══════════════════════════════════════════════
# SECURITY ERRORS
# ══════════════════════════════════════════════

class SecurityError(AgentBaseError):
    """Base security error — always logs and alerts."""
    pass


class ConstitutionViolationError(SecurityError):
    """Agent attempted a FORBIDDEN action — FATAL."""
    def __init__(self, action: str):
        super().__init__(
            f"CONSTITUTION VIOLATION: Attempted forbidden action: {action}",
            {"action": action}
        )


class UnauthorizedAccessError(SecurityError):
    """Unauthorized dashboard access attempt."""
    pass
