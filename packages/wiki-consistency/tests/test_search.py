from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
from types import SimpleNamespace

import pytest
import yaml

from wiki_consistency import evidence
from wiki_consistency import search

MODEL = "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"


def _wiki(tmp_path):
    instance = tmp_path / "instance"
    wiki = instance / "wiki"
    wiki.mkdir(parents=True)
    (wiki / "concepts").mkdir()
    (wiki / "concepts" / "quad.qmd").write_text(
        "# Quadratic formula\n\n"
        "The quadratic formula solves a quadratic equation.\n\n"
        "An ellipse has a major axis and a minor axis.\n"
    )
    cache = tmp_path / "cache"
    evidence_root = instance / "text" / "source"
    evidence_root.mkdir(parents=True)
    (evidence_root / "r1.qmd").write_text(
        "Evidence discusses quadratic equations and ellipses.\n"
    )
    return instance, cache


def _snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        if path.is_file()
        else None
        for path in root.rglob("*")
    }


def _qmd_environment(cache):
    return {
        "XDG_CACHE_HOME": str(cache),
        "QMD_CONFIG_DIR": str(cache / "qmd" / "config"),
        "QMD_EMBED_MODEL": MODEL,
        "QMD_FORCE_CPU": "1",
        "MESA_SHADER_CACHE_DIR": str(cache / "qmd" / "mesa_shader_cache"),
    }


