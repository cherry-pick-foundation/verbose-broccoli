"""The names below are invented synthetic fixtures, never private records."""

import json
import os

import pytest

from education_privacy_gate import roster
from education_privacy_gate.roster import GateError
from education_privacy_gate.roster import Registry
from education_privacy_gate.roster import load_registry
from education_privacy_gate.roster import registry_config_dir


def fixture_data():
    return {
        "version": 1,
        "entries": [
            {"kind": "person", "full": "가라온", "romanized": ["Ga Raon"]},
            {"kind": "person", "full": "남궁누리", "aliases": ["별누리"]},
            {
                "kind": "school",
                "spellings": [
                    "가상별빛고등학교",
                    "가상별빛고",
                    "synthetic-school",
                ],
            },
        ],
    }


def write_registry(tmp_path, text=None):
    directory = tmp_path / "registry"
    directory.mkdir(mode=0o700)
    file = directory / "registered-list.json"
    file.write_text(text or json.dumps(fixture_data()), encoding="utf-8")
    file.chmod(0o600)
    return directory, file


def test_config_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    for value in ("", "relative"):
        monkeypatch.setenv("XDG_CONFIG_HOME", value)
        assert registry_config_dir() == (
            tmp_path / ".config/verbose-broccoli/education-privacy-gate"
        )
    monkeypatch.delenv("XDG_CONFIG_HOME")
    assert registry_config_dir().is_absolute()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert registry_config_dir() == (
        tmp_path / "config/verbose-broccoli/education-privacy-gate"
    )


def test_snapshot(tmp_path):
    directory, file = write_registry(tmp_path)
    registry = load_registry(directory)
    file.write_text("broken")
    assert registry.spellings
    assert "라온" in registry.spellings
    assert "누리" in registry.spellings
    assert "궁누리" not in registry.spellings


@pytest.mark.parametrize(
    "text",
    [
        '{"version":1,"version":1,"entries":[]}',
        '{"version":true,"entries":[]}',
        '{"version":2,"entries":[]}',
        '{"version":1,"entries":[],"contact":"synthetic"}',
        '{"version":1,"entries":[{"kind":"teacher","full":"가라온"}]}',
        '{"version":1,"entries":[{"kind":"person","full":""}]}',
        '{"version":1,"entries":[{"kind":"person","full":"가라온","id":1}]}',
        '{"version":1,"entries":[{"kind":"school","spellings":[]}]}',
        '{"version":1,"entries":[{"kind":"person","full":"가라온",'
        '"aliases":null}]}',
        '{"version":1,"entries":[{"kind":"person","full":"가라온",'
        '"given":"온라"}]}',
        '{"version":1,"entries":NaN}',
    ],
)
def test_strict_json(tmp_path, text):
    directory, file = write_registry(tmp_path, text)
    before = file.read_bytes()
    with pytest.raises(GateError, match="^Privacy gate rejected the call\\.$"):
        load_registry(directory)
    assert file.read_bytes() == before


@pytest.mark.parametrize("target,mode", [("file", 0o644), ("dir", 0o755)])
def test_modes(tmp_path, target, mode):
    directory, file = write_registry(tmp_path)
    (file if target == "file" else directory).chmod(mode)
    with pytest.raises(GateError):
        load_registry(directory)


def test_symlinks_and_nonregular(tmp_path):
    directory, file = write_registry(tmp_path)
    linked = tmp_path / "linked"
    linked.symlink_to(directory, target_is_directory=True)
    with pytest.raises(GateError):
        load_registry(linked)
    file.unlink()
    target = tmp_path / "target"
    target.write_text("{}")
    file.symlink_to(target)
    with pytest.raises(GateError):
        load_registry(directory)
    file.unlink()
    os.mkfifo(file, 0o600)
    with pytest.raises(GateError):
        load_registry(directory)


def test_owner(tmp_path, monkeypatch):
    directory, unused_file = write_registry(tmp_path)
    monkeypatch.setattr(os, "getuid", lambda: os.stat(directory).st_uid + 1)
    with pytest.raises(GateError):
        load_registry(directory)


def test_conflicting_full_alias():
    data = fixture_data()
    data["entries"][1]["aliases"] = ["가라온"]
    with pytest.raises(GateError):
        Registry.from_data(data)


