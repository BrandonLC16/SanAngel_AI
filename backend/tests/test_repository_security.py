from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


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


def test_environment_example_keeps_openai_secret_empty() -> None:
    values = parse_environment_example()

    assert "OPENAI_API_KEY" in values
    assert values["OPENAI_API_KEY"] == ""


def test_gitignore_protects_local_environment_without_hiding_example() -> None:
    ignore_rules = {
        line.strip()
        for line in (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert ".env" in ignore_rules
    assert ".env.*" in ignore_rules
    assert "!.env.example" in ignore_rules
