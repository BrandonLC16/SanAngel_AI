"""Exact, deterministic, branch-scoped SQLAlchemy operations for prices."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.branch import Branch
from backend.app.db.models.price import Price
from backend.app.db.models.product import Product
from backend.app.schemas.price import PriceData, normalize_price_unit


class PriceRepository:
    """Price repository permanently scoped to one trusted branch object."""

    def __init__(self, session: Session, *, branch: Branch) -> None:
        if branch.id is None:
            raise ValueError("branch must be persisted before accessing its prices")
        self._session = session
        self._branch_id = branch.id

    def create(self, product: Product, data: PriceData) -> Price:
        self._require_owned_product(product)
        price = Price(
            branch_id=self._branch_id,
            product_id=product.id,
            **data.model_dump(),
        )
        self._session.add(price)
        self._session.flush()
        return price

    def get_for_product(self, product: Product, *, unit: str) -> Price | None:
        self._require_owned_product(product)
        normalized_unit = normalize_price_unit(unit)
        statement = select(Price).where(
            Price.branch_id == self._branch_id,
            Price.product_id == product.id,
            Price.unit == normalized_unit,
        )
        return self._session.scalar(statement)

    def list_for_product(self, product: Product) -> tuple[Price, ...]:
        self._require_owned_product(product)
        statement = (
            select(Price)
            .where(
                Price.branch_id == self._branch_id,
                Price.product_id == product.id,
            )
            .order_by(Price.unit, Price.id)
        )
        return tuple(self._session.scalars(statement))

    def list_all(self) -> tuple[Price, ...]:
        statement = (
            select(Price)
            .where(Price.branch_id == self._branch_id)
            .order_by(Price.product_id, Price.unit, Price.id)
        )
        return tuple(self._session.scalars(statement))

    def update(self, price: Price, data: PriceData) -> Price:
        self._require_owned_price(price)
        price.amount = data.amount
        price.unit = data.unit
        self._session.flush()
        return price

    def delete(self, price: Price) -> None:
        self._require_owned_price(price)
        self._session.delete(price)
        self._session.flush()

    def _require_owned_product(self, product: Product) -> None:
        if product.id is None:
            raise ValueError("product must be persisted before accessing its price")
        if product.branch_id != self._branch_id:
            raise ValueError("product does not belong to the repository branch")

    def _require_owned_price(self, price: Price) -> None:
        if price.branch_id != self._branch_id:
            raise ValueError("price does not belong to the repository branch")
