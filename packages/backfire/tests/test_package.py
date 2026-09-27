from importlib.metadata import version


def test_package_dependency_versions() -> None:
    assert version("mcp") == "2.2.0"
    assert version("rfc8785") == "0.1.4"
    assert version("system-one-adapter") == "0.2.1"
    assert version("typesafe-sdk") == "0.7.1"
