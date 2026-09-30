"""Education mode selects its own profile and accepts operator overrides."""

import pytest

from backfire import config


@pytest.fixture
def operator_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config/verbose-broccoli/backfire/config.toml"
    path.parent.mkdir(parents=True)
    return path


def test_education_mode_uses_the_work_profile(operator_config):
    code = config.load_profile()
    work = config.load_profile(education=True)
    assert code["name"] == "hive"
    assert work["name"] == "education"
    assert work["model"] == code["model"]
    assert work["credential"] == code["credential"]
    assert not operator_config.exists()


def test_operator_selection_applies_to_both_profiles(operator_config):
    operator_config.write_text(
        """provider = "synthetic"
[providers.synthetic]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "synthetic-model"
credential = "SYNTHETIC_KEY"
""",
        encoding="utf-8",
    )
    for education in (False, True):
        selected = config.load_profile(education=education)
        assert (selected["name"], selected["model"]) == (
            "synthetic",
            "synthetic-model",
        )


def test_operator_may_replace_only_the_selected_profile(operator_config):
    operator_config.write_text(
        """[providers.hive]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "synthetic-model"
credential = "SYNTHETIC_KEY"
""",
        encoding="utf-8",
    )
    selected = config.load_profile()
    work = config.load_profile(education=True)
    assert selected["model"] == "synthetic-model"
    assert work["name"] == "education"
    assert work["model"] != "synthetic-model"
