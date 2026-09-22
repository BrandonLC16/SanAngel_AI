from collections.abc import Generator
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_database_settings
from backend.app.db.models.branch import Branch
from backend.app.db.models.price import Price
from backend.app.db.models.product import Product
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.price import PriceData
from backend.app.schemas.product import ProductData

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def make_branch_data(code: str) -> BranchData:
    return BranchData(
        code=code,
        name=code,
        address=f"Dirección de {code}",
        phone=None,
        business_hours="Lunes a viernes",
    )


def make_product_data(name: str) -> ProductData:
    return ProductData(name=name, category="Res")


def make_price_data(**overrides: object) -> PriceData:
    values: dict[str, object] = {
        "amount": Decimal("199.90"),
        "unit": "kg",
    }
    values.update(overrides)
    return PriceData(**values)


def create_branch_and_product(
    session: Session,
    *,
    branch_code: str,
    product_name: str,
) -> tuple[Branch, Product]:
    branch = BranchRepository(session).create(make_branch_data(branch_code))
    product = ProductRepository(session, branch=branch).create(make_product_data(product_name))
    return branch, product


@pytest.fixture
def migrated_session_factory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[sessionmaker[Session]]:
    database_url = sqlite_url(tmp_path / "prices.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(REPOSITORY_ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    try:
        yield create_database_session_factory(engine)
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def test_price_data_preserves_exact_decimal_and_normalizes_unit() -> None:
    price = make_price_data(amount="199.90", unit="  KG  ")

    assert price.amount == Decimal("199.90")
    assert isinstance(price.amount, Decimal)
    assert price.unit == "kg"


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("amount", 199.90),
        ("amount", Decimal("-0.01")),
        ("amount", Decimal("1.001")),
        ("amount", Decimal("10000000000.00")),
        ("amount", "NaN"),
        ("unit", ""),
        ("unit", "por kilo"),
        ("unit", "kg--mayoreo"),
        ("unit", "-kg"),
        ("unit", "x" * 25),
    ),
)
def test_price_data_rejects_invalid_amounts_and_units(
    field_name: str,
    invalid_value: object,
) -> None:
    with pytest.raises(ValidationError):
        make_price_data(**{field_name: invalid_value})


def test_price_data_rejects_product_and_branch_fields() -> None:
    with pytest.raises(ValidationError):
        PriceData(  # type: ignore[call-arg]
            amount=Decimal("199.90"),
            unit="kg",
            product_id=1,
            branch_id=1,
        )


