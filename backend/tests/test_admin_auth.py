"""Offline admin authentication, session, CSRF, and throttling boundaries."""

import logging
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes.admin_auth import COOKIE_NAME, get_admin_auth_service
from backend.app.cli.create_admin_user import main as create_admin_main
from backend.app.core.config import AdminAuthSettings, HttpSettings, get_database_settings
from backend.app.core.exceptions import AdminAuthenticationError, AdminRateLimitError
from backend.app.db.models.admin_user import AdminLoginThrottle, AdminSession, AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.main import create_app
from backend.app.services.admin_auth_service import AdminAuthService

ROOT = Path(__file__).resolve().parents[2]
PASSWORD = "test-only-admin-password-123"
OTHER_PASSWORD = "test-only-other-password-456"
AUTH_KEY = "test-only-admin-auth-key-123456789012345"


def settings(branch: str = "sucursal-uno") -> AdminAuthSettings:
    return AdminAuthSettings(assistant_branch_code=branch, admin_auth_key=AUTH_KEY, _env_file=None)


@pytest.fixture
def sessions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[sessionmaker[Session]]:
    url = f"sqlite+pysqlite:///{(tmp_path / 'admin-auth.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = create_database_engine(url)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        session.add_all(
            (
                Branch(
                    code="sucursal-uno",
                    name="Sucursal Uno",
                    address="Dirección de prueba",
                    business_hours="Lunes a viernes",
                ),
                Branch(
                    code="sucursal-dos",
                    name="Sucursal Dos",
                    address="Dirección de prueba",
                    business_hours="Lunes a viernes",
                ),
            )
        )
    try:
        yield factory
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


@pytest.fixture
def client(sessions: sessionmaker[Session]) -> Generator[TestClient]:
    app = create_app(HttpSettings(app_env="testing", _env_file=None))
    app.dependency_overrides[get_admin_auth_service] = lambda: AdminAuthService(
        sessions, settings=settings()
    )
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client


