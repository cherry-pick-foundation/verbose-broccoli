from importlib.metadata import version


def test_endpoint_dependency_versions() -> None:
    assert version("system-one-adapter") == "0.2.1"
    assert version("typesafe-sdk") == "0.7.1"
