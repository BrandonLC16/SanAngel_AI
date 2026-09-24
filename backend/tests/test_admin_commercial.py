"""Offline admin CRUD, branch isolation, validation, and audit rollback."""

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes.admin_auth import get_admin_auth_service
from backend.app.api.routes.admin_commercial import get_admin_commercial_service
from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import AdminAuthSettings, HttpSettings, get_database_settings
from backend.app.db.models.admin_commercial import AdminCommercialAudit, ManagedFAQ
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.price import Price
from backend.app.db.models.product import Product
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.main import create_app
from backend.app.services.admin_auth_service import AdminAuthService
from backend.app.services.admin_commercial_service import AdminCommercialService

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "test-only-commercial-password-123"
AUTH_KEY = "test-only-commercial-auth-key-123456789012"
BASE = "/api/v1/admin/commercial"


def settings(branch: str = "sucursal-uno") -> AdminAuthSettings:
    return AdminAuthSettings(assistant_branch_code=branch, admin_auth_key=AUTH_KEY, _env_file=None)


@pytest.fixture
def sessions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[sessionmaker[Session]]:
    url = f"sqlite+pysqlite:///{(tmp_path / 'commercial.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = create_database_engine(url)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        session.add_all(
            [
                Branch(
                    code="sucursal-uno", name="Uno", address="Dirección uno", business_hours="Lunes"
                ),
                Branch(
                    code="sucursal-dos",
                    name="Dos",
                    address="Dirección dos",
                    business_hours="Martes",
                ),
            ]
        )
    try:
        yield factory
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


@pytest.fixture
def app(sessions: sessionmaker[Session]):
    application = create_app(HttpSettings(app_env="testing", _env_file=None))
    application.dependency_overrides[get_admin_auth_service] = lambda: AdminAuthService(
        sessions, settings=settings()
    )
    application.dependency_overrides[get_admin_commercial_service] = lambda: AdminCommercialService(
        sessions, settings=settings()
    )
    return application


def login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/admin/auth/login", json={"username": username, "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def test_roles_csrf_and_immutable_branch_scope(app, sessions: sessionmaker[Session]) -> None:
    auth = AdminAuthService(sessions, settings=settings())
    auth.create_user("viewer", PASSWORD)
    auth.create_user("editor", PASSWORD, role=AdminRole.EDITOR)
    auth.create_user("owner", PASSWORD, role=AdminRole.OWNER)
    with sessions.begin() as session:
        foreign = session.scalar(select(Branch).where(Branch.code == "sucursal-dos"))
        assert foreign is not None
        session.add(Product(branch_id=foreign.id, name="Rib eye ajeno", category="Res"))
        session.add(
            ManagedFAQ(
                branch_id=foreign.id,
                category="general",
                question="Pregunta ajena",
                question_key="pregunta ajena",
                answer="Respuesta ajena",
            )
        )
    with (
        TestClient(app, base_url="https://testserver") as viewer,
        TestClient(app, base_url="https://testserver") as editor,
        TestClient(app, base_url="https://testserver") as owner,
    ):
        assert viewer.get(f"{BASE}/branch").status_code == 401
        viewer_csrf = login(viewer, "viewer")
        editor_csrf = login(editor, "editor")
        owner_csrf = login(owner, "owner")
        assert viewer.get(f"{BASE}/branch").json()["code"] == "sucursal-uno"
        assert viewer.get(f"{BASE}/products").json() == []
        assert viewer.get(f"{BASE}/faqs").json() == []
        assert (
            viewer.post(
                f"{BASE}/products", json={"name": "Aguja", "category": "Res"}, headers=viewer_csrf
            ).status_code
            == 403
        )
        assert (
            editor.put(
                f"{BASE}/branch",
                json={"name": "Otro", "address": "Otro", "business_hours": "Lunes"},
                headers=editor_csrf,
            ).status_code
            == 403
        )
        assert (
            editor.post(f"{BASE}/products", json={"name": "Aguja", "category": "Res"}).status_code
            == 403
        )
        assert (
            editor.post(
                f"{BASE}/products", json={"name": "Aguja", "category": "Res"}, headers=editor_csrf
            ).status_code
            == 201
        )
        assert (
            owner.put(
                f"{BASE}/branch",
                json={
                    "name": "Actualizada",
                    "address": "Dirección nueva",
                    "phone": None,
                    "business_hours": "Lunes",
                    "code": "sucursal-dos",
                },
                headers=owner_csrf,
            ).status_code
            == 422
        )
        updated = owner.put(
            f"{BASE}/branch",
            json={
                "name": "Actualizada",
                "address": "Dirección nueva",
                "phone": None,
                "business_hours": "Lunes",
            },
            headers=owner_csrf,
        )
        assert updated.status_code == 200
        assert updated.json()["code"] == "sucursal-uno"
        assert owner.get(f"{BASE}/branch").headers["cache-control"] == "no-store"
        with TestClient(app, base_url="http://testserver") as plain:
            assert plain.get(f"{BASE}/branch").status_code == 403
    with sessions() as session:
        assert session.scalar(select(Branch.name).where(Branch.code == "sucursal-dos")) == "Dos"
        assert [(a.resource, a.action) for a in session.scalars(select(AdminCommercialAudit))] == [
            ("product", "create"),
            ("branch", "update"),
        ]


