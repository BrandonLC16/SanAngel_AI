from pathlib import Path

from sqlalchemy import literal, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_database_settings
from backend.app.db.session import (
    create_database_engine,
    create_database_session_factory,
    get_database_engine,
    get_database_session,
    get_database_session_factory,
)


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def test_engine_and_session_factory_use_isolated_sqlite_file(tmp_path: Path) -> None:
    database_path = tmp_path / "session.db"
    engine = create_database_engine(sqlite_url(database_path))
    session_factory = create_database_session_factory(engine)

    try:
        with session_factory.begin() as session:
            assert isinstance(session, Session)
            assert session.scalar(select(literal(1))) == 1

        assert database_path.is_file()
    finally:
        engine.dispose()


def test_session_factory_uses_explicit_transaction_boundaries(tmp_path: Path) -> None:
    engine = create_database_engine(sqlite_url(tmp_path / "transaction.db"))
    session_factory = create_database_session_factory(engine)

    try:
        with session_factory() as session:
            assert session.autoflush is False
            assert session.expire_on_commit is False
            assert session.in_transaction() is False
    finally:
        engine.dispose()


def test_lazy_process_engine_and_session_use_database_only_settings(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DATABASE_URL", sqlite_url(tmp_path / "lazy.db"))
    get_database_settings.cache_clear()
    get_database_session_factory.cache_clear()
    get_database_engine.cache_clear()

    try:
        engine = get_database_engine()

        assert get_database_engine() is engine
        assert get_database_session_factory() is get_database_session_factory()
        session_iterator = get_database_session()
        session = next(session_iterator)
        try:
            assert session.scalar(select(literal(1))) == 1
        finally:
            session_iterator.close()
    finally:
        get_database_session_factory.cache_clear()
        get_database_engine().dispose()
        get_database_engine.cache_clear()
        get_database_settings.cache_clear()
