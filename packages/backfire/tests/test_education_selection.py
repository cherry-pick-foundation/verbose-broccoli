import pytest

from backfire import config
from backfire.config import xdg_path
from backfire_tools.build import build


@pytest.fixture
def shipped_profiles(tmp_path):
    code = build(tmp_path / "code", plugin="code")
    work = build(tmp_path / "work", plugin="work")
    return {
        "code": code / "backfire/src/backfire/config.toml",
        "work": work / "backfire/src/backfire/config.toml",
    }


@pytest.fixture
def operator_config(tmp_path, monkeypatch):
    for kind in ("config", "data"):
        monkeypatch.setenv(f"XDG_{kind.upper()}_HOME", str(tmp_path / kind))
    path = xdg_path("config") / "backfire" / "config.toml"
    path.parent.mkdir(parents=True)
    return path


def profile(name, model):
    return f'''[providers.{name}]
api = "openai"
base_url = "https://operator.example/v1"
model = "{model}"
credential = "TEST_KEY"
thinking = {{ requested = "off" }}
'''


def test_education_table_replacement_changes_only_work(
    shipped_profiles,
    operator_config,
    monkeypatch,
):
    operator_config.write_text(
        profile("education", "operator-education"), encoding="utf-8"
    )

    monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped_profiles["work"])
    work = config.load_profile()
    monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped_profiles["code"])
    code = config.load_profile()

    assert (work["name"], work["model"]) == ("education", "operator-education")
    assert code["name"] == "hive"
    assert code["model"] != "operator-education"


def test_hive_table_replacement_changes_only_code(
    shipped_profiles,
    operator_config,
    monkeypatch,
):
    operator_config.write_text(
        profile("hive", "operator-hive"), encoding="utf-8"
    )

    monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped_profiles["code"])
    code = config.load_profile()
    monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped_profiles["work"])
    work = config.load_profile()

    assert (code["name"], code["model"]) == ("hive", "operator-hive")
    assert work["name"] == "education"
    assert work["model"] != "operator-hive"


def test_operator_provider_selection_applies_to_both_builds(
    shipped_profiles,
    operator_config,
    monkeypatch,
):
    operator_config.write_text(
        'provider = "shared"\n' + profile("shared", "shared-model"),
        encoding="utf-8",
    )

    for shipped in shipped_profiles.values():
        monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped)
        selected = config.load_profile()
        assert (selected["name"], selected["model"]) == (
            "shared",
            "shared-model",
        )


def test_work_credential_uses_education_env_and_accepts_hive_link(
    shipped_profiles,
    operator_config,
    monkeypatch,
):
    monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped_profiles["work"])
    selected = config.load_profile()
    education_env = operator_config.parent / "education.env"
    hive_env = operator_config.parent / "hive.env"

    assert selected["name"] == "education"
    education_env.write_text(
        "HIVE_API_KEY=synthetic-education-key\n", encoding="utf-8"
    )
    education_env.chmod(0o600)
    assert config.load_credential(selected) == "synthetic-education-key"

    education_env.unlink()
    hive_env.write_text("HIVE_API_KEY=synthetic-linked-key\n", encoding="utf-8")
    hive_env.chmod(0o600)
    education_env.symlink_to(hive_env)
    assert config.load_credential(selected) == "synthetic-linked-key"
