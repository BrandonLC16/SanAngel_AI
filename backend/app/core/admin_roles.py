"""Closed, backend-owned administrative roles and permissions."""

from enum import StrEnum


class AdminRole(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    OWNER = "owner"


class AdminPermission(StrEnum):
    PROFILE_READ = "profile:read"
    USERS_READ = "users:read"
    USERS_ROLE_WRITE = "users:role:write"
    COMMERCIAL_READ = "commercial:read"
    COMMERCIAL_WRITE = "commercial:write"
    BRANCH_WRITE = "branch:write"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[AdminRole, frozenset[AdminPermission]] = {
    AdminRole.VIEWER: frozenset({AdminPermission.PROFILE_READ, AdminPermission.COMMERCIAL_READ}),
    AdminRole.EDITOR: frozenset(
        {
            AdminPermission.PROFILE_READ,
            AdminPermission.USERS_READ,
            AdminPermission.COMMERCIAL_READ,
            AdminPermission.COMMERCIAL_WRITE,
        }
    ),
    AdminRole.OWNER: frozenset(AdminPermission),
}


def permits(role: AdminRole, permission: AdminPermission) -> bool:
    """Deny missing or unknown roles and permissions by default."""

    return permission in ROLE_PERMISSIONS.get(role, frozenset())
