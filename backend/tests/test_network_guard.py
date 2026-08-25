import socket

import pytest


def test_external_dns_resolution_is_blocked() -> None:
    with pytest.raises(AssertionError, match="external DNS"):
        socket.getaddrinfo("api.openai.com", 443)


def test_external_ip_connection_is_blocked_before_network_access() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        with pytest.raises(AssertionError, match="external network"):
            client.connect(("192.0.2.1", 443))


def test_loopback_resolution_remains_available_for_in_process_tests() -> None:
    addresses = socket.getaddrinfo("localhost", 80)

    assert addresses
