from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from backend.app.core.config import get_database_settings
from backend.app.db.session import create_database_engine

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INITIAL_REVISION = "20260921_0001"
BRANCH_REVISION = "20260922_0002"
PRODUCT_REVISION = "20260922_0003"


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def alembic_config() -> Config:
    return Config(str(REPOSITORY_ROOT / "alembic.ini"))


def test_migration_history_has_reproducible_product_revision() -> None:
    scripts = ScriptDirectory.from_config(alembic_config())
    revisions = list(scripts.walk_revisions())

    assert scripts.get_heads() == [PRODUCT_REVISION]
    assert len(revisions) == 3
    assert [revision.revision for revision in revisions] == [
        PRODUCT_REVISION,
        BRANCH_REVISION,
        INITIAL_REVISION,
    ]
    assert revisions[0].down_revision == BRANCH_REVISION
    assert revisions[1].down_revision == INITIAL_REVISION
    assert revisions[2].down_revision is None


def test_upgrade_head_creates_branch_and_product_schema(
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

        engine = create_database_engine(database_url)
        try:
            with engine.connect() as connection:
                current_revision = MigrationContext.configure(connection).get_current_revision()
                inspector = inspect(connection)
                table_names = inspector.get_table_names()
                branch_columns = {column["name"] for column in inspector.get_columns("branches")}
                unique_constraints = inspector.get_unique_constraints("branches")
                product_columns = {column["name"] for column in inspector.get_columns("products")}
                product_unique_constraints = inspector.get_unique_constraints("products")
                product_foreign_keys = inspector.get_foreign_keys("products")
                product_indexes = inspector.get_indexes("products")
        finally:
            engine.dispose()

        assert database_path.is_file()
        assert current_revision == PRODUCT_REVISION
        assert table_names == ["alembic_version", "branches", "products"]
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
            "uq_products_branch_id_name"
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
