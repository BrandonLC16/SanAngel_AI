"""Cross-route security regression checks for the administrative panel."""

import re
from datetime import UTC, datetime, timedelta

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from backend.app.api.routes.admin_auth import get_admin_auth_service
from backend.app.api.routes.admin_price_import import _service as get_price_import_service
from backend.app.api.routes.admin_review import get_admin_review_service
from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import HttpSettings
from backend.app.db.models.admin_user import AdminLoginThrottle, AdminSession
from backend.app.main import create_app
from backend.app.services.admin_auth_service import AdminAuthService
from backend.tests.test_admin_commercial import PASSWORD, login, settings

pytest_plugins = ("backend.tests.test_admin_commercial",)
ADMIN_PREFIX = "/api/v1/admin"
LOGIN_PATH = f"{ADMIN_PREFIX}/auth/login"
FAQ = {"category": "general", "question": "Horario", "answer": "Lunes", "is_active": True}


def admin_routes(app) -> list[tuple[str, str]]:
    def registered(routes):
        for route in routes:
            if isinstance(route, APIRoute):
                yield route
            elif hasattr(route, "original_router"):
                yield from registered(route.original_router.routes)

    routes = [
        (method, route.path)
        for route in registered(app.routes)
        if route.path.startswith(ADMIN_PREFIX)
        for method in route.methods or ()
        if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    ]
    assert len(routes) >= 20
    return routes


def concrete_path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", lambda match: "kg" if match.group() == "{unit}" else "1", path)


def request_options(method: str, path: str) -> dict[str, object]:
    if method == "PUT" and path.endswith("/branch"):
        return {"json": {"name": "Sucursal", "address": "Calle 1", "business_hours": "Lunes"}}
    if path.endswith("/products") and method == "POST":
        return {"json": {"name": "Aguja", "category": "Res"}}
    if method == "PUT" and re.search(r"/products/\{product_id\}$", path):
        return {"json": {"name": "Aguja", "category": "Res", "is_active": True}}
    if method == "PUT" and path.endswith("/prices/{unit}"):
        return {"json": {"amount": "10.00"}}
    if (path.endswith("/faqs") and method == "POST") or path.endswith("/faqs/{faq_id}"):
        return {"json": FAQ}
    if path.endswith("/users/{user_id}/role"):
        return {"json": {"role": "viewer"}}
    if path.endswith("/price-import/preview"):
        return {
            "content": b"invalid-workbook",
            "headers": {
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "X-File-Name": "precios.xlsx",
            },
        }
    if path.endswith("/price-import/confirm"):
        return {"json": {"preview_id": "a" * 32, "confirmed": True}}
    if path.endswith("/resolve"):
        return {"json": FAQ}
    return {}


def isolated_service_overrides(app) -> None:
    # These endpoint services are not reached when authentication or CSRF rejects a request.
    app.dependency_overrides[get_price_import_service] = object
    app.dependency_overrides[get_admin_review_service] = object


def test_every_admin_business_route_rejects_anonymous_requests(app) -> None:
    isolated_service_overrides(app)
    routes = admin_routes(app)
    # Login is public by design and grants no data without a password.
    assert ("POST", LOGIN_PATH) in routes
    with TestClient(app, base_url="https://testserver") as client:
        for method, path in routes:
            if (method, path) == ("POST", LOGIN_PATH):
                continue
            response = client.request(method, concrete_path(path), **request_options(method, path))
            assert response.status_code == 401, (method, path, response.status_code)
            assert "Traceback" not in response.text


def test_every_authenticated_admin_write_requires_its_own_csrf(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "owner", PASSWORD, role=AdminRole.OWNER
    )
    isolated_service_overrides(app)
    mutations = [
        (method, path)
        for method, path in admin_routes(app)
        if method in {"POST", "PUT", "PATCH", "DELETE"} and path != LOGIN_PATH
    ]
    assert len(mutations) >= 10
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "owner")["X-CSRF-Token"]
        for method, path in mutations:
            options = request_options(method, path)
            missing = client.request(method, concrete_path(path), **options)
            assert missing.status_code == 403, (method, path, missing.status_code)
            wrong_headers = {**options.get("headers", {}), "X-CSRF-Token": "wrong"}
            wrong = client.request(
                method, concrete_path(path), **{**options, "headers": wrong_headers}
            )
            assert wrong.status_code == 403, (method, path, wrong.status_code)
            assert csrf not in missing.text + wrong.text


