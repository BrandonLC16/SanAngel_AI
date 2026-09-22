from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from backend.app.core.config import get_database_settings
from backend.app.db.models.branch import Branch
from backend.app.db.models.price import Price
from backend.app.db.models.product import Product
from backend.app.db.session import create_database_engine, create_database_session_factory

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INITIAL_REVISION = "20260921_0001"
BRANCH_REVISION = "20260922_0002"
PRODUCT_REVISION = "20260922_0003"
PRICE_REVISION = "20260922_0004"


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def alembic_config() -> Config:
    return Config(str(REPOSITORY_ROOT / "alembic.ini"))


def test_migration_history_has_reproducible_price_revision() -> None:
    scripts = ScriptDirectory.from_config(alembic_config())
    revisions = list(scripts.walk_revisions())

    assert scripts.get_heads() == [PRICE_REVISION]
    assert len(revisions) == 4
    assert [revision.revision for revision in revisions] == [
        PRICE_REVISION,
        PRODUCT_REVISION,
        BRANCH_REVISION,
        INITIAL_REVISION,
    ]
    assert revisions[0].down_revision == PRODUCT_REVISION
    assert revisions[1].down_revision == BRANCH_REVISION
    assert revisions[2].down_revision == INITIAL_REVISION
    assert revisions[3].down_revision is None


def test_upgrade_head_creates_branch_product_and_price_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "migrated.db"
    database_url = sqlite_url(database_path)
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()

    try:
        command.upgrade(alembic_config(), "head")
        command.upgrade(alembic_config(), "head")
        command.check(alembic_config())

        engine = create_database_engine(database_url)
        try:
            with engine.connect() as connection:
                current_revision = MigrationContext.configure(connection).get_current_revision()
                inspector = inspect(connection)
                table_names = inspector.get_table_names()
                branch_columns = {column["name"] for column in inspector.get_columns("branches")}
                unique_constraints = inspector.get_unique_constraints("branches")
                branch_checks = inspector.get_check_constraints("branches")
                product_columns = {column["name"] for column in inspector.get_columns("products")}
                product_unique_constraints = inspector.get_unique_constraints("products")
                product_checks = inspector.get_check_constraints("products")
                product_foreign_keys = inspector.get_foreign_keys("products")
                product_indexes = inspector.get_indexes("products")
                price_columns = inspector.get_columns("prices")
                price_unique_constraints = inspector.get_unique_constraints("prices")
                price_foreign_keys = inspector.get_foreign_keys("prices")
                price_checks = inspector.get_check_constraints("prices")
        finally:
            engine.dispose()

        assert database_path.is_file()
        assert current_revision == PRICE_REVISION
        assert table_names == ["alembic_version", "branches", "prices", "products"]
        assert branch_columns == {
            "id",
            "code",
            "name",
            "address",
            "phone",
            "business_hours",
            "is_active",
            "created_at",
            "updated_at",
        }
        assert {constraint["name"] for constraint in unique_constraints} == {"uq_branches_code"}
        assert {constraint["name"] for constraint in branch_checks} == {
            "ck_branches_address_length",
            "ck_branches_business_hours_length",
            "ck_branches_code_characters",
            "ck_branches_code_hyphens",
            "ck_branches_code_length",
            "ck_branches_code_lowercase",
            "ck_branches_code_prefix",
            "ck_branches_code_suffix",
            "ck_branches_name_length",
            "ck_branches_phone_length",
        }
        assert product_columns == {
            "id",
            "branch_id",
            "name",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        }
        assert {constraint["name"] for constraint in product_unique_constraints} == {
            "uq_products_branch_id_name",
            "uq_products_id_branch_id",
        }
        assert {constraint["name"] for constraint in product_checks} == {
            "ck_products_category_length",
            "ck_products_name_length",
        }
        assert product_foreign_keys == [
            {
                "name": "fk_products_branch_id_branches",
                "constrained_columns": ["branch_id"],
                "referred_schema": None,
                "referred_table": "branches",
                "referred_columns": ["id"],
                "options": {"ondelete": "RESTRICT"},
            }
        ]
        assert {index["name"] for index in product_indexes} == {"ix_products_branch_catalog"}
        assert {column["name"] for column in price_columns} == {
            "id",
            "branch_id",
            "product_id",
            "amount",
            "unit",
            "created_at",
            "updated_at",
        }
        amount_column = next(column for column in price_columns if column["name"] == "amount")
        assert amount_column["type"].precision == 12
        assert amount_column["type"].scale == 2
        assert {constraint["name"] for constraint in price_unique_constraints} == {
            "uq_prices_branch_id_product_id_unit"
        }
        assert {
            (
                foreign_key["name"],
                tuple(foreign_key["constrained_columns"]),
                foreign_key["referred_table"],
                tuple(foreign_key["referred_columns"]),
                foreign_key["options"].get("ondelete"),
            )
            for foreign_key in price_foreign_keys
        } == {
            (
                "fk_prices_branch_id_branches",
                ("branch_id",),
                "branches",
                ("id",),
                "RESTRICT",
            ),
            (
                "fk_prices_product_id_branch_id_products",
                ("product_id", "branch_id"),
                "products",
                ("id", "branch_id"),
                "RESTRICT",
            ),
        }
        assert {constraint["name"] for constraint in price_checks} == {
            "ck_prices_amount_maximum",
            "ck_prices_amount_non_negative",
            "ck_prices_amount_scale",
            "ck_prices_unit_characters",
            "ck_prices_unit_hyphens",
            "ck_prices_unit_length",
            "ck_prices_unit_lowercase",
            "ck_prices_unit_prefix",
            "ck_prices_unit_suffix",
        }
    finally:
        get_database_settings.cache_clear()


