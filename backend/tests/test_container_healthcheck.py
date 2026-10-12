"""The container probe checks readiness without bypassing production TLS admission."""

import http.client

import pytest

from scripts import container_healthcheck


class Response:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self.body = body

    def read(self, amount: int) -> bytes:
        return self.body[:amount]


def test_container_probe_uses_loopback_and_trusted_proxy_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[object] = []

    class Connection:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            requests.append((host, port, timeout))

        def request(self, method: str, path: str, *, headers: dict[str, str]) -> None:
            requests.append((method, path, headers))

        def getresponse(self) -> Response:
            return Response(200, b'{"status":"ok","service":"carniceria-ai-chatbot"}')

        def close(self) -> None:
            requests.append("closed")

    monkeypatch.setenv("APP_PORT", "8123")
    monkeypatch.setattr(container_healthcheck.http.client, "HTTPConnection", Connection)

    assert container_healthcheck.main() == 0
    assert requests == [
        ("127.0.0.1", 8123, 2),
        ("GET", "/health", {"X-Forwarded-Proto": "https"}),
        "closed",
    ]


@pytest.mark.parametrize(
    ("status", "body"),
    [
        (403, b""),
        (200, b"invalid"),
        (200, b'{"status":"error"}'),
    ],
)
def test_container_probe_rejects_unhealthy_response(
    status: int, body: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    class Connection:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            pass

        def request(self, method: str, path: str, *, headers: dict[str, str]) -> None:
            pass

        def getresponse(self) -> Response:
            return Response(status, body)

        def close(self) -> None:
            pass

    monkeypatch.setattr(container_healthcheck.http.client, "HTTPConnection", Connection)
    assert container_healthcheck.main() == 1


def test_container_probe_fails_closed_on_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def connection(host: str, port: int, timeout: int) -> http.client.HTTPConnection:
        raise ConnectionRefusedError("test-only-placeholder")

    monkeypatch.setattr(container_healthcheck.http.client, "HTTPConnection", connection)
    assert container_healthcheck.main() == 1
