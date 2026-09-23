"""Confirmed, all-or-nothing price import for one configured branch."""

from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_import_audit_repository import (
    ImportActor,
    PriceImportAuditReport,
    PriceImportAuditRepository,
)
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.price import PriceData
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.price_import_parser import MAX_PRICE_IMPORT_BYTES, PriceImportIssue
from backend.app.services.price_import_preview import PriceImportPreview, PriceImportPreviewService


class PriceImportConfirmationError(ValueError):
    """An explicit approval for the reviewed workbook is missing or mismatched."""


class PriceImportValidationError(ValueError):
    """The workbook or scoped catalog has safe, row-addressable errors."""

    def __init__(self, issues: tuple[PriceImportIssue, ...]) -> None:
        super().__init__("price import validation failed")
        self.issues = issues


class PriceImportStalePreviewError(ValueError):
    """The reviewed business impact no longer matches current data."""


class PriceImportWriteError(RuntimeError):
    """A database failure rolled back the entire import."""


class PriceImportAuditError(RuntimeError):
    """An import attempt could not be recorded safely."""


@dataclass(frozen=True, slots=True)
class PreparedPriceImport:
    filename: str
    file_sha256: str
    branch_code: str
    preview: PriceImportPreview


@dataclass(frozen=True, slots=True)
class PriceImportReceipt:
    audit_id: int
    attempt_id: str
    file_sha256: str
    branch_code: str
    created: int
    updated: int
    unchanged: int


class PriceImportTransactionService:
    """Require a reviewed preview and own the complete write transaction."""

    def __init__(
        self, session_factory: sessionmaker[Session], *, branch_scope: BranchScope
    ) -> None:
        self._session_factory = session_factory
        self._branch_scope = branch_scope

    def prepare(self, content: bytes, *, filename: str) -> PreparedPriceImport:
        with self._session_factory() as session:
            preview = PriceImportPreviewService(session, branch_scope=self._branch_scope).preview(
                content, filename=filename
            )
        return PreparedPriceImport(
            filename=filename,
            file_sha256=sha256(content).hexdigest() if preview.is_valid else "",
            branch_code=self._branch_scope.branch_code,
            preview=preview,
        )

    def confirm(
        self,
        content: bytes,
        *,
        filename: str,
        prepared: PreparedPriceImport,
        confirmed: bool,
        actor: ImportActor,
    ) -> PriceImportReceipt:
        if not isinstance(actor, ImportActor):
            raise PriceImportConfirmationError("trusted audit actor is required")
        attempt_id = uuid4().hex
        file_sha256 = (
            sha256(content).hexdigest()
            if isinstance(content, bytes) and len(content) <= MAX_PRICE_IMPORT_BYTES
            else None
        )

        try:
            if confirmed is not True:
                raise PriceImportConfirmationError("explicit confirmation is required")
            if not isinstance(prepared, PreparedPriceImport):
                raise PriceImportConfirmationError(
                    "confirmed file does not match the reviewed file"
                )
            if (
                prepared.branch_code != self._branch_scope.branch_code
                or prepared.filename != filename
            ):
                raise PriceImportConfirmationError(
                    "confirmed file does not match the reviewed file"
                )
            if not prepared.preview.is_valid:
                raise PriceImportValidationError(prepared.preview.issues)
            if file_sha256 is None or prepared.file_sha256 != file_sha256:
                raise PriceImportConfirmationError(
                    "confirmed file does not match the reviewed file"
                )

            with self._session_factory.begin() as session:
                # SQLite's write lock keeps the revalidation and upserts on one stable view.
                session.connection().exec_driver_sql("BEGIN IMMEDIATE")
                fresh = PriceImportPreviewService(session, branch_scope=self._branch_scope).preview(
                    content, filename=filename
                )
                if not fresh.is_valid:
                    raise PriceImportValidationError(fresh.issues)
                if fresh != prepared.preview:
                    raise PriceImportStalePreviewError("reviewed price impact is stale")

                branch = BranchService(
                    BranchRepository(session),
                    assistant_branch_code=self._branch_scope.branch_code,
                ).get_current_branch()
                products = ProductRepository(session, branch=branch)
                prices = PriceRepository(session, branch=branch)
                created = updated = unchanged = 0
                for item in fresh.items:
                    product = products.get_by_id(item.product_id)
                    if (
                        product is None
                        or not product.is_active
                        or product.name != item.product_name
                    ):
                        raise PriceImportStalePreviewError("reviewed product changed")
                    current = prices.get_for_product(product, unit=item.unit)
                    current_amount = current.amount if current is not None else None
                    if current_amount != item.current_price_mxn:
                        raise PriceImportStalePreviewError("reviewed price changed")
                    if item.action == "unchanged":
                        unchanged += 1
                        continue

                    data = PriceData(amount=item.proposed_price_mxn, unit=item.unit)
                    if current is None:
                        prices.create(product, data)
                        created += 1
                    else:
                        prices.update(current, data)
                        updated += 1

                audit = PriceImportAuditRepository(session, branch_scope=self._branch_scope).record(
                    attempt_id=attempt_id,
                    actor=actor,
                    file_sha256=file_sha256,
                    status="success",
                    created=created,
                    updated=updated,
                    unchanged=unchanged,
                )
                receipt = PriceImportReceipt(
                    audit_id=audit.id,
                    attempt_id=attempt_id,
                    file_sha256=file_sha256,
                    branch_code=self._branch_scope.branch_code,
                    created=created,
                    updated=updated,
                    unchanged=unchanged,
                )
            return receipt
        except PriceImportConfirmationError:
            self._record_failure(attempt_id, actor, file_sha256, "confirmation_rejected")
            raise
        except PriceImportValidationError as exc:
            self._record_failure(
                attempt_id, actor, file_sha256, "validation_failed", issues=exc.issues
            )
            raise
        except PriceImportStalePreviewError:
            self._record_failure(attempt_id, actor, file_sha256, "stale_preview")
            raise
        except SQLAlchemyError:
            self._record_failure(attempt_id, actor, file_sha256, "database_error", failed=True)
            raise PriceImportWriteError("price import could not be committed") from None

    def get_report(self, audit_id: int) -> PriceImportAuditReport | None:
        with self._session_factory() as session:
            return PriceImportAuditRepository(session, branch_scope=self._branch_scope).get_report(
                audit_id
            )

    def list_reports(self, *, limit: int = 50) -> tuple[PriceImportAuditReport, ...]:
        with self._session_factory() as session:
            return PriceImportAuditRepository(session, branch_scope=self._branch_scope).list_recent(
                limit=limit
            )

    def _record_failure(
        self,
        attempt_id: str,
        actor: ImportActor,
        file_sha256: str | None,
        error_code: str,
        *,
        issues: tuple[PriceImportIssue, ...] = (),
        failed: bool = False,
    ) -> None:
        try:
            with self._session_factory.begin() as session:
                PriceImportAuditRepository(session, branch_scope=self._branch_scope).record(
                    attempt_id=attempt_id,
                    actor=actor,
                    file_sha256=file_sha256,
                    status="failed" if failed else "rejected",
                    error_code=error_code,
                    issues=issues,
                )
        except SQLAlchemyError:
            raise PriceImportAuditError("price import attempt could not be audited") from None
