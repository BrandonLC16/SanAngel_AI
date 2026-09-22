import json
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.cli.provision_assistant import load_profile, main
from backend.app.core.config import get_database_settings
from backend.app.core.exceptions import BranchNotConfiguredError, BranchScopeMismatchError
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.branch import AssistantProfile, BranchData
from backend.app.services.branch_service import BranchService

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BRANCH_CODE = "sucursal-demo"


def sqlite_url(path: Path) -> str:
    return f"sqlite+pysqlite:///{path.as_posix()}"


def make_branch_data(**overrides: object) -> BranchData:
    values: dict[str, object] = {
        "code": BRANCH_CODE,
        "name": "Sucursal de prueba",
        "address": "Avenida de prueba 123",
        "phone": "+520000000000",
        "business_hours": "Lunes a sábado de 09:00 a 19:00",
    }
    values.update(overrides)
    return BranchData(**values)


def make_profile(**overrides: object) -> AssistantProfile:
    return AssistantProfile(schema_version=1, branch=make_branch_data(**overrides))


@pytest.fixture
def migrated_session_factory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Generator[sessionmaker[Session]]:
    database_url = sqlite_url(tmp_path / "branches.db")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(REPOSITORY_ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    try:
        yield create_database_session_factory(engine)
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def test_branch_profile_normalizes_business_text() -> None:
    branch = make_branch_data(
        name="  Sucursal de prueba  ",
        address="  Avenida de prueba 123  ",
        business_hours="  Lunes a viernes  ",
    )

    assert branch.name == "Sucursal de prueba"
    assert branch.address == "Avenida de prueba 123"
    assert branch.business_hours == "Lunes a viernes"


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("code", "Sucursal-Demo"),
        ("code", "otra--sucursal"),
        ("name", "   "),
        ("address", ""),
        ("phone", "555 000 0000"),
        ("business_hours", "\t"),
    ),
)
def test_branch_profile_rejects_invalid_business_data(
    field_name: str,
    invalid_value: str,
) -> None:
    with pytest.raises(ValidationError):
        make_branch_data(**{field_name: invalid_value})


def test_branch_repository_supports_internal_crud(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        repository = BranchRepository(session)
        created = repository.create(make_branch_data())
        assert created.id is not None

    with migrated_session_factory.begin() as session:
        repository = BranchRepository(session)
        branch = repository.get_by_code(BRANCH_CODE)
        assert branch is not None
        assert [item.code for item in repository.list_all()] == [BRANCH_CODE]
        repository.update(branch, make_branch_data(name="Sucursal actualizada"))

    with migrated_session_factory.begin() as session:
        repository = BranchRepository(session)
        branch = repository.get_by_code(BRANCH_CODE)
        assert branch is not None
        assert branch.name == "Sucursal actualizada"
        repository.delete(branch)

    with migrated_session_factory() as session:
        assert BranchRepository(session).get_by_code(BRANCH_CODE) is None


def test_database_constraints_reject_duplicate_branch_code(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        repository = BranchRepository(session)
        repository.create(make_branch_data())

    with pytest.raises(IntegrityError):
        with migrated_session_factory.begin() as session:
            BranchRepository(session).create(make_branch_data(name="Duplicada"))


def test_branch_repository_does_not_change_immutable_code(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        repository = BranchRepository(session)
        branch = repository.create(make_branch_data())

        with pytest.raises(ValueError, match="immutable"):
            repository.update(branch, make_branch_data(code="sucursal-ajena"))


def test_branch_service_provisions_only_configured_branch(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory.begin() as session:
        service = BranchService(
            BranchRepository(session),
            assistant_branch_code=BRANCH_CODE,
        )
        first = service.provision(make_profile())
        second = service.provision(make_profile())
        third = service.provision(make_profile(name="Sucursal actualizada"))

        assert first.action == "created"
        assert second.action == "unchanged"
        assert third.action == "updated"
        assert service.get_current_branch().name == "Sucursal actualizada"

        with pytest.raises(BranchScopeMismatchError):
            service.provision(make_profile(code="sucursal-ajena"))

        assert BranchRepository(session).get_by_code("sucursal-ajena") is None


def test_branch_service_fails_closed_when_scoped_branch_is_missing(
    migrated_session_factory: sessionmaker[Session],
) -> None:
    with migrated_session_factory() as session:
        service = BranchService(
            BranchRepository(session),
            assistant_branch_code=BRANCH_CODE,
        )

        with pytest.raises(BranchNotConfiguredError):
            service.get_current_branch()


def test_profile_loader_rejects_unknown_fields(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid.json"
    payload = make_profile().model_dump()
    payload["unexpected"] = "not-allowed"
    profile_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_profile(profile_path)


def test_provisioning_cli_requires_confirmation_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database_path = tmp_path / "installation.db"
    database_url = sqlite_url(database_path)
    profile_path = tmp_path / "assistant-profile.json"
    profile_path.write_text(make_profile().model_dump_json(), encoding="utf-8")
    monkeypatch.setenv("ASSISTANT_BRANCH_CODE", BRANCH_CODE)
    monkeypatch.setenv("DATABASE_URL", database_url)

    assert main(["--profile", str(profile_path)]) == 0
    assert not database_path.exists()
    assert "no se realizaron cambios" in capsys.readouterr().out

    get_database_settings.cache_clear()
    command.upgrade(Config(str(REPOSITORY_ROOT / "alembic.ini")), "head")
    try:
        assert main(["--profile", str(profile_path), "--apply"]) == 0
        assert "(created)" in capsys.readouterr().out
        assert main(["--profile", str(profile_path), "--apply"]) == 0
        assert "(unchanged)" in capsys.readouterr().out
    finally:
        get_database_settings.cache_clear()


def test_provisioning_cli_rejects_profile_for_another_installation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    profile_path = tmp_path / "wrong-profile.json"
    profile_path.write_text(make_profile(code="sucursal-ajena").model_dump_json(), encoding="utf-8")
    monkeypatch.setenv("ASSISTANT_BRANCH_CODE", BRANCH_CODE)

    assert main(["--profile", str(profile_path), "--apply"]) == 2
    captured = capsys.readouterr()
    assert "No fue posible" in captured.err
    assert "sucursal-ajena" not in captured.err
