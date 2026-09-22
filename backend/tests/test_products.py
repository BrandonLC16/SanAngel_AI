from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_database_settings
from backend.app.db.models.branch import Branch
from backend.app.db.models.product import Product
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.product import ProductData

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def make_branch_data(code: str, *, name: str | None = None) -> BranchData:
    return BranchData(
        code=code,
        name=name or code,
        address=f"Dirección de {code}",
        phone=None,
        business_hours="Lunes a viernes",
    )


def make_product_data(**overrides: object) -> ProductData:
    values: dict[str, object] = {
        "name": "Aguja norteña",
        "category": "Res",
    }
    values.update(overrides)
    return ProductData(**values)


@pytest.fixture
def migrated_session_factory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[sessionmaker[Session]]:
    database_url = sqlite_url(tmp_path / "products.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(REPOSITORY_ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    try:
        yield create_database_session_factory(engine)
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def test_product_data_normalizes_catalog_text() -> None:
    product = make_product_data(name="  Aguja norteña  ", category="  Res  ")

    assert product.name == "Aguja norteña"
    assert product.category == "Res"


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("name", "   "),
        ("name", "---"),
        ("name", "Carne\nmolida"),
        ("name", "x" * 121),
        ("category", ""),
        ("category", "***"),
        ("category", "Res\tPremium"),
        ("category", "x" * 81),
    ),
)
def test_product_data_rejects_invalid_names_and_categories(
    field_name: str,
    invalid_value: str,
) -> None:
    with pytest.raises(ValidationError):
        make_product_data(**{field_name: invalid_value})


def test_product_data_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProductData(name="Aguja", category="Res", branch_id=1)  # type: ignore[call-arg]


def test_product_repository_supports_scoped_crud_and_deterministic_order(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch = BranchRepository(session).create(make_branch_data("sucursal-uno"))
        repository = ProductRepository(session, branch=branch)
        sirloin = repository.create(make_product_data(name="Sirloin"))
        aguja = repository.create(make_product_data(name="Aguja"))
        costilla = repository.create(make_product_data(name="Costilla", category="Cerdo"))

        repository.update(sirloin, make_product_data(name="Bistec"))
        repository.set_active(costilla, is_active=False)

        assert repository.get_by_id(aguja.id) is aguja
        assert [product.name for product in repository.list_active()] == ["Aguja", "Bistec"]
        assert [product.name for product in repository.list_all()] == [
            "Costilla",
            "Aguja",
            "Bistec",
        ]

        repository.delete(aguja)
        assert repository.get_by_id(aguja.id) is None


def test_product_repository_cannot_read_or_mutate_another_branch_catalog(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branches = BranchRepository(session)
        own_branch = branches.create(make_branch_data("sucursal-propia"))
        other_branch = branches.create(make_branch_data("sucursal-ajena"))
        own_repository = ProductRepository(session, branch=own_branch)
        other_repository = ProductRepository(session, branch=other_branch)
        own_product = own_repository.create(make_product_data(name="Producto propio"))
        other_product = other_repository.create(make_product_data(name="Producto ajeno"))

        assert [product.id for product in own_repository.list_active()] == [own_product.id]
        assert own_repository.get_by_id(other_product.id) is None

        with pytest.raises(ValueError, match="does not belong"):
            own_repository.update(other_product, make_product_data(name="Intrusión"))
        with pytest.raises(ValueError, match="does not belong"):
            own_repository.set_active(other_product, is_active=False)
        with pytest.raises(ValueError, match="does not belong"):
            own_repository.delete(other_product)

        assert other_product.name == "Producto ajeno"
        assert other_product.is_active is True


@pytest.mark.parametrize("product_id", (0, -1, True, "1"))
def test_product_repository_rejects_invalid_product_ids(
    migrated_session_factory: sessionmaker[Session],
    product_id: object,
) -> None:
    with migrated_session_factory.begin() as session:
        branch = BranchRepository(session).create(make_branch_data("sucursal-uno"))
        repository = ProductRepository(session, branch=branch)

        with pytest.raises(ValueError, match="positive integer"):
            repository.get_by_id(product_id)  # type: ignore[arg-type]


def test_product_repository_requires_a_persisted_branch() -> None:
    branch_data = make_branch_data("sucursal-uno")
    transient = Branch(**branch_data.model_dump())

    with pytest.raises(ValueError, match="persisted"):
        ProductRepository(Session(), branch=transient)


def test_database_rejects_duplicate_product_name_within_a_branch(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branch = BranchRepository(session).create(make_branch_data("sucursal-uno"))
        ProductRepository(session, branch=branch).create(make_product_data())

    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            branch = BranchRepository(session).get_by_code("sucursal-uno")
            assert branch is not None
            ProductRepository(session, branch=branch).create(make_product_data())


def test_database_allows_same_product_name_in_different_branches(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        branches = BranchRepository(session)
        first = branches.create(make_branch_data("sucursal-uno"))
        second = branches.create(make_branch_data("sucursal-dos"))

        ProductRepository(session, branch=first).create(make_product_data())
        ProductRepository(session, branch=second).create(make_product_data())


def test_database_enforces_product_foreign_key_and_text_constraints(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            session.add(Product(branch_id=9999, name="Producto", category="Res"))

    with migrated_session_factory.begin() as session:
        branch = BranchRepository(session).create(make_branch_data("sucursal-uno"))
        branch_id = branch.id

    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            session.add(Product(branch_id=branch_id, name="   ", category="Res"))
