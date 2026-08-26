import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SENSITIVE_ENV_NAMES = {
    "OPENAI_API_KEY",
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_VERIFY_TOKEN",
    "META_APP_SECRET",
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
    assert values["WHATSAPP_PHONE_NUMBER_ID"] == ""


def test_gitignore_protects_local_environment_without_hiding_example() -> None:
    ignore_rules = {
        line.strip()
        for line in (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".env" in ignore_rules
    assert ".env.*" in ignore_rules
    assert "!.env.example" in ignore_rules


def test_graph_api_version_default_is_centralized_in_application_config() -> None:
    version_pattern = re.compile(r"\bv[1-9][0-9]*\.0\b")
    files_with_versions = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "backend" / "app").rglob("*.py")
        if version_pattern.search(path.read_text(encoding="utf-8"))
    }

    assert files_with_versions == {"backend/app/core/config.py"}