def test_product_price_and_faq_lifecycle_with_audit(app, sessions: sessionmaker[Session]) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        product = client.post(
            f"{BASE}/products", json={"name": "Rib eye", "category": "Res"}, headers=csrf
        )
        assert product.status_code == 201
        product_id = product.json()["id"]
        assert (
            client.post(
                f"{BASE}/products", json={"name": "Rib eye", "category": "Res"}, headers=csrf
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"{BASE}/products", json={"name": " ", "category": "Res"}, headers=csrf
            ).status_code
            == 422
        )
        assert (
            client.put(
                f"{BASE}/products/{product_id}",
                json={"name": "Rib eye", "category": "Premium", "is_active": True},
                headers=csrf,
            ).status_code
            == 200
        )
        price_path = f"{BASE}/products/{product_id}/prices/kg"
        assert client.put(price_path, json={"amount": 123.45}, headers=csrf).status_code == 422
        assert (
            client.put(
                price_path, json={"amount": "123.45", "branch_id": 2}, headers=csrf
            ).status_code
            == 422
        )
        assert client.put(price_path, json={"amount": "123.45"}, headers=csrf).status_code == 200
        assert (
            client.put(price_path, json={"amount": "130.00"}, headers=csrf).json()["amount"]
            == "130.00"
        )
        assert client.get(f"{BASE}/products/{product_id}/prices").json()[0]["unit"] == "kg"
        assert client.delete(price_path, headers=csrf).status_code == 204
        assert client.delete(price_path, headers=csrf).status_code == 404
        faq_payload = {
            "category": "pagos",
            "question": "¿Aceptan tarjeta?",
            "answer": "Sí, aceptamos tarjeta.",
        }
        faq = client.post(f"{BASE}/faqs", json=faq_payload, headers=csrf)
        assert faq.status_code == 201
        faq_id = faq.json()["id"]
        assert (
            client.post(
                f"{BASE}/faqs", json={**faq_payload, "question": "aceptan TARJETA"}, headers=csrf
            ).status_code
            == 409
        )
        assert (
            client.post(
                f"{BASE}/faqs",
                json={**faq_payload, "answer": "Texto\ninválido"},
                headers=csrf,
            ).status_code
            == 422
        )
        assert (
            client.post(
                f"{BASE}/faqs", json={**faq_payload, "branch_id": 2}, headers=csrf
            ).status_code
            == 422
        )
        assert (
            client.put(
                f"{BASE}/faqs/{faq_id}",
                json={**faq_payload, "answer": "Sí, con terminal."},
                headers=csrf,
            ).status_code
            == 200
        )
        assert client.delete(f"{BASE}/faqs/{faq_id}", headers=csrf).status_code == 204
        assert client.get(f"{BASE}/faqs").json()[0]["is_active"] is False
        assert client.delete(f"{BASE}/products/{product_id}", headers=csrf).status_code == 204
        assert client.get(f"{BASE}/products").json()[0]["is_active"] is False
        assert (
            client.put(
                f"{BASE}/products/{product_id}",
                json={"name": "Rib eye", "category": "Premium", "is_active": True},
                headers=csrf,
            ).status_code
            == 200
        )
    with sessions() as session:
        audits = session.scalars(
            select(AdminCommercialAudit).order_by(AdminCommercialAudit.id)
        ).all()
        assert [(a.resource, a.action) for a in audits] == [
            ("product", "create"),
            ("product", "update"),
            ("price", "create"),
            ("price", "update"),
            ("price", "delete"),
            ("faq", "create"),
            ("faq", "update"),
            ("faq", "deactivate"),
            ("product", "deactivate"),
            ("product", "update"),
        ]
        assert str(audits[3].old_amount) == "123.45"
        assert str(audits[3].new_amount) == "130.00"
        assert all(
            audit.product_id == product_id and audit.unit == "kg"
            for audit in audits
            if audit.resource == "price"
        )
        assert "Sí, con terminal" not in repr(audits)


