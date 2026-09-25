"""Scoped, allowlisted audit view and traceable price changes."""

import json

from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.app.api.routes.admin_audit import get_admin_audit_service
from backend.app.core.admin_roles import AdminRole
from backend.app.db.models.admin_commercial import AdminCommercialAudit
from backend.app.db.models.admin_user import AdminRoleAudit, AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.product import Product
from backend.app.services.admin_audit_service import AdminAuditService
from backend.app.services.admin_auth_service import AdminAuthService
from backend.tests.test_admin_commercial import BASE as COMMERCIAL
from backend.tests.test_admin_commercial import PASSWORD, login, settings

pytest_plugins = ("backend.tests.test_admin_commercial",)
BASE = "/api/v1/admin/audit/events"


def test_owner_reads_manual_price_and_role_history_without_secrets(app, sessions) -> None:
    auth = AdminAuthService(sessions, settings=settings())
    auth.create_user("owner", PASSWORD, role=AdminRole.OWNER)
    auth.create_user("editor", PASSWORD, role=AdminRole.EDITOR)
    auth.create_user("viewer", PASSWORD)
    with sessions() as session:
        owner_id = session.scalar(select(AdminUser.id).where(AdminUser.username == "owner"))
        editor_id = session.scalar(select(AdminUser.id).where(AdminUser.username == "editor"))
    app.dependency_overrides[get_admin_audit_service] = lambda: AdminAuditService(
        sessions, settings=settings()
    )
    with (
        TestClient(app, base_url="https://testserver") as owner,
        TestClient(app, base_url="https://testserver") as editor,
        TestClient(app, base_url="https://testserver") as viewer,
    ):
        assert owner.get(BASE).status_code == 401
        owner_csrf = login(owner, "owner")
        editor_csrf = login(editor, "editor")
        login(viewer, "viewer")
        assert editor.get(BASE).status_code == 403
        assert viewer.get(BASE).status_code == 403
        product = editor.post(
            f"{COMMERCIAL}/products", json={"name": "Aguja", "category": "Res"}, headers=editor_csrf
        )
        assert product.status_code == 201
        product_id = product.json()["id"]
        price_url = f"{COMMERCIAL}/products/{product_id}/prices/kg"
        assert (
            editor.put(price_url, json={"amount": "123.45"}, headers=editor_csrf).status_code == 200
        )
        assert (
            editor.put(price_url, json={"amount": "130.00"}, headers=editor_csrf).status_code == 200
        )
        assert editor.delete(price_url, headers=editor_csrf).status_code == 204
        role = owner.patch(
            f"/api/v1/admin/users/{editor_id}/role",
            json={"role": "viewer"},
            headers=owner_csrf,
        )
        assert role.status_code == 200
        response = owner.get(BASE, params={"entity": "price", "product_id": product_id})
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        events = response.json()["items"]
        assert [item["action"] for item in events] == ["delete", "update", "create"]
        assert [item["before"] for item in events] == [
            {"amount": "130.00"},
            {"amount": "123.45"},
            None,
        ]
        assert [item["after"] for item in events] == [
            None,
            {"amount": "130.00"},
            {"amount": "123.45"},
        ]
        assert all(
            item["actor_user_id"] == editor_id
            and item["product_id"] == product_id
            and item["unit"] == "kg"
            for item in events
        )
        assert all(item["occurred_at"].endswith("Z") for item in events)
        role_event = owner.get(BASE, params={"entity": "admin_user"}).json()["items"][0]
        assert role_event["actor_user_id"] == owner_id
        assert role_event["entity_id"] == editor_id
        assert role_event["before"] == {"role": "editor"}
        assert role_event["after"] == {"role": "viewer"}
        assert owner.get(BASE, params={"entity": "price", "limit": 2}).json()["has_more"] is True
        assert (
            len(
                owner.get(BASE, params={"entity": "price", "limit": 2, "offset": 2}).json()["items"]
            )
            == 1
        )
        assert (
            owner.get(BASE, params={"entity": "faq", "product_id": product_id}).status_code == 422
        )
        assert owner.get(BASE, params={"limit": 101}).status_code == 422
        assert owner.get(BASE, params={"entity": "password"}).status_code == 422
        rendered = json.dumps(owner.get(BASE).json())
        assert PASSWORD not in rendered and "password_hash" not in rendered
        assert "csrf" not in rendered and "token" not in rendered


def test_foreign_branch_receipts_and_role_revocation_are_not_visible(app, sessions) -> None:
    own = AdminAuthService(sessions, settings=settings())
    own.create_user("owner", PASSWORD, role=AdminRole.OWNER)
    foreign = AdminAuthService(sessions, settings=settings("sucursal-dos"))
    foreign.create_user("outsider", PASSWORD, role=AdminRole.OWNER)
    with sessions.begin() as session:
        own_branch = session.scalar(select(Branch).where(Branch.code == "sucursal-uno"))
        foreign_branch = session.scalar(select(Branch).where(Branch.code == "sucursal-dos"))
        owner = session.scalar(select(AdminUser).where(AdminUser.username == "owner"))
        outsider = session.scalar(select(AdminUser).where(AdminUser.username == "outsider"))
        assert own_branch and foreign_branch and owner and outsider
        product = Product(branch_id=foreign_branch.id, name="Ajeno", category="Res")
        session.add(product)
        session.flush()
        session.add(
            AdminCommercialAudit(
                branch_id=foreign_branch.id,
                actor_user_id=outsider.id,
                resource="price",
                resource_id=99,
                action="update",
                product_id=product.id,
                unit="kg",
                old_amount="10.00",
                new_amount="20.00",
            )
        )
        session.add(
            AdminRoleAudit(
                branch_id=foreign_branch.id,
                actor_user_id=outsider.id,
                target_user_id=outsider.id,
                old_role="editor",
                new_role="owner",
            )
        )
        owner_id = owner.id
    app.dependency_overrides[get_admin_audit_service] = lambda: AdminAuditService(
        sessions, settings=settings()
    )
    with TestClient(app, base_url="https://testserver") as client:
        login(client, "owner")
        assert client.get(BASE).json() == {"items": [], "has_more": False}
        with sessions.begin() as session:
            session.query(AdminUser).filter(AdminUser.id == owner_id).update({"role": "viewer"})
        assert client.get(BASE).status_code == 403
    app.dependency_overrides[get_admin_audit_service] = lambda: AdminAuditService(
        sessions, settings=settings("sucursal-dos")
    )
    with TestClient(app, base_url="https://testserver") as client:
        login(client, "owner")
        assert client.get(BASE).status_code == 403
