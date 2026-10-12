import asyncio
from pathlib import Path

import httpx
import pytest
from fastapi import Request
from pydantic import ValidationError

from backend.app.core.config import HttpSettings
from backend.app.main import create_app
from scripts.run_backend import server_config


async def _request(
    *,
    scheme: str = "http",
    peer: str = "127.0.0.1",
    headers: list[tuple[str, str]] | None = None,
    path: str = "/health",
) -> httpx.Response:
    app = create_app(
        HttpSettings(app_env="production", trusted_proxy_ips=("127.0.0.1",), _env_file=None)
    )

    @app.get("/test-peer")
    async def test_peer(request: Request) -> dict[str, str]:
        return {"peer": request.client.host, "scheme": request.url.scheme}

    transport = httpx.ASGITransport(app=app, client=(peer, 12345))
    async with httpx.AsyncClient(transport=transport, base_url=f"{scheme}://testserver") as client:
        return await client.get(path, headers=headers)


def test_production_rejects_plain_http_without_redirecting_webhook() -> None:
    response = asyncio.run(_request())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "https_required"
    assert "location" not in response.headers
    assert "strict-transport-security" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_plain_http_webhook_is_rejected_before_reading_body() -> None:
    class UnreadableBody(httpx.AsyncByteStream):
        async def __aiter__(self):  # type: ignore[override]
            raise AssertionError("insecure webhook body was read")
            yield b""  # pragma: no cover

    app = create_app(HttpSettings(app_env="production", _env_file=None))

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post("/api/v1/whatsapp/webhook", content=UnreadableBody())

    response = asyncio.run(send())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "https_required"
    assert "location" not in response.headers


def test_direct_tls_and_trusted_proxy_https_are_accepted() -> None:
    direct = asyncio.run(_request(scheme="https", peer="198.51.100.10"))
    proxied = asyncio.run(
        _request(
            headers=[
                ("X-Forwarded-Proto", "https"),
                ("X-Forwarded-For", "203.0.113.7"),
                ("X-Forwarded-Host", "attacker.example"),
                ("Forwarded", "proto=http;host=attacker.example"),
            ],
            path="/test-peer",
        )
    )

    assert direct.status_code == 200
    assert proxied.status_code == 200
    assert proxied.json() == {"peer": "127.0.0.1", "scheme": "https"}
    assert proxied.headers["strict-transport-security"] == "max-age=31536000"


@pytest.mark.parametrize(
    ("peer", "headers"),
    [
        ("198.51.100.10", [("X-Forwarded-Proto", "https")]),
        ("127.0.0.1", [("X-Forwarded-Proto", "http")]),
        ("127.0.0.1", [("X-Forwarded-Proto", "https,http")]),
        ("127.0.0.1", [("X-Forwarded-Proto", "HTTPS")]),
        (
            "127.0.0.1",
            [("X-Forwarded-Proto", "https"), ("X-Forwarded-Proto", "https")],
        ),
        ("127.0.0.1", [("Forwarded", "proto=https")]),
    ],
)
def test_spoofed_or_ambiguous_forwarded_headers_do_not_grant_https(
    peer: str, headers: list[tuple[str, str]]
) -> None:
    response = asyncio.run(_request(peer=peer, headers=headers))
    assert response.status_code == 403
    assert "strict-transport-security" not in response.headers


def test_admin_api_responses_are_not_cached() -> None:
    response = asyncio.run(
        _request(headers=[("X-Forwarded-Proto", "https")], path="/api/v1/admin/auth/session")
    )
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


def test_outer_error_response_keeps_security_headers() -> None:
    app = create_app(HttpSettings(app_env="production", _env_file=None))
    app.state.resource_limits = None

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
            return await client.get("/api/v1/chat")

    response = asyncio.run(send())
    assert response.status_code == 500
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["strict-transport-security"] == "max-age=31536000"


def test_trusted_proxy_configuration_accepts_only_exact_unicast_ips() -> None:
    settings = HttpSettings(trusted_proxy_ips="127.0.0.1,::1", _env_file=None)
    assert settings.trusted_proxy_ips == ("127.0.0.1", "::1")
    for bad in ("0.0.0.0", "10.0.0.0/8", "*", "127.0.0.1,127.0.0.1", "bad"):
        with pytest.raises(ValidationError):
            HttpSettings(trusted_proxy_ips=bad, _env_file=None)


def test_production_runner_disables_uvicorn_proxy_headers_and_public_bind() -> None:
    settings = HttpSettings(app_env="production", _env_file=None)
    config = server_config(settings)
    assert config.proxy_headers is False
    assert config.access_log is False
    assert config.host == "127.0.0.1"
    with pytest.raises(ValueError, match="loopback"):
        server_config(HttpSettings(app_env="production", app_host="0.0.0.0", _env_file=None))


def test_panel_csp_is_delivered_by_https_proxy_configuration() -> None:
    caddyfile = (Path(__file__).resolve().parents[2] / "deploy" / "Caddyfile").read_text(
        encoding="utf-8"
    )
    assert "header Content-Security-Policy" in caddyfile
    assert "script-src 'self'" in caddyfile
    assert "object-src 'none'" in caddyfile
    assert "frame-ancestors 'none'" in caddyfile
    assert "header_up X-Forwarded-Proto https" in caddyfile
