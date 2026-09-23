"""Branch-scoped persistence for minimal price import audit records."""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.price_import_audit import PriceImportAudit
from backend.app.services.branch_scope import BranchScope
from backend.app.services.price_import_parser import PriceImportIssue

MAX_STORED_IMPORT_ISSUES = 200
ACTOR_ID_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
AuditStatus = Literal["success", "rejected", "failed"]


@dataclass(frozen=True, slots=True)
class ImportActor:
    """Opaque staff identity supplied by trusted backend authentication."""

    actor_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.actor_id, str) or ACTOR_ID_PATTERN.fullmatch(self.actor_id) is None:
            raise ValueError("audit actor must be an opaque staff identifier")


@dataclass(frozen=True, slots=True)
class PriceImportAuditReport:
    audit_id: int
    attempt_id: str
    branch_code: str
    actor_id: str
    occurred_at: datetime
    file_sha256: str | None
    status: AuditStatus
    created: int
    updated: int
    unchanged: int
    error_count: int
    error_code: str | None
    errors: tuple[PriceImportIssue, ...]

    def to_review_data(self) -> dict[str, object]:
        return {
            "audit_id": self.audit_id,
            "attempt_id": self.attempt_id,
            "branch_code": self.branch_code,
            "actor_id": self.actor_id,
            "occurred_at": self.occurred_at.isoformat(),
            "file_sha256": self.file_sha256,
            "status": self.status,
            "summary": {
                "created": self.created,
                "updated": self.updated,
                "unchanged": self.unchanged,
                "errors": self.error_count,
            },
            "error_code": self.error_code,
            "errors_truncated": self.error_count > len(self.errors),
            "errors": [
                {"row": issue.row, "field": issue.field, "code": issue.code}
                for issue in self.errors
            ],
        }


class PriceImportAuditRepository:
    def __init__(self, session: Session, *, branch_scope: BranchScope) -> None:
        self._session = session
        self._branch_code = branch_scope.branch_code

    def record(
        self,
        *,
        attempt_id: str,
        actor: ImportActor,
        file_sha256: str | None,
        status: AuditStatus,
        created: int = 0,
        updated: int = 0,
        unchanged: int = 0,
        error_code: str | None = None,
        issues: tuple[PriceImportIssue, ...] = (),
    ) -> PriceImportAudit:
        all_issues = issues or (
            (PriceImportIssue(None, None, error_code),) if error_code is not None else ()
        )
        stored_issues = all_issues[:MAX_STORED_IMPORT_ISSUES]
        errors_json = json.dumps(
            [
                {"row": issue.row, "field": issue.field, "code": issue.code}
                for issue in stored_issues
            ],
            separators=(",", ":"),
        )
        audit = PriceImportAudit(
            attempt_id=attempt_id,
            branch_code=self._branch_code,
            actor_id=actor.actor_id,
            occurred_at=datetime.now(UTC),
            file_sha256=file_sha256,
            status=status,
            created_count=created,
            updated_count=updated,
            unchanged_count=unchanged,
            error_count=len(all_issues),
            error_code=error_code,
            errors_json=errors_json,
        )
        self._session.add(audit)
        self._session.flush()
        return audit

    def get_report(self, audit_id: int) -> PriceImportAuditReport | None:
        if type(audit_id) is not int or audit_id <= 0:
            raise ValueError("audit_id must be a positive integer")
        audit = self._session.scalar(
            select(PriceImportAudit).where(
                PriceImportAudit.id == audit_id,
                PriceImportAudit.branch_code == self._branch_code,
            )
        )
        return _report(audit) if audit is not None else None

    def list_recent(self, *, limit: int = 50) -> tuple[PriceImportAuditReport, ...]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("audit report limit must be between 1 and 100")
        statement = (
            select(PriceImportAudit)
            .where(PriceImportAudit.branch_code == self._branch_code)
            .order_by(PriceImportAudit.id.desc())
            .limit(limit)
        )
        return tuple(_report(audit) for audit in self._session.scalars(statement))


def _report(audit: PriceImportAudit) -> PriceImportAuditReport:
    issues = tuple(PriceImportIssue(**item) for item in json.loads(audit.errors_json))
    occurred_at = audit.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    return PriceImportAuditReport(
        audit_id=audit.id,
        attempt_id=audit.attempt_id,
        branch_code=audit.branch_code,
        actor_id=audit.actor_id,
        occurred_at=occurred_at,
        file_sha256=audit.file_sha256,
        status=audit.status,
        created=audit.created_count,
        updated=audit.updated_count,
        unchanged=audit.unchanged_count,
        error_count=audit.error_count,
        error_code=audit.error_code,
        errors=issues,
    )
