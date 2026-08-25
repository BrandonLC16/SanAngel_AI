from fastapi import Request
from fastapi.responses import JSONResponse

from backend.app.core.exceptions import ApplicationError

REQUEST_ID_HEADER = "X-Request-ID"


def create_error_response(
    request: Request,
    *,
    status_code: int,
    error_code: str,
    public_message: str,
) -> JSONResponse:
    """Build a stable error response without exposing internal exception details."""

    request_id = request.state.request_id
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": public_message,
            },
            "request_id": request_id,
        },
        headers={REQUEST_ID_HEADER: request_id},
    )


async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """Map an internal application exception to its fixed public representation."""

    request.state.error_category = exc.error_code
    return create_error_response(
        request,
        status_code=exc.status_code,
        error_code=exc.error_code,
        public_message=exc.public_message,
    )
