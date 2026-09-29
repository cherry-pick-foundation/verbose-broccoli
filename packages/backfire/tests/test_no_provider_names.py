from pathlib import Path
import re
import tomllib

import pytest


def provider_names(root):
    return [
        str(path.relative_to(root))
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.relative_to(root)
        not in {
            Path("backfire/config.toml"),
            Path("backfire_education/config.toml"),
        }
        and re.search(rb"(?<!arc)hive", path.read_bytes(), re.IGNORECASE)
    ]


def test_source_has_no_provider_names():
    assert provider_names(Path(__file__).resolve().parents[1] / "src") == []


@pytest.mark.parametrize("name", ["hive", "HIVE_API_KEY", "prefixHiveSuffix"])
def test_guard_catches_names_in_any_file(tmp_path, name):
    path = tmp_path / "backfire_tools" / "sample.bin"
    path.parent.mkdir()
    path.write_bytes(b"\xff" + name.encode())
    assert provider_names(tmp_path) == ["backfire_tools/sample.bin"]


def test_guard_allows_archive_and_only_the_two_shipped_configs(tmp_path):
    runtime = tmp_path / "backfire"
    runtime.mkdir()
    (runtime / "config.toml").write_text("hive HIVE", encoding="utf-8")
    (runtime / "code.py").write_text(
        "archive ARCHIVE archived archives", encoding="utf-8"
    )
    education = tmp_path / "backfire_education"
    education.mkdir()
    (education / "config.toml").write_text("hive HIVE", encoding="utf-8")
    (education / "other.toml").write_text("hive", encoding="utf-8")
    (tmp_path / "config.toml").write_text("hive", encoding="utf-8")
    assert provider_names(tmp_path) == [
        "backfire_education/other.toml",
        "config.toml",
    ]


def test_education_profile_keeps_development_protection_settings():
    root = Path(__file__).resolve().parents[1] / "src"
    development = tomllib.loads((root / "backfire/config.toml").read_text())
    education = tomllib.loads(
        (root / "backfire_education/config.toml").read_text()
    )
    assert education == {
        "pseudonymize": True,
        "provider": "education",
        "providers": {
            "education": development["providers"][development["provider"]],
        },
    }