def test_index_and_keyword_search_use_cache_only(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    before = _snapshot(instance)
    calls = []
    mcp_calls = []
    servers = []
    real_run = search.subprocess.run
    real_stdio = search.stdio_client
    real_session = search.ClientSession

    def record_run(command, *args, **kwargs):
        calls.append(
            (
                tuple(map(str, command)),
                kwargs.get("env", {}),
                kwargs.get("umask"),
            )
        )
        return real_run(command, *args, **kwargs)

    @asynccontextmanager
    async def record_stdio(server):
        servers.append(server)
        async with real_stdio(server) as streams:
            yield streams

    class RecordingSession(real_session):
        async def call_tool(self, name, arguments):
            mcp_calls.append((name, arguments))
            return await super().call_tool(name, arguments)

    for name in (
        "HF_TOKEN",
        "HF_TOKEN_PATH",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "HF_ENDPOINT",
        "MODEL_ENDPOINT",
    ):
        monkeypatch.setenv(name, "synthetic-secret")
    monkeypatch.setattr(search.subprocess, "run", record_run)
    monkeypatch.setattr(search, "stdio_client", record_stdio)
    monkeypatch.setattr(search, "ClientSession", RecordingSession)

    result = search.index(instance, "wiki-a", cache, download=False)
    hits = search.search(
        "wiki-a",
        cache,
        [
            {
                "id": "q1",
                "text": "quadratic formula",
                "collection": "pages",
                "limit": 5,
            }
        ],
    )

    assert result["semantic"] is False
    assert result["pages"] == 1
    assert result["evidence"] == 1
    assert any(
        hit["path"] == "concepts/quad.qmd" and hit["mode"] == "lex"
        for hit in hits
    )
    assert all(hit["line"] >= 1 for hit in hits)
    assert _snapshot(instance) == before

    config = cache / "qmd" / "config" / "wiki-a.yml"
    collections = yaml.safe_load(config.read_text())["collections"]
    assert collections["pages"]["path"] == str((instance / "wiki").resolve())
    assert collections["evidence"]["path"] == str((instance / "text").resolve())
    for command, env, umask in calls:
        assert {
            key: env[key] for key in _qmd_environment(cache)
        } == _qmd_environment(cache)
        assert umask == 0o077
        assert all(name not in env for name in search.MODEL_TOKENS)
        if Path(command[0]).name == "qmd":
            assert command[1:3] == ("--index", "wiki-a")
    verbs = {command[3] for command, _, _ in calls}
    assert {"collection", "update"} <= verbs
    assert not verbs & {"embed", "pull", "search", "query", "vsearch"}
    assert len(servers) == 2
    assert "--index" in servers[-1].args[1]
    assert servers[-1].args[-1] == "wiki-a"
    assert "umask 077" in servers[-1].args[1]
    assert {
        key: servers[-1].env[key] for key in _qmd_environment(cache)
    } == _qmd_environment(cache)
    assert all(name not in servers[-1].env for name in search.MODEL_TOKENS)
    typed_searches = [
        search_args["searches"]
        for name, search_args in mcp_calls
        if name == "query"
    ]
    assert typed_searches == [[{"type": "lex", "query": "quadratic formula"}]]
    assert (cache / "qmd").stat().st_mode & 0o777 == 0o700
    assert (cache / "qmd" / "config").stat().st_mode & 0o777 == 0o700


@pytest.mark.parametrize("download", [False, True])
def test_index_embeds_only_after_download_is_requested(
    tmp_path, monkeypatch, download
):
    instance, cache = _wiki(tmp_path)
    calls = []
    run_qmd = search._run_qmd

    def record_qmd(wiki_id, cache_root, args, *, budget_action):
        calls.append(tuple(args))
        if list(args) == ["embed"]:
            return subprocess.CompletedProcess(
                ["qmd", "embed"], 0, stdout="", stderr=""
            )
        return run_qmd(wiki_id, cache_root, args, budget_action=budget_action)

    monkeypatch.setattr(search, "_run_qmd", record_qmd)

    search.index(instance, "wiki-a", cache, download=download)

    assert (("embed",) in calls) is download
    assert all(args[0] != "pull" for args in calls)


def test_search_refuses_a_missing_index(tmp_path):
    with pytest.raises(LookupError, match="index.*missing|missing.*index"):
        search.search("wiki-a", tmp_path / "cache", [])


@pytest.mark.parametrize(
    ("content", "expected_pages"),
    [("\ufeff", 1), ("\x1c", 2)],
    ids=["byte-order-mark", "unit-separator"],
)
def test_index_and_search_match_qmd_trim_rules(
    tmp_path, content, expected_pages
):
    instance, cache = _wiki(tmp_path)
    (instance / "wiki" / "concepts" / "trim.qmd").write_text(
        content, encoding="utf-8"
    )

    result = search.index(instance, "wiki-a", cache, download=False)

    search.search("wiki-a", cache, [])
    assert result["pages"] == expected_pages


def test_index_and_search_skip_symlinked_pages(tmp_path):
    instance, cache = _wiki(tmp_path)
    target = tmp_path / "outside.qmd"
    target.write_text("Synthetic outside page.\n", encoding="utf-8")
    (instance / "wiki" / "concepts" / "linked.qmd").symlink_to(target)

    result = search.index(instance, "wiki-a", cache, download=False)

    search.search("wiki-a", cache, [])
    assert result["pages"] == 1


@pytest.mark.parametrize(
    ("change", "text", "expected_paths"),
    [
        ("modified", "fresh changed phrase", {"concepts/quad.qmd"}),
        ("added", "fresh added phrase", {"concepts/new.qmd"}),
        ("deleted", "quadratic formula", set()),
        ("empty", "quadratic formula", set()),
    ],
)
def test_search_refreshes_stale_index_with_qmd_update(
    tmp_path, change, text, expected_paths
):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    page = instance / "wiki" / "concepts" / "quad.qmd"
    if change == "modified":
        page.write_text("# Changed page\n\nFresh changed phrase.\n")
    elif change == "added":
        (instance / "wiki" / "concepts" / "new.qmd").write_text(
            "# New page\n\nFresh added phrase.\n"
        )
    elif change == "deleted":
        page.unlink()
    else:
        page.write_text(" \t\n", encoding="utf-8")

    hits = search.search(
        "wiki-a",
        cache,
        [
            {
                "id": "q1",
                "text": text,
                "collection": "pages",
                "limit": 5,
            }
        ],
    )

    assert {
        hit["path"] for hit in hits if hit["collection"] == "pages"
    } == expected_paths


def test_evidence_allowed_paths_return_hits_beyond_limit(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    evidence_root = instance / "text" / "source"
    for index in range(5):
        (evidence_root / f"a-{index}.qmd").write_text(
            "# Synthetic evidence\n\n" + "rarephrase " * 50,
            encoding="utf-8",
        )
    target_path = "source/z-late.qmd"
    (evidence_root / "z-late.qmd").write_text(
        "# Synthetic evidence\n\nrarephrase\n", encoding="utf-8"
    )
    search.index(instance, "wiki-a", cache, download=False)
    assert search._collection_chunk_count("wiki-a", cache, "evidence") > 1

    calls = []
    real_stdio = search.stdio_client

    @asynccontextmanager
    async def record_stdio(server):
        calls.append(server)
        async with real_stdio(server) as streams:
            yield streams

    monkeypatch.setattr(search, "stdio_client", record_stdio)
    hits = search.search(
        "wiki-a",
        cache,
        [
            {
                "id": "evidence-query",
                "text": "rarephrase",
                "collection": "evidence",
                "limit": 1,
                "allowed_paths": [target_path],
            }
        ],
    )

    assert any(hit["path"] == target_path for hit in hits)
    assert len(calls) == 1
    assert "mcp" in calls[0].args[1]
    assert "--index" in calls[0].args[1]


def test_collection_chunk_count_uses_qmd_document_count(tmp_path):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)

    assert search._collection_chunk_count("wiki-a", cache, "evidence") == 1


def test_semantic_ready_uses_mcp_embedding_status(tmp_path, monkeypatch):
    monkeypatch.setattr(search, "_model_is_cached", lambda unused_cache: True)
    monkeypatch.setattr(
        search,
        "_run_mcp_search",
        lambda unused_wiki_id, unused_cache, unused_queries: (
            {"needsEmbedding": 0},
            [],
        ),
    )

    assert search.semantic_ready("wiki-a", tmp_path / "cache")


def test_collection_chunk_count_propagates_qmd_errors(tmp_path, monkeypatch):
    qmd_root = tmp_path / "cache" / "qmd"
    qmd_root.mkdir(parents=True)
    (qmd_root / "wiki-a.sqlite").touch()

    def fail_qmd(unused_wiki_id, unused_cache, unused_queries):
        raise subprocess.CalledProcessError(1, ["qmd", "ls"])

    monkeypatch.setattr(search, "_run_mcp_search", fail_qmd)

    with pytest.raises(subprocess.CalledProcessError):
        search._collection_chunk_count("wiki-a", tmp_path / "cache", "evidence")


def test_qmd_cli_uses_pinned_version():
    package = (
        Path(search.__file__).parents[2]
        / "node_modules"
        / "@tobilu"
        / "qmd"
        / "package.json"
    )

    assert json.loads(package.read_text(encoding="utf-8"))["version"] == "2.8.3"


def test_search_uses_keyword_when_cached_model_needs_embeddings(
    tmp_path, monkeypatch
):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    model_dir = cache / "qmd" / "models"
    model_dir.mkdir(parents=True)
    model = model_dir / "synthetic-model.gguf"
    model.touch()
    monkeypatch.setattr(search, "EMBED_MODEL", str(model))

    hits = search.search(
        "wiki-a",
        cache,
        [
            {
                "id": "q1",
                "text": "quadratic formula",
                "collection": "pages",
                "limit": 5,
            }
        ],
    )

    assert any(
        hit["path"] == "concepts/quad.qmd" and hit["mode"] == "lex"
        for hit in hits
    )
    assert not any(hit["mode"] == "vec" for hit in hits)


def test_index_uses_index_health_after_failed_embedding(tmp_path, monkeypatch):
    instance = tmp_path / "instance"
    (instance / "wiki").mkdir(parents=True)
    cache = tmp_path / "cache"
    model_dir = cache / "qmd" / "models"
    model_dir.mkdir(parents=True)
    model_name = "synthetic-model.gguf"
    (model_dir / model_name).touch()
    monkeypatch.setattr(search, "EMBED_MODEL", f"hf:synthetic/{model_name}")
    run_qmd = search._run_qmd

    def fail_embedding(wiki_id, cache_root, args, *, budget_action):
        if list(args) == ["embed"]:
            raise subprocess.CalledProcessError(
                1, "qmd embed", stderr="synthetic embedding failure"
            )
        return run_qmd(wiki_id, cache_root, args, budget_action=budget_action)

    monkeypatch.setattr(search, "_run_qmd", fail_embedding)

    result = search.index(instance, "wiki-a", cache, download=False)

    assert result["semantic"] is True
    assert result["semantic_error"] == "synthetic embedding failure"


def test_index_reports_successful_embedding_with_pending_chunks(
    tmp_path, monkeypatch
):
    instance, cache = _wiki(tmp_path)
    model_name = "synthetic-model.gguf"
    model_dir = cache / "qmd" / "models"
    model_dir.mkdir(parents=True)
    (model_dir / model_name).touch()
    monkeypatch.setattr(search, "EMBED_MODEL", f"hf:synthetic/{model_name}")
    run_qmd = search._run_qmd

    def embed_with_warning(wiki_id, cache_root, args, *, budget_action):
        if list(args) == ["embed"]:
            return subprocess.CompletedProcess(
                ["qmd", "embed"],
                0,
                stdout="⚠ 1 chunks still failed after retries\n",
                stderr="",
            )
        return run_qmd(wiki_id, cache_root, args, budget_action=budget_action)

    monkeypatch.setattr(search, "_run_qmd", embed_with_warning)
    monkeypatch.setattr(
        search,
        "semantic_ready",
        lambda unused_wiki_id, unused_cache_root: False,
    )

    result = search.index(instance, "wiki-a", cache, download=False)

    assert result["semantic"] is False
    assert (
        isinstance(result["semantic_error"], str) and result["semantic_error"]
    )
    assert "\n" not in result["semantic_error"]


def test_index_and_search_match_qmd_document_scan_rules(tmp_path):
    instance, cache = _wiki(tmp_path)
    wiki = instance / "wiki"
    ignored = [
        "concepts/build/x.qmd",
        "node_modules/x.qmd",
        ".cache/x.qmd",
        "vendor/x.qmd",
        "dist/x.qmd",
        ".hidden.qmd",
        "concepts/.hidden/x.qmd",
    ]
    for relative in ignored:
        path = wiki / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Synthetic ignored page\n", encoding="utf-8")
    blank = wiki / "concepts" / "blank.qmd"
    blank.write_text(" \n\t\n", encoding="utf-8")

    result = search.index(instance, "wiki-a", cache, download=False)
    assert result["pages"] == 1

    hits = search.search(
        "wiki-a",
        cache,
        [
            {
                "id": "q1",
                "text": "quadratic formula",
                "collection": "pages",
                "limit": 5,
            }
        ],
    )

    assert any(hit["path"] == "concepts/quad.qmd" for hit in hits)


def test_search_refuses_stale_retained_text_root(tmp_path):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    config = cache / "qmd" / "config" / "wiki-a.yml"
    value = yaml.safe_load(config.read_text())
    value["collections"]["evidence"]["path"] = str(tmp_path / "old-text")
    config.write_text(yaml.safe_dump(value))
    with pytest.raises(LookupError, match="index"):
        search.search("wiki-a", cache, [])


@pytest.mark.parametrize("collection", ["pages", "evidence"])
def test_search_refuses_stale_masks_before_update(tmp_path, collection):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    config = cache / "qmd" / "config" / "wiki-a.yml"
    value = yaml.safe_load(config.read_text())
    value["collections"][collection]["pattern"] = "**/*.md"
    config.write_text(yaml.safe_dump(value))
    with pytest.raises(LookupError, match="mask.*reindex"):
        search.search("wiki-a", cache, [])


def test_index_replaces_same_path_md_mask_and_removes_stale_docs(tmp_path):
    instance, cache = _wiki(tmp_path)
    old = instance / "wiki" / "concepts" / "old.md"
    old.write_text("Obsolete sentinelnoun.\n")
    search._collection(
        "wiki-a",
        cache,
        "add",
        str(instance / "wiki"),
        "--name",
        "pages",
        "--mask",
        "**/*.md",
    )
    result = search.index(instance, "wiki-a", cache, download=False)
    config = cache / "qmd" / "config" / "wiki-a.yml"
    value = yaml.safe_load(config.read_text())["collections"]
    assert all(item["pattern"] == "**/*.qmd" for item in value.values())
    assert result["pages"] == result["evidence"] == 1
    hits = search.search(
        "wiki-a",
        cache,
        [
            {"id": "old", "text": "sentinelnoun", "collection": "pages"},
            {"id": "new", "text": "quadratic", "collection": "pages"},
            {"id": "text", "text": "ellipses", "collection": "evidence"},
        ],
    )
    assert not any(hit["query"] == "old" for hit in hits)
    assert {hit["path"] for hit in hits if hit["query"] == "new"} == {
        "concepts/quad.qmd"
    }
    assert {hit["path"] for hit in hits if hit["query"] == "text"} == {
        "source/r1.qmd"
    }


def test_model_cache_accepts_qmd_filename_and_rejects_partial_or_directory(
    tmp_path,
):
    model_dir = tmp_path / "qmd" / "models"
    model_dir.mkdir(parents=True)

    model = model_dir / f"hf_Qwen_{MODEL.rsplit('/', 1)[-1]}"
    model.touch()

    assert search._model_is_cached(tmp_path)

    model.unlink()
    partial = model_dir / f"{model.name}.ipull"
    partial.touch()

    assert not search._model_is_cached(tmp_path)

    partial.unlink()
    model.mkdir()
    assert not search._model_is_cached(tmp_path)


def test_qmd_paths_refuse_symlinks(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (cache / "qmd").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="symlinks"):
        search._paths("wiki-a", cache)


def test_qmd_budget_refuses_before_running_commands(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    qmd = cache / "qmd"
    qmd.mkdir(parents=True)
    (qmd / "large-cache-file").write_bytes(b"x" * 32)
    calls = []
    monkeypatch.setattr(search, "QMD_BUDGET_BYTES", 16)
    monkeypatch.setattr(
        search.subprocess,
        "run",
        lambda *args, **unused_kwargs: calls.append(args),
    )

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
        [
            {
                "id": "q1",
                "text": "quadratic formula",
                "collection": "pages",
                "limit": 5,
            }
        ],
    )


@pytest.mark.parametrize("interrupt", [False, True])
def test_failed_or_interrupted_update_deletes_the_index(
    tmp_path, monkeypatch, interrupt
):
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


def test_batched_lexical_search_matches_qmd_cli(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    queries = [
        {
            "id": "q1",
            "text": "quadratic formula",
            "collection": "pages",
            "limit": 5,
        },
        {
            "id": "q2",
            "text": "ellipse major axis",
            "collection": "pages",
            "limit": 5,
        },
    ]
    servers = []
    real_run = search.subprocess.run
    real_stdio = search.stdio_client

    @asynccontextmanager
    async def record_stdio(server):
        servers.append(server)
        async with real_stdio(server) as streams:
            yield streams

    monkeypatch.setattr(search, "stdio_client", record_stdio)
    hits = search.search("wiki-a", cache, queries)
    assert len(servers) == 1
    assert "--index" in servers[0].args[1]
    assert servers[0].args[-1] == "wiki-a"
    qmd = search._qmd_path()
    env = search._environment(cache)
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
            umask=0o077,
        )
        cli_hits = json.loads(cli.stdout)
        api_results = {
            (hit["path"], hit["line"])
            for hit in hits
            if hit["query"] == query["id"] and hit["mode"] == "lex"
        }
        cli_results = {
            (
                str(hit["file"]).split("?", 1)[0].removeprefix("qmd://pages/"),
                hit["line"],
            )
            for hit in cli_hits
        }
        assert api_results
        assert api_results == cli_results
    assert all(0 <= hit["score"] <= 1 for hit in hits)


def test_batched_vector_search_uses_one_mcp_process(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    search.index(instance, "wiki-a", cache, download=False)
    monkeypatch.setattr(search, "_model_is_cached", lambda unused_cache: True)
    calls = []
    servers = []

    class FakeSession:
        def __init__(self, read, write):
            del read, write

        async def __aenter__(self):
            return self

        async def __aexit__(self, *unused_args):
            return None

        async def initialize(self):
            return None

        async def call_tool(self, name, arguments):
            calls.append((name, arguments))
            if name == "status":
                return SimpleNamespace(
                    is_error=False,
                    structured_content={
                        "needsEmbedding": 0,
                        "collections": [
                            {
                                "name": "pages",
                                "path": str(instance / "wiki"),
                            },
                            {
                                "name": "evidence",
                                "path": str(instance / "text"),
                            },
                        ],
                    },
                )
            collection = arguments["collections"][0]
            path = (
                "concepts/quad.qmd"
                if collection == "pages"
                else "source/r1.qmd"
            )
            return SimpleNamespace(
                is_error=False,
                structured_content={
                    "results": [
                        {
                            "file": f"qmd://{collection}/{path}?index=wiki-a",
                            "line": 2,
                            "score": 0.76,
                        }
                    ]
                },
            )

    @asynccontextmanager
    async def fake_stdio_client(server):
        servers.append(server)
        yield object(), object()

    monkeypatch.setattr(search, "ClientSession", FakeSession)
    monkeypatch.setattr(search, "stdio_client", fake_stdio_client)

    hits = search.search(
        "wiki-a",
        cache,
        [
            {
                "id": "page-query",
                "text": "a semantic page query",
                "collection": "pages",
                "limit": 4,
            },
            {
                "id": "evidence-query",
                "text": "a semantic evidence query",
                "collection": "evidence",
                "limit": 1,
                "allowed_paths": ["source/r1.qmd"],
            },
        ],
    )

    assert len(servers) == 1
    assert "--index" in servers[0].args[1]
    assert servers[0].args[-1] == "wiki-a"
    assert servers[0].env["QMD_FORCE_CPU"] == "1"
    assert calls[0] == ("status", {})
    query_calls = [arguments for name, arguments in calls if name == "query"]
    assert [arguments["searches"] for arguments in query_calls] == [
        [{"type": "lex", "query": "a semantic page query"}],
        [{"type": "vec", "query": "a semantic page query"}],
        [{"type": "lex", "query": "a semantic evidence query"}],
        [{"type": "vec", "query": "a semantic evidence query"}],
    ]
    assert [arguments["limit"] for arguments in query_calls] == [
        4,
        4,
        100000,
        100000,
    ]
    assert all(arguments["rerank"] is False for arguments in query_calls)
    assert {
        (hit["query"], hit["mode"]) for hit in hits if hit["mode"] == "vec"
    } == {
        ("page-query", "vec"),
        ("evidence-query", "vec"),
    }


def test_search_uses_converter_version_from_evidence(tmp_path, monkeypatch):
    instance, cache = _wiki(tmp_path)
    monkeypatch.setattr(evidence, "CONVERTER_VERSION", "synthetic-version")

    search.index(instance, "wiki-a", cache, download=False)

    config = yaml.safe_load(
        (cache / "qmd" / "config" / "wiki-a.yml").read_text()
    )
    assert config["collections"]["evidence"]["path"] == str(
        (instance / "text").resolve()
    )


def test_search_reuses_evidence_helpers():
    assert search._component is evidence._component
    assert search._tree_size is evidence._tree_size
    assert search._clean_on_signals is evidence._clean_on_signals
