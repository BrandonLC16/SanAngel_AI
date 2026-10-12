"""Offline checks for the production SQLite backup command."""

import os
import sqlite3
import stat
from contextlib import closing
from pathlib import Path

import pytest

from scripts import backup_sqlite
from scripts.backup_sqlite import main


def test_backup_command_captures_committed_wal_data_and_passes_integrity_check(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"

    with closing(sqlite3.connect(source)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE example (value TEXT NOT NULL)")
        connection.execute("INSERT INTO example (value) VALUES (?)", ("dato",))
        connection.commit()

        assert main(["--source", str(source), "--destination", str(destination)]) == 0

    with closing(sqlite3.connect(destination)) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert connection.execute("SELECT value FROM example").fetchall() == [("dato",)]
    if os.name == "posix":
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600


def test_backup_refuses_to_replace_an_existing_file(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"
    sqlite3.connect(source).close()
    destination.write_text("existing backup", encoding="utf-8")

    assert main(["--source", str(source), "--destination", str(destination)]) == 1
    assert destination.read_text(encoding="utf-8") == "existing backup"
    assert "Respaldo SQLite verificado" not in capsys.readouterr().out


def test_backup_rejects_missing_source_without_creating_destination(tmp_path: Path, capsys) -> None:
    source = tmp_path / "missing.db"
    destination = tmp_path / "backup.db"

    assert main(["--source", str(source), "--destination", str(destination)]) == 1
    assert not source.exists()
    assert not destination.exists()
    captured = capsys.readouterr()
    assert str(source) not in captured.err
    assert str(destination) not in captured.err


def test_backup_rejects_foreign_key_violation(tmp_path: Path, capsys) -> None:
    source = tmp_path / "source.db"
    destination = tmp_path / "backup.db"
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE child (parent_id INTEGER REFERENCES parent(id))")
        connection.execute("INSERT INTO child (parent_id) VALUES (1)")
        connection.commit()

    assert main(["--source", str(source), "--destination", str(destination)]) == 1
    assert not destination.exists()
    assert str(source) not in capsys.readouterr().err


@pytest.mark.skipif(os.name != "posix", reason="Windows ACLs are configured by the operator")
def test_backup_requires_owner_only_destination_directory(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    public_directory = tmp_path / "public"
    public_directory.mkdir(mode=0o755)
    public_directory.chmod(0o755)
    sqlite3.connect(source).close()

    assert main(["--source", str(source), "--destination", str(public_directory / "copy.db")]) == 1
    assert not (public_directory / "copy.db").exists()


def test_backup_rejects_destination_inside_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.db"
    sqlite3.connect(source).close()
    monkeypatch.setattr(backup_sqlite, "REPOSITORY_ROOT", tmp_path)

    assert main(["--source", str(source), "--destination", str(tmp_path / "copy.db")]) == 1
    assert not (tmp_path / "copy.db").exists()
