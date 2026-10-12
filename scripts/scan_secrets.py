"""Run the Git history secret scan without exposing findings in CI output."""

import argparse
import subprocess
import sys
from pathlib import Path


def scan_history(scanner: Path, repository: Path) -> bool:
    """Fail closed if Gitleaks reports a finding, times out, or cannot start."""
    try:
        result = subprocess.run(
            [
                str(scanner),
                "git",
                "--redact=100",
                "--no-banner",
                "--no-color",
                "--log-level=error",
                "--log-opts=--all",
                str(repository),
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan committed Git history for secrets.")
    parser.add_argument("--scanner", required=True, type=Path)
    parser.add_argument("--repository", default=Path("."), type=Path)
    args = parser.parse_args(argv)

    if scan_history(args.scanner, args.repository):
        print("Secret scan passed.")
        return 0
    print(
        "Secret scan failed. Review privately and rotate any exposed credential.", file=sys.stderr
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
