"""Deterministic, branch-scoped SQLAlchemy operations for products."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.branch import Branch
from backend.app.db.models.product import Product
from backend.app.schemas.product import ProductData


class ProductRepository:
    """Catalog repository permanently scoped to one trusted branch object."""

    def __init__(self, session: Session, *, branch: Branch) -> None:
        if branch.id is None:
            raise ValueError("branch must be persisted before accessing its catalog")
        self._session = session
        self._branch_id = branch.id

    def create(self, data: ProductData) -> Product:
        product = Product(branch_id=self._branch_id, **data.model_dump(), is_active=True)
        self._session.add(product)
        self._session.flush()
        return product

    def get_by_id(self, product_id: int) -> Product | None:
        self._validate_product_id(product_id)
        statement = select(Product).where(
            Product.id == product_id,
            Product.branch_id == self._branch_id,
        )
        return self._session.scalar(statement)

    def list_active(self) -> tuple[Product, ...]:
        statement = (
            select(Product)
            .where(
                Product.branch_id == self._branch_id,
                Product.is_active.is_(True),
            )
            .order_by(Product.category, Product.name, Product.id)
        )
        return tuple(self._session.scalars(statement))

    def list_all(self) -> tuple[Product, ...]:
        statement = (
            select(Product)
            .where(Product.branch_id == self._branch_id)
            .order_by(Product.category, Product.name, Product.id)
        )
        return tuple(self._session.scalars(statement))

    def update(self, product: Product, data: ProductData) -> Product:
        self._require_owned(product)
        product.name = data.name
        product.category = data.category
        self._session.flush()
        return product

    def set_active(self, product: Product, *, is_active: bool) -> Product:
        self._require_owned(product)
        if not isinstance(is_active, bool):
            raise ValueError("is_active must be a boolean")
        product.is_active = is_active
        self._session.flush()
        return product

    def delete(self, product: Product) -> None:
        self._require_owned(product)
        self._session.delete(product)
        self._session.flush()

    def _require_owned(self, product: Product) -> None:
        if product.branch_id != self._branch_id:
            raise ValueError("product does not belong to the repository branch")

    @staticmethod
    def _validate_product_id(product_id: int) -> None:
        if type(product_id) is not int or product_id <= 0:
            raise ValueError("product_id must be a positive integer")
