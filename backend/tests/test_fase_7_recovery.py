"""A new Fase 7 database can be migrated, backed up, and restored offline."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import func, select

from backend.app.core.config import get_database_settings
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.message import Message
from backend.app.db.models.unresolved_question import UnresolvedQuestion
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.session import create_database_engine, create_database_session_factory
from scripts.backup_sqlite import backup_sqlite

ROOT = Path(__file__).resolve().parents[2]
HEAD = "20260924_0007"


def test_fase_7_migration_from_zero_survives_isolated_backup_restore(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{source.as_posix()}")
    get_database_settings.cache_clear()
    config = Config(str(ROOT / "alembic.ini"))

    try:
        command.upgrade(config, "head")
        command.check(config)
        engine = create_database_engine(f"sqlite+pysqlite:///{source.as_posix()}")
        try:
            with create_database_session_factory(engine).begin() as session:
                branch = Branch(
                    code="sucursal-prueba",
                    name="Sucursal de prueba",
                    address="Dirección de prueba",
                    business_hours="Lunes a viernes",
                )
                session.add(branch)
                session.flush()
                conversation = Conversation(branch_id=branch.id, external_user_key="a" * 64)
                session.add(conversation)
                session.flush()
                session.add_all(
                    (
                        Message(
                            branch_id=branch.id,
                            conversation_id=conversation.id,
                            direction="inbound",
                        ),
                        WhatsAppEventReceipt(
                            branch_id=branch.id,
                            provider_message_id="event-offline-test",
                            status="completed",
                            completed_at=datetime.now(UTC),
                        ),
                        UnresolvedQuestion(
                            branch_id=branch.id,
                            reason="faq_unknown",
                            question_key="b" * 64,
                            occurrences=2,
                        ),
                    )
                )
        finally:
            engine.dispose()

        backup_sqlite(source, backup)
        assert not restored.exists()
        backup_sqlite(backup, restored)
        monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{restored.as_posix()}")
        get_database_settings.cache_clear()
        command.check(config)

        engine = create_database_engine(f"sqlite+pysqlite:///{restored.as_posix()}")
        try:
            with engine.connect() as connection:
                assert connection.exec_driver_sql("PRAGMA integrity_check").scalar() == "ok"
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []
                assert MigrationContext.configure(connection).get_current_revision() == HEAD
            with create_database_session_factory(engine)() as session:
                assert session.scalar(select(Branch.code)) == "sucursal-prueba"
                assert session.scalar(select(func.count()).select_from(Conversation)) == 1
                assert session.scalar(select(func.count()).select_from(Message)) == 1
                assert session.scalar(select(func.count()).select_from(WhatsAppEventReceipt)) == 1
                assert session.scalar(select(UnresolvedQuestion.occurrences)) == 2
        finally:
            engine.dispose()
    finally:
        get_database_settings.cache_clear()
