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