def test_backend_roles_ignore_forged_role_claims(app, sessions) -> None:
    auth = AdminAuthService(sessions, settings=settings())
    auth.create_user("viewer", PASSWORD)
    auth.create_user("editor", PASSWORD, role=AdminRole.EDITOR)
    with (
        TestClient(app, base_url="https://testserver") as viewer,
        TestClient(app, base_url="https://testserver") as editor,
    ):
        viewer_csrf = login(viewer, "viewer")
        editor_csrf = login(editor, "editor")
        forged = {"X-Admin-Role": "owner", "X-Branch-Code": "sucursal-dos"}
        assert viewer.get(f"{ADMIN_PREFIX}/commercial/branch", headers=forged).status_code == 200
        assert viewer.get(f"{ADMIN_PREFIX}/users", headers=forged).status_code == 403
        assert viewer.get(f"{ADMIN_PREFIX}/audit/events", headers=forged).status_code == 403
        assert (
            viewer.post(
                f"{ADMIN_PREFIX}/commercial/products",
                json={"name": "Aguja", "category": "Res"},
                headers={**forged, **viewer_csrf},
            ).status_code
            == 403
        )
        assert editor.get(f"{ADMIN_PREFIX}/users").status_code == 200
        assert editor.get(f"{ADMIN_PREFIX}/audit/events", headers=forged).status_code == 403
        assert (
            editor.put(
                f"{ADMIN_PREFIX}/commercial/branch",
                json={"name": "Ajena", "address": "Calle 1", "business_hours": "Lunes"},
                headers={**forged, **editor_csrf},
            ).status_code
            == 403
        )


def test_cors_preflight_does_not_grant_admin_access(sessions) -> None:
    app = create_app(
        HttpSettings(
            app_env="testing", cors_allowed_origins=("https://panel.example",), _env_file=None
        )
    )
    app.dependency_overrides[get_admin_auth_service] = lambda: AdminAuthService(
        sessions, settings=settings()
    )
    with TestClient(app, base_url="https://testserver") as client:
        path = f"{ADMIN_PREFIX}/commercial/products"
        allowed = client.options(
            path,
            headers={
                "Origin": "https://panel.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-csrf-token",
            },
        )
        denied = client.options(
            path,
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-csrf-token",
            },
        )
        assert allowed.status_code == 200
        assert allowed.headers["access-control-allow-origin"] == "https://panel.example"
        assert allowed.headers["access-control-allow-credentials"] == "true"
        assert denied.status_code == 400
        assert "access-control-allow-origin" not in denied.headers
        actual = client.post(
            path,
            json={"name": "Aguja", "category": "Res"},
            headers={"Origin": "https://panel.example"},
        )
        assert actual.status_code == 401


def test_throttle_persists_and_recovers_after_window(app, sessions, monkeypatch) -> None:
    import backend.app.services.admin_auth_service as auth_module

    monkeypatch.setattr(auth_module, "USERNAME_LIMIT", 2)
    AdminAuthService(sessions, settings=settings()).create_user(
        "owner", PASSWORD, role=AdminRole.OWNER
    )
    with TestClient(app, base_url="https://testserver") as client:
        for _ in range(2):
            assert (
                client.post(
                    LOGIN_PATH, json={"username": "owner", "password": "incorrect"}
                ).status_code
                == 401
            )
        assert (
            client.post(LOGIN_PATH, json={"username": "owner", "password": PASSWORD}).status_code
            == 429
        )
    with sessions.begin() as session:
        buckets = session.scalars(select(AdminLoginThrottle)).all()
        assert len(buckets) == 2
        assert all(len(bucket.bucket_key) == 64 for bucket in buckets)
        assert "owner" not in repr(buckets)
        session.execute(
            update(AdminLoginThrottle).values(
                window_started_at=datetime.now(UTC) - timedelta(minutes=16)
            )
        )
    with TestClient(app, base_url="https://testserver") as client:
        assert (
            client.post(LOGIN_PATH, json={"username": "owner", "password": PASSWORD}).status_code
            == 200
        )


def test_expired_cookie_cannot_read_or_write_admin_data(app, sessions) -> None:
    AdminAuthService(sessions, settings=settings()).create_user(
        "owner", PASSWORD, role=AdminRole.OWNER
    )
    with TestClient(app, base_url="https://testserver") as client:
        csrf = login(client, "owner")
        assert client.get(f"{ADMIN_PREFIX}/me").status_code == 200
        with sessions.begin() as session:
            session.execute(
                update(AdminSession).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
            )
        assert client.get(f"{ADMIN_PREFIX}/auth/session").status_code == 401
        assert client.get(f"{ADMIN_PREFIX}/me").status_code == 401
        assert client.get(f"{ADMIN_PREFIX}/audit/events").status_code == 401
        assert (
            client.post(
                f"{ADMIN_PREFIX}/commercial/products",
                json={"name": "Aguja", "category": "Res"},
                headers=csrf,
            ).status_code
            == 401
        )
