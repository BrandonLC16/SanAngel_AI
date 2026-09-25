"""Scoped, privacy-minimal review and audited FAQ resolution."""

import json
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError

from backend.app.api.routes.admin_review import get_admin_review_service
from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import ConversationIdentitySettings
from backend.app.db.models.admin_commercial import AdminCommercialAudit, ManagedFAQ
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.message import Message
from backend.app.db.models.unresolved_question import UnresolvedQuestion
from backend.app.services.admin_auth_service import AdminAuthService
from backend.app.services.admin_review_service import AdminReviewService
from backend.app.services.faq_response_policy import (
    UNKNOWN_FALLBACK,
    FAQFallback,
    HumanHelpReason,
    request_human_help,
)
from backend.app.services.unresolved_question_service import UnresolvedQuestionService
from backend.tests.test_admin_commercial import PASSWORD, login, settings

pytest_plugins = ("backend.tests.test_admin_commercial",)
BASE = "/api/v1/admin/review"
IDENTITY_KEY = "test-only-admin-review-identity-key-123456789"


def identity_settings(branch: str = "sucursal-uno") -> ConversationIdentitySettings:
    return ConversationIdentitySettings(
        assistant_branch_code=branch,
        conversation_identity_key=IDENTITY_KEY,
        _env_file=None,
    )


def configure(app, sessions) -> None:
    app.dependency_overrides[get_admin_review_service] = lambda: AdminReviewService(
        sessions, admin_settings=settings(), identity_settings=identity_settings()
    )


def fallback(reason: HumanHelpReason = HumanHelpReason.FAQ_UNKNOWN) -> FAQFallback:
    return FAQFallback(text=UNKNOWN_FALLBACK, human_help=request_human_help(reason))


