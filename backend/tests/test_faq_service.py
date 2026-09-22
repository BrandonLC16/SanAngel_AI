"""Offline tests for bounded branch-scoped FAQ loading and lookup."""

import csv
from pathlib import Path

import pytest

from backend.app.core.config import AssistantSettings
from backend.app.core.exceptions import FAQQueryInputError, FAQSourceError
from backend.app.schemas.faq import FAQ_TSV_COLUMNS, FAQCategory
from backend.app.services.branch_scope import BranchScope
from backend.app.services.faq_service import MAX_FAQ_BYTES, MAX_FAQ_ROWS, FAQService

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "faq_table.example.tsv"


def make_scope(code: str = "sucursal-demo") -> BranchScope:
    return BranchScope.from_settings(AssistantSettings(assistant_branch_code=code))


def make_row(
    question: str,
    answer: str = "Respuesta aprobada.",
    *,
    branch_code: str = "sucursal-demo",
    category: str = "general",
) -> tuple[str, ...]:
    return ("1", branch_code, category, question, answer)


def write_faq(path: Path, rows: list[tuple[str, ...]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as source:
        writer = csv.writer(source, delimiter="\t")
        writer.writerow(FAQ_TSV_COLUMNS)
        writer.writerows(rows)
    return path


def test_example_is_searchable_without_openai_and_uses_configured_scope() -> None:
    service = FAQService(EXAMPLE, branch_scope=make_scope())

    matches = service.search_faq("  QUE FORMAS DE PAGO ACEPTAN?  ")

    assert len(matches) == 1
    assert matches[0].category is FAQCategory.PAGOS
    assert matches[0].branch_code == "sucursal-demo"
    assert matches[0].answer.startswith("EJEMPLO FICTICIO:")
    assert service.search_faq("pregunta sin coincidencia") == ()


def test_search_ranks_exact_prefix_and_partial_matches_and_limits_results(tmp_path: Path) -> None:
    questions = [
        "¿Tienen carne?",
        "Carne molida",
        "Carne",
        "¿Venden carne?",
        "¿Preparan carne?",
        "¿Empacan carne?",
        "¿Cortan carne?",
    ]
    path = write_faq(tmp_path / "ranked.tsv", [make_row(question) for question in questions])
    service = FAQService(path, branch_scope=make_scope())

    matches = service.search_faq("CARNE")

    assert [record.question for record in matches[:2]] == ["Carne", "Carne molida"]
    assert len(matches) == 5
    assert all(record.branch_code == "sucursal-demo" for record in matches)


def test_service_keeps_validated_snapshot_after_file_changes(tmp_path: Path) -> None:
    path = write_faq(tmp_path / "snapshot.tsv", [make_row("Primera pregunta")])
    service = FAQService(path, branch_scope=make_scope())
    write_faq(path, [make_row("Segunda pregunta")])

    assert [record.question for record in service.search_faq("primera")] == ["Primera pregunta"]
    assert service.search_faq("segunda") == ()


def test_header_only_source_has_no_answers(tmp_path: Path) -> None:
    path = write_faq(tmp_path / "empty.tsv", [])

    assert FAQService(path, branch_scope=make_scope()).search_faq("pregunta") == ()


@pytest.mark.parametrize(
    ("configured_code", "foreign_code"),
    (("sucursal-demo", "sucursal-ajena"), ("sucursal-ajena", "sucursal-demo")),
)
def test_foreign_branch_row_rejects_entire_file_without_partial_results(
    tmp_path: Path, configured_code: str, foreign_code: str
) -> None:
    path = write_faq(
        tmp_path / "mixed.tsv",
        [
            make_row("Pregunta propia", branch_code=configured_code),
            make_row("Pregunta ajena", branch_code=foreign_code),
        ],
    )

    with pytest.raises(FAQSourceError) as error:
        FAQService(path, branch_scope=make_scope(configured_code))

    assert foreign_code not in str(error.value)
    assert str(path) not in str(error.value)


@pytest.mark.parametrize("query", ("", "   ", "?", "x\ntexto", "x" * 241, 12))
def test_search_rejects_invalid_queries(tmp_path: Path, query: object) -> None:
    path = write_faq(tmp_path / "queries.tsv", [make_row("Una pregunta")])
    service = FAQService(path, branch_scope=make_scope())

    with pytest.raises(FAQQueryInputError):
        service.search_faq(query)  # type: ignore[arg-type]


def test_missing_file_wrong_extension_and_directory_fail_closed(tmp_path: Path) -> None:
    paths = [tmp_path / "missing.tsv", tmp_path / "wrong.txt", tmp_path / "directory.tsv"]
    paths[2].mkdir()

    for path in paths:
        with pytest.raises(FAQSourceError) as error:
            FAQService(path, branch_scope=make_scope())
        assert str(path) not in str(error.value)


def test_loader_rejects_oversized_file_and_excess_rows(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized.tsv"
    oversized.write_bytes(b"x" * (MAX_FAQ_BYTES + 1))
    with pytest.raises(FAQSourceError):
        FAQService(oversized, branch_scope=make_scope())

    rows = [make_row(f"Pregunta {index}") for index in range(MAX_FAQ_ROWS + 1)]
    excessive = write_faq(tmp_path / "excessive.tsv", rows)
    with pytest.raises(FAQSourceError):
        FAQService(excessive, branch_scope=make_scope())


@pytest.mark.parametrize(
    "content",
    (
        b"\xff\xfe",
        b"branch_code\tcategory\tquestion\tanswer\n",
        b"schema_version\tbranch_code\tcategory\tquestion\tanswer\n"
        b'1\tsucursal-demo\tgeneral\t"sin cerrar',
        b"schema_version\tbranch_code\tcategory\tquestion\tanswer\n1\tsucursal-demo\tgeneral\tQ\n",
    ),
)
def test_loader_rejects_invalid_encoding_header_csv_and_rows(
    tmp_path: Path, content: bytes
) -> None:
    path = tmp_path / "invalid.tsv"
    path.write_bytes(content)

    with pytest.raises(FAQSourceError):
        FAQService(path, branch_scope=make_scope())


def test_source_error_does_not_reveal_file_content(tmp_path: Path) -> None:
    marker = "contenido-privado-de-prueba"
    path = write_faq(tmp_path / "private.tsv", [make_row("Pregunta", f" {marker}")])

    with pytest.raises(FAQSourceError) as error:
        FAQService(path, branch_scope=make_scope())

    assert marker not in str(error.value)
