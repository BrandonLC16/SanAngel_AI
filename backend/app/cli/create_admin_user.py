"""Provision one branch-scoped admin locally without a password command-line argument."""

import argparse
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import AdminAuthSettings, DatabaseSettings
from backend.app.core.exceptions import ApplicationError
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.services.admin_auth_service import AdminAuthService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Crear usuario administrador de esta instalación.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--role", choices=[role.value for role in AdminRole], default="viewer")
    args = parser.parse_args(argv)
    engine = None
    try:
        password = getpass.getpass("Contraseña: ")
        confirmation = getpass.getpass("Confirmar contraseña: ")
        if password != confirmation:
            raise ValueError("password confirmation mismatch")
        settings = AdminAuthSettings()
        database = DatabaseSettings()
        engine = create_database_engine(database.database_url.get_secret_value())
        AdminAuthService(create_database_session_factory(engine), settings=settings).create_user(
            args.username, password, role=AdminRole(args.role)
        )
    except (OSError, ValueError, ValidationError, ApplicationError, SQLAlchemyError):
        print("No fue posible crear el usuario administrador.", file=sys.stderr)
        return 2
    finally:
        if engine is not None:
            engine.dispose()
    print("Usuario administrador creado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
