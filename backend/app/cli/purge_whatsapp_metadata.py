"""Preview or apply branch-scoped WhatsApp metadata retention."""

import argparse
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import AssistantSettings, DatabaseSettings
from backend.app.core.exceptions import ApplicationError
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.services.whatsapp_privacy_service import WhatsAppPrivacyService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Revisa o purga metadatos de WhatsApp expirados.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ejecuta el borrado; sin esta opción solo muestra conteos",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    engine = None
    try:
        assistant_settings = AssistantSettings()
        database_settings = DatabaseSettings()
        engine = create_database_engine(database_settings.database_url.get_secret_value())
        service = WhatsAppPrivacyService(
            create_database_session_factory(engine), settings=assistant_settings
        )
        result = service.purge_expired(apply=args.apply)
    except (OSError, ValidationError, ApplicationError, SQLAlchemyError, ValueError):
        print("No fue posible revisar o purgar metadatos de WhatsApp.", file=sys.stderr)
        return 2
    finally:
        if engine is not None:
            engine.dispose()

    action = "Purgados" if args.apply else "Candidatos"
    print(
        f"{action}: conversaciones={result.conversations}, mensajes={result.messages}, "
        f"recibos_completados={result.completed_receipts}; "
        f"reservas_para_revision={result.claimed_for_review}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
