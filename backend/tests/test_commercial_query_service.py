import inspect
from collections.abc import Generator
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import AssistantSettings, get_database_settings
from backend.app.core.exceptions import (
    BranchNotConfiguredError,
    CommercialQueryInputError,
    ProductNotFoundError,
    ProductPriceNotFoundError,
)
from backend.app.db.models.product import Product
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.commercial import BranchInfo, ProductPriceInfo, ProductSummary
from backend.app.schemas.price import PriceData
from backend.app.schemas.product import ProductData
from backend.app.services.branch_scope import BranchScope
from backend.app.services.commercial_query_service import CommercialQueryService

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def make_branch_data(code: str, *, name: str | None = None) -> BranchData:
    return BranchData(
        code=code,
        name=name or code,
        address=f"Dirección de {code}",
        phone="+520000000000",
        business_hours="Lunes a viernes",
    )


def create_branch(session: Session, code: str, *, name: str | None = None):
    return BranchRepository(session).create(make_branch_data(code, name=name))


def create_product(
    session: Session,
    branch,
    *,
    name: str,
    category: str = "Res",
    is_active: bool = True,
) -> Product:
    repository = ProductRepository(session, branch=branch)
    product = repository.create(ProductData(name=name, category=category))
    if not is_active:
        repository.set_active(product, is_active=False)
    return product


def create_price(
    session: Session,
    branch,
    product: Product,
    *,
    amount: str,
    unit: str = "kg",
):
    return PriceRepository(session, branch=branch).create(
        product,
        PriceData(amount=amount, unit=unit),
    )


def make_service(session: Session, branch_code: str) -> CommercialQueryService:
    settings = AssistantSettings(assistant_branch_code=branch_code)
    return CommercialQueryService(
        session,
        branch_scope=BranchScope.from_settings(settings),
    )


