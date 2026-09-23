"""Deterministic product choices for the assistant's configured branch."""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from backend.app.schemas.commercial import ProductSummary
from backend.app.services.branch_scope import BranchScope
from backend.app.services.commercial_query_service import (
    CommercialQueryService,
    _normalize_search_text,
    _search_key,
)

MAX_DISPLAYED_PRODUCTS = 5


@dataclass(frozen=True, slots=True)
class ProductDisambiguationResult:
    status: Literal["unique", "needs_confirmation", "ambiguous", "not_found"]
    branch_name: str
    product: ProductSummary | None
    options: tuple[str, ...]
    text: str


class ProductDisambiguationService:
    """Resolve an explicit product term without accepting a customer-selected branch."""

    def __init__(self, session: Session, *, branch_scope: BranchScope) -> None:
        self._commercial = CommercialQueryService(session, branch_scope=branch_scope)

    def resolve(self, product_query: str) -> ProductDisambiguationResult:
        """Return only scoped products; never infer a product from an imprecise term."""

        matches = self._commercial.search_product(product_query)
        branch_name = self._commercial.get_branch_info().name
        if not matches:
            return ProductDisambiguationResult(
                status="not_found",
                branch_name=branch_name,
                product=None,
                options=(),
                text=(f"En {branch_name} no encontré ese producto. ¿Podrías confirmar el nombre?"),
            )
        if len(matches) == 1:
            if _search_key(matches[0].name) != _search_key(_normalize_search_text(product_query)):
                return ProductDisambiguationResult(
                    status="needs_confirmation",
                    branch_name=branch_name,
                    product=None,
                    options=(matches[0].name,),
                    text=(
                        f"En {branch_name} encontré una posible coincidencia: "
                        f"{matches[0].name}. ¿Es ese producto?"
                    ),
                )
            return ProductDisambiguationResult(
                status="unique",
                branch_name=branch_name,
                product=matches[0],
                options=(),
                text=f"En {branch_name} encontré {matches[0].name}.",
            )

        options = tuple(product.name for product in matches[:MAX_DISPLAYED_PRODUCTS])
        names = ", ".join(options)
        suffix = ", entre otros" if len(matches) > len(options) else ""
        return ProductDisambiguationResult(
            status="ambiguous",
            branch_name=branch_name,
            product=None,
            options=options,
            text=f"En {branch_name} encontré varias opciones: {names}{suffix}. ¿Cuál buscas?",
        )
