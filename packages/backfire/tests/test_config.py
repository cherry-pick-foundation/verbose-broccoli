"""Profile selection and private credentials use synthetic files only."""

import tomllib

import pytest

from backfire import config
from backfire.failures import JudgmentError


@pytest.fixture
def operator(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    path = tmp_path / "config/verbose-broccoli/backfire/config.toml"
    path.parent.mkdir(parents=True)
    return path


def write_profile(path, *, provider="local"):
    path.write_text(
        f'''provider = "{provider}"
[providers.{provider}]
api = "openai"
base_url = "http://127.0.0.1:8080/v1"
model = "synthetic-model"
credential = "SYNTHETIC_API_KEY"
request = {{ max_tokens = 32 }}
''',
        encoding="utf-8",
    )


def test_shipped_selection_and_unselected_vercel_profile_are_present(operator):
    shipped = tomllib.loads(config.SHIPPED_CONFIG.read_text(encoding="utf-8"))
    selected = config.load_profile()
    assert selected["name"] == shipped["provider"]
    assert (
        selected["model"] == shipped["providers"][shipped["provider"]]["model"]
    )
    assert shipped["providers"]["vercel"]["credential"] == "AI_GATEWAY_API_KEY"
    assert shipped["providers"]["hive"]["credential_file"] == (
        "../providers/hive.env"
    )
    assert shipped["providers"]["vercel"]["credential_file"] == (
        "../providers/vercel.env"
    )
    education = tomllib.loads(
        config.EDUCATION_CONFIG.read_text(encoding="utf-8")
    )
    assert education["providers"]["education"]["credential_file"] == (
        "../providers/hive.env"
    )
    assert shipped["provider"] != "openrouter"
    assert shipped["providers"]["openrouter"] == {
        "api": "jev",
        "jev_provider": "openrouter",
        "credential": "OPENROUTER_API_KEY",
        "credential_file": "../providers/openrouter.env",
    }
    assert not operator.exists()


def test_operator_profile_is_read_and_can_use_relative_key_file(operator):
    write_profile(operator)
    selected = config.load_profile()
    credential = operator.parent / "local.env"
    credential.write_text(
        "SYNTHETIC_API_KEY=synthetic-value\n", encoding="utf-8"
    )
    credential.chmod(0o600)
    selected["credential_file"] = "local.env"
    assert selected["model"] == "synthetic-model"
    assert config.load_credential(selected) == "synthetic-value"


def test_shipped_key_file_in_the_shared_provider_folder_is_read(operator):
    operator.parent.rmdir()
    shared = operator.parent.parent / "providers/hive.env"
    shared.parent.mkdir()
    shared.write_text("HIVE_API_KEY=synthetic-value\n", encoding="utf-8")
    shared.chmod(0o600)
    selected = config.load_profile()
    assert selected["credential_file"] == "../providers/hive.env"
    assert config.load_credential(selected) == "synthetic-value"


def test_operator_retry_table_is_passed_through(operator):
    operator.write_text(
        """provider = "local"
[providers.local]
api = "openai"
base_url = "http://127.0.0.1:8080/v1"
model = "synthetic-model"
credential = "SYNTHETIC_API_KEY"
[providers.local.retry]
per_attempt_timeout = 1
budget = 2
""",
        encoding="utf-8",
    )

    assert config.load_profile()["retry"] == {
        "per_attempt_timeout": 1,
        "budget": 2,
    }


def test_education_profile_is_selected_without_loading_its_key(operator):
    selected = config.load_profile(education=True)
    assert selected["name"] == "education"
    assert selected["api"] == "openai"
    assert not operator.exists()


@pytest.mark.parametrize("mode", [0o644, 0o400])
def test_key_file_must_be_owned_and_private(operator, mode):
    write_profile(operator)
    selected = config.load_profile()
    path = operator.parent / "local.env"
    path.write_text("SYNTHETIC_API_KEY=synthetic-value\n", encoding="utf-8")
    path.chmod(mode)
    selected["credential_file"] = str(path)
    with pytest.raises(JudgmentError, match="^backend_not_configured:"):
        config.load_credential(selected)


def test_invalid_profile_fails_with_safe_configuration_error(operator):
    operator.write_text('provider = "missing"\n', encoding="utf-8")
    with pytest.raises(JudgmentError) as caught:
        config.load_profile()
    assert caught.value.error_type == "backend_not_configured"
    assert str(operator) in str(caught.value)


def test_bad_credential_file_fails_without_exposing_contents(operator):
    write_profile(operator)
    selected = config.load_profile()
    path = operator.parent / "local.env"
    path.write_text("OTHER_KEY=synthetic-secret-marker\n", encoding="utf-8")
    path.chmod(0o600)
    selected["credential_file"] = str(path)
    with pytest.raises(JudgmentError) as caught:
        config.load_credential(selected)
    assert "synthetic-secret-marker" not in str(caught.value)