@pytest.fixture
def migrated_session_factory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[sessionmaker[Session]]:
    database_url = sqlite_url(tmp_path / "commercial-queries.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(REPOSITORY_ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    try:
        yield create_database_session_factory(engine)
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def test_branch_scope_is_created_from_backend_settings() -> None:
    settings = AssistantSettings(assistant_branch_code="sucursal-uno")

    scope = BranchScope.from_settings(settings)

    assert scope.branch_code == "sucursal-uno"
    with pytest.raises((AttributeError, TypeError)):
        scope.branch_code = "sucursal-dos"  # type: ignore[misc]


def test_commercial_service_exposes_only_read_methods_without_branch_arguments() -> None:
    public_methods = {
        name
        for name, value in CommercialQueryService.__dict__.items()
        if not name.startswith("_") and callable(value)
    }
    assert public_methods == {"get_branch_info", "get_product_price", "search_product"}

    for method_name in public_methods:
        parameter_names = inspect.signature(getattr(CommercialQueryService, method_name)).parameters
        assert "branch_id" not in parameter_names
        assert "branch_code" not in parameter_names


def test_commercial_service_returns_deterministic_detached_results(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch = create_branch(session, "sucursal-uno", name="Sucursal Uno")
        exact = create_product(session, branch, name="Aguja")
        north = create_product(session, branch, name="Aguja norteña")
        premium = create_product(session, branch, name="Aguja Premium")
        create_product(session, branch, name="Aguja descontinuada", is_active=False)
        create_price(session, branch, exact, amount="189.90")
        create_price(session, branch, north, amount="199.90")
        create_price(session, branch, premium, amount="209.90")
        service = make_service(session, "sucursal-uno")

        branch_info = service.get_branch_info()
        matches = service.search_product("  AGUJA  ")
        accent_match = service.search_product("aguja nortena")
        price = service.get_product_price(north.id, unit=" KG ")

        assert branch_info == BranchInfo(
            name="Sucursal Uno",
            address="Dirección de sucursal-uno",
            phone="+520000000000",
            business_hours="Lunes a viernes",
        )
        assert [match.name for match in matches] == [
            "Aguja",
            "Aguja norteña",
            "Aguja Premium",
        ]
        assert accent_match == (
            ProductSummary(
                product_id=north.id,
                name="Aguja norteña",
                category="Res",
            ),
        )
        assert price == ProductPriceInfo(
            product_id=north.id,
            product_name="Aguja norteña",
            category="Res",
            amount=Decimal("199.90"),
            unit="kg",
            updated_at=price.updated_at,
        )
        assert isinstance(price.amount, Decimal)
        assert not session.new
        assert not session.dirty
        assert not session.deleted

        with pytest.raises(ValidationError):
            price.amount = Decimal("1.00")


def test_search_product_returns_empty_tuple_when_no_match_exists(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch = create_branch(session, "sucursal-uno")
        create_product(session, branch, name="Aguja")

        assert make_service(session, "sucursal-uno").search_product("sirloin") == ()


@pytest.mark.parametrize(
    "query",
    ("", "   ", "---", "Aguja\nPremium", "x" * 121, f"{' ' * 120}a", 1),
)
def test_search_product_rejects_invalid_queries(
    migrated_session_factory: sessionmaker[Session],
    query: object,
) -> None:
    with migrated_session_factory.begin() as session:
        create_branch(session, "sucursal-uno")
        service = make_service(session, "sucursal-uno")

        with pytest.raises(CommercialQueryInputError):
            service.search_product(query)  # type: ignore[arg-type]


def test_get_product_price_handles_missing_or_inactive_data(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch = create_branch(session, "sucursal-uno")
        without_price = create_product(session, branch, name="Sin precio")
        inactive = create_product(session, branch, name="Inactivo", is_active=False)
        create_price(session, branch, inactive, amount="10.00")
        service = make_service(session, "sucursal-uno")

        with pytest.raises(ProductNotFoundError):
            service.get_product_price(9999, unit="kg")
        with pytest.raises(ProductNotFoundError):
            service.get_product_price(inactive.id, unit="kg")
        with pytest.raises(ProductPriceNotFoundError):
            service.get_product_price(without_price.id, unit="kg")

        create_price(session, branch, without_price, amount="20.00", unit="piece")
        with pytest.raises(ProductPriceNotFoundError):
            service.get_product_price(without_price.id, unit="kg")


@pytest.mark.parametrize(
    ("product_id", "unit"),
    (
        (0, "kg"),
        (-1, "kg"),
        (True, "kg"),
        ("1", "kg"),
        (1, ""),
        (1, "por kilo"),
    ),
)
def test_get_product_price_rejects_invalid_arguments(
    migrated_session_factory: sessionmaker[Session],
    product_id: object,
    unit: str,
) -> None:
    with migrated_session_factory.begin() as session:
        create_branch(session, "sucursal-uno")
        service = make_service(session, "sucursal-uno")

        with pytest.raises(CommercialQueryInputError):
            service.get_product_price(product_id, unit=unit)  # type: ignore[arg-type]


def test_commercial_service_fails_closed_when_scoped_branch_is_unavailable(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        with pytest.raises(BranchNotConfiguredError):
            make_service(session, "sucursal-ausente")

        branch = create_branch(session, "sucursal-inactiva")
        branch.is_active = False
        session.flush()
        with pytest.raises(BranchNotConfiguredError):
            make_service(session, "sucursal-inactiva")


def test_commercial_service_cannot_cross_branch_scope(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        own_branch = create_branch(session, "sucursal-propia", name="Sucursal Propia")
        other_branch = create_branch(session, "sucursal-ajena", name="Sucursal Ajena")
        own_product = create_product(session, own_branch, name="Producto propio")
        other_product = create_product(session, other_branch, name="Producto ajeno")
        create_price(session, own_branch, own_product, amount="100.00")
        create_price(session, other_branch, other_product, amount="999.00")
        own_service = make_service(session, "sucursal-propia")

        assert own_service.get_branch_info().name == "Sucursal Propia"
        assert [match.name for match in own_service.search_product("producto")] == [
            "Producto propio"
        ]
        assert own_service.search_product("sucursal-ajena") == ()
        assert own_service.get_product_price(own_product.id, unit="kg").amount == Decimal("100.00")
        with pytest.raises(ProductNotFoundError):
            own_service.get_product_price(other_product.id, unit="kg")

        other_service = make_service(session, "sucursal-ajena")
        assert other_service.get_branch_info().name == "Sucursal Ajena"
        assert other_service.get_product_price(other_product.id, unit="kg").amount == Decimal(
            "999.00"
        )


def test_commercial_query_implementation_has_no_openai_dependency() -> None:
    source_files = (
        REPOSITORY_ROOT / "backend" / "app" / "services" / "branch_scope.py",
        REPOSITORY_ROOT / "backend" / "app" / "services" / "commercial_query_service.py",
    )

    assert all("openai" not in path.read_text(encoding="utf-8").lower() for path in source_files)
