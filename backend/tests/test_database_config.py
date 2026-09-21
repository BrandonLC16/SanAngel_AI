from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.app.core.config import (
    DEFAULT_DATABASE_URL,
    DatabaseSettings,
    get_database_settings,
)


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def test_database_settings_use_safe_sqlite_default() -> None:
    settings = DatabaseSettings(_env_file=None)

    assert settings.database_url.get_secret_value() == DEFAULT_DATABASE_URL
    assert DEFAULT_DATABASE_URL not in repr(settings)
    assert repr(settings) == "DatabaseSettings()"


def test_database_settings_load_environment_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    configured_url = sqlite_url(tmp_path / "configured.db")
    monkeypatch.setenv("DATABASE_URL", configured_url)

    settings = DatabaseSettings(_env_file=None)

    assert settings.database_url.get_secret_value() == configured_url


@pytest.mark.parametrize(
    "database_url",
    (
        "",
        " sqlite+pysqlite:///./database.db ",
        "sqlite+pysqlite://",
        "sqlite+pysqlite://user:password@/database.db",
        "postgresql://database.example/app",
        "not-a-database-url",
        "sqlite+pysqlite:///./bad\x00name.db",
    ),
)
def test_database_settings_reject_invalid_or_unsupported_urls(database_url: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        DatabaseSettings(database_url=database_url, _env_file=None)

    error_text = str(exc_info.value)
    assert "database_url" in error_text
    if database_url:
        assert database_url not in error_text


def test_get_database_settings_caches_validated_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first_url = sqlite_url(tmp_path / "first.db")
    second_url = sqlite_url(tmp_path / "second.db")
    monkeypatch.setenv("DATABASE_URL", first_url)
    get_database_settings.cache_clear()

    try:
        first_settings = get_database_settings()
        monkeypatch.setenv("DATABASE_URL", second_url)

        assert get_database_settings() is first_settings
        assert get_database_settings().database_url.get_secret_value() == first_url
    finally:
        get_database_settings.cache_clear()
