"""The dispatcher accepts only validated, scoped tools and bounds caller wait."""

import csv
import json
import logging
from collections.abc import Generator
from decimal import Decimal
from pathlib import Path
from threading import Event, get_ident
from unittest.mock import Mock

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import AssistantSettings, get_database_settings
from backend.app.core.exceptions import ToolExecutionTimeoutError
from backend.app.core.logging import TOOL_AUDIT_LOGGER_NAME
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.commercial import BranchInfo, ProductPriceInfo
from backend.app.schemas.faq import FAQ_TSV_COLUMNS
from backend.app.schemas.price import PriceData
from backend.app.schemas.product import ProductData
from backend.app.services.faq_response_policy import FAQAnswer, FAQFallback, HumanHelpProposal
from backend.app.services.tool_contracts import ToolCallValidationError
from backend.app.services.tool_dispatcher import ToolDispatcher
from backend.app.services.tool_handlers import ProductPriceNotFoundResult

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = AssistantSettings(assistant_branch_code="sucursal-uno", _env_file=None)


@pytest.fixture
def session_factory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[sessionmaker[Session]]:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'tool-dispatcher.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    try:
        yield create_database_session_factory(engine)
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def make_dispatcher(session_factory, faq_path: Path, *, timeout: float = 3.0) -> ToolDispatcher:
    return ToolDispatcher(
        session_factory=session_factory,
        faq_source_path=faq_path,
        assistant_settings=SETTINGS,
        timeout_seconds=timeout,
    )


def test_exact_allowlist_dispatches_each_tool_with_backend_branch(
    session_factory: sessionmaker[Session], tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with session_factory.begin() as session:
        own_branch = BranchRepository(session).create(
            BranchData(
                code="sucursal-uno",
                name="Sucursal Uno",
                address="Dirección ficticia uno",
                phone="+520000000000",
                business_hours="Lunes a viernes",
            )
        )
        other_branch = BranchRepository(session).create(
            BranchData(
                code="sucursal-dos",
                name="Sucursal Dos",
                address="Dirección ficticia dos",
                phone="+520000000000",
                business_hours="Sábado",
            )
        )
        own = ProductRepository(session, branch=own_branch).create(
            ProductData(name="Aguja ficticia", category="Res")
        )
        foreign = ProductRepository(session, branch=other_branch).create(
            ProductData(name="Producto ajeno", category="Res")
        )
        PriceRepository(session, branch=own_branch).create(
            own, PriceData(amount="189.90", unit="kg")
        )
        PriceRepository(session, branch=other_branch).create(
            foreign, PriceData(amount="999.00", unit="kg")
        )
        own_id, foreign_id = own.id, foreign.id

    faq_path = tmp_path / "faq.tsv"
    with faq_path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source, delimiter="\t")
        writer.writerow(FAQ_TSV_COLUMNS)
        writer.writerow(
            ("1", "sucursal-uno", "general", "¿Tienen entrega?", "EJEMPLO FICTICIO: Sí.")
        )
    dispatcher = make_dispatcher(session_factory, faq_path)

    with caplog.at_level(logging.INFO, logger=TOOL_AUDIT_LOGGER_NAME):
        price = dispatcher.dispatch(
            "get_product_price", json.dumps({"product_id": own_id, "unit": "kg"})
        )
        foreign_price = dispatcher.dispatch(
            "get_product_price", json.dumps({"product_id": foreign_id, "unit": "kg"})
        )
        branch = dispatcher.dispatch("get_branch_info", "{}")
        faq = dispatcher.dispatch("search_faq", json.dumps({"query": "Tienen entrega?"}))
        fallback = dispatcher.dispatch("search_faq", json.dumps({"query": "Pregunta desconocida"}))
        help_proposal = dispatcher.dispatch("request_human_help", '{"reason":"customer_requested"}')

    assert isinstance(price, ProductPriceInfo)
    assert price.amount == Decimal("189.90")
    assert foreign_price == ProductPriceNotFoundResult()
    assert isinstance(branch, BranchInfo)
    assert branch.name == "Sucursal Uno"
    assert isinstance(faq, FAQAnswer)
    assert faq.trust_level == "untrusted_source"
    assert isinstance(fallback, FAQFallback)
    assert isinstance(help_proposal, HumanHelpProposal)
    assert help_proposal.executed is False
    assert [
        record.getMessage() for record in caplog.records if record.name == TOOL_AUDIT_LOGGER_NAME
    ] == [
        "tool=get_product_price status=ok",
        "tool=get_product_price status=not_found",
        "tool=get_branch_info status=ok",
        "tool=search_faq status=ok",
        "tool=search_faq status=fallback",
        "tool=request_human_help status=proposed",
    ]
    assert "189.90" not in caplog.text
    assert "999.00" not in caplog.text
    assert "Direcci" not in caplog.text


@pytest.mark.parametrize(
    "name",
    ("execute_sql", "run_sql", "update_price", "__getattribute__", "get_product_price.extra"),
)
def test_unknown_tool_is_rejected_before_session_access(name: str, tmp_path: Path) -> None:
    factory = Mock()
    dispatcher = make_dispatcher(factory, tmp_path / "missing.tsv")

    with pytest.raises(ToolCallValidationError, match="unsupported tool"):
        dispatcher.dispatch(name, '{"query":"DROP TABLE prices"}')

    factory.assert_not_called()


