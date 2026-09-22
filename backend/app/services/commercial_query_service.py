"""Deterministic read-only commercial queries for the configured branch."""

import unicodedata

from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    CommercialQueryInputError,
    ProductNotFoundError,
    ProductPriceNotFoundError,
)
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.commercial import BranchInfo, ProductPriceInfo, ProductSummary
from backend.app.schemas.price import normalize_price_unit
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService

MAX_PRODUCT_SEARCH_CHARS = 120


class CommercialQueryService:
    """Expose a minimal read-only API with branch scope injected by the backend."""

    def __init__(self, session: Session, *, branch_scope: BranchScope) -> None:
        branch = BranchService(
            BranchRepository(session),
            assistant_branch_code=branch_scope.branch_code,
        ).get_current_branch()
        self._branch = branch
        self._products = ProductRepository(session, branch=branch)
        self._prices = PriceRepository(session, branch=branch)

    def get_branch_info(self) -> BranchInfo:
        return BranchInfo(
            name=self._branch.name,
            address=self._branch.address,
            phone=self._branch.phone,
            business_hours=self._branch.business_hours,
        )

    def search_product(self, query: str) -> tuple[ProductSummary, ...]:
        normalized_query = _normalize_search_text(query)
        query_key = _search_key(normalized_query)
        matches: list[tuple[int, str, int, ProductSummary]] = []

        for product in self._products.list_active():
            name_key = _search_key(product.name)
            if query_key not in name_key:
                continue
            rank = 0 if name_key == query_key else 1 if name_key.startswith(query_key) else 2
            matches.append(
                (
                    rank,
                    name_key,
                    product.id,
                    ProductSummary(
                        product_id=product.id,
                        name=product.name,
                        category=product.category,
                    ),
                )
            )

        matches.sort(key=lambda match: match[:3])
        return tuple(match[3] for match in matches)

    def get_product_price(self, product_id: int, *, unit: str) -> ProductPriceInfo:
        if type(product_id) is not int or product_id <= 0:
            raise CommercialQueryInputError("product_id must be a positive integer")
        try:
            normalized_unit = normalize_price_unit(unit)
        except ValueError as exc:
            raise CommercialQueryInputError("unit has an invalid format") from exc

        product = self._products.get_by_id(product_id)
        if product is None or not product.is_active:
            raise ProductNotFoundError("active product was not found in scoped catalog")

        price = self._prices.get_for_product(product, unit=normalized_unit)
        if price is None:
            raise ProductPriceNotFoundError("current scoped product price was not found")

        return ProductPriceInfo(
            product_id=product.id,
            product_name=product.name,
            category=product.category,
            amount=price.amount,
            unit=price.unit,
            updated_at=price.updated_at,
        )


def _normalize_search_text(value: str) -> str:
    if not isinstance(value, str):
        raise CommercialQueryInputError("product query must be a string")
    if len(value) > MAX_PRODUCT_SEARCH_CHARS:
        raise CommercialQueryInputError("product query exceeds the size limit")
    normalized = unicodedata.normalize("NFKC", value).strip()
    if (
        not normalized
        or not normalized.isprintable()
        or not any(character.isalnum() for character in normalized)
    ):
        raise CommercialQueryInputError("product query has an invalid format")
    return " ".join(normalized.split())


def _search_key(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return " ".join(without_marks.split())
