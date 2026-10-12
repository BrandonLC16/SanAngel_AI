import hashlib
import http.client
import json
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from http.server import ThreadingHTTPServer

from scripts.f93_target_gate import WEBHOOK_PATH, make_handler

TOKEN = "test-only-webhook-token-12345678901234567890"
INSTANCE_ID = "123456789012"
TEST_CHAT = "5210000000000@c.us"
OTHER_CHAT = "5210000000001@c.us"
TEST_TEXT = "F9.3 entrada única de prueba"


@contextmanager
def running_gate(
    *,
    forward_result: int = 200,
    eligible: bool | Callable[[], bool] = True,
) -> Iterator[tuple[int, list[tuple[bytes, str]], list[dict[str, str | int]]]]:
    forwarded: list[tuple[bytes, str]] = []
    records: list[dict[str, str | int]] = []

    def forward(body: bytes, request_id: str) -> int:
        forwarded.append((body, request_id))
        return forward_result

    handler = make_handler(
        webhook_token=TOKEN,
        instance_id=INSTANCE_ID,
        target_chat_id=TEST_CHAT,
        expected_text_sha256=hashlib.sha256(TEST_TEXT.encode()).hexdigest(),
        not_before=100,
        forward=forward,
        eligible=eligible if callable(eligible) else lambda: eligible,
        audit=records.append,
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port, forwarded, records
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def request(
    port: int,
    path: str,
    *,
    body: bytes = b"",
    authorization: str | None = None,
    method: str = "POST",
) -> int:
    headers = {"Content-Type": "application/json"}
    if authorization is not None:
        headers["Authorization"] = authorization
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        response.read()
        return response.status
    finally:
        connection.close()


def event(
    *,
    event_type: str = "incomingMessageReceived",
    chat_id: str = TEST_CHAT,
    text: str = TEST_TEXT,
    timestamp: int = 101,
) -> bytes:
    return json.dumps(
        {
            "typeWebhook": event_type,
            "instanceData": {"idInstance": int(INSTANCE_ID), "typeInstance": "whatsapp"},
            "timestamp": timestamp,
            "idMessage": "test-message-id",
            "senderData": {"chatId": chat_id},
            "messageData": {
                "typeMessage": "textMessage",
                "textMessageData": {"textMessage": text},
            },
        }
    ).encode()


def test_only_exact_new_test_message_can_reach_backend() -> None:
    with running_gate() as (port, forwarded, records):
        assert request(port, WEBHOOK_PATH) == 403
        assert request(port, "/api/v1/admin/me") == 404
        assert (
            request(
                port, WEBHOOK_PATH, body=event(chat_id=OTHER_CHAT), authorization=f"Bearer {TOKEN}"
            )
            == 503
        )
        assert (
            request(
                port,
                WEBHOOK_PATH,
                body=event(text="another message"),
                authorization=f"Bearer {TOKEN}",
            )
            == 503
        )
        assert (
            request(port, WEBHOOK_PATH, body=event(timestamp=99), authorization=f"Bearer {TOKEN}")
            == 503
        )
        assert (
            request(
                port,
                WEBHOOK_PATH,
                body=event(event_type="stateInstanceChanged"),
                authorization=f"Bearer {TOKEN}",
            )
            == 503
        )
        assert request(port, WEBHOOK_PATH, body=event(), authorization=f"Bearer {TOKEN}") == 200

    assert len(forwarded) == 1
    assert forwarded[0][0] == event()
    assert len(forwarded[0][1]) == 32
    assert records[-1]["request_id"] == forwarded[0][1]
    assert records[-1]["backend_result"] == 200
    assert records[-1]["message_sha256"] == hashlib.sha256(b"test-message-id").hexdigest()
    assert TEST_CHAT not in repr(records)
    assert TEST_TEXT not in repr(records)
    assert TOKEN not in repr(records)


def test_human_assignment_and_backend_result_fail_closed() -> None:
    with running_gate(eligible=False) as (port, forwarded, records):
        assert request(port, WEBHOOK_PATH, body=event(), authorization=f"Bearer {TOKEN}") == 503
    assert forwarded == []
    assert records[-1]["result"] == 503

    def broken_eligibility() -> bool:
        raise RuntimeError("database unavailable")

    with running_gate(eligible=broken_eligibility) as (port, forwarded, records):
        assert request(port, WEBHOOK_PATH, body=event(), authorization=f"Bearer {TOKEN}") == 503
    assert forwarded == []
    assert records[-1]["result"] == 503

    with running_gate(forward_result=500) as (port, forwarded, records):
        assert request(port, WEBHOOK_PATH, body=event(), authorization=f"Bearer {TOKEN}") == 503
    assert len(forwarded) == 1
    assert records[-1]["backend_result"] == 500


def test_malformed_event_and_wrong_instance_never_forward() -> None:
    with running_gate() as (port, forwarded, records):
        assert request(port, WEBHOOK_PATH, body=b"not-json", authorization=f"Bearer {TOKEN}") == 400
        wrong = json.loads(event())
        wrong["instanceData"]["idInstance"] = 999
        assert (
            request(
                port, WEBHOOK_PATH, body=json.dumps(wrong).encode(), authorization=f"Bearer {TOKEN}"
            )
            == 403
        )
        assert request(port, WEBHOOK_PATH, body=b"[]", authorization=f"Bearer {TOKEN}") == 400
    assert forwarded == []
    assert all(set(record) == {"utc", "event_type", "result"} for record in records)