def test_migrations_round_trip_from_empty_database_preserves_earlier_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = sqlite_url(tmp_path / "round-trip.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    config = alembic_config()

    def snapshot() -> tuple[str | None, list[str]]:
        engine = create_database_engine(database_url)
        try:
            with engine.connect() as connection:
                return (
                    MigrationContext.configure(connection).get_current_revision(),
                    inspect(connection).get_table_names(),
                )
        finally:
            engine.dispose()

    try:
        command.upgrade(config, INITIAL_REVISION)
        assert snapshot() == (INITIAL_REVISION, ["alembic_version"])

        command.upgrade(config, BRANCH_REVISION)
        assert snapshot() == (BRANCH_REVISION, ["alembic_version", "branches"])

        command.upgrade(config, PRODUCT_REVISION)
        assert snapshot() == (
            PRODUCT_REVISION,
            ["alembic_version", "branches", "products"],
        )

        engine = create_database_engine(database_url)
        try:
            with create_database_session_factory(engine).begin() as session:
                branch = Branch(
                    code="sucursal-uno",
                    name="Sucursal uno",
                    address="Dirección uno",
                    business_hours="Lunes a viernes",
                )
                session.add(branch)
                session.flush()
                session.add(Product(branch_id=branch.id, name="Aguja", category="Res"))
        finally:
            engine.dispose()

        command.upgrade(config, "head")
        assert snapshot() == (
            PRICE_REVISION,
            ["alembic_version", "branches", "prices", "products"],
        )

        engine = create_database_engine(database_url)
        try:
            with create_database_session_factory(engine).begin() as session:
                branch_id = session.scalar(select(Branch.id))
                product_id = session.scalar(select(Product.id))
                session.add(
                    Price(
                        branch_id=branch_id,
                        product_id=product_id,
                        amount=Decimal("199.90"),
                        unit="kg",
                    )
                )
        finally:
            engine.dispose()

        command.downgrade(config, PRODUCT_REVISION)
        assert snapshot() == (
            PRODUCT_REVISION,
            ["alembic_version", "branches", "products"],
        )

        engine = create_database_engine(database_url)
        try:
            with create_database_session_factory(engine)() as session:
                assert session.scalar(select(Branch.code)) == "sucursal-uno"
                assert session.scalar(select(Product.name)) == "Aguja"
        finally:
            engine.dispose()

        command.upgrade(config, "head")
        assert snapshot()[0] == PRICE_REVISION

        engine = create_database_engine(database_url)
        try:
            with create_database_session_factory(engine)() as session:
                assert session.scalars(select(Price)).all() == []
        finally:
            engine.dispose()

        command.downgrade(config, "base")
        assert snapshot() == (None, ["alembic_version"])

        command.upgrade(config, "head")
        assert snapshot() == (
            PRICE_REVISION,
            ["alembic_version", "branches", "prices", "products"],
        )
    finally:
        get_database_settings.cache_clear()


def test_constraint_failure_rolls_back_whole_transaction(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = sqlite_url(tmp_path / "rollback.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()

    try:
        command.upgrade(alembic_config(), "head")
        engine = create_database_engine(database_url)
        try:
            session_factory = create_database_session_factory(engine)
            with pytest.raises(IntegrityError):
                with session_factory.begin() as session:
                    branch = Branch(
                        code="sucursal-uno",
                        name="Sucursal uno",
                        address="Dirección uno",
                        business_hours="Lunes a viernes",
                    )
                    session.add(branch)
                    session.flush()
                    session.add(Product(branch_id=branch.id, name=" ", category="Res"))
                    session.flush()

            with session_factory() as session:
                assert session.scalars(select(Branch)).all() == []
                assert session.scalars(select(Product)).all() == []
        finally:
            engine.dispose()
    finally:
        get_database_settings.cache_clear()


def test_downgrade_base_removes_current_revision(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "downgraded.db"
    database_url = sqlite_url(database_path)
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()

    try:
        config = alembic_config()
        command.upgrade(config, "head")
        command.downgrade(config, "base")

        engine = create_database_engine(database_url)
        try:
            with engine.connect() as connection:
                current_revision = MigrationContext.configure(connection).get_current_revision()
        finally:
            engine.dispose()

        assert current_revision is None
    finally:
        get_database_settings.cache_clear()


def test_downgrade_product_revision_removes_only_product_schema(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = sqlite_url(tmp_path / "product-downgrade.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()

    try:
        config = alembic_config()
        command.upgrade(config, "head")
        command.downgrade(config, BRANCH_REVISION)

        engine = create_database_engine(database_url)
        try:
            with engine.connect() as connection:
                current_revision = MigrationContext.configure(connection).get_current_revision()
                table_names = inspect(connection).get_table_names()
        finally:
            engine.dispose()

        assert current_revision == BRANCH_REVISION
        assert table_names == ["alembic_version", "branches"]
    finally:
        get_database_settings.cache_clear()


def test_downgrade_price_revision_removes_price_schema_and_auxiliary_constraint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    database_url = sqlite_url(tmp_path / "price-downgrade.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()

    try:
        config = alembic_config()
        command.upgrade(config, "head")
        command.downgrade(config, PRODUCT_REVISION)

        engine = create_database_engine(database_url)
        try:
            with engine.connect() as connection:
                current_revision = MigrationContext.configure(connection).get_current_revision()
                inspector = inspect(connection)
                table_names = inspector.get_table_names()
                product_unique_constraints = inspector.get_unique_constraints("products")
        finally:
            engine.dispose()

        assert current_revision == PRODUCT_REVISION
        assert table_names == ["alembic_version", "branches", "products"]
        assert {constraint["name"] for constraint in product_unique_constraints} == {
            "uq_products_branch_id_name"
        }
    finally:
        get_database_settings.cache_clear()
