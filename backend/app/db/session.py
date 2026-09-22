"""Lazy SQLAlchemy engine and session construction."""

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_database_settings


def create_database_engine(database_url: str) -> Engine:
    """Create a synchronous SQLite engine without logging its configured URL."""

    parsed_url = make_url(database_url)
    if parsed_url.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise ValueError("database_url must use SQLite")

    engine = create_engine(
        parsed_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    return engine


def _enable_sqlite_foreign_keys(
    dbapi_connection: Any,
    _connection_record: Any,
) -> None:
    """Enforce declared relationships on every SQLite connection."""

    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


def create_database_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create the session factory used by repositories and application services."""

    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )


@lru_cache
def get_database_engine() -> Engine:
    """Return one lazily constructed engine for the current process."""

    settings = get_database_settings()
    return create_database_engine(settings.database_url.get_secret_value())


@lru_cache
def get_database_session_factory() -> sessionmaker[Session]:
    """Return one session factory bound to the process engine."""

    return create_database_session_factory(get_database_engine())


def get_database_session() -> Iterator[Session]:
    """Yield a session and always close it at the dependency boundary."""

    with get_database_session_factory()() as session:
        yield session
