"""Education mode uses shared provider profiles and accepts overrides."""

from jev_judge_mcp.settings import Settings
import pytest

from backfire import config
from backfire.providers import provider_factory


@pytest.fixture
def operator_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    path = tmp_path / "config/verbose-broccoli/backfire/config.toml"
    path.parent.mkdir(parents=True)
    return path


def test_education_mode_uses_the_shared_profile_order(operator_config):
    provider = provider_factory(education=True)(Settings.model_construct())
    assert provider._education is True
    assert [profile["name"] for profile in provider._profiles] == [
        "openrouter",
        "hive",
    ]
    assert provider._profiles == config.load_profiles()
    assert not operator_config.exists()


def test_operator_selection_applies_to_shared_profiles(operator_config):
    operator_config.write_text(
        """order = ["synthetic"]
[providers.synthetic]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "synthetic-model"
credential = "SYNTHETIC_KEY"
""",
        encoding="utf-8",
    )
    selected = config.load_profiles()
    assert [(profile["name"], profile["model"]) for profile in selected] == [
        ("synthetic", "synthetic-model")
    ]


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
    selected = config.load_profiles()
    hive = next(profile for profile in selected if profile["name"] == "hive")
    assert hive["model"] == "synthetic-model"