def test_price_repository_supports_exact_scoped_crud(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch, product = create_branch_and_product(
            session,
            branch_code="sucursal-uno",
            product_name="Aguja",
        )
        repository = PriceRepository(session, branch=branch)
        kilogram = repository.create(product, make_price_data())
        piece = repository.create(
            product,
            make_price_data(amount=Decimal("49.50"), unit="piece"),
        )

        assert kilogram.amount == Decimal("199.90")
        assert isinstance(kilogram.amount, Decimal)
        assert kilogram.updated_at is not None
        assert repository.get_for_product(product, unit=" KG ") is kilogram
        assert [price.unit for price in repository.list_for_product(product)] == ["kg", "piece"]
        assert [price.id for price in repository.list_all()] == [kilogram.id, piece.id]

        kilogram.updated_at = datetime(2000, 1, 1)
        session.flush()
        repository.update(kilogram, make_price_data(amount=Decimal("205.25")))
        session.refresh(kilogram)
        assert kilogram.amount == Decimal("205.25")
        assert kilogram.updated_at.year > 2000

        repository.delete(piece)
        assert [price.unit for price in repository.list_for_product(product)] == ["kg"]


def test_price_repository_cannot_read_or_mutate_another_branch_price(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        own_branch, own_product = create_branch_and_product(
            session,
            branch_code="sucursal-propia",
            product_name="Producto propio",
        )
        other_branch, other_product = create_branch_and_product(
            session,
            branch_code="sucursal-ajena",
            product_name="Producto ajeno",
        )
        own_repository = PriceRepository(session, branch=own_branch)
        other_repository = PriceRepository(session, branch=other_branch)
        own_price = own_repository.create(own_product, make_price_data())
        other_price = other_repository.create(other_product, make_price_data())

        assert [price.id for price in own_repository.list_all()] == [own_price.id]
        with pytest.raises(ValueError, match="product does not belong"):
            own_repository.get_for_product(other_product, unit="kg")
        with pytest.raises(ValueError, match="price does not belong"):
            own_repository.update(other_price, make_price_data(amount=Decimal("1.00")))
        with pytest.raises(ValueError, match="price does not belong"):
            own_repository.delete(other_price)

        assert other_price.amount == Decimal("199.90")


def test_price_repository_requires_persisted_scoped_entities() -> None:
    branch_data = make_branch_data("sucursal-uno")
    transient_branch = Branch(**branch_data.model_dump())

    with pytest.raises(ValueError, match="branch must be persisted"):
        PriceRepository(Session(), branch=transient_branch)

    persisted_branch = Branch(id=1, **branch_data.model_dump())
    transient_product = Product(
        branch_id=1,
        **make_product_data("Aguja").model_dump(),
    )
    repository = PriceRepository(Session(), branch=persisted_branch)
    with pytest.raises(ValueError, match="product must be persisted"):
        repository.create(transient_product, make_price_data())


def test_database_rejects_duplicate_price_for_product_branch_and_unit(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch, product = create_branch_and_product(
            session,
            branch_code="sucursal-uno",
            product_name="Aguja",
        )
        PriceRepository(session, branch=branch).create(product, make_price_data())

    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            branch = BranchRepository(session).get_by_code("sucursal-uno")
            assert branch is not None
            product = ProductRepository(session, branch=branch).list_active()[0]
            PriceRepository(session, branch=branch).create(product, make_price_data())


def test_database_allows_same_unit_for_products_in_different_branches(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        first_branch, first_product = create_branch_and_product(
            session,
            branch_code="sucursal-uno",
            product_name="Aguja",
        )
        second_branch, second_product = create_branch_and_product(
            session,
            branch_code="sucursal-dos",
            product_name="Aguja",
        )

        PriceRepository(session, branch=first_branch).create(first_product, make_price_data())
        PriceRepository(session, branch=second_branch).create(second_product, make_price_data())


def test_database_rejects_product_and_branch_mismatch(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        own_branch, _ = create_branch_and_product(
            session,
            branch_code="sucursal-propia",
            product_name="Producto propio",
        )
        _, other_product = create_branch_and_product(
            session,
            branch_code="sucursal-ajena",
            product_name="Producto ajeno",
        )
        own_branch_id = own_branch.id
        other_product_id = other_product.id

    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            session.add(
                Price(
                    branch_id=own_branch_id,
                    product_id=other_product_id,
                    amount=Decimal("10.00"),
                    unit="kg",
                )
            )


@pytest.mark.parametrize(
    ("amount", "unit"),
    (
        (Decimal("-0.01"), "kg"),
        (Decimal("1.001"), "kg"),
        (Decimal("10.00"), "KG"),
        (Decimal("10.00"), "kg--mayoreo"),
    ),
)
def test_database_enforces_amount_and_unit_constraints(
    migrated_session_factory: sessionmaker[Session],
    amount: Decimal,
    unit: str,
) -> None:
    with migrated_session_factory.begin() as session:
        branch, product = create_branch_and_product(
            session,
            branch_code="sucursal-uno",
            product_name="Aguja",
        )
        branch_id = branch.id
        product_id = product.id

    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            session.add(
                Price(
                    branch_id=branch_id,
                    product_id=product_id,
                    amount=amount,
                    unit=unit,
                )
            )
