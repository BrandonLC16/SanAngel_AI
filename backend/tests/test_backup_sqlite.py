"""Offline checks for the production SQLite backup command."""

import sqlite3
from contextlib import closing
from pathlib import Path

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
