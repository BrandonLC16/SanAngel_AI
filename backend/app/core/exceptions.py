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


class WhatsAppClientInputError(InvalidRequestError):
    """Raised when an outbound WhatsApp message violates client-side validation."""


class WhatsAppClientConfigurationError(ServiceUnavailableError):
    """Raised when required backend-only WhatsApp configuration is absent."""


class WhatsAppProviderError(ServiceUnavailableError):
    """Base exception for failures returned by Meta's Graph API."""

    error_code = "whatsapp_service_unavailable"
    public_message = "El canal de WhatsApp no está disponible temporalmente."


class WhatsAppProviderTimeoutError(WhatsAppProviderError):
    """Raised when Graph API exceeds the configured timeout."""


class WhatsAppProviderRateLimitError(WhatsAppProviderError):
    """Raised when Graph API rejects a request due to rate limits."""


class WhatsAppProviderConnectionError(WhatsAppProviderError):
    """Raised when Graph API cannot be reached."""


class WhatsAppProviderStatusError(WhatsAppProviderError):
    """Raised when Graph API returns a non-success HTTP status."""


class WhatsAppProviderResponseError(WhatsAppProviderError):
    """Raised when a successful Graph API response has no usable message ID."""


class MessageProcessingError(ServiceUnavailableError):
    """Raised when an inbound message cannot complete the application flow."""

    error_code = "message_processing_failed"
    public_message = "No fue posible procesar el mensaje recibido."


class IdempotencyStoreError(ServiceUnavailableError):
    """Raised when the idempotency boundary cannot safely claim or retain an ID."""

    error_code = "idempotency_store_unavailable"
    public_message = "No fue posible verificar el estado del mensaje."
