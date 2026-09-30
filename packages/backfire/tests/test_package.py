from importlib.metadata import version


def test_package_dependency_versions() -> None:
    assert version("jev-judge-mcp") == "0.6.0"
    assert version("system-one-adapter") == "0.2.1"
    assert version("typesafe-sdk") == "0.7.1"
