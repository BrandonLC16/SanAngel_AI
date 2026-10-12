"""Validate a branch-specific SQLite snapshot against this application image."""

import sqlite3
from contextlib import closing
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

from backend.app.core.config import validate_branch_code

ROOT = Path(__file__).resolve().parents[1]


def current_revision() -> str:
    heads = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini"))).get_heads()
    if len(heads) != 1:
        raise ValueError("expected exactly one database revision head")
    return heads[0]


def verify_sqlite_installation(path: Path, expected_branch_code: str) -> None:
    """Reject damaged, cross-branch, or incompatible restored data."""

    validate_branch_code(expected_branch_code)
    expected_revision = current_revision()
    with closing(sqlite3.connect(f"{path.resolve(strict=True).as_uri()}?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("SQLite integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ValueError("SQLite foreign key check failed")
        if db.execute("SELECT code FROM branches").fetchall() != [(expected_branch_code,)]:
            raise ValueError("SQLite branch mismatch")
        if db.execute("SELECT version_num FROM alembic_version").fetchall() != [
            (expected_revision,)
        ]:
            raise ValueError("SQLite revision mismatch")
