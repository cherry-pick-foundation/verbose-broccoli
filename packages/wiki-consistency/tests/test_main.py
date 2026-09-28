import json
from pathlib import Path

import pytest

from conftest import make_instance
from test_prepare import _ready
from wiki_consistency.__main__ import main


def _setenv(monkeypatch, env):
    for name, value in env.items():
        monkeypatch.setenv(name, value)


@pytest.mark.parametrize("args", [
    ["convert", "--scope", "invalid"],
    ["prepare"],
    ["prepare", "--scope", "changed", "--max-evidence-chars", "0"],
    ["prepare", "--scope", "lint", "--candidates", "0"],
    ["index", "--scope", "lint"],
])
def test_new_subcommand_argument_errors_return_two(tmp_path, monkeypatch, capsys, args):
    _, env = make_instance(tmp_path)
    _setenv(monkeypatch, env)

    with pytest.raises(SystemExit) as error:
        main(args)

    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err


def test_convert_command_runs_offline_and_prints_result(tmp_path, monkeypatch, capsys):
    instance, env = make_instance(tmp_path)
    _setenv(monkeypatch, env)

    status = main(["convert", "--wiki", instance.name, "--scope", "lint"])

    output = capsys.readouterr()
    result = json.loads(output.out)
    assert status == 0
    assert output.err == ""
    assert result["converted"] == 1
    assert result["present"] == 0
    assert result["unreadable"] == []


def test_index_command_allows_download_and_prints_result(tmp_path, monkeypatch, capsys):
    instance, env = make_instance(tmp_path)
    _setenv(monkeypatch, env)
    calls = []

    def index(path, wiki_id, cache, *, download):
        calls.append((path, wiki_id, cache, download))
        return {"pages": 3, "evidence": 1, "semantic": False}

    monkeypatch.setattr("wiki_consistency.__main__.search.index", index)

    status = main(["index", "--wiki", instance.name])

    output = capsys.readouterr()
    assert status == 0
    assert output.err == ""
    assert json.loads(output.out) == {"pages": 3, "evidence": 1, "semantic": False}
    assert calls == [(instance, instance.name, Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli", True)]


def test_prepare_command_runs_after_offline_convert_and_index(tmp_path, monkeypatch, capsys):
    instance, _, env = _ready(tmp_path)
    _setenv(monkeypatch, env)

    status = main(["prepare", "--wiki", instance.name, "--scope", "lint"])

    output = capsys.readouterr()
    result = json.loads(output.out)
    assert status == 0
    assert output.err == ""
    assert result["wiki"] == instance.name
    assert result["scope"] == "lint"
    assert result["requests"]
