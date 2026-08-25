class ApplicationError(Exception):
    """Base exception whose internal detail must never be returned to clients."""

    error_code = "application_error"
    public_message = "No fue posible completar la solicitud."
    status_code = 500

    def __init__(self, internal_detail: str | None = None) -> None:
        super().__init__(internal_detail or self.error_code)


class ServiceUnavailableError(ApplicationError):
    """Raised when an application dependency is temporarily unavailable."""

    error_code = "service_unavailable"
    public_message = "El servicio no está disponible temporalmente."
    status_code = 503


class InvalidRequestError(ApplicationError):
    """Raised when application-level input validation rejects a request."""

    error_code = "invalid_request"
    public_message = "La solicitud no es válida."
    status_code = 422


class AIProviderError(ServiceUnavailableError):
    """Base exception for failures returned by the configured AI provider."""

    error_code = "ai_service_unavailable"
    public_message = "El asistente no está disponible temporalmente."


class AIProviderTimeoutError(AIProviderError):
    """Raised when the AI provider exceeds the configured timeout."""


class AIProviderRateLimitError(AIProviderError):
    """Raised when the AI provider rejects a request due to rate limits."""


class AIProviderConnectionError(AIProviderError):
    """Raised when the AI provider cannot be reached."""


class AIProviderStatusError(AIProviderError):
    """Raised when the AI provider returns a non-success HTTP status."""


class AIProviderResponseError(AIProviderError):
    """Raised when the AI provider response has no usable text output."""
