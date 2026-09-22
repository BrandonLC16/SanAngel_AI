"""Create a verified SQLite backup before a production migration."""

import argparse
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path


def backup_sqlite(source_path: Path, destination_path: Path) -> None:
    """Back up an existing database without replacing an earlier backup."""

    source = source_path.resolve(strict=True)
    destination = destination_path.resolve()
    if not source.is_file() or source == destination:
        raise ValueError("invalid SQLite backup source or destination")

    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    try:
        with closing(sqlite3.connect(f"{source.as_uri()}?mode=ro", uri=True)) as original:
            with closing(sqlite3.connect(destination)) as backup:
                original.backup(backup)
                result = backup.execute("PRAGMA integrity_check").fetchone()
                if result != ("ok",):
                    raise ValueError("SQLite backup integrity check failed")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a verified SQLite backup")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        backup_sqlite(args.source, args.destination)
    except (OSError, ValueError, sqlite3.Error):
        print("No se pudo crear un respaldo SQLite verificado.", file=sys.stderr)
        return 1

    print("Respaldo SQLite verificado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
