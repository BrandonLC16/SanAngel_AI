"""Explicit local revocation of every active admin session in this installation."""

import argparse
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import get_admin_auth_settings, get_database_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.services.admin_auth_service import AdminAuthService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Revocar sesiones admin de la sucursal configurada."
    )
    parser.add_argument("--apply", action="store_true", help="Ejecutar la revocación")
    args = parser.parse_args(argv)
    if not args.apply:
        print("Se requiere --apply para revocar sesiones.", file=sys.stderr)
        return 2

    engine = None
    try:
        settings = get_admin_auth_settings()
        database = get_database_settings()
        engine = create_database_engine(database.database_url.get_secret_value())
        count = AdminAuthService(
            create_database_session_factory(engine), settings=settings
        ).revoke_all_sessions()
    except (OSError, ValueError, ValidationError, ApplicationError, SQLAlchemyError):
        print("No fue posible revocar las sesiones administrativas.", file=sys.stderr)
        return 2
    finally:
        if engine is not None:
            engine.dispose()
    print(f"Sesiones administrativas revocadas: {count}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
