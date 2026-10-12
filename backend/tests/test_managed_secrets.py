"""Production credentials come only from a mounted, external secret manager."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.app.core.config import (
    SECRET_FILE_NAMES,
    get_admin_auth_settings,
    get_conversation_identity_settings,
    get_http_settings,
    get_settings,
    validate_runtime_secrets,
)
from scripts.run_backend import main as run_backend_main


@pytest.fixture
def managed_secrets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    directory = tmp_path / "manager-mount"
    directory.mkdir()
    for name in SECRET_FILE_NAMES:
        (directory / name).write_text(
            f"test-only-{name.lower()}-placeholder-123456", encoding="utf-8"
        )
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ASSISTANT_BRANCH_CODE", "sucursal-uno")
    monkeypatch.setenv("SECRETS_DIR", str(directory))
    _clear_settings_caches()
    yield directory
    _clear_settings_caches()


def _clear_settings_caches() -> None:
    get_http_settings.cache_clear()
    get_settings.cache_clear()
    get_admin_auth_settings.cache_clear()
    get_conversation_identity_settings.cache_clear()


def test_production_loads_external_manager_files(managed_secrets: Path) -> None:
    validate_runtime_secrets()

    assert get_settings().openai_api_key.get_secret_value() == (
        managed_secrets / "OPENAI_API_KEY"
    ).read_text(encoding="utf-8")
    assert get_settings().green_api_token_instance is not None
    assert get_settings().green_api_webhook_token is not None
    assert get_admin_auth_settings().admin_auth_key.get_secret_value() == (
        managed_secrets / "ADMIN_AUTH_KEY"
    ).read_text(encoding="utf-8")
    assert get_conversation_identity_settings().conversation_identity_key.get_secret_value() == (
        managed_secrets / "CONVERSATION_IDENTITY_KEY"
    ).read_text(encoding="utf-8")


def test_production_rejects_environment_secret_even_with_mount(
    managed_secrets: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    marker = "test-only-environment-credential-placeholder"
    monkeypatch.setenv("OPENAI_API_KEY", marker)

    with pytest.raises(ValueError, match="must not come from an environment variable") as error:
        validate_runtime_secrets()
    assert marker not in str(error.value)


def test_production_missing_file_fails_closed_without_dotenv_fallback(
    managed_secrets: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (managed_secrets / "GREEN_API_WEBHOOK_TOKEN").unlink()
    (tmp_path / ".env").write_text(
        "GREEN_API_WEBHOOK_TOKEN=test-only-dotenv-credential-placeholder\n", encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="production secrets are unavailable"):
        validate_runtime_secrets()


def test_production_rejects_repository_secret_directory(
    managed_secrets: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del managed_secrets
    monkeypatch.setenv("SECRETS_DIR", str(Path(__file__).resolve().parents[2]))

    with pytest.raises(ValueError, match="invalid production secrets directory"):
        validate_runtime_secrets()


def test_production_rejects_oversized_secret_file(managed_secrets: Path) -> None:
    (managed_secrets / "ADMIN_AUTH_KEY").write_text("x" * 4097, encoding="utf-8")

    with pytest.raises(ValueError, match="invalid managed secret file size"):
        validate_runtime_secrets()


def test_production_rejects_newline_in_secret_file(managed_secrets: Path) -> None:
    (managed_secrets / "OPENAI_API_KEY").write_text("test-only-value\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid managed secret file content"):
        validate_runtime_secrets()


def test_production_rejects_secret_target_outside_manager_mount(
    managed_secrets: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external = tmp_path / "external-token"
    external.write_text("test-only-external-secret-placeholder", encoding="utf-8")
    target = managed_secrets / "OPENAI_API_KEY"
    original_resolve = Path.resolve

    def resolve(path: Path, *args: object, **kwargs: object) -> Path:
        if path == target:
            return external
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)

    with pytest.raises(ValueError, match="invalid managed secret file"):
        validate_runtime_secrets()


def test_rotation_takes_effect_after_restart_cache_clear(managed_secrets: Path) -> None:
    original = get_settings().openai_api_key.get_secret_value()
    replacement = "test-only-rotated-openai-placeholder"
    (managed_secrets / "OPENAI_API_KEY").write_text(replacement, encoding="utf-8")

    assert get_settings().openai_api_key.get_secret_value() == original
    get_settings.cache_clear()
    assert get_settings().openai_api_key.get_secret_value() == replacement


def test_production_runner_fails_before_listening_without_managed_secrets(
    managed_secrets: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    del managed_secrets
    monkeypatch.delenv("SECRETS_DIR")

    with pytest.raises(ValueError, match="production requires an absolute SECRETS_DIR"):
        run_backend_main()
