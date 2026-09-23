"""Versioned layout contract for one branch's Excel price import file."""

PRICE_IMPORT_SHEET = "Precios"
PRICE_IMPORT_SCHEMA_VERSION = 1
PRICE_IMPORT_VERSION_LABEL_CELL = "A3"
PRICE_IMPORT_VERSION_CELL = "B3"
PRICE_IMPORT_BRANCH_LABEL_CELL = "D3"
PRICE_IMPORT_BRANCH_CELL = "E3"
PRICE_IMPORT_HEADER_ROW = 6
PRICE_IMPORT_FIRST_DATA_ROW = 7
PRICE_IMPORT_COLUMNS = (
    "product_id",
    "product_name",
    "unit",
    "price_mxn",
    "verified_on",
)
