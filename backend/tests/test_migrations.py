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


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def alembic_config() -> Config:
    return Config(str(REPOSITORY_ROOT / "alembic.ini"))


def test_migration_history_has_one_reproducible_baseline() -> None:
    scripts = ScriptDirectory.from_config(alembic_config())
    revisions = list(scripts.walk_revisions())

    assert scripts.get_heads() == [INITIAL_REVISION]
    assert len(revisions) == 1
    assert revisions[0].revision == INITIAL_REVISION
    assert revisions[0].down_revision is None


def test_upgrade_head_creates_only_alembic_baseline(
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
                table_names = inspect(connection).get_table_names()
        finally:
            engine.dispose()

        assert database_path.is_file()
        assert current_revision == INITIAL_REVISION
        assert table_names == ["alembic_version"]
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
