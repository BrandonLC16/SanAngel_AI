"""Bounded read-only FAQ lookup for the configured assistant branch."""

import csv
import io
import unicodedata
from pathlib import Path

from pydantic import ValidationError

from backend.app.core.exceptions import FAQQueryInputError, FAQSourceError
from backend.app.schemas.faq import validate_faq_columns
from backend.app.services.branch_scope import BranchScope
from backend.app.services.faq_scope import FAQRecord, validate_scoped_faq_row

MAX_FAQ_BYTES = 256 * 1024
MAX_FAQ_ROWS = 500
MAX_FAQ_QUERY_CHARS = 240
MAX_FAQ_RESULTS = 5


class FAQService:
    """Load one validated snapshot and search it without provider or database access."""

    def __init__(
        self,
        source_path: Path,
        *,
        branch_scope: BranchScope,
        managed_records: tuple[FAQRecord, ...] = (),
        overridden_questions: frozenset[str] = frozenset(),
    ) -> None:
        source_records = _load_faq(source_path, branch_scope)
        self._records = (
            tuple(
                record
                for record in source_records
                if normalize_faq_question(record.question) not in overridden_questions
            )
            + managed_records
        )

    def search_faq(self, query: str) -> tuple[FAQRecord, ...]:
        """Return ranked matches from this installation, or an empty tuple."""

        query_key = _query_key(query)
        matches: list[tuple[int, str, str, str, FAQRecord]] = []
        for record in self._records:
            question_key = normalize_faq_question(record.question)
            if query_key not in question_key:
                continue
            rank = (
                0 if question_key == query_key else 1 if question_key.startswith(query_key) else 2
            )
            matches.append((rank, question_key, record.category.value, record.answer, record))
        matches.sort(key=lambda item: item[:4])
        return tuple(item[4] for item in matches[:MAX_FAQ_RESULTS])


def _load_faq(source_path: Path, branch_scope: BranchScope) -> tuple[FAQRecord, ...]:
    if source_path.suffix.lower() != ".tsv":
        raise FAQSourceError()
    try:
        with source_path.open("rb") as source:
            data = source.read(MAX_FAQ_BYTES + 1)
    except OSError:
        raise FAQSourceError() from None

    if len(data) > MAX_FAQ_BYTES:
        raise FAQSourceError()
    try:
        content = data.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content, newline=""), delimiter="\t", strict=True)
        validate_faq_columns(reader.fieldnames)
        records = []
        for row_number, row in enumerate(reader, start=1):
            if row_number > MAX_FAQ_ROWS:
                raise FAQSourceError()
            records.append(validate_scoped_faq_row(row, branch_scope))
    except (UnicodeError, csv.Error, ValueError, ValidationError):
        raise FAQSourceError() from None
    return tuple(records)


def _query_key(value: str) -> str:
    if not isinstance(value, str) or len(value) > MAX_FAQ_QUERY_CHARS:
        raise FAQQueryInputError()
    normalized = unicodedata.normalize("NFKC", value).strip()
    if (
        not normalized
        or len(normalized) > MAX_FAQ_QUERY_CHARS
        or not normalized.isprintable()
        or not any(character.isalnum() for character in normalized)
    ):
        raise FAQQueryInputError()
    return normalize_faq_question(normalized)


def normalize_faq_question(value: str) -> str:
    """Use one canonical key for both retrieval and exact-answer decisions."""

    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return " ".join(without_marks.strip(" ¿?¡!.,;:").split())
