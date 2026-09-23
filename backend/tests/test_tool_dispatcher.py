"""The dispatcher accepts only validated, scoped tools and bounds caller wait."""

import csv
import json
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
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.commercial import BranchInfo, ProductPriceInfo
from backend.app.schemas.faq import FAQ_TSV_COLUMNS
from backend.app.schemas.price import PriceData
from backend.app.schemas.product import ProductData
from backend.app.services.faq_response_policy import FAQAnswer, HumanHelpProposal
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
    session_factory: sessionmaker[Session], tmp_path: Path
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

    price = dispatcher.dispatch(
        "get_product_price", json.dumps({"product_id": own_id, "unit": "kg"})
    )
    foreign_price = dispatcher.dispatch(
        "get_product_price", json.dumps({"product_id": foreign_id, "unit": "kg"})
    )
    branch = dispatcher.dispatch("get_branch_info", "{}")
    faq = dispatcher.dispatch("search_faq", json.dumps({"query": "Tienen entrega?"}))
    help_proposal = dispatcher.dispatch("request_human_help", '{"reason":"customer_requested"}')

    assert isinstance(price, ProductPriceInfo)
    assert price.amount == Decimal("189.90")
    assert foreign_price == ProductPriceNotFoundResult()
    assert isinstance(branch, BranchInfo)
    assert branch.name == "Sucursal Uno"
    assert isinstance(faq, FAQAnswer)
    assert faq.trust_level == "untrusted_source"
    assert isinstance(help_proposal, HumanHelpProposal)
    assert help_proposal.executed is False


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


def test_worker_owns_its_session_and_timeout_bounds_caller_wait(tmp_path: Path) -> None:
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
        with pytest.raises(ToolExecutionTimeoutError):
            dispatcher.dispatch("request_human_help", '{"reason":"customer_requested"}')
        assert started.is_set()
        assert thread_ids[0] != get_ident()
    finally:
        release.set()

    follow_up = dispatcher.dispatch("request_human_help", '{"reason":"faq_unknown"}')
    assert isinstance(follow_up, HumanHelpProposal)
    assert follow_up.executed is False


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
