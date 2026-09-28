import json
import os
import traceback

import pytest

from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire_education.roster import given_name, load_roster


@pytest.fixture
def roster(tmp_path):
    path = tmp_path / "roster.csv"
    config = xdg_path("config") / "backfire" / "education.toml"
    config.parent.mkdir(parents=True)
    config.write_text(f"roster = {json.dumps(str(path))}\n")
    return path


def test_bom_spaces_extra_columns_duplicates_and_precedence(roster):
    roster.write_text(
        "\ufeffname,school,guardians,grade\n"
        " 가라온 , 가상별학교 , 다루미 ; 마누리 ,3\n"
        "가라온,가상별학교,다루미,3\n"
        "나라온,가상별학교,가라온; 라온,2\n"
        "다새봄,다루미,새봄,1\n", encoding="utf-8",
    )
    values = load_roster()
    assert values == {
        "가라온": ("student", "가라온"), "나라온": ("student", "나라온"),
        "다새봄": ("student", "다새봄"), "라온": ("given", "라온"),
        "새봄": ("student", "다새봄"), "다루미": ("guardian", "다루미"),
        "마누리": ("guardian", "마누리"), "가상별학교": ("school", "가상별학교"),
    }
    roster.write_text("name\n가라온\n가라온\n", encoding="utf-8")
    assert load_roster() == {"가라온": ("student", "가라온"), "라온": ("student", "가라온")}
    assert len(list(roster.parent.glob("*.csv"))) == 1


@pytest.mark.parametrize("name, expected", [
    ("가라온", "라온"), ("가하늘빛", "하늘빛"),
    *((surname + "라온", "라온") for surname in ("남궁", "황보", "제갈", "선우", "서문", "독고", "사공")),
    ("남궁빛", "궁빛"), ("가온", None), ("가", None),
    ("Synthetic Name", None), ("가A온", None), ("가 라온", None),
])
def test_given_name_rule(name, expected):
    assert given_name(name) == expected


def test_full_name_wins_over_another_students_given_name(roster):
    roster.write_text("name\n가라온빛\n라온빛\n", encoding="utf-8")
    assert load_roster()["라온빛"] == ("student", "라온빛")


@pytest.mark.parametrize("content", [
    b"", b"school\nsynthetic\n", b"name,school\n,synthetic\n", b"name\n \n",
    b"name\n\xff\n", b'name\n"unclosed\n',
])
def test_bad_rosters_fail_with_only_the_path(roster, content):
    roster.write_bytes(content)
    with pytest.raises(JudgmentError) as caught:
        load_roster()
    assert caught.value.error_type == "backend_not_configured"
    assert caught.value.detail == str(roster)
    assert "synthetic" not in str(caught.value)


@pytest.mark.parametrize("content", [
    b"", b'roster = "relative.csv"', b"roster = 1", b"roster = [", b"\xff",
    b'roster = "/unused"\nextra = true',
])
def test_bad_configuration_names_only_education_file(roster, content):
    config = xdg_path("config") / "backfire" / "education.toml"
    config.write_bytes(content)
    with pytest.raises(JudgmentError) as caught:
        load_roster()
    assert caught.value.detail == str(config)


@pytest.mark.parametrize("target", ["config", "roster"])
@pytest.mark.parametrize("kind", ["missing", "directory", "fifo", "unreadable"])
def test_unusable_files_fail_without_blocking_or_diagnostics(roster, monkeypatch, target, kind):
    roster.write_text("name\n가라온\n", encoding="utf-8")
    path = roster if target == "roster" else xdg_path("config") / "backfire" / "education.toml"
    path.unlink()
    if kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "unreadable":
        original = os.open

        def deny(candidate, *args, **kwargs):
            if candidate == path:
                raise PermissionError("synthetic-private-diagnostic")
            return original(candidate, *args, **kwargs)

        monkeypatch.setattr(os, "open", deny)
    with pytest.raises(JudgmentError) as caught:
        load_roster()
    assert caught.value.detail == str(path)
    assert "synthetic-private-diagnostic" not in "".join(traceback.format_exception(caught.value))


def test_relative_config_root_fails(roster, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative")
    with pytest.raises(JudgmentError) as caught:
        load_roster()
    assert caught.value.detail == "XDG_CONFIG_HOME"
