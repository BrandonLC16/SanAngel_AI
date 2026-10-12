"""Offline negative checks for protected, branch-scoped SQLite recovery."""

import sqlite3
from contextlib import closing
from pathlib import Path

from scripts.backup_sqlite import main as backup_main
from scripts.restore_sqlite import main
from scripts.sqlite_validation import current_revision


def _backup_fixture(
    path: Path, *, branch: str = "sucursal-prueba", revision: str | None = None
) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE branches (code TEXT NOT NULL)")
        connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
        connection.execute("CREATE TABLE orders (reference TEXT NOT NULL)")
        connection.execute("INSERT INTO branches (code) VALUES (?)", (branch,))
        connection.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (revision or current_revision(),),
        )
        connection.execute("INSERT INTO orders (reference) VALUES ('offline-test')")
        connection.commit()


def test_restore_command_verifies_branch_revision_and_payload(tmp_path: Path, capsys) -> None:
    backup = tmp_path / "backup.db"
    destination = tmp_path / "restored.db"
    _backup_fixture(backup)

    assert (
        main(
            [
                "--backup",
                str(backup),
                "--destination",
                str(destination),
                "--branch-code",
                "sucursal-prueba",
            ]
        )
        == 0
    )
    with closing(sqlite3.connect(destination)) as connection:
        assert connection.execute("SELECT reference FROM orders").fetchall() == [("offline-test",)]
    assert capsys.readouterr().out.strip() == "Restauración SQLite verificada."


def test_scoped_backup_rejects_wrong_branch_and_keeps_source(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"
    _backup_fixture(source)

    assert (
        backup_main(
            [
                "--source",
                str(source),
                "--destination",
                str(destination),
                "--branch-code",
                "other-branch",
            ]
        )
        == 1
    )
    assert source.exists()
    assert not destination.exists()
    assert str(source) not in capsys.readouterr().err


def test_restore_rejects_wrong_branch_without_exposing_details(tmp_path: Path, capsys) -> None:
    backup = tmp_path / "backup.db"
    destination = tmp_path / "restored.db"
    _backup_fixture(backup)

    assert (
        main(
            [
                "--backup",
                str(backup),
                "--destination",
                str(destination),
                "--branch-code",
                "other-branch",
            ]
        )
        == 1
    )
    assert backup.exists()
    assert not destination.exists()
    error = capsys.readouterr().err
    assert "No se pudo restaurar" in error
    assert "sucursal-prueba" not in error
    assert str(backup) not in error


def test_restore_rejects_wrong_revision_and_removes_new_file(tmp_path: Path) -> None:
    backup = tmp_path / "backup.db"
    destination = tmp_path / "restored.db"
    _backup_fixture(backup, revision="older-revision")

    assert (
        main(
            [
                "--backup",
                str(backup),
                "--destination",
                str(destination),
                "--branch-code",
                "sucursal-prueba",
            ]
        )
        == 1
    )
    assert backup.exists()
    assert not destination.exists()


def test_restore_never_overwrites_existing_destination(tmp_path: Path) -> None:
    backup = tmp_path / "backup.db"
    destination = tmp_path / "restored.db"
    _backup_fixture(backup)
    destination.write_text("keep-existing", encoding="utf-8")

    assert (
        main(
            [
                "--backup",
                str(backup),
                "--destination",
                str(destination),
                "--branch-code",
                "sucursal-prueba",
            ]
        )
        == 1
    )
    assert destination.read_text(encoding="utf-8") == "keep-existing"


def test_restore_rejects_corrupt_backup(tmp_path: Path) -> None:
    backup = tmp_path / "backup.db"
    destination = tmp_path / "restored.db"
    backup.write_bytes(b"not a sqlite database")

    assert (
        main(
            [
                "--backup",
                str(backup),
                "--destination",
                str(destination),
                "--branch-code",
                "sucursal-prueba",
            ]
        )
        == 1
    )
    assert not destination.exists()
