import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SENSITIVE_ENV_NAMES = {
    "OPENAI_API_KEY",
    "GREEN_API_TOKEN_INSTANCE",
    "GREEN_API_WEBHOOK_TOKEN",
}


def parse_environment_example() -> dict[str, str]:
    values: dict[str, str] = {}
    example_path = REPOSITORY_ROOT / ".env.example"

    for raw_line in example_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")

    return values


def test_environment_example_keeps_all_secrets_empty() -> None:
    values = parse_environment_example()

    assert SENSITIVE_ENV_NAMES <= values.keys()
    assert all(values[name] == "" for name in SENSITIVE_ENV_NAMES)
    assert values["GREEN_API_INSTANCE_ID"] == ""
    assert values["GREEN_API_API_URL"] == "https://api.green-api.com"


def test_gitignore_protects_local_environment_without_hiding_example() -> None:
    ignore_rules = {
        line.strip()
        for line in (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".env" in ignore_rules
    assert ".env.*" in ignore_rules
    assert "!.env.example" in ignore_rules


def test_green_api_host_default_is_centralized_in_application_config() -> None:
    host_pattern = re.compile(r"https://api\.green-api\.com")
    files_with_hosts = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "backend" / "app").rglob("*.py")
        if host_pattern.search(path.read_text(encoding="utf-8"))
    }

    assert files_with_hosts == {"backend/app/core/config.py"}
