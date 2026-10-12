"""Restore a SQLite snapshot to a new file after scoped verification."""

import argparse
import sys
from pathlib import Path

from scripts.backup_sqlite import backup_sqlite
from scripts.sqlite_validation import verify_sqlite_installation


def restore_sqlite(backup_path: Path, destination_path: Path, expected_branch_code: str) -> None:
    """Copy a backup to a new path; remove only our new file if verification fails."""

    backup_sqlite(backup_path, destination_path)
    try:
        verify_sqlite_installation(destination_path, expected_branch_code)
    except Exception:
        destination_path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify and restore a SQLite backup")
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--branch-code", required=True)
    args = parser.parse_args(argv)

    try:
        restore_sqlite(args.backup, args.destination, args.branch_code)
    except Exception:
        print("No se pudo restaurar un respaldo SQLite verificado.", file=sys.stderr)
        return 1

    print("Restauración SQLite verificada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
