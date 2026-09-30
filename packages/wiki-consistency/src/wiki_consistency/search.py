"""qmd indexing and batched local search for Wiki Markdown."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import subprocess

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp.client.stdio import stdio_client
import yaml

from wiki_consistency import evidence
from wiki_consistency.evidence import _clean_on_signals
from wiki_consistency.evidence import _component
from wiki_consistency.evidence import _tree_size

QMD_BUDGET_BYTES = 3 * 1024**3
EMBED_MODEL = "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"
MODEL_TOKENS = set(
    "HF_TOKEN HF_TOKEN_PATH GITHUB_TOKEN "
    "GH_TOKEN HF_ENDPOINT MODEL_ENDPOINT".split()
)


def _paths(wiki_id: str, cache: Path) -> tuple[Path, Path, Path]:
    wiki_id = _component(wiki_id)
    root = Path(cache).resolve() / "qmd"
    index, config = (
        root / f"{wiki_id}.sqlite",
        root / "config" / f"{wiki_id}.yml",
    )
    if any(path.is_symlink() for path in (root, index, config.parent, config)):
        raise ValueError("qmd cache paths cannot be symlinks")
    return root, index, config


def _qmd_path() -> Path:
    return Path(__file__).resolve().parents[2] / "node_modules" / ".bin" / "qmd"


def _environment(cache: Path) -> dict[str, str]:
    root = Path(cache).resolve()
    qmd = root / "qmd"
    env = os.environ.copy()
    for name in MODEL_TOKENS:
        env.pop(name, None)
    env.update(
        XDG_CACHE_HOME=str(root),
        QMD_CONFIG_DIR=str(qmd / "config"),
        QMD_EMBED_MODEL=EMBED_MODEL,
        QMD_FORCE_CPU="1",
        MESA_SHADER_CACHE_DIR=str(qmd / "mesa_shader_cache"),
    )
    return env


def _secure_qmd(root: Path, action: str) -> None:
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    if _tree_size(root) >= QMD_BUDGET_BYTES:
        raise ValueError(f"qmd cache budget exceeded before {action}")


def _run_qmd(wiki_id, cache, args, *, budget_action):
    qmd_root, _, _ = _paths(wiki_id, cache)
    _secure_qmd(qmd_root, budget_action)
    return subprocess.run(
        [str(_qmd_path()), "--index", _component(wiki_id), *args],
        env=_environment(cache),
        check=True,
        capture_output=True,
        text=True,
        umask=0o077,
    )


def _collection(wiki_id, cache, *args):
    _run_qmd(
        wiki_id,
        cache,
        ["collection", *args],
        budget_action="collection",
    )


def _collections(path):
    config = (
        yaml.safe_load(path.read_text(encoding="utf-8"))
        if path.is_file()
        else {}
    )
    return (config or {}).get("collections", {})


def _ensure_collections(wiki_id, cache, expected):
    _, _, config_path = _paths(wiki_id, cache)
    configured = _collections(config_path)
    for name, path in expected.items():
        path = path.resolve()
        current = configured.get(name)
        if current and Path(current["path"]).resolve() == path:
            continue
        if current:
            _collection(wiki_id, cache, "remove", name)
        _collection(wiki_id, cache, "add", str(path), "--name", name)


def _model_is_cached(cache: Path) -> bool:
    return any(
        path.is_file()
        for path in Path(cache).glob(
            f"qmd/models/*{EMBED_MODEL.rsplit('/', 1)[-1]}"
        )
    )


def _markdown_count(root: Path) -> int:
    return sum(path.is_file() for path in root.rglob("*.md"))


def _remove_index(index: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{index}{suffix}").unlink(missing_ok=True)


def _update_index(wiki_id: str, cache: Path, index: Path) -> None:
    try:
        with _clean_on_signals():
            _run_qmd(wiki_id, cache, ["update"], budget_action="update")
    except BaseException:
        _remove_index(index)
        raise


async def _call(session, name, args):
    result = await session.call_tool(name, args)
    if result.is_error:
        raise LookupError(result.content[0].text)
    return result.structured_content


async def _mcp_search(parameters, queries, model_cached):
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            status = await _call(session, "status", {})
            vector_ready = model_cached and status["needsEmbedding"] == 0
            hits = []
            for query in queries:
                text = " ".join(str(query["text"]).split())
                limit = (
                    100000
                    if query.get("allowed_paths")
                    else query.get("limit", 20)
                )
                for mode in ("lex", "vec") if vector_ready else ("lex",):
                    args = {
                        "searches": [{"type": mode, "query": text}],
                        "collections": [query["collection"]],
                        "limit": limit,
                        "rerank": False,
                    }
                    result = await _call(session, "query", args)
                    hits.append((query, mode, result["results"]))
            return status, hits


def _run_mcp_search(wiki_id, cache, queries):
    qmd_root, index, _ = _paths(wiki_id, cache)
    if not index.is_file():
        raise LookupError(f"missing qmd index for {wiki_id}; run index")
    _secure_qmd(qmd_root, "MCP search")
    parameters = StdioServerParameters(
        command="/bin/sh",
        args=[
            "-c",
            'umask 077; exec "$1" --index "$2" mcp',
            "qmd",
            str(_qmd_path()),
            _component(wiki_id),
        ],
        env=_environment(cache),
    )
    with _clean_on_signals():
        return asyncio.run(
            _mcp_search(parameters, queries, _model_is_cached(cache))
        )


def _counts(status):
    return {item["name"]: item["documents"] for item in status["collections"]}


def index(instance, wiki_id, cache, *, download):
    """Build the pinned qmd index and report status."""
    wiki_id = _component(wiki_id)
    instance, cache = Path(instance), Path(cache).resolve()
    wiki_root = instance / "wiki"
    evidence_root = cache / "wiki-evidence" / wiki_id
    evidence_root /= f"markitdown-{evidence.CONVERTER_VERSION}"
    evidence_root.mkdir(parents=True, exist_ok=True)
    _, index_path, _ = _paths(wiki_id, cache)
    _ensure_collections(
        wiki_id,
        cache,
        {"pages": wiki_root.resolve(), "evidence": evidence_root.resolve()},
    )
    _update_index(wiki_id, cache, index_path)

    cached = _model_is_cached(cache)
    attempted = cached or download
    error = None
    if attempted:
        try:
            with _clean_on_signals():
                _run_qmd(wiki_id, cache, ["embed"], budget_action="embed")
        except subprocess.CalledProcessError as exc:
            error = " ".join((exc.stderr or exc.stdout or str(exc)).split())
    status, _ = _run_mcp_search(wiki_id, cache, [])
    semantic = _model_is_cached(cache) and status["needsEmbedding"] == 0
    if attempted and not semantic and error is None:
        error = "qmd embed completed but semantic search is still not ready"
    counts = _counts(status)
    return {
        "pages": counts.get("pages", 0),
        "evidence": counts.get("evidence", 0),
        "semantic": semantic,
        "semantic_error": error,
    }


def _collection_chunk_count(wiki_id: str, cache: Path, collection: str) -> int:
    # qmd returns document counts; request builders keep this function name.
    status, _ = _run_mcp_search(wiki_id, cache, [])
    return _counts(status).get(collection, 0)


def semantic_ready(wiki_id: str, cache: Path) -> bool:
    """Return whether qmd reports all documents embedded."""
    return (
        _model_is_cached(cache)
        and _run_mcp_search(wiki_id, cache, [])[0]["needsEmbedding"] == 0
    )


def _hits(results, query, mode, root):
    collection = query["collection"]
    hits = []
    for result in results:
        path = str(result["file"]).split("?", 1)[0]
        path = path.removeprefix(f"qmd://{collection}/").removeprefix(
            f"{collection}/"
        )
        allowed_paths = query.get("allowed_paths")
        if allowed_paths is not None and path not in allowed_paths:
            continue
        document = (root / path).resolve()
        if not document.is_relative_to(root.resolve()):
            continue
        try:
            if (
                not document.is_file()
                or not document.read_text(encoding="utf-8").strip()
            ):
                continue
        except OSError, UnicodeError:
            continue
        hits.append(
            {
                "query": query["id"],
                "collection": collection,
                "path": path,
                "line": int(result["line"]),
                "score": float(result["score"]),
                "mode": mode,
            }
        )
    return hits


def search(wiki_id, cache, queries, *, expected_pages_root=None):
    """Search queries through one qmd MCP session."""
    wiki_id, cache = _component(wiki_id), Path(cache).resolve()
    _, index_path, config_path = _paths(wiki_id, cache)
    if not index_path.is_file():
        raise LookupError(f"missing qmd index for {wiki_id}; run index")
    configured = _collections(config_path)
    roots = {
        name: Path(configured[name]["path"]) for name in ("pages", "evidence")
    }
    if (
        expected_pages_root is not None
        and roots["pages"].resolve() != Path(expected_pages_root).resolve()
    ):
        raise LookupError("qmd pages root changed; reindex")
    evidence_root = cache / "wiki-evidence" / wiki_id
    evidence_root /= f"markitdown-{evidence.CONVERTER_VERSION}"
    evidence_root = evidence_root.resolve()
    if roots["evidence"].resolve() != evidence_root:
        raise LookupError("evidence converter changed; reindex")
    _update_index(wiki_id, cache, index_path)
    results = _run_mcp_search(wiki_id, cache, queries)[1]
    return [
        hit
        for query, mode, hits in results
        for hit in _hits(hits, query, mode, roots[str(query["collection"])])
    ]
