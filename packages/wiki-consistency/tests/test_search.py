import json
import os
import signal
import subprocess
from pathlib import Path

import pytest
import yaml

from wiki_consistency import evidence, search


MODEL = "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"


def _wiki(tmp_path):
    instance = tmp_path / "instance"
    wiki = instance / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "concepts").mkdir()
    (wiki / "concepts" / "quad.md").write_text(
        "# Quadratic formula\n\n"
        "The quadratic formula solves a quadratic equation.\n\n"
        "An ellipse has a major axis and a minor axis.\n"
    )
    cache = tmp_path / "cache"
    evidence = cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8" / "source"
    evidence.mkdir(parents=True)
    (evidence / "r1.md").write_text("Evidence discusses quadratic equations and ellipses.\n")
    return instance, cache


def _snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def _qmd_environment(cache):
    return {
        "XDG_CACHE_HOME": str(cache),
        "QMD_CONFIG_DIR": str(cache / "qmd" / "config"),
        "QMD_EMBED_MODEL": MODEL,
        "MESA_SHADER_CACHE_DIR": str(cache / "qmd" / "mesa_shader_cache"),
    }


def test_index_and_keyword_search_use_cache_only(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    before = _snapshot(instance)
    calls = []
    real_run = search.subprocess.run

    def record_run(command, *args, **kwargs):
        calls.append((tuple(map(str, command)), kwargs.get("env", {})))
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(search.subprocess, "run", record_run)

    result = search.index(instance, "wiki-a", cache, download=False)
    hits = search.search(
        "wiki-a",
        cache,
        [{"id": "q1", "text": "quadratic formula", "collection": "pages", "limit": 5}],
    )

    assert result["semantic"] is False
    assert result["pages"] == 1
    assert result["evidence"] == 1
    assert any(hit["path"] == "concepts/quad.md" and hit["mode"] == "lex" for hit in hits)
    assert all(hit["line"] >= 1 for hit in hits)
    assert _snapshot(instance) == before

    config = cache / "qmd" / "config" / "wiki-a.yml"
    collections = yaml.safe_load(config.read_text())["collections"]
    assert collections["pages"]["path"] == str((instance / "wiki").resolve())
    assert collections["evidence"]["path"] == str(
        (cache / "wiki-evidence" / "wiki-a" / "markitdown-0.1.8").resolve()
    )
    for command, env in calls:
        assert {key: env[key] for key in _qmd_environment(cache)} == _qmd_environment(cache)
        if Path(command[0]).name == "qmd":
            assert command[1:3] == ("--index", "wiki-a")
    assert any("update" in command for command, _ in calls)
    assert not any("embed" in command for command, _ in calls)


def test_search_refuses_a_missing_index(tmp_path):
    with pytest.raises(LookupError, match="index.*missing|missing.*index"):
        search.search("wiki-a", tmp_path / "cache", [])


@pytest.mark.parametrize("change", ["modified", "added", "deleted"])
def test_search_refuses_stale_document_paths_and_content_hashes(tmp_path, change):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    page = instance / "wiki" / "concepts" / "quad.md"
    if change == "modified":
        page.write_text(page.read_text() + "A changed synthetic line.\n")
    elif change == "added":
        (instance / "wiki" / "concepts" / "new.md").write_text("# New page\n")
    else:
        page.unlink()

    with pytest.raises(LookupError, match="wiki-consistency index"):
        search.search(
            "wiki-a",
            cache,
            [{"id": "q1", "text": "quadratic formula", "collection": "pages", "limit": 5}],
        )


def test_search_refuses_unembedded_documents_when_semantic_model_is_cached(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    model_dir = cache / "qmd" / "models"
    model_dir.mkdir(parents=True)
    model = model_dir / "synthetic-model.gguf"
    model.touch()
    monkeypatch.setattr(search, "EMBED_MODEL", str(model))

    with pytest.raises(LookupError, match="wiki-consistency index"):
        search.search(
            "wiki-a",
            cache,
            [{"id": "q1", "text": "quadratic formula", "collection": "pages", "limit": 5}],
        )


def test_model_cache_requires_exact_final_filename(tmp_path):
    model_dir = tmp_path / "qmd" / "models"
    model_dir.mkdir(parents=True)
    partial = model_dir / f"{MODEL.rsplit('/', 1)[-1]}.ipull"
    partial.touch()

    assert not search._model_is_cached(tmp_path)

    partial.rename(model_dir / MODEL.rsplit("/", 1)[-1])
    assert search._model_is_cached(tmp_path)


def test_qmd_budget_refuses_before_running_commands(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    qmd = cache / "qmd"
    qmd.mkdir(parents=True)
    (qmd / "large-cache-file").write_bytes(b"x" * 32)
    calls = []
    monkeypatch.setattr(search, "QMD_BUDGET_BYTES", 16)
    monkeypatch.setattr(search.subprocess, "run", lambda *args, **kwargs: calls.append(args))

    with pytest.raises(ValueError, match="qmd.*budget"):
        search.index(instance, "wiki-a", cache, download=False)

    assert calls == []


def test_deleted_index_is_rebuilt(tmp_path):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    index_path = cache / "qmd" / "wiki-a.sqlite"
    index_path.unlink()

    search.index(instance, "wiki-a", cache, download=False)

    assert index_path.is_file()
    assert search.search(
        "wiki-a",
        cache,
        [{"id": "q1", "text": "quadratic formula", "collection": "pages", "limit": 5}],
    )


@pytest.mark.parametrize("interrupt", [False, True])
def test_failed_or_interrupted_update_deletes_the_index(tmp_path, monkeypatch, interrupt):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    index_path = cache / "qmd" / "wiki-a.sqlite"
    run_qmd = search._run_qmd

    def fail_update(wiki_id, cache_root, args, *, budget_action):
        if list(args) == ["update"]:
            if interrupt:
                os.kill(os.getpid(), signal.SIGTERM)
            raise subprocess.CalledProcessError(1, "qmd update")
        return run_qmd(wiki_id, cache_root, args, budget_action=budget_action)

    monkeypatch.setattr(search, "_run_qmd", fail_update)
    expected = SystemExit if interrupt else subprocess.CalledProcessError
    with pytest.raises(expected):
        search.index(instance, "wiki-a", cache, download=False)

    assert not index_path.exists()


def test_batched_search_uses_one_node_process_and_matches_qmd_cli(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    queries = [
        {"id": "q1", "text": "quadratic formula", "collection": "pages", "limit": 5},
        {"id": "q2", "text": "ellipse major axis", "collection": "pages", "limit": 5},
    ]
    calls = []
    real_run = search.subprocess.run

    def record_run(command, *args, **kwargs):
        calls.append(tuple(map(str, command)))
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(search.subprocess, "run", record_run)
    hits = search.search("wiki-a", cache, queries)
    node_calls = [command for command in calls if Path(command[0]).name == "node"]

    assert len(node_calls) == 1
    qmd = search._qmd_path()
    env = os.environ.copy()
    env.update(_qmd_environment(cache))
    for query in queries:
        cli = real_run(
            [
                str(qmd),
                "--index",
                "wiki-a",
                "search",
                query["text"],
                "-c",
                query["collection"],
                "--format",
                "json",
                "-n",
                str(query["limit"]),
            ],
            env=env,
            capture_output=True,
            check=True,
            text=True,
        )
        cli_hits = json.loads(cli.stdout)
        api_paths = {
            hit["path"]
            for hit in hits
            if hit["query"] == query["id"] and hit["mode"] == "lex"
        }
        cli_paths = {
            str(hit["file"]).split("?", 1)[0].removeprefix("qmd://pages/")
            for hit in cli_hits
        }
        cli_lines = {hit["line"] for hit in cli_hits}
        api_lines = {
            hit["line"]
            for hit in hits
            if hit["query"] == query["id"] and hit["mode"] == "lex"
        }
        assert api_paths
        assert api_paths == cli_paths
        assert api_lines == cli_lines


def test_search_uses_converter_version_from_evidence(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    monkeypatch.setattr(evidence, "CONVERTER_VERSION", "synthetic-version")

    search.index(instance, "wiki-a", cache, download=False)

    config = yaml.safe_load((cache / "qmd" / "config" / "wiki-a.yml").read_text())
    assert config["collections"]["evidence"]["path"] == str(
        (cache / "wiki-evidence" / "wiki-a" / "markitdown-synthetic-version").resolve()
    )


def test_search_reuses_evidence_helpers():
    assert search._component is evidence._component
    assert search._tree_size is evidence._tree_size
    assert search._clean_on_signals is evidence._clean_on_signals
