"""Unresolved FAQ aggregates are scoped, atomic, and free of question text."""

import csv
import json
import logging
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import ConversationIdentitySettings, get_database_settings
from backend.app.db.models.unresolved_question import UnresolvedQuestion
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.faq import FAQ_TSV_COLUMNS
from backend.app.services.faq_response_policy import (
    UNKNOWN_FALLBACK,
    FAQFallback,
    HumanHelpReason,
    request_human_help,
)
from backend.app.services.tool_dispatcher import ToolDispatcher
from backend.app.services.unresolved_question_service import UnresolvedQuestionService
from backend.app.services.whatsapp_privacy_service import WhatsAppPrivacyService

ROOT = Path(__file__).resolve().parents[2]
KEY = "test-only-unresolved-question-key-123456789"


def settings(branch_code: str = "sucursal-uno") -> ConversationIdentitySettings:
    return ConversationIdentitySettings(
        assistant_branch_code=branch_code,
        conversation_identity_key=KEY,
        _env_file=None,
    )


@pytest.fixture
def sessions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[sessionmaker[Session]]:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'unresolved.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        for code in ("sucursal-uno", "sucursal-dos"):
            BranchRepository(session).create(
                BranchData(
                    code=code,
                    name=code,
                    address="Dirección de prueba",
                    business_hours="Lunes a viernes",
                )
            )
    try:
        yield factory
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def fallback(reason: HumanHelpReason = HumanHelpReason.FAQ_UNKNOWN) -> FAQFallback:
    return FAQFallback(text=UNKNOWN_FALLBACK, human_help=request_human_help(reason))


def test_normalized_questions_increment_once_per_branch_and_reason_without_pii(
    sessions: sessionmaker[Session], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        with sessions.begin() as session:
            own = UnresolvedQuestionService(session, settings=settings())
            own.record_faq_fallback(" ¿Cuál es el precio de RIB ÉYE? ", fallback())
            own.record_faq_fallback("cual es el precio de rib eye", fallback())
            own.record_faq_fallback(
                "cual es el precio de rib eye", fallback(HumanHelpReason.FAQ_AMBIGUOUS)
            )
            UnresolvedQuestionService(
                session, settings=settings("sucursal-dos")
            ).record_faq_fallback("cual es el precio de rib eye", fallback())
        with sessions() as session:
            own_rows = UnresolvedQuestionService(session, settings=settings()).list_most_frequent()
            other_rows = UnresolvedQuestionService(
                session, settings=settings("sucursal-dos")
            ).list_most_frequent()
            stored = session.scalars(select(UnresolvedQuestion)).all()

    assert [(item.reason, item.occurrences) for item in own_rows] == [
        (HumanHelpReason.FAQ_UNKNOWN, 2),
        (HumanHelpReason.FAQ_AMBIGUOUS, 1),
    ]
    assert len(other_rows) == 1 and other_rows[0].occurrences == 1
    assert own_rows[0].question_key == other_rows[0].question_key
    assert len(stored) == 3
    assert all(len(item.question_key) == 64 for item in stored)
    assert "rib eye" not in repr(stored) + caplog.text
    assert KEY not in repr(stored) + caplog.text


def test_sensitive_query_is_only_stored_as_key_and_list_is_bounded(
    sessions: sessionmaker[Session],
) -> None:
    private_query = "Mi correo es cliente@example.com y mi teléfono 5512345678"
    with sessions.begin() as session:
        service = UnresolvedQuestionService(session, settings=settings())
        service.record_faq_fallback(private_query, fallback())
    with sessions() as session:
        row = session.scalar(select(UnresolvedQuestion))
        assert row is not None
        assert private_query not in repr(row)
        assert "cliente@example.com" not in repr(row)
        assert "5512345678" not in repr(row)
        service = UnresolvedQuestionService(session, settings=settings())
        assert len(service.list_most_frequent()) == 1
        with pytest.raises(ValueError):
            service.list_most_frequent(limit=101)


def test_invalid_query_cannot_create_an_aggregate(sessions: sessionmaker[Session]) -> None:
    with sessions.begin() as session:
        service = UnresolvedQuestionService(session, settings=settings())
        for query in ("", "x" * 241, "pregunta\nprivada"):
            with pytest.raises(ValueError, match="invalid unresolved question"):
                service.record_faq_fallback(query, fallback())
    with sessions() as session:
        assert session.scalars(select(UnresolvedQuestion)).all() == []


def test_concurrent_records_use_atomic_counter(sessions: sessionmaker[Session]) -> None:
    def record() -> None:
        with sessions.begin() as session:
            UnresolvedQuestionService(session, settings=settings()).record_faq_fallback(
                "¿Tienen arrachera?", fallback()
            )

    with ThreadPoolExecutor(max_workers=4) as workers:
        list(workers.map(lambda _: record(), range(8)))
    with sessions() as session:
        rows = UnresolvedQuestionService(session, settings=settings()).list_most_frequent()
    assert len(rows) == 1 and rows[0].occurrences == 8


def test_dispatcher_records_only_deterministic_faq_fallback(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    faq_path = tmp_path / "faq.tsv"
    with faq_path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source, delimiter="\t")
        writer.writerow(FAQ_TSV_COLUMNS)
        writer.writerow(("1", "sucursal-uno", "general", "¿Tienen entrega?", "Sí"))
    dispatcher = ToolDispatcher(
        session_factory=sessions,
        faq_source_path=faq_path,
        assistant_settings=settings(),
        unresolved_settings=settings(),
    )
    assert dispatcher.dispatch("search_faq", json.dumps({"query": "Tienen entrega?"})).text == "Sí"
    result = dispatcher.dispatch("search_faq", json.dumps({"query": "¿Aceptan vales?"}))
    assert isinstance(result, FAQFallback)
    with sessions() as session:
        rows = UnresolvedQuestionService(session, settings=settings()).list_most_frequent()
    assert len(rows) == 1 and rows[0].reason is HumanHelpReason.FAQ_UNKNOWN


def test_dispatcher_rejects_cross_branch_recorder(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="scope must match"):
        ToolDispatcher(
            session_factory=sessions,
            faq_source_path=tmp_path / "unused.tsv",
            assistant_settings=settings(),
            unresolved_settings=settings("sucursal-dos"),
        )


def test_expired_aggregates_are_purged_only_for_configured_branch(
    sessions: sessionmaker[Session],
) -> None:
    now = datetime.now(UTC)
    with sessions.begin() as session:
        for branch_code in ("sucursal-uno", "sucursal-dos"):
            service = UnresolvedQuestionService(session, settings=settings(branch_code))
            service.record_faq_fallback("¿Pregunta antigua?", fallback())
        own = UnresolvedQuestionService(session, settings=settings())
        old_key = own.list_most_frequent()[0].question_key
        own.record_faq_fallback("¿Pregunta nueva?", fallback())
        for row in session.scalars(select(UnresolvedQuestion)).all():
            if row.question_key == old_key:
                row.last_seen_at = now - timedelta(days=31)
    privacy = WhatsAppPrivacyService(sessions, settings=settings())
    assert privacy.purge_expired(now=now).unresolved_questions == 1
    assert privacy.purge_expired(now=now, apply=True).unresolved_questions == 1
    with sessions() as session:
        remaining = session.scalars(select(UnresolvedQuestion)).all()
        assert len(remaining) == 2
        assert (
            UnresolvedQuestionService(session, settings=settings())
            .list_most_frequent()[0]
            .question_key
            != old_key
        )
        assert (
            UnresolvedQuestionService(session, settings=settings("sucursal-dos"))
            .list_most_frequent()[0]
            .question_key
            == old_key
        )
