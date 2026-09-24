"""Persistent branch-scoped admin authentication with opaque revocable sessions."""

import hashlib
import hmac
import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from threading import BoundedSemaphore

from argon2 import PasswordHasher
from argon2.exceptions import HashingError, InvalidHashError, VerificationError
from sqlalchemy import case, delete, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, aliased, sessionmaker

from backend.app.core.admin_roles import AdminPermission, AdminRole, permits
from backend.app.core.config import AdminAuthSettings
from backend.app.core.exceptions import (
    AdminAuthenticationError,
    AdminAuthorizationError,
    AdminCsrfError,
    AdminRateLimitError,
    AdminUserNotFoundError,
    ServiceUnavailableError,
)
from backend.app.db.models.admin_user import (
    AdminLoginThrottle,
    AdminRoleAudit,
    AdminSession,
    AdminUser,
)
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService

SESSION_SECONDS = 8 * 60 * 60
THROTTLE_WINDOW = timedelta(minutes=15)
USERNAME_LIMIT = 5
PEER_LIMIT = 20
USERNAME_PATTERN = re.compile(r"[a-z][a-z0-9._-]{2,63}")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")
PASSWORD_HASHER = PasswordHasher()
_HASH_SLOTS = BoundedSemaphore(4)


@lru_cache
def _dummy_hash() -> str:
    return PASSWORD_HASHER.hash("test-only-dummy-password")


@dataclass(frozen=True, slots=True)
class AdminSessionInfo:
    username: str
    expires_at: datetime
    csrf_token: str = field(repr=False)
    user_id: int
    branch_id: int
    role: AdminRole


@dataclass(frozen=True, slots=True)
class AdminUserSummary:
    id: int
    username: str
    role: AdminRole
    is_active: bool


@dataclass(frozen=True, slots=True)
class AdminLoginResult:
    token: str = field(repr=False)
    session: AdminSessionInfo