def test_shared_given():
    data = fixture_data()
    data["entries"].append({"kind": "person", "full": "나라온"})
    registry = Registry.from_data(data)
    matches = [m for m in registry.matches if m.pattern.fullmatch("라온")]
    assert len({m.identity for m in matches}) == 1
    assert matches[0].identity[0] == "given"


def test_spelling_bounds():
    def data(size, count=1):
        return {
            "version": 1,
            "entries": [
                {
                    "kind": "school",
                    "spellings": [
                        "x" * size + str(i).zfill(4) for i in range(count)
                    ],
                }
            ],
        }

    Registry.from_data(data(252))
    with pytest.raises(GateError):
        Registry.from_data(data(253))
    Registry.from_data(data(1, 4096))
    with pytest.raises(GateError):
        Registry.from_data(data(1, 4097))
    for count in (4091, 4092):
        expanded = {
            "version": 1,
            "entries": [
                {"kind": "person", "full": "가라온", "romanized": ["Ga Raon"]},
                {
                    "kind": "school",
                    "spellings": [f"x{i:04d}" for i in range(count)],
                },
            ],
        }
        assert len(Registry.from_data(expanded).matches) >= count + 5


@pytest.mark.parametrize("count", [4096, 4097])
def test_registered_count_includes_repeated_explicit_spellings(count):
    data = {
        "version": 1,
        "entries": [
            {"kind": "school", "spellings": ["synthetic-school"] * count}
        ],
    }
    if count == 4096:
        Registry.from_data(data)
    else:
        with pytest.raises(GateError):
            Registry.from_data(data)


def test_820_people_with_romanized_spellings():
    entries = []
    for index in range(820):
        suffix = "".join(
            chr(65 + index // divisor % 26) for divisor in (676, 26, 1)
        )
        entries.append(
            {
                "kind": "person",
                "full": "가" + chr(0xAC00 + index) + "온",
                "romanized": ["Synthetic " + suffix],
            }
        )
    registry = Registry.from_data({"version": 1, "entries": entries})
    assert len(registry.matches) > 4096


def test_derived_pattern_ceiling(monkeypatch):
    monkeypatch.setattr(roster, "MAX_DERIVED_PATTERNS", 4, raising=False)
    with pytest.raises(GateError):
        Registry.from_data(fixture_data())


def test_registered_bound_refusal_keeps_old_bytes(tmp_path):
    directory, file = write_registry(tmp_path)
    before = file.read_bytes()
    data = {
        "version": 1,
        "entries": [
            {"kind": "school", "spellings": ["synthetic-school"] * 4097}
        ],
    }
    with pytest.raises(GateError):
        Registry.from_data(data)
    assert file.read_bytes() == before
    assert load_registry(directory).spellings


def test_byte_bound(tmp_path):
    text = '{"version":1,"entries":[]}'
    directory, file = write_registry(
        tmp_path, text + " " * (1048576 - len(text))
    )
    load_registry(directory)
    with file.open("a") as handle:
        handle.write(" ")
    with pytest.raises(GateError):
        load_registry(directory)


def test_no_private_fields():
    for key in ("scores", "contacts", "student_number", "source_path"):
        data = fixture_data()
        data["entries"][0][key] = "fictional"
        with pytest.raises(GateError):
            Registry.from_data(data)


@pytest.mark.parametrize("given", [None, 1, False, "", []])
def test_explicit_given_is_a_spelling(given):
    data = fixture_data()
    data["entries"][0]["given"] = given
    with pytest.raises(GateError):
        Registry.from_data(data)


def test_flexible_full_alias_conflict():
    data = fixture_data()
    data["entries"][1]["romanized"] = ["Raon Ga"]
    with pytest.raises(GateError):
        Registry.from_data(data)


def test_missing_registry_and_nested_duplicate(tmp_path):
    with pytest.raises(GateError):
        load_registry(tmp_path / "missing")
    directory, unused_file = write_registry(
        tmp_path,
        '{"version":1,"entries":[{"kind":"person","full":"가라온",'
        '"full":"가라온"}]}',
    )
    with pytest.raises(GateError):
        load_registry(directory)
