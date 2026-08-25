import asyncio
import logging
import re

import httpx
import pytest
from fastapi import FastAPI

from backend.app.core.config import HttpSettings
from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.core.logging import HTTP_LOGGER_NAME
from backend.app.main import create_app


def make_http_settings() -> HttpSettings:
    return HttpSettings(
        app_env="testing",
        cors_allowed_origins=("https://panel.example.com",),
        log_level="INFO",
        _env_file=None,
    )


async def send_request(
    application: FastAPI,
    method: str,
    path: str,
    **kwargs: object,
) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.request(method, path, **kwargs)


def test_request_id_is_propagated_and_logs_exclude_sensitive_request_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = create_app(make_http_settings())
    request_id = "request-123"
    body_marker = "private-body-marker"
    authorization_marker = "private-authorization-marker"
    query_marker = "private-query-marker"

    @application.post("/logging-check")
    async def logging_check() -> dict[str, bool]:
        return {"ok": True}

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(
            send_request(
                application,
                "POST",
                f"/logging-check?query={query_marker}",
                headers={
                    "Authorization": f"Bearer {authorization_marker}",
                    "X-Request-ID": request_id,
                },
                content=body_marker,
            )
        )

    log_output = caplog.text
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert f"request_id={request_id}" in log_output
    assert "method=POST" in log_output
    assert "endpoint=/logging-check" in log_output
    assert "status_code=200" in log_output
    assert body_marker not in log_output
    assert authorization_marker not in log_output
    assert query_marker not in log_output
    assert "Authorization" not in log_output


def test_missing_or_unsafe_request_id_is_replaced() -> None:
    application = create_app(make_http_settings())

    missing_response = asyncio.run(send_request(application, "GET", "/health"))
    unsafe_response = asyncio.run(
        send_request(
            application,
            "GET",
            "/health",
            headers={"X-Request-ID": "unsafe request id"},
        )
    )

    assert re.fullmatch(r"[0-9a-f]{32}", missing_response.headers["X-Request-ID"])
    assert re.fullmatch(r"[0-9a-f]{32}", unsafe_response.headers["X-Request-ID"])


def test_application_error_maps_to_fixed_safe_response() -> None:
    application = create_app(make_http_settings())
    internal_marker = "private-provider-detail"

    @application.get("/application-error")
    async def application_error() -> None:
        raise ServiceUnavailableError(internal_marker)

    response = asyncio.run(
        send_request(
            application,
            "GET",
            "/application-error",
            headers={"X-Request-ID": "application-error-id"},
        )
    )

    assert response.status_code == 503
    assert response.headers["X-Request-ID"] == "application-error-id"
    assert response.json() == {
        "error": {
            "code": "service_unavailable",
            "message": "El servicio no está disponible temporalmente.",
        },
        "request_id": "application-error-id",
    }
    assert internal_marker not in response.text
    assert "Traceback" not in response.text


def test_unhandled_error_returns_generic_response_and_safe_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = create_app(make_http_settings())
    internal_marker = "private-unhandled-detail"

    @application.get("/unexpected-error")
    async def unexpected_error() -> None:
        raise RuntimeError(internal_marker)

    with caplog.at_level(logging.ERROR, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(
            send_request(
                application,
                "GET",
                "/unexpected-error",
                headers={
                    "Origin": "https://panel.example.com",
                    "X-Request-ID": "unexpected-error-id",
                },
            )
        )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "unexpected-error-id"
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Ocurrió un error interno.",
        },
        "request_id": "unexpected-error-id",
    }
    assert internal_marker not in response.text
    assert internal_marker not in caplog.text
    assert "Traceback" not in response.text
    assert "error_category=unhandled_exception" in caplog.text
    assert response.headers["access-control-allow-origin"] == "https://panel.example.com"


def test_cors_allows_only_configured_origin_and_exposes_request_id() -> None:
    application = create_app(make_http_settings())

    allowed_response = asyncio.run(
        send_request(
            application,
            "GET",
            "/health",
            headers={"Origin": "https://panel.example.com"},
        )
    )
    denied_response = asyncio.run(
        send_request(
            application,
            "GET",
            "/health",
            headers={"Origin": "https://attacker.example.com"},
        )
    )

    assert allowed_response.headers["access-control-allow-origin"] == ("https://panel.example.com")
    assert allowed_response.headers["access-control-expose-headers"] == "X-Request-ID"
    assert "access-control-allow-origin" not in denied_response.headers


def test_cors_preflight_uses_explicit_method_and_header_allowlists() -> None:
    application = create_app(make_http_settings())

    response = asyncio.run(
        send_request(
            application,
            "OPTIONS",
            "/health",
            headers={
                "Origin": "https://panel.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Authorization,X-Request-ID",
            },
        )
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://panel.example.com"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "Authorization" in response.headers["access-control-allow-headers"]
    assert "X-Request-ID" in response.headers["access-control-allow-headers"]
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])
