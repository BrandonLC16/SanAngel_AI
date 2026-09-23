"""Confirmed price imports are scoped, exact, and atomic."""

from collections.abc import Generator
from datetime import date
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from openpyxl import Workbook
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import AssistantSettings, get_database_settings
from backend.app.db.models.price import Price
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.price_repository import PriceRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.schemas.branch import BranchData
from backend.app.schemas.price import PriceData
from backend.app.schemas.price_import_template import PRICE_IMPORT_COLUMNS
from backend.app.schemas.product import ProductData
from backend.app.services.branch_scope import BranchScope
from backend.app.services.price_import_transaction import (
    PriceImportConfirmationError,
    PriceImportStalePreviewError,
    PriceImportTransactionService,
    PriceImportValidationError,
    PriceImportWriteError,
)

ROOT = Path(__file__).resolve().parents[2]
SCOPE = BranchScope.from_settings(AssistantSettings(assistant_branch_code="sucursal-demo"))
VERIFIED_ON = date(2026, 1, 15)


def workbook_bytes(
    rows: list[tuple[int, str, str, int | float, date]], *, branch: str = "sucursal-demo"
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Precios"
    sheet["A3"] = "schema_version"
    sheet["B3"] = 1
    sheet["D3"] = "branch_code"
    sheet["E3"] = branch
    for column, header in enumerate(PRICE_IMPORT_COLUMNS, start=1):
        sheet.cell(6, column, header)
    for source_row, values in enumerate(rows, start=7):
        for column, value in enumerate(values, start=1):
            sheet.cell(source_row, column, value)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def make_branch(session: Session, code: str):
    return BranchRepository(session).create(
        BranchData(
            code=code,
            name=f"Sucursal {code}",
            address="Dirección ficticia",
            phone=None,
            business_hours="Lunes a viernes",
        )
    )


@pytest.fixture
def catalog(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[tuple[sessionmaker[Session], dict[str, int]]]:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'import.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = create_database_engine(database_url)
    factory = create_database_session_factory(engine)
    identifiers: dict[str, int] = {}
    try:
        with factory.begin() as session:
            branch = make_branch(session, "sucursal-demo")
            other_branch = make_branch(session, "otra-sucursal")
            products = ProductRepository(session, branch=branch)
            for name in ("Nuevo", "Cambio", "Igual", "Cambiante"):
                product = products.create(ProductData(name=name, category="Res"))
                identifiers[name] = product.id
                if name in {"Cambio", "Igual"}:
                    amount = "100.00" if name == "Cambio" else "30.00"
                    PriceRepository(session, branch=branch).create(
                        product, PriceData(amount=amount, unit="kg")
                    )
            foreign = ProductRepository(session, branch=other_branch).create(
                ProductData(name="Ajeno", category="Res")
            )
            identifiers["foreign"] = foreign.id
            PriceRepository(session, branch=other_branch).create(
                foreign, PriceData(amount="999.00", unit="kg")
            )
        yield factory, identifiers
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def prices(factory: sessionmaker[Session]) -> tuple[tuple[int, str, Decimal], ...]:
    with factory() as session:
        return tuple(
            session.execute(
                select(Price.product_id, Price.unit, Price.amount).order_by(Price.product_id)
            ).all()
        )


def import_content(identifiers: dict[str, int]) -> bytes:
    return workbook_bytes(
        [
            (identifiers["Nuevo"], "Nuevo", "kg", 75.25, VERIFIED_ON),
            (identifiers["Cambio"], "Cambio", "kg", 120.55, VERIFIED_ON),
            (identifiers["Igual"], "Igual", "kg", 30, VERIFIED_ON),
        ]
    )


def test_confirmed_import_upserts_exact_prices_and_returns_receipt(
    catalog: tuple[sessionmaker[Session], dict[str, int]],
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    content = import_content(identifiers)
    before = prices(factory)
    prepared = service.prepare(content, filename="precios.xlsx")

    assert prepared.preview.is_valid
    assert prices(factory) == before
    receipt = service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=True)

    assert (receipt.created, receipt.updated, receipt.unchanged) == (1, 1, 1)
    assert receipt.file_sha256 == sha256(content).hexdigest()
    assert receipt.branch_code == SCOPE.branch_code
    assert prices(factory) == (
        (identifiers["Nuevo"], "kg", Decimal("75.25")),
        (identifiers["Cambio"], "kg", Decimal("120.55")),
        (identifiers["Igual"], "kg", Decimal("30.00")),
        (identifiers["foreign"], "kg", Decimal("999.00")),
    )

    with pytest.raises(PriceImportStalePreviewError):
        service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=True)
    refreshed = service.prepare(content, filename="precios.xlsx")
    repeat = service.confirm(content, filename="precios.xlsx", prepared=refreshed, confirmed=True)
    assert (repeat.created, repeat.updated, repeat.unchanged) == (0, 0, 3)


@pytest.mark.parametrize("confirmation", (False, None, "true", 1))
def test_explicit_boolean_confirmation_is_required(
    catalog: tuple[sessionmaker[Session], dict[str, int]], confirmation: object
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    content = import_content(identifiers)
    prepared = service.prepare(content, filename="precios.xlsx")
    before = prices(factory)

    with pytest.raises(PriceImportConfirmationError):
        service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=confirmation)
    assert prices(factory) == before


def test_confirmation_is_bound_to_file_name_bytes_and_branch(
    catalog: tuple[sessionmaker[Session], dict[str, int]],
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    content = import_content(identifiers)
    prepared = service.prepare(content, filename="precios.xlsx")
    before = prices(factory)
    other_content = workbook_bytes([(identifiers["Nuevo"], "Nuevo", "kg", 70, VERIFIED_ON)])

    for candidate_content, filename, scope in (
        (other_content, "precios.xlsx", SCOPE),
        (content, "otro.xlsx", SCOPE),
        (content, "precios.xlsx", BranchScope("otra-sucursal")),
    ):
        with pytest.raises(PriceImportConfirmationError):
            PriceImportTransactionService(factory, branch_scope=scope).confirm(
                candidate_content, filename=filename, prepared=prepared, confirmed=True
            )
    assert prices(factory) == before


def test_invalid_or_foreign_product_never_writes(
    catalog: tuple[sessionmaker[Session], dict[str, int]],
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    before = prices(factory)
    for content in (
        workbook_bytes([(identifiers["Nuevo"], "Nuevo", "kg", -1, VERIFIED_ON)]),
        workbook_bytes([(identifiers["foreign"], "Ajeno", "kg", 10, VERIFIED_ON)]),
        workbook_bytes(
            [(identifiers["Nuevo"], "Nuevo", "kg", 10, VERIFIED_ON)],
            branch="otra-sucursal",
        ),
    ):
        prepared = service.prepare(content, filename="precios.xlsx")
        assert not prepared.preview.is_valid
        assert prepared.file_sha256 == ""
        with pytest.raises(PriceImportValidationError) as captured:
            service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=True)
        assert captured.value.issues
    assert prices(factory) == before


def test_changed_catalog_or_price_blocks_stale_preview(
    catalog: tuple[sessionmaker[Session], dict[str, int]],
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    content = import_content(identifiers)
    prepared = service.prepare(content, filename="precios.xlsx")
    with factory.begin() as session:
        branch = BranchRepository(session).get_by_code(SCOPE.branch_code)
        product = ProductRepository(session, branch=branch).get_by_id(identifiers["Cambio"])
        current = PriceRepository(session, branch=branch).get_for_product(product, unit="kg")
        PriceRepository(session, branch=branch).update(
            current, PriceData(amount="105.00", unit="kg")
        )
    before = prices(factory)

    with pytest.raises(PriceImportStalePreviewError):
        service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=True)
    assert prices(factory) == before


def test_product_renamed_after_preview_blocks_every_write(
    catalog: tuple[sessionmaker[Session], dict[str, int]],
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    content = import_content(identifiers)
    prepared = service.prepare(content, filename="precios.xlsx")
    with factory.begin() as session:
        branch = BranchRepository(session).get_by_code(SCOPE.branch_code)
        product = ProductRepository(session, branch=branch).get_by_id(identifiers["Cambio"])
        ProductRepository(session, branch=branch).update(
            product, ProductData(name="Renombrado", category="Res")
        )
    before = prices(factory)

    with pytest.raises(PriceImportValidationError) as captured:
        service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=True)
    assert captured.value.issues[0].code == "product_name_mismatch"
    assert prices(factory) == before


def test_late_database_failure_rolls_back_earlier_price_write(
    catalog: tuple[sessionmaker[Session], dict[str, int]],
) -> None:
    factory, identifiers = catalog
    service = PriceImportTransactionService(factory, branch_scope=SCOPE)
    content = import_content(identifiers)
    prepared = service.prepare(content, filename="precios.xlsx")
    before = prices(factory)
    writes = 0

    def fail_second_write(_connection, _cursor, statement, parameters, _context, _executemany):
        nonlocal writes
        if statement.lstrip().upper().startswith(("INSERT INTO PRICES", "UPDATE PRICES")):
            writes += 1
            if writes == 2:
                raise IntegrityError(statement, parameters, Exception("synthetic failure"))

    engine = factory.kw["bind"]
    event.listen(engine, "before_cursor_execute", fail_second_write)
    try:
        with pytest.raises(PriceImportWriteError, match="could not be committed"):
            service.confirm(content, filename="precios.xlsx", prepared=prepared, confirmed=True)
    finally:
        event.remove(engine, "before_cursor_execute", fail_second_write)

    assert writes == 2
    assert prices(factory) == before
