"""Create a verified SQLite snapshot without replacing an earlier backup."""

import argparse
import os
import sqlite3
import stat
import sys
from contextlib import closing
from pathlib import Path

from scripts.sqlite_validation import verify_sqlite_installation

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def backup_sqlite(
    source_path: Path, destination_path: Path, expected_branch_code: str | None = None
) -> None:
    """Back up an existing database without replacing an earlier backup."""

    source = source_path.resolve(strict=True)
    destination = destination_path.resolve()
    if not source.is_file() or source == destination:
        raise ValueError("invalid SQLite backup source or destination")
    parent = destination.parent.resolve(strict=True)
    if not parent.is_dir() or destination.is_relative_to(REPOSITORY_ROOT):
        raise ValueError("backup destination must be outside the repository")
    if os.name == "posix":
        parent_stat = parent.stat()
        if parent_stat.st_uid != os.geteuid() or stat.S_IMODE(parent_stat.st_mode) & 0o077:
            raise ValueError("backup destination directory must be owner-only")

    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(destination)) as backup:
                original.backup(backup)
                result = backup.execute("PRAGMA integrity_check").fetchone()
                if result != ("ok",):
                    raise ValueError("SQLite backup integrity check failed")
                if backup.execute("PRAGMA foreign_key_check").fetchone() is not None:
                    raise ValueError("SQLite backup foreign key check failed")
        if expected_branch_code is not None:
            verify_sqlite_installation(destination, expected_branch_code)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a verified SQLite backup")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--branch-code")
    args = parser.parse_args(argv)

    try:
        backup_sqlite(args.source, args.destination, args.branch_code)
    except Exception:
        print("No se pudo crear un respaldo SQLite verificado.", file=sys.stderr)
        return 1

    print("Respaldo SQLite verificado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
