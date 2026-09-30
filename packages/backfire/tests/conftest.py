"""Keep offline tests away from the operator's configuration and records."""

import json

import pytest

from backfire.config import xdg_path

ROSTER = """name,school,guardians,grade,id,romanized
가라온,가상별학교,다누리,3,7700101,Ga Raon
나하늘,byeolbit-h,,2,7700102,Na Haneul
다하늘,바람숲학교,다누리,1,7700103,Da Haneul
"""


@pytest.fixture(autouse=True)
def isolated_xdg(tmp_path, monkeypatch):
    """Point each test at isolated XDG directories."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


@pytest.fixture
def synthetic_roster(tmp_path):
    """Write a synthetic roster with every column and point backfire at it."""
    path = tmp_path / "roster.csv"
    path.write_text(ROSTER, encoding="utf-8")
    config = xdg_path("config") / "backfire" / "education.toml"
    config.parent.mkdir(parents=True)
    config.write_text(f"roster = {json.dumps(str(path))}\n", encoding="utf-8")
    return path
