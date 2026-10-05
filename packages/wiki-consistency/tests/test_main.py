import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from conftest import SOURCE_ID
from conftest import make_instance
from conftest import tree_hash
from conftest import update_regions
import pytest
from test_prepare import KEY
from test_prepare import _page
from test_prepare import _ready
from test_prepare import _retain

from wiki_consistency import evidence
from wiki_consistency import search
from wiki_consistency.__main__ import _parser
from wiki_consistency.__main__ import main
from wiki_consistency.instance import revisions


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


@pytest.mark.parametrize("name", ("default", "chat", "code", "work"))
def test_check_cli_does_not_write_cache_files(tmp_path, name):
    instance, env = make_instance(tmp_path, wiki_id=name)
    update_regions(instance)

    before = tree_hash(instance)
    assert instance.parent.name == "llm-wiki"
    assert not (instance.parent.parent / "vaults").exists()
    result = _run_cli(instance, env, "check")
    assert result.returncode == 0, result.stderr
    assert tree_hash(instance) == before

    cache = Path(env["XDG_CACHE_HOME"])
    assert not [path for path in cache.rglob("*") if path.is_file()]


def test_convert_cli_retains_text_and_reports_missing_locator_evidence(
    tmp_path,
):
    instance, env = make_instance(tmp_path)

    result = _run_cli(instance, env, "convert")
    assert result.returncode == 1
    assert "missing locator evidence" in result.stderr
    assert list((instance / "text").rglob("*.qmd"))

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
    assert status == 1
    assert output.out == ""
    assert "missing locator evidence" in output.err
    assert list((instance / "text").rglob("*.qmd"))


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
        lambda unused_wiki_id, unused_environment: instance,
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


def test_prepare_cli_returns_failure_for_unresolved_sentences(
    tmp_path, monkeypatch, capsys
):

    instance, _, env = _ready(tmp_path)
    _page(instance, "Unsupported opening.\n")
    _setenv(monkeypatch, env)
    assert main(["prepare", "--wiki", instance.name, "--scope", "lint"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert any(
        item["reason"] == "missing sentence citation"
        for item in result["unverifiable"]
    )


def test_prepare_cli_accepts_only_explicit_actual_review_receipts(
    tmp_path, monkeypatch, capsys
):

    instance, _, env = _ready(tmp_path)
    _setenv(monkeypatch, env)
    retained = _retain(instance, **{"checked-against-original": True})
    args = ["prepare", "--wiki", instance.name, "--scope", "lint"]
    assert main(args) == 1
    assert "review evidence" in capsys.readouterr().out
    receipt = tmp_path / "review-receipts.json"
    record = revisions(instance)[SOURCE_ID][-1]
    receipt.write_text(
        json.dumps(
            {
                KEY: {
                    "sha256": evidence._raw_record(instance, record)[1],
                    "extraction-sha256": hashlib.sha256(
                        retained.read_bytes()
                    ).hexdigest(),
                    "evidence": "/private/SYNTHETIC-REVIEW-REFERENCE",
                }
            }
        )
    )
    assert main(args + ["--review-receipts", str(receipt)]) == 0
    output = capsys.readouterr()
    assert output.err == ""
    assert "SYNTHETIC-REVIEW-REFERENCE" not in output.out
    assert json.loads(output.out)["requests"]


def test_prepare_cli_rejects_invalid_receipt_mapping(
    tmp_path, monkeypatch, capsys
):
    instance, _, env = _ready(tmp_path)
    _setenv(monkeypatch, env)
    receipt = tmp_path / "review-receipts.json"
    receipt.write_text("[]")
    args = [
        "prepare",
        "--wiki",
        instance.name,
        "--scope",
        "lint",
        "--review-receipts",
        str(receipt),
    ]
    assert main(args) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "canonical-key mapping" in output.err


@pytest.mark.parametrize(
    "body",
    [
        "> Supported [@{key}, p. 25].\n",
        "::: {{.callout-note}}\nSupported [@{key}, p. 25].\n:::\n",
        "| Claim | Evidence |\n| --- | --- |\n| Result | [@{key}, p. 25] |\n",
        "An **unsupported mapping** [@{key}, p. 25].\n",
    ],
)
def test_prepare_cli_exposes_unsupported_shapes_as_unresolved_failure(
    tmp_path, monkeypatch, capsys, body
):
    instance, _, env = _ready(tmp_path)
    page = _page(instance, body.format(key=KEY))
    before = page.read_bytes()
    _setenv(monkeypatch, env)
    assert main(["prepare", "--wiki", instance.name, "--scope", "lint"]) == 1
    output = capsys.readouterr()
    assert output.err == ""
    result = json.loads(output.out)
    units = [
        unit
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/alpha.qmd"
    ]
    assert units and all(unit["outcome"] == "unverifiable" for unit in units)
    ids = {unit["id"] for unit in units}
    assert all(
        any(
            item["unit"] == unit_id and item["reason"]
            for item in result["unverifiable"]
        )
        for unit_id in ids
    )
    assert not any(
        ids.intersection(request["units"]) for request in result["requests"]
    )
    assert page.read_bytes() == before
