import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from conftest import make_instance, update_regions
from test_prepare import _ready
from wiki_consistency import search
from wiki_consistency.__main__ import _parser, main


def _setenv(monkeypatch, env):
    for name, value in env.items():
        monkeypatch.setenv(name, value)


def _run_cli(instance, env, command):
    child_env = os.environ.copy()
    child_env.update(env)
    child_env.pop("ORT_DISABLE_TELEMETRY", None)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "wiki_consistency",
            "--wiki",
            instance.name,
            command,
        ],
        env=child_env,
        capture_output=True,
        check=False,
        text=True,
    )


@pytest.mark.parametrize(
    "args",
    [
        ["check"],
        ["update"],
        ["convert"],
        ["index"],
        ["prepare", "--scope", "changed"],
    ],
)
def test_each_subcommand_defaults_to_work(args):
    assert _parser().parse_args(args).wiki_id == "work"


def test_check_cli_does_not_write_cache_files(tmp_path):
    instance, env = make_instance(tmp_path)
    update_regions(instance)

    result = _run_cli(instance, env, "check")
    assert result.returncode == 0, result.stderr

    cache = Path(env["XDG_CACHE_HOME"])
    assert not [path for path in cache.rglob("*") if path.is_file()]


def test_convert_cli_writes_only_wiki_evidence_to_cache(tmp_path):
    instance, env = make_instance(tmp_path)

    result = _run_cli(instance, env, "convert")
    assert result.returncode == 0, result.stderr

    cache = Path(env["XDG_CACHE_HOME"])
    allowed = cache / "verbose-broccoli" / "wiki-evidence"
    outside = [
        path
        for path in cache.rglob("*")
        if path.is_file() and not path.is_relative_to(allowed)
    ]
    assert not outside


@pytest.mark.parametrize(
    "args",
    [
        ["convert", "--scope", "invalid"],
        ["prepare"],
        ["prepare", "--scope", "changed", "--max-evidence-chars", "0"],
        ["prepare", "--scope", "lint", "--candidates", "0"],
        ["index", "--scope", "lint"],
    ],
)
def test_new_subcommand_argument_errors_return_two(
    tmp_path, monkeypatch, capsys, args
):
    _, env = make_instance(tmp_path)
    _setenv(monkeypatch, env)

    with pytest.raises(SystemExit) as error:
        main(args)

    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err


def test_convert_command_runs_offline_and_prints_result(
    tmp_path, monkeypatch, capsys
):
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


def test_index_command_allows_download_and_prints_result(
    tmp_path, monkeypatch, capsys
):
    instance, env = make_instance(tmp_path)
    _setenv(monkeypatch, env)
    calls = []

    def index(path, wiki_id, cache, *, download):
        calls.append((path, wiki_id, cache, download))
        return {
            "pages": 3,
            "evidence": 1,
            "semantic": False,
            "semantic_error": None,
        }

    monkeypatch.setattr("wiki_consistency.__main__.search.index", index)

    status = main(["index", "--wiki", instance.name])

    output = capsys.readouterr()
    assert status == 0
    assert output.err == ""
    assert json.loads(output.out) == {
        "pages": 3,
        "evidence": 1,
        "semantic": False,
        "semantic_error": None,
    }
    assert calls == [
        (
            instance,
            instance.name,
            Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli",
            True,
        )
    ]


def test_index_command_keeps_keyword_index_when_embedding_fails(
    tmp_path, monkeypatch, capsys
):
    instance, env = make_instance(tmp_path)
    _setenv(monkeypatch, env)
    monkeypatch.setattr(
        "wiki_consistency.__main__.instance_path",
        lambda wiki_id, environment: instance,
    )
    run_qmd = search._run_qmd

    def fail_embed(wiki_id, cache, args, *, budget_action):
        if list(args) == ["embed"]:
            raise subprocess.CalledProcessError(
                1,
                "qmd embed",
                stderr="synthetic embedding failed\nwith details",
            )
        return run_qmd(wiki_id, cache, args, budget_action=budget_action)

    monkeypatch.setattr(search, "_run_qmd", fail_embed)

    status = main(["index", "--wiki", instance.name])

    output = capsys.readouterr()
    result = json.loads(output.out)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    assert status == 0
    assert output.err == ""
    assert result["semantic"] is False
    assert result["semantic_error"] == "synthetic embedding failed with details"
    assert (cache / "qmd" / f"{instance.name}.sqlite").is_file()
    assert search.search(
        instance.name,
        cache,
        [
            {
                "id": "keyword",
                "text": "Alpha",
                "collection": "pages",
                "limit": 5,
            }
        ],
    )


def test_prepare_command_runs_after_offline_convert_and_index(
    tmp_path, monkeypatch, capsys
):
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
