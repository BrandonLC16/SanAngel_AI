"""Temporary F9.3 HTTPS gate for one approved inbound WhatsApp test message."""

import argparse
import hashlib
import hmac
import http.client
import json
import re
import ssl
from collections.abc import Callable
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

from sqlalchemy import select

from backend.app.core.config import Settings, get_conversation_identity_settings
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.session import get_database_session_factory
from backend.app.services.conversation_recipient_cipher import ConversationRecipientCipher
from backend.app.services.whatsapp_webhook_service import WhatsAppWebhookService
from scripts.f93_delivery_probe import (
    KNOWN_EVENT_TYPES,
    MAX_AUTHORIZATION_BYTES,
    MAX_BODY_BYTES,
    WEBHOOK_PATH,
)

Forward = Callable[[bytes, str], int]
Eligibility = Callable[[], bool]
Audit = Callable[[dict[str, str | int]], None]


def emit_audit(record: dict[str, str | int]) -> None:
    """Never log raw webhooks, headers, phone numbers, or message text."""

    print(json.dumps(record, separators=(",", ":")), flush=True)


def make_handler(
    *,
    webhook_token: str,
    instance_id: str,
    target_chat_id: str,
    expected_text_sha256: str,
    not_before: int,
    forward: Forward,
    eligible: Eligibility,
    audit: Audit = emit_audit,
) -> type[BaseHTTPRequestHandler]:
    expected_authorization = f"Bearer {webhook_token}".encode("ascii")
    parser = WhatsAppWebhookService(max_text_chars=10_000, expected_instance_id=instance_id)

    class TargetGate(BaseHTTPRequestHandler):
        def log_message(self, format_string: str, *args: object) -> None:
            pass

        def _respond(
            self,
            result: int,
            event_type: str = "unread",
            *,
            request_id: str | None = None,
            message_sha256: str | None = None,
            backend_result: int | None = None,
        ) -> None:
            self.close_connection = True
            self.send_response_only(result)
            self.send_header("Content-Length", "0")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            record: dict[str, str | int] = {
                "utc": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "result": result,
            }
            if request_id is not None:
                record["request_id"] = request_id
            if message_sha256 is not None:
                record["message_sha256"] = message_sha256
            if backend_result is not None:
                record["backend_result"] = backend_result
            audit(record)

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

            raw_type = payload.get("typeWebhook")
            event_type = (
                raw_type if isinstance(raw_type, str) and raw_type in KNOWN_EVENT_TYPES else "other"
            )
            instance_data = payload.get("instanceData")
            if not isinstance(instance_data, dict) or (
                isinstance(instance_data.get("idInstance"), bool)
                or str(instance_data.get("idInstance")) != instance_id
            ):
                self._respond(403, event_type)
                return
            if event_type != "incomingMessageReceived":
                self._respond(503, event_type)
                return

            messages = parser.parse_messages(raw_body)
            if len(messages) != 1:
                self._respond(503, event_type)
                return
            message = messages[0]
            try:
                still_eligible = eligible()
            except Exception:
                still_eligible = False
            if (
                message.sender_id != target_chat_id
                or message.timestamp is None
                or message.timestamp < not_before
                or hashlib.sha256(message.text.encode("utf-8")).hexdigest() != expected_text_sha256
                or not still_eligible
            ):
                self._respond(503, event_type)
                return

            request_id = uuid4().hex
            message_sha256 = hashlib.sha256(message.external_message_id.encode()).hexdigest()
            try:
                backend_result = forward(raw_body, request_id)
            except (OSError, http.client.HTTPException):
                self._respond(503, event_type, request_id=request_id, message_sha256=message_sha256)
                return
            self._respond(
                200 if backend_result == 200 else 503,
                event_type,
                request_id=request_id,
                message_sha256=message_sha256,
                backend_result=backend_result,
            )

        def do_GET(self) -> None:
            self._respond(404)

        do_HEAD = do_GET
        do_PUT = do_GET
        do_PATCH = do_GET
        do_DELETE = do_GET
        do_OPTIONS = do_GET
        do_TRACE = do_GET
        do_CONNECT = do_GET

    return TargetGate


def _target_and_eligibility(conversation_id: int, operator: str) -> tuple[str, Eligibility]:
    sessions = get_database_session_factory()
    cipher = ConversationRecipientCipher(get_conversation_identity_settings())
    with sessions() as session:
        conversation = session.get(Conversation, conversation_id)
        if conversation is None:
            raise ValueError("test conversation unavailable")
        target = cipher.decrypt(conversation)
        branch_id = conversation.branch_id

    def eligible() -> bool:
        with sessions() as session:
            state = session.get(ConversationResponderState, conversation_id)
            owner = (
                session.scalar(
                    select(AdminUser).where(
                        AdminUser.id == state.assigned_admin_user_id,
                        AdminUser.branch_id == branch_id,
                    )
                )
                if state is not None and state.assigned_admin_user_id is not None
                else None
            )
            return bool(
                state is not None
                and state.branch_id == branch_id
                and state.mode == "HUMAN"
                and state.ai_reply_count == 0
                and owner is not None
                and owner.username == operator
                and owner.is_active
            )

    if not eligible():
        raise ValueError("test conversation is not assigned in HUMAN mode")
    return target, eligible


def main() -> None:
    args_parser = argparse.ArgumentParser(description=__doc__)
    args_parser.add_argument("--certfile", required=True)
    args_parser.add_argument("--keyfile", required=True)
    args_parser.add_argument("--backend-ca", required=True)
    args_parser.add_argument("--conversation-id", type=int, required=True)
    args_parser.add_argument("--operator", required=True)
    args_parser.add_argument("--expected-text-sha256", required=True)
    args_parser.add_argument("--not-before", type=int, required=True)
    args_parser.add_argument("--port", type=int, default=8001)
    args = args_parser.parse_args()

    if re.fullmatch(r"[0-9a-f]{64}", args.expected_text_sha256) is None:
        raise SystemExit("Invalid test message digest")
    try:
        settings = Settings()
        if settings.green_api_webhook_token is None or settings.green_api_instance_id is None:
            raise ValueError("missing webhook configuration")
        target, eligible = _target_and_eligibility(args.conversation_id, args.operator)
        backend_context = ssl.create_default_context(cafile=args.backend_ca)
        public_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        public_context.minimum_version = ssl.TLSVersion.TLSv1_2
        public_context.load_cert_chain(args.certfile, args.keyfile)
    except (OSError, ValueError):
        raise SystemExit("Target gate configuration invalid") from None

    def forward(raw_body: bytes, request_id: str) -> int:
        connection = http.client.HTTPSConnection(
            "127.0.0.1", 8000, context=backend_context, timeout=20
        )
        try:
            connection.request(
                "POST",
                WEBHOOK_PATH,
                body=raw_body,
                headers={
                    "Authorization": "Bearer "
                    + settings.green_api_webhook_token.get_secret_value(),
                    "Content-Type": "application/json",
                    "X-Request-ID": request_id,
                },
            )
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()

    handler = make_handler(
        webhook_token=settings.green_api_webhook_token.get_secret_value(),
        instance_id=settings.green_api_instance_id,
        target_chat_id=target,
        expected_text_sha256=args.expected_text_sha256,
        not_before=args.not_before,
        forward=forward,
        eligible=eligible,
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    server.socket = public_context.wrap_socket(server.socket, server_side=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