def test_foreign_ids_never_modify_other_branch(app, sessions: sessionmaker[Session]) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "owner", PASSWORD, role=AdminRole.OWNER
    )
    with sessions.begin() as session:
        foreign = session.scalar(select(Branch).where(Branch.code == "sucursal-dos"))
        assert foreign is not None
        product = Product(branch_id=foreign.id, name="Ajeno", category="Res")
        session.add(product)
        session.flush()
        session.add(Price(branch_id=foreign.id, product_id=product.id, unit="kg", amount="90.00"))
        faq = ManagedFAQ(
            branch_id=foreign.id,
            category="general",
            question="Ajena",
            question_key="ajena",
            answer="No",
        )
        session.add(faq)
        session.flush()
        product_id, faq_id = product.id, faq.id
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "owner")
        assert (
            client.put(
                f"{BASE}/products/{product_id}",
                json={"name": "Cambio", "category": "Res", "is_active": True},
                headers=csrf,
            ).status_code
            == 404
        )
        assert client.delete(f"{BASE}/products/{product_id}", headers=csrf).status_code == 404
        assert client.get(f"{BASE}/products/{product_id}/prices").status_code == 404
        assert (
            client.put(
                f"{BASE}/products/{product_id}/prices/kg", json={"amount": "1.00"}, headers=csrf
            ).status_code
            == 404
        )
        assert (
            client.delete(f"{BASE}/products/{product_id}/prices/kg", headers=csrf).status_code
            == 404
        )
        assert (
            client.put(
                f"{BASE}/faqs/{faq_id}",
                json={"category": "general", "question": "Ajena", "answer": "Cambiada"},
                headers=csrf,
            ).status_code
            == 404
        )
        assert client.delete(f"{BASE}/faqs/{faq_id}", headers=csrf).status_code == 404
        assert client.get(f"{BASE}/products").json() == []
        assert client.get(f"{BASE}/faqs").json() == []
    with sessions() as session:
        assert session.get(Product, product_id).name == "Ajeno"
        assert session.get(ManagedFAQ, faq_id).answer == "No"
        assert session.scalars(select(AdminCommercialAudit)).all() == []
        own_branch_id = session.scalar(select(Branch.id).where(Branch.code == "sucursal-uno"))
        owner_id = session.scalar(select(AdminUser.id).where(AdminUser.username == "owner"))
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(
                AdminCommercialAudit(
                    branch_id=own_branch_id,
                    actor_user_id=owner_id,
                    resource="price",
                    resource_id=999,
                    action="delete",
                    product_id=product_id,
                    unit="kg",
                    old_amount="90.00",
                )
            )


def test_audit_failure_rolls_back_price_change(app, sessions: sessionmaker[Session]) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        product_id = client.post(
            f"{BASE}/products", json={"name": "Aguja", "category": "Res"}, headers=csrf
        ).json()["id"]

        def reject_audit(*_args: object) -> None:
            raise IntegrityError("test audit failure", {}, Exception("private test detail"))

        event.listen(AdminCommercialAudit, "before_insert", reject_audit)
        try:
            response = client.put(
                f"{BASE}/products/{product_id}/prices/kg", json={"amount": "50.00"}, headers=csrf
            )
        finally:
            event.remove(AdminCommercialAudit, "before_insert", reject_audit)
        assert response.status_code == 503
        assert "private test detail" not in response.text
        assert client.get(f"{BASE}/products/{product_id}/prices").json() == []
    with sessions() as session:
        assert (
            session.scalars(
                select(AdminCommercialAudit).where(AdminCommercialAudit.resource == "price")
            ).all()
            == []
        )


def test_sql_like_text_stays_data_and_is_not_copied_to_audit(
    app, sessions: sessionmaker[Session]
) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "editor", PASSWORD, role=AdminRole.EDITOR
    )
    injected = "Rib eye'); DROP TABLE branches;--"
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "editor")
        created = client.post(
            f"{BASE}/products", json={"name": injected, "category": "Res"}, headers=csrf
        )
        assert created.status_code == 201
        assert created.json()["name"] == injected
        assert (
            client.put(
                f"{BASE}/products/{created.json()['id']}/prices/kg",
                json={"amount": "1; DROP TABLE prices"},
                headers=csrf,
            ).status_code
            == 422
        )
        faq = client.post(
            f"{BASE}/faqs",
            json={
                "category": "general",
                "question": "¿Hay rib eye?",
                "answer": "<script>alert('dato')</script>",
            },
            headers=csrf,
        )
        assert faq.status_code == 201
        assert faq.json()["answer"] == "<script>alert('dato')</script>"
        assert client.get(f"{BASE}/branch").status_code == 200
    with sessions() as session:
        assert session.scalar(select(Branch.name).where(Branch.code == "sucursal-uno")) == "Uno"
        receipts = session.scalars(select(AdminCommercialAudit)).all()
        assert len(receipts) == 2
        assert injected not in repr(receipts)
        assert "<script>" not in repr(receipts)