class AdminAuthService:
    """Never accept a branch from callers or persist a raw password or session token."""

    def __init__(self, sessions: sessionmaker[Session], *, settings: AdminAuthSettings) -> None:
        self._sessions = sessions
        self._scope = BranchScope.from_settings(settings)
        self._key = settings.admin_auth_key.get_secret_value().encode("ascii")

    def create_user(
        self, username: str, password: str, *, role: AdminRole = AdminRole.VIEWER
    ) -> None:
        """Local provisioning operation; there is intentionally no public registration route."""
        normalized = self._username(username)
        if not isinstance(password, str) or not 12 <= len(password) <= 1024:
            raise ValueError("password length must be between 12 and 1024")
        if not isinstance(role, AdminRole):
            raise ValueError("invalid admin role")
        try:
            password_hash = PASSWORD_HASHER.hash(password)
        except HashingError:
            raise ServiceUnavailableError("password hashing failed") from None
        try:
            with self._sessions.begin() as session:
                branch_id = self._branch_id(session)
                session.add(
                    AdminUser(
                        branch_id=branch_id,
                        username=normalized,
                        password_hash=password_hash,
                        role=role.value,
                    )
                )
        except IntegrityError:
            raise ValueError("admin user already exists") from None
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin provisioning failed") from None

    def login(self, username: str, password: str, *, peer: str) -> AdminLoginResult:
        normalized = self._username(username)
        if not isinstance(password, str) or not 1 <= len(password) <= 1024:
            raise AdminAuthenticationError() from None
        if not isinstance(peer, str) or not 1 <= len(peer) <= 128:
            peer = "unknown"
        now = datetime.now(UTC)
        try:
            with self._sessions.begin() as session:
                branch_id = self._branch_id(session)
                session.execute(
                    delete(AdminLoginThrottle).where(
                        AdminLoginThrottle.branch_id == branch_id,
                        AdminLoginThrottle.window_started_at < now - timedelta(days=1),
                    )
                )
                session.execute(
                    delete(AdminSession).where(
                        AdminSession.branch_id == branch_id,
                        AdminSession.expires_at < now - timedelta(days=1),
                    )
                )
                peer_attempts = self._increment_bucket(session, branch_id, "peer", peer, now)
                username_attempts = (
                    self._increment_bucket(session, branch_id, "user", normalized, now)
                    if peer_attempts <= PEER_LIMIT
                    else 0
                )
                limited = peer_attempts > PEER_LIMIT or username_attempts > USERNAME_LIMIT
            if limited:
                raise AdminRateLimitError()

            with self._sessions.begin() as session:
                branch_id = self._branch_id(session)
                user = session.scalar(
                    select(AdminUser).where(
                        AdminUser.branch_id == branch_id,
                        AdminUser.username == normalized,
                        AdminUser.is_active.is_(True),
                    )
                )
                if not _HASH_SLOTS.acquire(timeout=1):
                    raise AdminRateLimitError()
                try:
                    try:
                        verified = PASSWORD_HASHER.verify(
                            user.password_hash if user is not None else _dummy_hash(), password
                        )
                    except (InvalidHashError, VerificationError):
                        verified = False
                finally:
                    _HASH_SLOTS.release()
                if not verified or user is None:
                    raise AdminAuthenticationError()
                if PASSWORD_HASHER.check_needs_rehash(user.password_hash):
                    try:
                        user.password_hash = PASSWORD_HASHER.hash(password)
                    except HashingError:
                        raise ServiceUnavailableError("password rehash failed") from None
                token = secrets.token_urlsafe(32)
                expires_at = now + timedelta(seconds=SESSION_SECONDS)
                session.add(
                    AdminSession(
                        branch_id=branch_id,
                        user_id=user.id,
                        token_hash=self._token_hash(token),
                        created_at=now,
                        expires_at=expires_at,
                    )
                )
            return AdminLoginResult(
                token=token,
                session=AdminSessionInfo(
                    username=normalized,
                    expires_at=expires_at,
                    csrf_token=self._csrf_token(token),
                    user_id=user.id,
                    branch_id=branch_id,
                    role=AdminRole(user.role),
                ),
            )
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin login persistence failed") from None

    def get_session(self, token: str | None) -> AdminSessionInfo:
        if not isinstance(token, str) or TOKEN_PATTERN.fullmatch(token) is None:
            raise AdminAuthenticationError() from None
        try:
            with self._sessions() as session:
                branch_id = self._branch_id(session)
                result = session.execute(
                    select(AdminSession, AdminUser)
                    .join(
                        AdminUser,
                        (AdminUser.id == AdminSession.user_id)
                        & (AdminUser.branch_id == AdminSession.branch_id),
                    )
                    .where(
                        AdminSession.branch_id == branch_id,
                        AdminSession.token_hash == self._token_hash(token),
                        AdminSession.revoked_at.is_(None),
                        AdminSession.expires_at > datetime.now(UTC),
                        AdminUser.is_active.is_(True),
                    )
                ).one_or_none()
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin session lookup failed") from None
        if result is None:
            raise AdminAuthenticationError()
        stored, user = result
        expires_at = stored.expires_at
        expires_at = (
            expires_at.replace(tzinfo=UTC)
            if expires_at.tzinfo is None
            else expires_at.astimezone(UTC)
        )
        return AdminSessionInfo(
            username=user.username,
            expires_at=expires_at,
            csrf_token=self._csrf_token(token),
            user_id=user.id,
            branch_id=stored.branch_id,
            role=AdminRole(user.role),
        )

    def list_users(self, token: str | None) -> list[AdminUserSummary]:
        principal = self.get_session(token)
        self._require_permission(principal, AdminPermission.USERS_READ)
        try:
            with self._sessions() as session:
                current_role = session.scalar(
                    select(AdminUser.role).where(
                        AdminUser.id == principal.user_id,
                        AdminUser.branch_id == principal.branch_id,
                        AdminUser.is_active.is_(True),
                    )
                )
                if current_role is None or not permits(
                    AdminRole(current_role), AdminPermission.USERS_READ
                ):
                    raise AdminAuthorizationError()
                users = session.scalars(
                    select(AdminUser)
                    .where(AdminUser.branch_id == principal.branch_id)
                    .order_by(AdminUser.id)
                ).all()
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin user lookup failed") from None
        return [self._user_summary(user) for user in users]

    def change_role(
        self, token: str | None, csrf_token: str | None, user_id: int, role: AdminRole
    ) -> AdminUserSummary:
        principal = self.get_session(token)
        self._require_permission(principal, AdminPermission.USERS_ROLE_WRITE)
        if not isinstance(csrf_token, str) or not hmac.compare_digest(
            csrf_token, principal.csrf_token
        ):
            raise AdminCsrfError()
        if not isinstance(role, AdminRole) or not isinstance(user_id, int) or user_id < 1:
            raise AdminAuthorizationError()
        if user_id == principal.user_id:
            raise AdminAuthorizationError("self role change refused")
        try:
            with self._sessions.begin() as session:
                current_role = session.scalar(
                    select(AdminUser.role).where(
                        AdminUser.id == principal.user_id,
                        AdminUser.branch_id == principal.branch_id,
                        AdminUser.is_active.is_(True),
                    )
                )
                if current_role != AdminRole.OWNER.value:
                    raise AdminAuthorizationError()
                target = session.scalar(
                    select(AdminUser).where(
                        AdminUser.id == user_id,
                        AdminUser.branch_id == principal.branch_id,
                    )
                )
                if target is None:
                    raise AdminUserNotFoundError()
                if target.role == role.value:
                    return self._user_summary(target)
                old_role = target.role
                actor = aliased(AdminUser)
                actor_is_owner = (
                    select(actor.id)
                    .where(
                        actor.id == principal.user_id,
                        actor.branch_id == principal.branch_id,
                        actor.role == AdminRole.OWNER.value,
                        actor.is_active.is_(True),
                    )
                    .exists()
                )
                changed = session.execute(
                    update(AdminUser)
                    .where(
                        AdminUser.id == user_id,
                        AdminUser.branch_id == principal.branch_id,
                        AdminUser.role == old_role,
                        actor_is_owner,
                    )
                    .values(role=role.value)
                )
                if changed.rowcount != 1:
                    raise AdminAuthorizationError("role changed during request")
                session.add(
                    AdminRoleAudit(
                        branch_id=principal.branch_id,
                        actor_user_id=principal.user_id,
                        target_user_id=user_id,
                        old_role=old_role,
                        new_role=role.value,
                    )
                )
                summary = AdminUserSummary(user_id, target.username, role, target.is_active)
            return summary
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin role update failed") from None

    @staticmethod
    def _require_permission(principal: AdminSessionInfo, permission: AdminPermission) -> None:
        if not permits(principal.role, permission):
            raise AdminAuthorizationError()

    @staticmethod
    def _user_summary(user: AdminUser) -> AdminUserSummary:
        return AdminUserSummary(user.id, user.username, AdminRole(user.role), user.is_active)

    def logout(self, token: str | None, csrf_token: str | None) -> None:
        self.get_session(token)
        if not isinstance(csrf_token, str) or not hmac.compare_digest(
            csrf_token, self._csrf_token(token)
        ):
            raise AdminCsrfError()
        try:
            with self._sessions.begin() as session:
                branch_id = self._branch_id(session)
                result = session.execute(
                    update(AdminSession)
                    .where(
                        AdminSession.branch_id == branch_id,
                        AdminSession.token_hash == self._token_hash(token),
                        AdminSession.revoked_at.is_(None),
                        AdminSession.expires_at > datetime.now(UTC),
                    )
                    .values(revoked_at=datetime.now(UTC))
                )
                if result.rowcount != 1:
                    raise AdminAuthenticationError()
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin session revocation failed") from None

    def _increment_bucket(
        self, session: Session, branch_id: int, kind: str, value: str, now: datetime
    ) -> int:
        bucket_key = hmac.new(
            self._key, f"admin-throttle:{kind}:{value}".encode(), hashlib.sha256
        ).hexdigest()
        cutoff = now - THROTTLE_WINDOW
        expired = AdminLoginThrottle.window_started_at < cutoff
        statement = insert(AdminLoginThrottle).values(
            branch_id=branch_id,
            bucket_key=bucket_key,
            attempts=1,
            window_started_at=now,
        )
        attempts = session.scalar(
            statement.on_conflict_do_update(
                index_elements=["branch_id", "bucket_key"],
                set_={
                    "attempts": case((expired, 1), else_=AdminLoginThrottle.attempts + 1),
                    "window_started_at": case(
                        (expired, now), else_=AdminLoginThrottle.window_started_at
                    ),
                },
            ).returning(AdminLoginThrottle.attempts)
        )
        assert attempts is not None
        return attempts

    def _branch_id(self, session: Session) -> int:
        return (
            BranchService(BranchRepository(session), assistant_branch_code=self._scope.branch_code)
            .get_current_branch()
            .id
        )

    def _csrf_token(self, token: str) -> str:
        return hmac.new(self._key, f"admin-csrf:{token}".encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("ascii")).hexdigest()

    @staticmethod
    def _username(username: str) -> str:
        if not isinstance(username, str):
            raise AdminAuthenticationError()
        normalized = username.strip().lower()
        if USERNAME_PATTERN.fullmatch(normalized) is None:
            raise AdminAuthenticationError()
        return normalized
