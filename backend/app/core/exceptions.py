class ApplicationError(Exception):
    """Base exception whose internal detail must never be returned to clients."""

    error_code = "application_error"
    public_message = "No fue posible completar la solicitud."
    status_code = 500

    def __init__(self, internal_detail: str | None = None) -> None:
        super().__init__(internal_detail or self.error_code)


class AdminAuthenticationError(ApplicationError):
    error_code = "admin_authentication_failed"
    public_message = "Credenciales o sesión no válidas."
    status_code = 401


class AdminAuthorizationError(ApplicationError):
    error_code = "admin_forbidden"
    public_message = "No tienes permiso para esta operación."
    status_code = 403


class AdminUserNotFoundError(ApplicationError):
    error_code = "admin_user_not_found"
    public_message = "No se encontró el usuario."
    status_code = 404


class AdminRateLimitError(ApplicationError):
    error_code = "admin_login_limited"
    public_message = "Demasiados intentos. Inténtalo más tarde."
    status_code = 429


class AdminCsrfError(ApplicationError):
    error_code = "admin_csrf_invalid"
    public_message = "La solicitud no es válida."
    status_code = 403


class AdminTransportError(ApplicationError):
    error_code = "admin_https_required"
    public_message = "Se requiere una conexión segura."
    status_code = 403


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
    """Base exception for failures returned by the configured WhatsApp provider."""

    error_code = "whatsapp_service_unavailable"
    public_message = "El canal de WhatsApp no está disponible temporalmente."


class WhatsAppProviderTimeoutError(WhatsAppProviderError):
    """Raised when the WhatsApp provider exceeds the configured timeout."""


class WhatsAppProviderRateLimitError(WhatsAppProviderError):
    """Raised when the WhatsApp provider rejects a request due to rate limits."""


class WhatsAppProviderConnectionError(WhatsAppProviderError):
    """Raised when the WhatsApp provider cannot be reached."""


class WhatsAppProviderStatusError(WhatsAppProviderError):
    """Raised when the WhatsApp provider returns a failure response."""

    def __init__(
        self,
        internal_detail: str | None = None,
        *,
        provider_code: int | None = None,
        provider_subcode: int | None = None,
    ) -> None:
        super().__init__(internal_detail)
        self.provider_code = provider_code
        self.provider_subcode = provider_subcode


class WhatsAppProviderResponseError(WhatsAppProviderError):
    """Raised when a provider response has no usable message ID."""


class MessageProcessingError(ServiceUnavailableError):
    """Raised when an inbound message cannot complete the application flow."""

    error_code = "message_processing_failed"
    public_message = "No fue posible procesar el mensaje recibido."

    def __init__(
        self,
        internal_detail: str | None = None,
        *,
        source_error_code: str | None = None,
        provider_code: int | None = None,
        provider_subcode: int | None = None,
    ) -> None:
        super().__init__(internal_detail)
        self.source_error_code = source_error_code
        self.provider_code = provider_code
        self.provider_subcode = provider_subcode


class IdempotencyStoreError(ServiceUnavailableError):
    """Raised when the idempotency boundary cannot safely claim or retain an ID."""

    error_code = "idempotency_store_unavailable"
    public_message = "No fue posible verificar el estado del mensaje."


class BranchScopeMismatchError(InvalidRequestError):
    """Raised when installation data targets a different branch."""

    error_code = "branch_scope_mismatch"
    public_message = "El perfil no corresponde a esta instalación."


class BranchNotConfiguredError(ServiceUnavailableError):
    """Raised when the configured branch is absent or inactive."""

    error_code = "branch_not_configured"
    public_message = "La información de la sucursal no está configurada."


class CommercialQueryInputError(InvalidRequestError):
    """Raised when a read-only commercial query has invalid arguments."""

    error_code = "commercial_query_invalid"
    public_message = "La consulta comercial no es válida."


class ProductNotFoundError(ApplicationError):
    """Raised when no active product exists inside the configured branch."""

    error_code = "product_not_found"
    public_message = "No encontramos ese producto en esta sucursal."
    status_code = 404


class ProductPriceNotFoundError(ApplicationError):
    """Raised when a scoped product has no current price for the requested unit."""

    error_code = "product_price_not_found"
    public_message = "No encontramos un precio vigente para ese producto y unidad."
    status_code = 404


class FAQSourceError(ServiceUnavailableError):
    """Raised when the configured FAQ source cannot be used safely."""

    error_code = "faq_source_unavailable"
    public_message = "La información FAQ no está disponible temporalmente."


class FAQQueryInputError(InvalidRequestError):
    """Raised when an FAQ search query has an invalid format."""

    error_code = "faq_query_invalid"
    public_message = "La consulta FAQ no es válida."


class ToolExecutionTimeoutError(ServiceUnavailableError):
    """Raised when a scoped tool exceeds its backend execution budget."""

    error_code = "tool_execution_timeout"
    public_message = "La consulta tardó demasiado. Inténtalo de nuevo."