@pytest.mark.parametrize(
    ("name", "arguments_json"),
    (
        ("get_branch_info", '{"branch_code":"sucursal-dos"}'),
        ("get_product_price", '{"product_id":1,"unit":"kg","branch_id":2}'),
        ("get_product_price", '{"product_id":1,"unit":"kg","unit":"piece"}'),
        ("search_faq", '{"query":"\n"}'),
        ("request_human_help", '{"reason":"transfer_now"}'),
    ),
)
def test_arguments_are_validated_before_session_access(
    name: str, arguments_json: str, tmp_path: Path
) -> None:
    factory = Mock()
    dispatcher = make_dispatcher(factory, tmp_path / "missing.tsv")

    with pytest.raises(ToolCallValidationError, match="invalid tool arguments"):
        dispatcher.dispatch(name, arguments_json)

    factory.assert_not_called()


@pytest.mark.parametrize(
    ("name", "arguments_json"),
    (
        ("get_product_price", '{"product_id":"1 OR 1=1 --","unit":"kg"}'),
        ("get_product_price", '{"product_id":1,"unit":"kg","sql":"DROP TABLE prices"}'),
        ("get_branch_info", '{"branch_code":"sucursal-dos","role":"admin"}'),
        ("search_faq", '{"query":"Horario","url":"https://attacker.invalid/collect"}'),
        ("request_human_help", '{"reason":"customer_requested","phone":"private-marker"}'),
    ),
)
def test_adversarial_arguments_never_reach_a_handler_or_audit_data(
    name: str, arguments_json: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    factory = Mock()
    dispatcher = make_dispatcher(factory, tmp_path / "missing.tsv")

    with caplog.at_level(logging.INFO, logger=TOOL_AUDIT_LOGGER_NAME):
        with pytest.raises(ToolCallValidationError) as error:
            dispatcher.dispatch(name, arguments_json)

    factory.assert_not_called()
    assert str(error.value) == "invalid tool arguments"
    assert [
        record.getMessage() for record in caplog.records if record.name == TOOL_AUDIT_LOGGER_NAME
    ] == [f"tool={name} status=rejected"]
    assert arguments_json not in caplog.text


def test_untrusted_tool_name_is_redacted_in_audit(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    factory = Mock()
    dispatcher = make_dispatcher(factory, tmp_path / "missing.tsv")
    hostile_name = "read_env\nprivate-marker"

    with caplog.at_level(logging.INFO, logger=TOOL_AUDIT_LOGGER_NAME):
        with pytest.raises(ToolCallValidationError, match="unsupported tool"):
            dispatcher.dispatch(hostile_name, '{"url":"https://attacker.invalid"}')

    factory.assert_not_called()
    assert [
        record.getMessage() for record in caplog.records if record.name == TOOL_AUDIT_LOGGER_NAME
    ] == ["tool=unsupported status=rejected"]
    assert hostile_name not in caplog.text
    assert "attacker.invalid" not in caplog.text


def test_sql_text_in_faq_query_is_only_search_data(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    faq_path = tmp_path / "faq.tsv"
    with faq_path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source, delimiter="\t")
        writer.writerow(FAQ_TSV_COLUMNS)
        writer.writerow(("1", "sucursal-uno", "general", "¿Tienen entrega?", "Respuesta ficticia."))
    dispatcher = make_dispatcher(lambda: Session(), faq_path)

    with caplog.at_level(logging.INFO, logger=TOOL_AUDIT_LOGGER_NAME):
        result = dispatcher.dispatch(
            "search_faq", json.dumps({"query": "SELECT * FROM prices; DROP TABLE prices;"})
        )

    assert isinstance(result, FAQFallback)
    assert "tool=search_faq status=fallback" in caplog.text
    assert "DROP TABLE" not in caplog.text


def test_worker_owns_its_session_and_timeout_bounds_caller_wait(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    started = Event()
    release = Event()
    thread_ids: list[int] = []

    def slow_session_factory() -> Session:
        thread_ids.append(get_ident())
        started.set()
        release.wait(timeout=2)
        return Session()

    dispatcher = make_dispatcher(slow_session_factory, tmp_path / "missing.tsv", timeout=0.05)
    try:
        with caplog.at_level(logging.INFO, logger=TOOL_AUDIT_LOGGER_NAME):
            with pytest.raises(ToolExecutionTimeoutError):
                dispatcher.dispatch("request_human_help", '{"reason":"customer_requested"}')
        assert started.is_set()
        assert thread_ids[0] != get_ident()
    finally:
        release.set()

    assert "tool=request_human_help status=timeout" in caplog.text
    follow_up = dispatcher.dispatch("request_human_help", '{"reason":"faq_unknown"}')
    assert isinstance(follow_up, HumanHelpProposal)
    assert follow_up.executed is False


def test_handler_failure_audit_has_no_exception_detail(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    marker = "private-handler-detail"
    factory = Mock(side_effect=RuntimeError(marker))
    dispatcher = make_dispatcher(factory, tmp_path / "missing.tsv")

    with caplog.at_level(logging.INFO, logger=TOOL_AUDIT_LOGGER_NAME):
        with pytest.raises(RuntimeError, match=marker):
            dispatcher.dispatch("get_branch_info", "{}")

    assert [
        record.getMessage() for record in caplog.records if record.name == TOOL_AUDIT_LOGGER_NAME
    ] == ["tool=get_branch_info status=error"]
    assert marker not in caplog.text


@pytest.mark.parametrize("timeout", (0, -1, 31, float("inf"), float("nan"), True, "3", 10**1000))
def test_invalid_timeout_configuration_is_rejected(timeout: object, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="tool timeout"):
        make_dispatcher(Mock(), tmp_path / "missing.tsv", timeout=timeout)


def test_dispatcher_requires_backend_settings(tmp_path: Path) -> None:
    with pytest.raises(ToolCallValidationError, match="trusted branch configuration"):
        ToolDispatcher(
            session_factory=Mock(),
            faq_source_path=tmp_path / "missing.tsv",
            assistant_settings="sucursal-dos",  # type: ignore[arg-type]
        )
