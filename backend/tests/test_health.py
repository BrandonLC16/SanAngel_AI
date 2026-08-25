import asyncio
import socket

import httpx
import pytest

from backend.app.core import config
from backend.app.main import app


def test_health_returns_stable_minimal_response_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_external_dependency(*args: object, **kwargs: object) -> None:
        raise AssertionError("health check attempted an external dependency")

    monkeypatch.setattr(socket, "getaddrinfo", reject_external_dependency)
    monkeypatch.setattr(config, "get_settings", reject_external_dependency)

    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "carniceria-ai-chatbot",
    }
