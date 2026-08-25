from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.errors import REQUEST_ID_HEADER, application_error_handler
from backend.app.api.middleware import request_context_middleware, safe_exception_middleware
from backend.app.api.routes.health import router as health_router
from backend.app.core.config import HttpSettings, get_http_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.core.logging import configure_logging


def create_app(settings: HttpSettings | None = None) -> FastAPI:
    """Create the HTTP application with safe cross-cutting middleware."""

    http_settings = settings or get_http_settings()
    configure_logging(http_settings.log_level)

    application = FastAPI(title=http_settings.app_name)
    application.add_exception_handler(ApplicationError, application_error_handler)
    application.middleware("http")(safe_exception_middleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(http_settings.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    application.middleware("http")(request_context_middleware)
    application.include_router(health_router)
    return application


app = create_app()
