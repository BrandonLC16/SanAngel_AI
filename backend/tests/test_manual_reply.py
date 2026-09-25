"""Offline human reply through the scoped GreenAPI client and admin session."""

import json
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.api.routes.admin_review import (
    get_admin_review_service,
    get_conversation_mode_service,
    get_manual_reply_service,
)
from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import ConversationIdentitySettings, Settings
from backend.app.core.exceptions import ServiceUnavailableError
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.manual_send_receipt import ManualSendReceipt
from backend.app.db.models.message import Message
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.admin_auth_service import AdminAuthService
from backend.app.services.admin_review_service import AdminReviewService
from backend.app.services.conversation_identity_service import ConversationIdentityService
from backend.app.services.conversation_mode_service import ConversationModeService
from backend.app.services.manual_reply_service import ManualReplyService
from backend.app.services.whatsapp_client import WhatsAppClient
from backend.app.services.whatsapp_privacy_service import WhatsAppPrivacyService
from backend.tests.test_admin_commercial import PASSWORD, login, settings

pytest_plugins = ("backend.tests.test_admin_commercial",)
BASE = "/api/v1/admin/review/conversations"
CHAT_ID = "5215550000001@c.us"
IDENTITY_KEY = "test-only-manual-reply-identity-key-000000"


def identity_settings(branch: str = "sucursal-uno") -> ConversationIdentitySettings:
    return ConversationIdentitySettings(
        assistant_branch_code=branch,
        conversation_identity_key=IDENTITY_KEY,
        _env_file=None,
    )


def whatsapp_settings(branch: str = "sucursal-uno") -> Settings:
    return Settings(
        assistant_branch_code=branch,
        openai_api_key="test-only-openai-placeholder",
        green_api_instance_id="123456",
        green_api_token_instance="test-only-provider-token-1234",
        green_api_webhook_token="test-only-webhook-token-1234567890123",
        _env_file=None,
    )


class ProviderStub:
    def __init__(self, *, timeout: bool = False) -> None:
        self.timeout = timeout
        self.calls: list[dict[str, object]] = []

    async def post(self, url: str, **kwargs: object) -> httpx.Response:
        self.calls.append({"url": url, **kwargs})
        if self.timeout:
            raise httpx.ReadTimeout("test-only-timeout")
        return httpx.Response(200, json={"idMessage": "test-only-provider-message-id"})


def configure(app, sessions, provider: ProviderStub) -> None:
    app.dependency_overrides[get_admin_review_service] = lambda: AdminReviewService(
        sessions, admin_settings=settings(), identity_settings=identity_settings()
    )
    app.dependency_overrides[get_conversation_mode_service] = lambda: ConversationModeService(
        sessions, settings=settings()
    )
    app.dependency_overrides[get_manual_reply_service] = lambda: ManualReplyService(
        sessions,
        admin_settings=settings(),
        identity_settings=identity_settings(),
        whatsapp_settings=whatsapp_settings(),
        sender_factory=lambda: WhatsAppClient(whatsapp_settings(), http_client=provider),
    )


def create_conversation(sessions, *, branch: str = "sucursal-uno") -> int:
    with sessions.begin() as session:
        context = ConversationIdentityService(session, settings=identity_settings(branch)).resolve(
            InboundMessage(external_message_id="test-inbound", sender_id=CHAT_ID, text="Hola")
        )
        return context.conversation_id


def payload(request_id: str | None = None) -> dict[str, object]:
    return {
        "request_id": request_id or str(uuid4()),
        "text": "¿En qué puedo ayudarte?",
        "confirmed": True,
    }


