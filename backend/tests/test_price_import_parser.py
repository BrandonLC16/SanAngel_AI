"""Adversarial workbook validation stays separate from database writes."""

import sqlite3
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from backend.app.services.branch_scope import BranchScope
from backend.app.services.price_import_parser import (
    MAX_PRICE_IMPORT_BYTES,
    parse_price_import,
)

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "price_import.example.xlsx"
SCOPE = BranchScope("sucursal-demo")


def edited_workbook(edit: Callable[[Worksheet], None]) -> bytes:
    workbook = load_workbook(EXAMPLE)
    edit(workbook.active)
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def parse(content: bytes, filename: str = "precios.xlsx"):
    return parse_price_import(content, filename=filename, branch_scope=SCOPE)


def test_example_parses_typed_rows_for_configured_branch() -> None:
    result = parse(EXAMPLE.read_bytes())

    assert result.is_valid
    assert result.issues == ()
    assert [(row.source_row, row.product_id, row.unit) for row in result.rows] == [
        (7, 900001, "kg"),
        (8, 900002, "piece"),
    ]
    assert result.rows[0].price_mxn == Decimal("199.9")
    assert result.rows[0].verified_on == date(2026, 1, 15)


@pytest.mark.parametrize(
    "filename",
    ("precios.xlsm", "../precios.xlsx", "x\\precios.xlsx", "C:precios.xlsx", "..precios.xlsx"),
)
def test_rejects_extension_and_path_traversal(filename: str) -> None:
    result = parse(EXAMPLE.read_bytes(), filename)

    assert result.rows == ()
    assert result.issues[0].code == "invalid_filename"


def test_rejects_oversized_or_malformed_input() -> None:
    assert parse(b"x" * (MAX_PRICE_IMPORT_BYTES + 1)).issues[0].code == "invalid_size"
    assert parse(b"not a workbook").issues[0].code == "invalid_workbook"


def test_rejects_foreign_branch_before_rows() -> None:
    result = parse_price_import(
        EXAMPLE.read_bytes(), filename="precios.xlsx", branch_scope=BranchScope("otra-sucursal")
    )

    assert result.rows == ()
    assert result.issues[0].code == "branch_mismatch"


@pytest.mark.parametrize(
    ("cell", "value", "code"),
    (
        ("B3", 2, "invalid_metadata"),
        ("A6", "otro_id", "invalid_headers"),
        ("F6", "otro", "invalid_headers"),
        ("A7", "900001", "invalid_positive_integer"),
        ("A7", -1, "invalid_positive_integer"),
        ("A7", 2**63, "invalid_positive_integer"),
        ("B7", "", "invalid_text"),
        ("C7", "KG", "invalid_code"),
        ("D7", "199.90", "invalid_number"),
        ("D7", -1, "out_of_range"),
        ("D7", 1.001, "out_of_range"),
        ("D7", 10000000000, "out_of_range"),
        ("E7", "2026-01-15", "invalid_date"),
        ("E7", date.today() + timedelta(days=1), "invalid_date"),
        ("F7", "extra", "unexpected_value"),
    ),
)
def test_rejects_invalid_metadata_headers_and_rows(cell: str, value: object, code: str) -> None:
    def edit(sheet: Worksheet) -> None:
        sheet[cell] = value

    result = parse(edited_workbook(edit))

    assert result.rows == ()
    assert any(issue.code == code for issue in result.issues)
    if cell[1:] == "7" and cell != "B7":
        assert any(issue.row == 7 for issue in result.issues)


def test_reports_multiple_row_errors_without_partial_rows() -> None:
    def edit(sheet: Worksheet) -> None:
        sheet["A7"] = "bad"
        sheet["D8"] = -1

    result = parse(edited_workbook(edit))

    assert not result.is_valid
    assert result.rows == ()
    assert {(issue.row, issue.field) for issue in result.issues} == {
        (7, "product_id"),
        (8, "price_mxn"),
    }


def test_rejects_duplicate_product_and_unit() -> None:
    def edit(sheet: Worksheet) -> None:
        sheet["A8"] = 900001
        sheet["C8"] = "kg"

    result = parse(edited_workbook(edit))

    assert result.rows == ()
    assert result.issues == (type(result.issues[0])(8, "product_id/unit", "duplicate"),)


@pytest.mark.parametrize("part_name", ("../outside.txt", "xl/vbaProject.bin"))
def test_rejects_unsafe_package_members(part_name: str) -> None:
    output = BytesIO()
    with ZipFile(EXAMPLE) as source, ZipFile(output, "w") as target:
        for member in source.infolist():
            target.writestr(member, source.read(member.filename))
        target.writestr(part_name, b"untrusted")

    result = parse(output.getvalue())

    assert result.rows == ()
    assert result.issues[0].code == "unsafe_package"


def test_rejects_formula_and_external_relationship() -> None:
    formula = edited_workbook(lambda sheet: sheet.__setitem__("D7", "=1+1"))
    assert parse(formula).issues[0].code == "unsafe_package"

    output = BytesIO()
    with ZipFile(EXAMPLE) as source, ZipFile(output, "w") as target:
        for member in source.infolist():
            target.writestr(member, source.read(member.filename))
        target.writestr(
            "xl/_rels/unsafe.rels",
            '<Relationships><Relationship TargetMode="External" Target="https://invalid.example"/></Relationships>',
        )
    assert parse(output.getvalue()).issues[0].code == "unsafe_package"


def test_declared_dimension_cannot_hide_a_later_row() -> None:
    output = BytesIO()
    with ZipFile(EXAMPLE) as source, ZipFile(output, "w") as target:
        for member in source.infolist():
            content = source.read(member.filename)
            if member.filename == "xl/worksheets/sheet1.xml":
                content = content.replace(
                    b"</x:sheetPr>", b'</x:sheetPr><x:dimension ref="A1:E7" />'
                )
            target.writestr(member, content)

    result = parse(output.getvalue())

    assert result.is_valid
    assert [row.source_row for row in result.rows] == [7, 8]


@pytest.mark.parametrize("cell", ("G7", "A1007"))
def test_rejects_data_outside_bounded_table(cell: str) -> None:
    def edit(sheet: Worksheet) -> None:
        sheet[cell] = "extra"

    result = parse(edited_workbook(edit))

    assert result.rows == ()
    assert result.issues[0].code == "unsafe_package"


def test_invalid_and_foreign_files_leave_database_unchanged(tmp_path: Path) -> None:
    database = tmp_path / "prices.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE prices (product_id INTEGER, amount TEXT)")
        connection.execute("INSERT INTO prices VALUES (900001, '199.90')")
    before = database.read_bytes()

    invalid = parse(edited_workbook(lambda sheet: sheet.__setitem__("D7", -1)))
    foreign = parse_price_import(
        EXAMPLE.read_bytes(), filename="precios.xlsx", branch_scope=BranchScope("otra-sucursal")
    )

    assert invalid.rows == foreign.rows == ()
    assert database.read_bytes() == before
