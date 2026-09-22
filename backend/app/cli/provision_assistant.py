"""Validate and load the branch profile assigned to this assistant installation."""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import AssistantSettings, DatabaseSettings
from backend.app.core.exceptions import ApplicationError
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.branch import AssistantProfile
from backend.app.services.branch_service import BranchProvisioningResult, BranchService

MAX_PROFILE_BYTES = 64 * 1024


def load_profile(path: Path) -> AssistantProfile:
    """Load a bounded UTF-8 JSON profile without accepting alternate formats."""

    if path.suffix.lower() != ".json" or not path.is_file():
        raise ValueError("profile must be an existing JSON file")
    if path.stat().st_size > MAX_PROFILE_BYTES:
        raise ValueError("profile exceeds the maximum allowed size")
    return AssistantProfile.model_validate_json(path.read_bytes())


def validate_profile_scope(profile: AssistantProfile, branch_code: str) -> None:
    if profile.branch.code != branch_code:
        raise ValueError("profile branch does not match ASSISTANT_BRANCH_CODE")


def apply_profile(
    profile: AssistantProfile,
    *,
    branch_code: str,
    database_url: str,
) -> BranchProvisioningResult:
    """Apply one profile in a single transaction and dispose the local engine."""

    engine = create_database_engine(database_url)
    session_factory = create_database_session_factory(engine)
    try:
        with session_factory.begin() as session:
            service = BranchService(
                BranchRepository(session),
                assistant_branch_code=branch_code,
            )
            return service.provision(profile)
    finally:
        engine.dispose()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Valida o carga el perfil de la sucursal asignada a este asistente.",
    )
    parser.add_argument("--profile", type=Path, required=True, help="Archivo JSON del perfil")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Confirma la escritura; sin esta opción solo se valida el archivo",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        assistant_settings = AssistantSettings()
        profile = load_profile(args.profile)
        validate_profile_scope(profile, assistant_settings.assistant_branch_code)

        if not args.apply:
            print(
                "Perfil válido para la instalación; no se realizaron cambios. "
                "Use --apply para cargarlo."
            )
            return 0

        database_settings = DatabaseSettings()
        result = apply_profile(
            profile,
            branch_code=assistant_settings.assistant_branch_code,
            database_url=database_settings.database_url.get_secret_value(),
        )
    except (OSError, UnicodeError, ValueError, ValidationError, ApplicationError, SQLAlchemyError):
        print(
            "No fue posible validar o cargar el perfil. Revise el archivo, el código de "
            "sucursal y que las migraciones estén aplicadas.",
            file=sys.stderr,
        )
        return 2

    print(f"Perfil de sucursal cargado correctamente ({result.action}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
