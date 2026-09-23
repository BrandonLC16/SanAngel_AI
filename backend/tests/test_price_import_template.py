"""Inspect the versioned Excel template without executing workbook content."""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from backend.app.schemas.price_import_template import (
    PRICE_IMPORT_BRANCH_CELL,
    PRICE_IMPORT_BRANCH_LABEL_CELL,
    PRICE_IMPORT_COLUMNS,
    PRICE_IMPORT_FIRST_DATA_ROW,
    PRICE_IMPORT_HEADER_ROW,
    PRICE_IMPORT_SCHEMA_VERSION,
    PRICE_IMPORT_SHEET,
    PRICE_IMPORT_VERSION_CELL,
    PRICE_IMPORT_VERSION_LABEL_CELL,
)

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "price_import.example.xlsx"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def workbook_cells(package: ZipFile) -> dict[str, tuple[str | None, str | None, str | None]]:
    root = ElementTree.fromstring(package.read("xl/worksheets/sheet1.xml"))
    return {
        cell.attrib["r"]: (
            cell.attrib.get("t"),
            cell.attrib.get("s"),
            cell.findtext("x:v", namespaces=NS),
        )
        for cell in root.findall(".//x:sheetData/x:row/x:c", NS)
    }


def test_template_has_one_branch_and_exact_versioned_columns() -> None:
    with ZipFile(EXAMPLE) as package:
        workbook = ElementTree.fromstring(package.read("xl/workbook.xml"))
        sheets = workbook.findall(".//x:sheets/x:sheet", NS)
        cells = workbook_cells(package)

    assert [sheet.attrib["name"] for sheet in sheets] == [PRICE_IMPORT_SHEET]
    assert cells[PRICE_IMPORT_VERSION_LABEL_CELL][2] == "schema_version"
    assert cells[PRICE_IMPORT_VERSION_CELL][0] == "n"
    assert cells[PRICE_IMPORT_VERSION_CELL][2] == "1"
    assert PRICE_IMPORT_SCHEMA_VERSION == 1
    assert cells[PRICE_IMPORT_BRANCH_LABEL_CELL][2] == "branch_code"
    assert cells[PRICE_IMPORT_BRANCH_CELL][2] == "sucursal-demo"
    expected_columns = (
        "product_id",
        "product_name",
        "unit",
        "price_mxn",
        "verified_on",
    )
    assert tuple(cells[f"{column}{PRICE_IMPORT_HEADER_ROW}"][2] for column in "ABCDE") == (
        expected_columns
    )
    assert PRICE_IMPORT_COLUMNS == expected_columns
    assert PRICE_IMPORT_FIRST_DATA_ROW == PRICE_IMPORT_HEADER_ROW + 1
    assert "branch_code" not in PRICE_IMPORT_COLUMNS


def test_example_has_only_fictitious_typed_price_rows() -> None:
    with ZipFile(EXAMPLE) as package:
        cells = workbook_cells(package)
        styles = ElementTree.fromstring(package.read("xl/styles.xml"))

    formats = {
        item.attrib["numFmtId"]: item.attrib["formatCode"]
        for item in styles.findall(".//x:numFmts/x:numFmt", NS)
    }
    cell_styles = styles.findall(".//x:cellXfs/x:xf", NS)
    for row in (7, 8):
        product_id = cells[f"A{row}"]
        product_name = cells[f"B{row}"]
        unit = cells[f"C{row}"]
        price = cells[f"D{row}"]
        verified_on = cells[f"E{row}"]

        assert product_id[0] == "n" and int(product_id[2]) >= 900000
        assert "ejemplo" in product_name[2].lower()
        assert unit[2] in {"kg", "piece"}
        assert price[0] == "n" and Decimal(price[2]) >= 0
        assert formats[cell_styles[int(price[1])].attrib["numFmtId"]] == "#,##0.00"
        assert verified_on[0] == "n"
        assert date(1899, 12, 30) + timedelta(days=int(verified_on[2])) == date(2026, 1, 15)
        assert formats[cell_styles[int(verified_on[1])].attrib["numFmtId"]] == "yyyy-mm-dd"


def test_template_contains_no_macros_formulas_or_external_links() -> None:
    with ZipFile(EXAMPLE) as package:
        names = package.namelist()
        sheet = ElementTree.fromstring(package.read("xl/worksheets/sheet1.xml"))
        content_types = package.read("[Content_Types].xml").lower()

    assert EXAMPLE.suffix == ".xlsx"
    assert not any(
        "vba" in name.lower() or "macrosheet" in name.lower() or "externallink" in name.lower()
        for name in names
    )
    assert b"macroenabled" not in content_types
    assert not sheet.findall(".//x:f", NS)
