import http.client
import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import ThreadingHTTPServer

from scripts.f93_delivery_probe import WEBHOOK_PATH, emit_audit, make_handler

TOKEN = "test-only-webhook-token-12345678901234567890"
INSTANCE_ID = "123456789012"


@contextmanager
def running_probe() -> Iterator[tuple[int, list[tuple[str, int]]]]:
    events: list[tuple[str, int]] = []
    handler = make_handler(TOKEN, INSTANCE_ID, lambda event, result: events.append((event, result)))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, events
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(
    port: int,
    method: str,
    path: str,
    *,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
) -> int:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        response.read()
        return response.status
    finally:
        connection.close()


def event_body(instance_id: int = 123_456_789_012) -> bytes:
    return json.dumps(
        {
            "typeWebhook": "stateInstanceChanged",
            "instanceData": {"idInstance": instance_id},
            "senderData": {"chatId": "5210000000000@c.us"},
            "textMessageData": {"textMessage": "private test text"},
        }
    ).encode()


def test_probe_requires_bearer_and_never_acknowledges_event() -> None:
    with running_probe() as (port, events):
        body = event_body()
        assert request(port, "POST", WEBHOOK_PATH, body=body) == 403
        assert (
            request(
                port,
                "POST",
                WEBHOOK_PATH,
                body=body,
                headers={"Authorization": "Bearer wrong"},
            )
            == 403
        )
        assert (
            request(
                port,
                "POST",
                WEBHOOK_PATH,
                body=body,
                headers={"Authorization": f"Bearer {TOKEN}"},
            )
            == 503
        )
    assert events == [("unread", 403), ("unread", 403), ("stateInstanceChanged", 503)]


def test_probe_rejects_other_routes_and_wrong_instance() -> None:
    with running_probe() as (port, events):
        assert request(port, "GET", "/") == 404
        assert request(port, "GET", WEBHOOK_PATH) == 404
        assert request(port, "POST", "/api/v1/admin/me") == 404
        assert request(port, "POST", WEBHOOK_PATH + ".") == 404
        assert (
            request(
                port,
                "POST",
                WEBHOOK_PATH,
                body=event_body(999999),
                headers={"Authorization": f"Bearer {TOKEN}"},
            )
            == 403
        )
    assert events == [("unread", 404)] * 4 + [("unread", 403)]


def test_probe_logs_only_safe_categories(capsys) -> None:
    emit_audit("stateInstanceChanged", 503)
    record = json.loads(capsys.readouterr().out)
    assert set(record) == {"utc", "event_type", "result"}
    assert record["event_type"] == "stateInstanceChanged"
    assert record["result"] == 503


def test_duplicate_authorization_is_rejected_before_reading_body() -> None:
    with running_probe() as (port, events):
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.putrequest("POST", WEBHOOK_PATH)
            connection.putheader("Authorization", f"Bearer {TOKEN}")
            connection.putheader("Authorization", f"Bearer {TOKEN}")
            connection.putheader("Content-Length", "1000000")
            connection.endheaders()
            response = connection.getresponse()
            response.read()
            assert response.status == 403
        finally:
            connection.close()
    assert events == [("unread", 403)]


def test_untrusted_event_type_is_not_logged_verbatim() -> None:
    private_marker = "private-contact-5210000000000"
    body = json.dumps(
        {
            "typeWebhook": private_marker,
            "instanceData": {"idInstance": int(INSTANCE_ID)},
        }
    ).encode()
    with running_probe() as (port, events):
        assert (
            request(
                port,
                "POST",
                WEBHOOK_PATH,
                body=body,
                headers={"Authorization": f"Bearer {TOKEN}"},
            )
            == 503
        )
    assert events == [("other", 503)]
    assert private_marker not in repr(events)
