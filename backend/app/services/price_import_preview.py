"""Read-only, branch-scoped impact preview for a validated price workbook."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.orm import Session

from backend.app.core.exceptions import BranchNotConfiguredError
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.price_import_parser import PriceImportIssue, parse_price_import

PriceImportAction = Literal["new", "changed", "unchanged"]


@dataclass(frozen=True, slots=True)
class PriceImportPreviewItem:
    source_row: int
    product_id: int
    product_name: str
    unit: str
    current_price_mxn: Decimal | None
    proposed_price_mxn: Decimal
    verified_on: date
    action: PriceImportAction


@dataclass(frozen=True, slots=True)
class PriceImportPreview:
    items: tuple[PriceImportPreviewItem, ...]
    issues: tuple[PriceImportIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues

    @property
    def new_count(self) -> int:
        return sum(item.action == "new" for item in self.items)

    @property
    def changed_count(self) -> int:
        return sum(item.action == "changed" for item in self.items)

    @property
    def unchanged_count(self) -> int:
        return sum(item.action == "unchanged" for item in self.items)

    @property
    def error_count(self) -> int:
        return len(self.issues)

    def to_review_data(self) -> dict[str, object]:
        """Return only the business fields needed to review impact as JSON data."""

        return {
            "is_valid": self.is_valid,
            "summary": {
                "new": self.new_count,
                "changed": self.changed_count,
                "unchanged": self.unchanged_count,
                "errors": self.error_count,
            },
            "items": [
                {
                    "source_row": item.source_row,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "unit": item.unit,
                    "current_price_mxn": (
                        str(item.current_price_mxn) if item.current_price_mxn is not None else None
                    ),
                    "proposed_price_mxn": str(item.proposed_price_mxn),
                    "verified_on": item.verified_on.isoformat(),
                    "action": item.action,
                }
                for item in self.items
            ],
            "issues": [
                {"row": issue.row, "field": issue.field, "code": issue.code}
                for issue in self.issues
            ],
        }


class PriceImportPreviewService:
    """Compare a workbook with current prices without mutating the session."""

    def __init__(self, session: Session, *, branch_scope: BranchScope) -> None:
        self._session = session
        self._branch_scope = branch_scope

    def preview(self, content: bytes, *, filename: str) -> PriceImportPreview:
        parsed = parse_price_import(content, filename=filename, branch_scope=self._branch_scope)
        if not parsed.is_valid:
            return PriceImportPreview((), parsed.issues)
        if self._session.new or self._session.dirty or self._session.deleted:
            raise ValueError("price preview requires a clean database session")

        with self._session.no_autoflush:
            try:
                branch = BranchService(
                    BranchRepository(self._session),
                    assistant_branch_code=self._branch_scope.branch_code,
                ).get_current_branch()
            except BranchNotConfiguredError:
                return PriceImportPreview((), (PriceImportIssue(None, None, "branch_unavailable"),))

            products = ProductRepository(self._session, branch=branch)
            prices = PriceRepository(self._session, branch=branch)
            items: list[PriceImportPreviewItem] = []
            issues: list[PriceImportIssue] = []
            for row in parsed.rows:
                product = products.get_by_id(row.product_id)
                if product is None or not product.is_active:
                    issues.append(
                        PriceImportIssue(row.source_row, "product_id", "product_unavailable")
                    )
                    continue
                if product.name != row.product_name:
                    issues.append(
                        PriceImportIssue(row.source_row, "product_name", "product_name_mismatch")
                    )
                    continue

                current = prices.get_for_product(product, unit=row.unit)
                current_amount = current.amount if current is not None else None
                action: PriceImportAction = (
                    "new"
                    if current_amount is None
                    else "unchanged"
                    if current_amount == row.price_mxn
                    else "changed"
                )
                items.append(
                    PriceImportPreviewItem(
                        source_row=row.source_row,
                        product_id=product.id,
                        product_name=product.name,
                        unit=row.unit,
                        current_price_mxn=current_amount,
                        proposed_price_mxn=row.price_mxn,
                        verified_on=row.verified_on,
                        action=action,
                    )
                )
            return PriceImportPreview(tuple(items), tuple(issues))