def test_conversation_filters_detail_and_foreign_id_are_minimal(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user("viewer", PASSWORD)
    now = datetime.now(UTC)
    with sessions.begin() as session:
        own = session.scalar(select(Branch).where(Branch.code == "sucursal-uno"))
        foreign = session.scalar(select(Branch).where(Branch.code == "sucursal-dos"))
        assert own is not None and foreign is not None
        current = Conversation(
            branch_id=own.id,
            channel="whatsapp",
            external_user_key="a" * 64,
            created_at=now - timedelta(days=3),
            updated_at=now,
        )
        older = Conversation(
            branch_id=own.id,
            channel="whatsapp",
            external_user_key="b" * 64,
            created_at=now - timedelta(days=20),
            updated_at=now - timedelta(days=20),
        )
        other = Conversation(
            branch_id=foreign.id,
            channel="whatsapp",
            external_user_key="c" * 64,
            created_at=now,
            updated_at=now,
        )
        session.add_all([current, older, other])
        session.flush()
        own_id, older_id, foreign_id = current.id, older.id, other.id
        session.add_all(
            [
                Message(
                    branch_id=own.id,
                    conversation_id=current.id,
                    direction="inbound",
                    occurred_at=now,
                ),
                Message(
                    branch_id=own.id,
                    conversation_id=current.id,
                    direction="outbound",
                    occurred_at=now,
                ),
                Message(
                    branch_id=foreign.id,
                    conversation_id=other.id,
                    direction="inbound",
                    occurred_at=now,
                ),
            ]
        )
    configure(app, sessions)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.get(f"{BASE}/conversations").status_code == 401
        login(client, "viewer")
        page = client.get(f"{BASE}/conversations?limit=1")
        assert page.status_code == 200
        assert page.headers["cache-control"] == "no-store"
        assert [item["id"] for item in page.json()["items"]] == [own_id]
        assert page.json()["has_more"] is True
        assert [
            item["id"]
            for item in client.get(f"{BASE}/conversations?limit=1&offset=1").json()["items"]
        ] == [older_id]
        date_filter = (now - timedelta(days=1)).date().isoformat()
        filtered = client.get(f"{BASE}/conversations", params={"updated_from": date_filter})
        assert [item["id"] for item in filtered.json()["items"]] == [own_id]
        assert client.get(f"{BASE}/conversations?limit=101").status_code == 422
        assert (
            client.get(
                f"{BASE}/conversations?updated_from=2026-09-25&updated_to=2026-09-20"
            ).status_code
            == 422
        )
        detail = client.get(f"{BASE}/conversations/{own_id}")
        assert detail.status_code == 200
        assert detail.json()["message_count"] == 2
        assert {item["direction"] for item in detail.json()["recent_messages"]} == {
            "inbound",
            "outbound",
        }
        assert client.get(f"{BASE}/conversations/{foreign_id}").status_code == 404
        rendered = json.dumps(page.json()) + json.dumps(detail.json())
        assert "a" * 64 not in rendered
        assert "c" * 64 not in rendered
        assert "chatId" not in rendered and "text" not in rendered


def test_unresolved_filters_and_faq_resolution_require_match_csrf_and_scope(app, sessions) -> None:
    auth = AdminAuthService(sessions, settings=settings())
    auth.create_user("viewer", PASSWORD)
    auth.create_user("editor", PASSWORD, role=AdminRole.EDITOR)
    question = "¿Aceptan vales?"
    private_question = "Mi correo cliente@example.com necesita ayuda"
    with sessions.begin() as session:
        own = UnresolvedQuestionService(session, settings=identity_settings())
        own.record_faq_fallback(question, fallback())
        own.record_faq_fallback(question, fallback())
        own.record_faq_fallback("¿Tienen entrega?", fallback(HumanHelpReason.FAQ_AMBIGUOUS))
        own.record_faq_fallback(private_question, fallback())
        UnresolvedQuestionService(
            session, settings=identity_settings("sucursal-dos")
        ).record_faq_fallback("¿Pregunta ajena?", fallback())
    with sessions() as session:
        rows = session.scalars(select(UnresolvedQuestion)).all()
        target = next(row for row in rows if row.occurrences == 2)
        private = next(
            row
            for row in rows
            if row.branch_id == target.branch_id
            and row.id != target.id
            and row.reason == "faq_unknown"
        )
        foreign = next(row for row in rows if row.branch_id != target.branch_id)
        target_id, private_id, foreign_id = target.id, private.id, foreign.id
        target_key = target.question_key
    configure(app, sessions)
    payload = {
        "category": "pagos",
        "question": question,
        "answer": "Sí, aceptamos vales.",
        "is_active": True,
    }
    with (
        TestClient(app, base_url="https://testserver") as viewer,
        TestClient(app, base_url="https://testserver") as editor,
    ):
        viewer_csrf = login(viewer, "viewer")
        editor_csrf = login(editor, "editor")
        page = viewer.get(
            f"{BASE}/unresolved", params={"reason": "faq_unknown", "min_occurrences": 2}
        )
        assert page.status_code == 200
        assert [item["id"] for item in page.json()["items"]] == [target_id]
        ambiguous = viewer.get(f"{BASE}/unresolved", params={"reason": "faq_ambiguous"})
        assert len(ambiguous.json()["items"]) == 1
        assert viewer.get(f"{BASE}/unresolved/{target_id}").json()["occurrences"] == 2
        assert viewer.get(f"{BASE}/unresolved/{foreign_id}").status_code == 404
        assert viewer.get(f"{BASE}/unresolved?reason=other").status_code == 422
        assert (
            viewer.post(
                f"{BASE}/unresolved/{target_id}/resolve", json=payload, headers=viewer_csrf
            ).status_code
            == 403
        )
        assert (
            editor.post(f"{BASE}/unresolved/{target_id}/resolve", json=payload).status_code == 403
        )
        assert (
            editor.post(
                f"{BASE}/unresolved/{foreign_id}/resolve", json=payload, headers=editor_csrf
            ).status_code
            == 404
        )
        assert (
            editor.post(
                f"{BASE}/unresolved/{target_id}/resolve",
                json={**payload, "branch_id": 2},
                headers=editor_csrf,
            ).status_code
            == 422
        )
        assert (
            editor.post(
                f"{BASE}/unresolved/{target_id}/resolve",
                json={**payload, "question": "Otra pregunta"},
                headers=editor_csrf,
            ).status_code
            == 409
        )
        assert (
            editor.post(
                f"{BASE}/unresolved/{private_id}/resolve",
                json={**payload, "question": private_question},
                headers=editor_csrf,
            ).status_code
            == 422
        )
        assert (
            editor.post(
                f"{BASE}/unresolved/{target_id}/resolve",
                json={**payload, "answer": "Escríbenos a cliente@example.com"},
                headers=editor_csrf,
            ).status_code
            == 422
        )
        rendered = json.dumps(page.json())
        assert (
            target_key not in rendered
            and question not in rendered
            and private_question not in rendered
        )
        resolved = editor.post(
            f"{BASE}/unresolved/{target_id}/resolve", json=payload, headers=editor_csrf
        )
        assert resolved.status_code == 200
        assert resolved.json()["unresolved_id"] == target_id
        assert question not in resolved.text and target_key not in resolved.text
        assert editor.get(f"{BASE}/unresolved/{target_id}").status_code == 404
    with sessions() as session:
        faq = session.scalar(select(ManagedFAQ).where(ManagedFAQ.question == question))
        assert faq is not None and faq.is_active
        assert session.get(UnresolvedQuestion, target_id) is None
        assert session.get(UnresolvedQuestion, foreign_id) is not None
        audits = session.scalars(select(AdminCommercialAudit)).all()
        assert len(audits) == 1 and audits[0].resource == "faq" and audits[0].action == "create"


def test_resolution_rolls_back_when_audit_fails(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    question = "¿Venden arrachera?"
    with sessions.begin() as session:
        UnresolvedQuestionService(session, settings=identity_settings()).record_faq_fallback(
            question, fallback()
        )
    with sessions() as session:
        target_id = session.scalar(select(UnresolvedQuestion.id))
    configure(app, sessions)

    def reject_audit(*_args: object) -> None:
        raise IntegrityError("test audit failure", {}, Exception("private test detail"))

    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        event.listen(AdminCommercialAudit, "before_insert", reject_audit)
        try:
            response = client.post(
                f"{BASE}/unresolved/{target_id}/resolve",
                json={"category": "general", "question": question, "answer": "Sí."},
                headers=csrf,
            )
        finally:
            event.remove(AdminCommercialAudit, "before_insert", reject_audit)
        assert response.status_code == 503
        assert "private test detail" not in response.text
    with sessions() as session:
        assert session.get(UnresolvedQuestion, target_id) is not None
        assert session.scalars(select(ManagedFAQ)).all() == []
        assert session.scalars(select(AdminCommercialAudit)).all() == []
