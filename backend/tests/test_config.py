from pathlib import Path
from secrets import token_urlsafe

import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings, get_settings


def make_non_key_secret_marker() -> str:
    return token_urlsafe(24)


def test_settings_use_safe_defaults() -> None:
    settings = Settings(openai_api_key=make_non_key_secret_marker(), _env_file=None)

    assert settings.app_env == "development"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000
    assert settings.openai_model == "gpt-5.6"
    assert settings.openai_store_responses is False
    assert settings.openai_timeout_seconds == 30
    assert settings.chat_max_message_chars == 2000
    assert settings.log_level == "INFO"


def test_settings_load_environment_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    secret_marker = make_non_key_secret_marker()
    monkeypatch.setenv("OPENAI_API_KEY", secret_marker)
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    monkeypatch.setenv("OPENAI_STORE_RESPONSES", "true")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "45.5")
    monkeypatch.setenv("CHAT_MAX_MESSAGE_CHARS", "1500")

    settings = Settings(_env_file=None)

    assert settings.openai_api_key.get_secret_value() == secret_marker
    assert settings.openai_model == "configured-model"
    assert settings.openai_store_responses is True
    assert settings.openai_timeout_seconds == 45.5
    assert settings.chat_max_message_chars == 1500


def test_settings_load_dotenv_file(tmp_path: Path) -> None:
    secret_marker = make_non_key_secret_marker()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            (
                f"OPENAI_API_KEY={secret_marker}",
                "APP_ENV=testing",
                "OPENAI_MODEL=dotenv-model",
                "OPENAI_TIMEOUT_SECONDS=12",
                "CHAT_MAX_MESSAGE_CHARS=750",
            )
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.app_env == "testing"
    assert settings.openai_model == "dotenv-model"
    assert settings.openai_timeout_seconds == 12
    assert settings.chat_max_message_chars == 750


def test_settings_require_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)

    error_text = str(exc_info.value)
    assert "openai_api_key" in error_text
    assert "Field required" in error_text


def test_settings_hide_secret_from_text_representations() -> None:
    secret_marker = make_non_key_secret_marker()
    settings = Settings(openai_api_key=secret_marker, _env_file=None)

    rendered_settings = f"{settings!r}\n{settings}\n{settings.model_dump_json()}"

    assert secret_marker not in rendered_settings
    assert "**********" in rendered_settings


def test_invalid_secret_error_does_not_reveal_value() -> None:
    secret_marker = make_non_key_secret_marker()

    with pytest.raises(ValidationError) as exc_info:
        Settings(openai_api_key=f" {secret_marker} ", _env_file=None)

    error_text = str(exc_info.value)
    assert "openai_api_key" in error_text
    assert secret_marker not in error_text


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("openai_timeout_seconds", 0),
        ("openai_timeout_seconds", 121),
        ("chat_max_message_chars", 0),
        ("chat_max_message_chars", 10_001),
    ),
)
def test_settings_reject_unsafe_numeric_limits(field_name: str, invalid_value: int) -> None:
    secret_marker = make_non_key_secret_marker()

    with pytest.raises(ValidationError) as exc_info:
        Settings(openai_api_key=secret_marker, _env_file=None, **{field_name: invalid_value})

    error_text = str(exc_info.value)
    assert field_name in error_text
    assert secret_marker not in error_text


def test_get_settings_caches_validated_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", make_non_key_secret_marker())
    monkeypatch.setenv("OPENAI_MODEL", "first-model")
    get_settings.cache_clear()

    try:
        first_settings = get_settings()
        monkeypatch.setenv("OPENAI_MODEL", "second-model")

        assert get_settings() is first_settings
        assert get_settings().openai_model == "first-model"
    finally:
        get_settings.cache_clear()
