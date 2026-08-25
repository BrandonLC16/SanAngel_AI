from importlib import import_module


def test_application_package_is_importable() -> None:
    module = import_module("backend.app")

    assert module.__name__ == "backend.app"
