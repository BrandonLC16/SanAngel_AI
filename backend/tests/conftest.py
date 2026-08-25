import ipaddress
import socket
from collections.abc import Generator
from typing import Any

import pytest

NON_SECRET_CREDENTIAL_PLACEHOLDER = "test-only-credential-placeholder"
LOOPBACK_HOSTNAMES = {"localhost", "localhost.localdomain"}


def is_loopback_host(host: object) -> bool:
    if host is None:
        return True
    normalized_host = str(host).strip("[]").lower()
    if normalized_host in LOOPBACK_HOSTNAMES:
        return True
    try:
        return ipaddress.ip_address(normalized_host).is_loopback
    except ValueError:
        return False


def assert_loopback_address(address: object) -> None:
    if not isinstance(address, tuple) or not address:
        return
    if not is_loopback_host(address[0]):
        raise AssertionError(f"test attempted an external network connection to {address[0]!r}")


@pytest.fixture
def non_secret_credential() -> str:
    """Return an explicit placeholder that cannot be mistaken for a real credential."""

    return NON_SECRET_CREDENTIAL_PLACEHOLDER


@pytest.fixture(autouse=True)
def block_external_network(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Fail every test that resolves or connects to a non-loopback network address."""

    original_getaddrinfo = socket.getaddrinfo
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection

    def guarded_getaddrinfo(host: object, *args: object, **kwargs: object) -> Any:
        if not is_loopback_host(host):
            raise AssertionError(f"test attempted external DNS resolution for {host!r}")
        return original_getaddrinfo(host, *args, **kwargs)

    def guarded_connect(client: socket.socket, address: object) -> None:
        assert_loopback_address(address)
        original_connect(client, address)  # type: ignore[arg-type]

    def guarded_connect_ex(client: socket.socket, address: object) -> int:
        assert_loopback_address(address)
        return original_connect_ex(client, address)  # type: ignore[arg-type]

    def guarded_create_connection(
        address: tuple[str, int],
        *args: object,
        **kwargs: object,
    ) -> socket.socket:
        assert_loopback_address(address)
        return original_create_connection(address, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    monkeypatch.setattr(socket, "create_connection", guarded_create_connection)
    yield