def test_manual_reply_uses_same_chat_and_instance_only_for_assignee(app, sessions) -> None:
    auth = AdminAuthService(sessions, settings=settings())
    auth.create_user("viewer", PASSWORD)
    auth.create_user("editor", PASSWORD, role=AdminRole.EDITOR)
    auth.create_user("other_editor", PASSWORD, role=AdminRole.EDITOR)
    auth.create_user("owner", PASSWORD, role=AdminRole.OWNER)
    own_id = create_conversation(sessions)
    foreign_id = create_conversation(sessions, branch="sucursal-dos")
    provider = ProviderStub()
    configure(app, sessions, provider)
    request = payload()
    with (
        TestClient(app, base_url="https://testserver") as anonymous,
        TestClient(app, base_url="https://testserver") as viewer,
        TestClient(app, base_url="https://testserver") as editor,
        TestClient(app, base_url="https://testserver") as other_editor,
        TestClient(app, base_url="https://testserver") as owner,
    ):
        url = f"{BASE}/{own_id}/messages"
        assert anonymous.post(url, json=request).status_code == 401
        viewer_csrf = login(viewer, "viewer")
        editor_csrf = login(editor, "editor")
        other_csrf = login(other_editor, "other_editor")
        owner_csrf = login(owner, "owner")
        assert viewer.post(url, json=request, headers=viewer_csrf).status_code == 403
        assert editor.post(url, json=request).status_code == 403
        assert editor.post(url, json=request, headers=editor_csrf).status_code == 403
        assert editor.post(f"{BASE}/{own_id}/take", headers=editor_csrf).status_code == 200
        assert other_editor.post(url, json=request, headers=other_csrf).status_code == 403
        assert owner.post(url, json=request, headers=owner_csrf).status_code == 403
        foreign = editor.post(f"{BASE}/{foreign_id}/messages", json=request, headers=editor_csrf)
        assert foreign.status_code == 404
        assert (
            editor.post(url, json={**request, "confirmed": False}, headers=editor_csrf).status_code
            == 422
        )
        result = editor.post(url, json=request, headers=editor_csrf)
        assert result.status_code == 200
        assert result.headers["cache-control"] == "no-store"
        assert result.json()["status"] == "accepted"
        receipt_id = result.json()["receipt_id"]
        assert editor.post(url, json=request, headers=editor_csrf).json() == result.json()
        assert len(provider.calls) == 1
        call = provider.calls[0]
        assert call["url"] == (
            "https://api.green-api.com/waInstance123456/sendMessage/test-only-provider-token-1234"
        )
        assert call["json"] == {
            "chatId": CHAT_ID,
            "message": "¿En qué puedo ayudarte?",
            "linkPreview": False,
        }
        detail = editor.get(f"{BASE}/{own_id}")
        assert detail.json()["latest_manual_send"]["receipt_id"] == receipt_id
        assert detail.json()["latest_manual_send"]["status"] == "accepted"
        assert detail.json()["message_count"] == 1
        assert detail.json()["manual_send_blocked"] is False
        assert editor.post(f"{BASE}/{own_id}/release", headers=editor_csrf).status_code == 200
        response_text = json.dumps(result.json()) + detail.text
        assert CHAT_ID not in response_text
        assert "test-only-provider-token" not in response_text
        assert "test-only-provider-message-id" not in response_text
        assert request["text"] not in response_text
    with sessions() as session:
        receipt = session.get(ManualSendReceipt, receipt_id)
        assert receipt is not None and receipt.status == "accepted"
        assert receipt.actor_user_id > 0 and receipt.provider_message_id is not None
        assert session.scalar(select(Message.direction)) == "outbound"
        own = session.get(Conversation, own_id)
        assert own is not None and CHAT_ID not in own.recipient_ciphertext


def test_timeout_is_uncertain_and_blocks_release_or_duplicate_send(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    conversation_id = create_conversation(sessions)
    provider = ProviderStub(timeout=True)
    configure(app, sessions, provider)
    request = payload()
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        assert client.post(f"{BASE}/{conversation_id}/take", headers=csrf).status_code == 200
        url = f"{BASE}/{conversation_id}/messages"
        first = client.post(url, json=request, headers=csrf)
        assert first.status_code == 200 and first.json()["status"] == "uncertain"
        assert client.post(url, json=request, headers=csrf).json() == first.json()
        assert client.post(url, json=payload(), headers=csrf).status_code == 409
        assert client.post(f"{BASE}/{conversation_id}/release", headers=csrf).status_code == 409
        detail = client.get(f"{BASE}/{conversation_id}").json()
        assert detail["manual_send_blocked"] is True
        assert detail["latest_manual_send"]["status"] == "uncertain"
        assert len(provider.calls) == 1
    with sessions() as session:
        state = session.get(ConversationResponderState, conversation_id)
        assert state is not None and state.manual_send_blocked
        assert session.scalars(select(Message)).all() == []


def test_missing_recipient_and_mismatched_instance_fail_closed(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    with sessions.begin() as session:
        branch = session.scalar(select(Branch).where(Branch.code == "sucursal-uno"))
        assert branch is not None
        conversation = Conversation(branch_id=branch.id, external_user_key="a" * 64)
        session.add(conversation)
        session.flush()
        conversation_id = conversation.id
    provider = ProviderStub()
    configure(app, sessions, provider)
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        assert client.post(f"{BASE}/{conversation_id}/take", headers=csrf).status_code == 200
        response = client.post(f"{BASE}/{conversation_id}/messages", json=payload(), headers=csrf)
        assert response.status_code == 409
        assert provider.calls == []
        assert client.post(f"{BASE}/{conversation_id}/release", headers=csrf).status_code == 200
    with pytest.raises(ServiceUnavailableError):
        ManualReplyService(
            sessions,
            admin_settings=settings(),
            identity_settings=identity_settings(),
            whatsapp_settings=whatsapp_settings("sucursal-dos"),
        )


def test_corrupt_recipient_fails_closed_and_erasure_removes_send_receipt(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    conversation_id = create_conversation(sessions)
    provider = ProviderStub()
    configure(app, sessions, provider)
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        assert client.post(f"{BASE}/{conversation_id}/take", headers=csrf).status_code == 200
        with sessions.begin() as session:
            conversation = session.get(Conversation, conversation_id)
            assert conversation is not None
            original = conversation.recipient_ciphertext
            conversation.recipient_ciphertext = "corrupt-ciphertext"
        url = f"{BASE}/{conversation_id}/messages"
        assert client.post(url, json=payload(), headers=csrf).status_code == 503
        assert provider.calls == []
        with sessions.begin() as session:
            conversation = session.get(Conversation, conversation_id)
            assert conversation is not None
            conversation.recipient_ciphertext = original
        sent = client.post(url, json=payload(), headers=csrf)
        assert sent.status_code == 200
        receipt_id = sent.json()["receipt_id"]
    assert WhatsAppPrivacyService(sessions, settings=identity_settings()).erase_sender(CHAT_ID)
    with sessions() as session:
        assert session.get(ManualSendReceipt, receipt_id) is None
        assert session.get(Conversation, conversation_id) is None
