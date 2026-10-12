"""Secret scan failures never disclose scanner findings through application output."""

import subprocess
from pathlib import Path

import pytest

from scripts import scan_secrets


def test_secret_scan_passes_full_history_with_suppressed_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seen: dict[str, object] = {}

    def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.update(args=args, **kwargs)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(scan_secrets.subprocess, "run", run)

    assert scan_secrets.main(["--scanner", "gitleaks", "--repository", "repo"]) == 0
    assert seen["args"] == [
        "gitleaks",
        "git",
        "--redact=100",
        "--no-banner",
        "--no-color",
        "--log-level=error",
        "--log-opts=--all",
        "repo",
    ]
    assert seen["stdout"] is subprocess.DEVNULL
    assert seen["stderr"] is subprocess.DEVNULL
    assert seen["timeout"] == 300
    assert capsys.readouterr().out == "Secret scan passed.\n"


@pytest.mark.parametrize(
    "failure", [1, 126, FileNotFoundError(), subprocess.TimeoutExpired("gitleaks", 300)]
)
def test_secret_scan_fails_closed_without_disclosing_findings(
    failure: int | Exception,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    marker = "test-only-sensitive-finding-placeholder"

    def run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        if isinstance(failure, Exception):
            raise failure
        return subprocess.CompletedProcess(args, failure, stdout=marker, stderr=marker)

    monkeypatch.setattr(scan_secrets.subprocess, "run", run)

    assert scan_secrets.main(["--scanner", "gitleaks", "--repository", str(tmp_path)]) == 1
    captured = capsys.readouterr()
    assert marker not in captured.out + captured.err
    assert "Secret scan failed." in captured.err
