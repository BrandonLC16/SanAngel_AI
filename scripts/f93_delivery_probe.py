"""Isolated F9.3 HTTPS probe: inspect webhook delivery without acknowledging it."""

import argparse
import hmac
import json
import re
import ssl
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pydantic import ValidationError

from backend.app.core.config import get_settings

WEBHOOK_PATH = "/api/v1/whatsapp/webhook"
MAX_BODY_BYTES = 65_536
MAX_AUTHORIZATION_BYTES = 2_048
KNOWN_EVENT_TYPES = frozenset(
    {
        "incomingMessageReceived",
        "outgoingMessageReceived",
        "outgoingAPIMessageReceived",
        "outgoingMessageStatus",
        "stateInstanceChanged",
        "statusInstanceChanged",
    }
)
AuditSink = Callable[[str, int], None]


def emit_audit(event_type: str, result: int) -> None:
    """Write only time, a closed event category and the HTTP result."""

    print(
        json.dumps(
            {
                "utc": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "result": result,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )


def make_handler(
    webhook_token: str,
    instance_id: str,
    audit: AuditSink = emit_audit,
) -> type[BaseHTTPRequestHandler]:
    expected_authorization = f"Bearer {webhook_token}".encode("ascii")

    class DeliveryProbe(BaseHTTPRequestHandler):
        def log_message(self, format_string: str, *args: object) -> None:
            pass

        def _respond(self, result: int, event_type: str = "unread") -> None:
            self.close_connection = True
            self.send_response_only(result)
            self.send_header("Content-Length", "0")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            audit(event_type, result)

        def do_POST(self) -> None:
            if self.path != WEBHOOK_PATH:
                self._respond(404)
                return

            authorizations = self.headers.get_all("Authorization", [])
            if len(authorizations) != 1:
                self._respond(403)
                return
            received = authorizations[0].encode("utf-8")
            if len(received) > MAX_AUTHORIZATION_BYTES or not hmac.compare_digest(
                received, expected_authorization
            ):
                self._respond(403)
                return

            lengths = self.headers.get_all("Content-Length", [])
            if self.headers.get("Transfer-Encoding") is not None or len(lengths) != 1:
                self._respond(400)
                return
            if re.fullmatch(r"[0-9]{1,10}", lengths[0]) is None:
                self._respond(400)
                return
            content_length = int(lengths[0])
            if content_length > MAX_BODY_BYTES:
                self._respond(413)
                return

            self.connection.settimeout(5)
            try:
                raw_body = self.rfile.read(content_length)
                payload = json.loads(raw_body)
            except (OSError, ValueError):
                self._respond(400)
                return
            if len(raw_body) != content_length or not isinstance(payload, dict):
                self._respond(400)
                return

            instance_data = payload.get("instanceData")
            if not isinstance(instance_data, dict):
                self._respond(400)
                return
            received_instance = instance_data.get("idInstance")
            if (
                isinstance(received_instance, bool)
                or not isinstance(received_instance, (int, str))
                or str(received_instance) != instance_id
            ):
                self._respond(403)
                return

            raw_type = payload.get("typeWebhook")
            if not isinstance(raw_type, str):
                self._respond(400)
                return
            event_type = raw_type if raw_type in KNOWN_EVENT_TYPES else "other"
            self._respond(503, event_type)

        def do_GET(self) -> None:
            self._respond(404)

        do_HEAD = do_GET
        do_PUT = do_GET
        do_PATCH = do_GET
        do_DELETE = do_GET
        do_OPTIONS = do_GET
        do_TRACE = do_GET
        do_CONNECT = do_GET

    return DeliveryProbe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certfile", required=True)
    parser.add_argument("--keyfile", required=True)
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    try:
        settings = get_settings()
        if settings.green_api_webhook_token is None or settings.green_api_instance_id is None:
            raise ValueError("missing webhook configuration")
        handler = make_handler(
            settings.green_api_webhook_token.get_secret_value(),
            settings.green_api_instance_id,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(args.certfile, args.keyfile)
    except (OSError, ValueError, ValidationError):
        raise SystemExit("Probe configuration invalid") from None

    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