def test_password_never_plain_and_cookie_session_revokes_on_logout(
    sessions: sessionmaker[Session], client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    AdminAuthService(sessions, settings=settings()).create_user("Owner", PASSWORD)
    with sessions() as session:
        user = session.scalar(select(AdminUser))
        assert user is not None
        assert user.username == "owner"
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash + repr(user)

    with caplog.at_level(logging.INFO):
        wrong = client.post(
            "/api/v1/admin/auth/login", json={"username": "owner", "password": OTHER_PASSWORD}
        )
        assert wrong.status_code == 401
        logged_in = client.post(
            "/api/v1/admin/auth/login", json={"username": "OWNER", "password": PASSWORD}
        )
        assert logged_in.status_code == 200
        cookie = logged_in.headers["set-cookie"]
        assert cookie.startswith(f"{COOKIE_NAME}=")
        assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=strict" in cookie
        assert "Path=/" in cookie and "Domain=" not in cookie
        assert "Max-Age=28800" in cookie
        assert logged_in.headers["cache-control"] == "no-store"
        assert "token" not in logged_in.json()
        assert PASSWORD not in logged_in.text
        session_info = client.get("/api/v1/admin/auth/session")
        assert session_info.status_code == 200
        assert session_info.json()["username"] == "owner"
        assert session_info.json()["expires_at"].endswith("Z")
        csrf = session_info.json()["csrf_token"]
        assert csrf == logged_in.json()["csrf_token"]
        assert client.post("/api/v1/admin/auth/logout").status_code == 403
        assert (
            client.post(
                "/api/v1/admin/auth/logout", headers={"X-CSRF-Token": "invalid"}
            ).status_code
            == 403
        )
        assert (
            client.post("/api/v1/admin/auth/logout", headers={"X-CSRF-Token": csrf}).status_code
            == 204
        )
        assert client.get("/api/v1/admin/auth/session").status_code == 401

    with sessions() as session:
        stored = session.scalar(select(AdminSession))
        assert stored is not None and stored.revoked_at is not None
        assert len(stored.token_hash) == 64
        raw_token = cookie.split(";", 1)[0].split("=", 1)[1]
        assert raw_token not in stored.token_hash + repr(stored)
    assert PASSWORD not in caplog.text
    assert OTHER_PASSWORD not in caplog.text
    assert csrf not in caplog.text
    assert AUTH_KEY not in caplog.text


def test_login_is_limited_by_username_and_peer_without_storing_their_values(
    sessions: sessionmaker[Session], client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import backend.app.services.admin_auth_service as auth_module

    monkeypatch.setattr(auth_module, "USERNAME_LIMIT", 2)
    for _ in range(2):
        assert (
            client.post(
                "/api/v1/admin/auth/login", json={"username": "missing", "password": PASSWORD}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/v1/admin/auth/login", json={"username": "missing", "password": PASSWORD}
        ).status_code
        == 429
    )
    with sessions() as session:
        buckets = session.scalars(select(AdminLoginThrottle)).all()
        assert len(buckets) == 2
        assert all(len(bucket.bucket_key) == 64 for bucket in buckets)
        assert "missing" not in repr(buckets)

    monkeypatch.setattr(auth_module, "PEER_LIMIT", 5)
    assert (
        client.post(
            "/api/v1/admin/auth/login", json={"username": "another", "password": PASSWORD}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/admin/auth/login", json={"username": "third", "password": PASSWORD}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/admin/auth/login", json={"username": "fourth", "password": PASSWORD}
        ).status_code
        == 429
    )


def test_branch_scope_expiry_and_rehash(sessions: sessionmaker[Session]) -> None:
    own = AdminAuthService(sessions, settings=settings())
    foreign = AdminAuthService(sessions, settings=settings("sucursal-dos"))
    own.create_user("owner", PASSWORD)
    foreign.create_user("owner", OTHER_PASSWORD)
    with pytest.raises(AdminAuthenticationError):
        foreign.login("owner", PASSWORD, peer="local")

    weak_hash = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    with sessions.begin() as session:
        user = session.scalar(
            select(AdminUser).where(AdminUser.username == "owner", AdminUser.branch_id == 1)
        )
        assert user is not None
        user.password_hash = weak_hash
    result = own.login("owner", PASSWORD, peer="local")
    with sessions.begin() as session:
        user = session.scalar(
            select(AdminUser).where(AdminUser.username == "owner", AdminUser.branch_id == 1)
        )
        assert user is not None
        assert user.password_hash != weak_hash
        assert not PasswordHasher().check_needs_rehash(user.password_hash)
        stored = session.scalar(select(AdminSession).where(AdminSession.branch_id == 1))
        assert stored is not None
        stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(AdminAuthenticationError):
        own.get_session(result.token)
    with pytest.raises(AdminAuthenticationError):
        foreign.get_session(result.token)


def test_concurrent_login_attempts_observe_persistent_limit(
    sessions: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    import backend.app.services.admin_auth_service as auth_module

    monkeypatch.setattr(auth_module, "USERNAME_LIMIT", 2)
    service = AdminAuthService(sessions, settings=settings())

    def attempt() -> str:
        try:
            service.login("missing", PASSWORD, peer="same-peer")
        except AdminRateLimitError:
            return "limited"
        except AdminAuthenticationError:
            return "invalid"
        return "unexpected"

    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: attempt(), range(6)))
    assert results.count("invalid") == 2
    assert results.count("limited") == 4


def test_admin_auth_rejects_plain_http_without_issuing_cookie(client: TestClient) -> None:
    with TestClient(client.app, base_url="http://testserver") as plain_client:
        response = plain_client.post(
            "/api/v1/admin/auth/login",
            json={"username": "owner", "password": PASSWORD},
        )
    assert response.status_code == 403
    assert "set-cookie" not in response.headers


def test_auth_settings_hide_secret_and_reject_short_key() -> None:
    assert AUTH_KEY not in repr(settings())
    with pytest.raises(ValueError) as exc_info:
        AdminAuthSettings(
            assistant_branch_code="sucursal-uno",
            admin_auth_key="short",
            _env_file=None,
        )
    assert "short" not in str(exc_info.value)


def test_invalid_login_body_does_not_echo_password(client: TestClient) -> None:
    private_password = "test-only-rejected-password"
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "owner", "password": private_password, "extra": "invalid"},
    )
    assert response.status_code == 422
    assert private_password not in response.text


def test_database_rejects_plain_password_and_cross_branch_session(
    sessions: sessionmaker[Session],
) -> None:
    own = AdminAuthService(sessions, settings=settings())
    own.create_user("owner", PASSWORD)
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(AdminUser(branch_id=1, username="plain", password_hash=PASSWORD))
            session.flush()
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            user = session.scalar(select(AdminUser).where(AdminUser.username == "owner"))
            assert user is not None
            session.add(
                AdminSession(
                    branch_id=2,
                    user_id=user.id,
                    token_hash="a" * 64,
                    created_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )
            session.flush()


def test_local_provisioning_prompts_without_password_argument_or_output(
    sessions: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ASSISTANT_BRANCH_CODE", "sucursal-uno")
    monkeypatch.setenv("ADMIN_AUTH_KEY", AUTH_KEY)
    monkeypatch.setattr(
        "backend.app.cli.create_admin_user.getpass.getpass", lambda _prompt: PASSWORD
    )
    assert create_admin_main(["--username", "operator"]) == 0
    captured = capsys.readouterr()
    assert PASSWORD not in captured.out + captured.err
    with sessions() as session:
        user = session.scalar(select(AdminUser).where(AdminUser.username == "operator"))
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
