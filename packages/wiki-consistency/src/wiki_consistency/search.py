"""qmd indexing and batched local search for Wiki Markdown."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Mapping, Sequence

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
MODEL_TOKENS = (
    "HF_TOKEN",
    "HF_TOKEN_PATH",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "HF_ENDPOINT",
    "MODEL_ENDPOINT",
)


def _paths(wiki_id: str, cache: Path) -> tuple[Path, Path, Path]:
    wiki_id = _component(wiki_id)
    cache_root = Path(cache).resolve()
    qmd_root = cache_root / "qmd"
    index_path = qmd_root / f"{wiki_id}.sqlite"
    config_path = qmd_root / "config" / f"{wiki_id}.yml"
    qmd_resolved = qmd_root.resolve()
    if (
        not qmd_resolved.is_relative_to(cache_root)
        or not index_path.resolve().is_relative_to(qmd_resolved)
        or not config_path.parent.resolve().is_relative_to(qmd_resolved)
        or (
            config_path.is_symlink()
            and not config_path.resolve().is_relative_to(qmd_resolved)
        )
    ):
        raise ValueError("qmd path escapes the cache")
    return qmd_root, index_path, config_path


def _secure_cache(cache: Path) -> None:
    cache_root = Path(cache).resolve()
    cache_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    cache_root.chmod(0o700)
    qmd_root, _, _ = _paths("wiki", cache_root)
    qmd_root.mkdir(mode=0o700, exist_ok=True)
    qmd_root.chmod(0o700)
    config_dir = qmd_root / "config"
    config_dir.mkdir(mode=0o700, exist_ok=True)
    config_dir.chmod(0o700)


def _qmd_path() -> Path:
    return Path(__file__).resolve().parents[2] / "node_modules" / ".bin" / "qmd"


def _check_budget(root: Path, action: str) -> None:
    used = _tree_size(root)
    if used >= QMD_BUDGET_BYTES:
        raise ValueError(
            f"qmd cache budget exceeded before {action}: "
            f"{used} bytes used of {QMD_BUDGET_BYTES}"
        )


def _environment(cache: Path) -> dict[str, str]:
    qmd_root = Path(cache).resolve() / "qmd"
    environment = os.environ.copy()
    for name in MODEL_TOKENS:
        environment.pop(name, None)
    environment.update(
        {
            "XDG_CACHE_HOME": str(Path(cache).resolve()),
            "QMD_CONFIG_DIR": str((qmd_root / "config").resolve()),
            "QMD_EMBED_MODEL": EMBED_MODEL,
            "QMD_FORCE_CPU": "1",
            "MESA_SHADER_CACHE_DIR": str(
                (qmd_root / "mesa_shader_cache").resolve()
            ),
        }
    )
    return environment


def _run_qmd(
    wiki_id: str,
    cache: Path,
    args: Sequence[str],
    *,
    budget_action: str,
) -> subprocess.CompletedProcess[str]:
    qmd = _qmd_path()
    if not qmd.is_file():
        raise FileNotFoundError(f"qmd is not installed at {qmd}")
    _secure_cache(cache)
    qmd_root, _, _ = _paths(wiki_id, cache)
    _check_budget(qmd_root, budget_action)
    return subprocess.run(
        [str(qmd), "--index", wiki_id, *args],
        cwd=qmd.parents[2],
        env=_environment(cache),
        check=True,
        capture_output=True,
        text=True,
        umask=0o077,
    )


def _collections(config_path: Path) -> dict[str, Mapping[str, object]]:
    if not config_path.is_file():
        return {}
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    values = config.get("collections", {}) if isinstance(config, dict) else {}
    return values if isinstance(values, dict) else {}


def _ensure_collections(
    wiki_id: str,
    cache: Path,
    expected: Mapping[str, Path],
) -> None:
    _, _, config_path = _paths(wiki_id, cache)
    configured = _collections(config_path)
    for name in sorted(configured):
        value = configured[name]
        path = (
            Path(str(value.get("path", ""))).resolve()
            if isinstance(value, dict)
            else None
        )
        update_hook = isinstance(value, dict) and bool(value.get("update"))
        if (
            name not in expected
            or path != expected[name].resolve()
            or update_hook
        ):
            _run_qmd(
                wiki_id,
                cache,
                ["collection", "remove", name],
                budget_action="collection update",
            )
    configured = _collections(config_path)
    for name, path in expected.items():
        if name not in configured:
            _run_qmd(
                wiki_id,
                cache,
                ["collection", "add", str(path.resolve()), "--name", name],
                budget_action="collection add",
            )


def _remove_index(index_path: Path) -> None:
    sidecars = (
        index_path.with_name(index_path.name + "-wal"),
        index_path.with_name(index_path.name + "-shm"),
    )
    for path in (index_path, *sidecars):
        path.unlink(missing_ok=True)


def _model_is_cached(cache: Path) -> bool:
    model_dir = Path(cache) / "qmd" / "models"
    filename = EMBED_MODEL.rsplit("/", 1)[-1]
    return any(path.is_file() for path in model_dir.glob(f"*{filename}"))


def _markdown_count(root: Path) -> int:
    return (
        sum(path.is_file() for path in root.rglob("*.md"))
        if root.is_dir()
        else 0
    )


def _collection_document_counts(wiki_id: str, cache: Path) -> dict[str, int]:
    _, index_path, _ = _paths(wiki_id, cache)
    if not index_path.is_file():
        raise LookupError(
            f"qmd index is missing; run wiki-consistency index for {wiki_id}"
        )
    output = _run_qmd(
        wiki_id, cache, ["ls"], budget_action="collection count"
    ).stdout
    counts = {}
    for line in output.splitlines():
        match = re.fullmatch(r"\s*qmd://([^/]+)/\s+\((\d+) files\)", line)
        if match:
            counts[match.group(1)] = int(match.group(2))
    return counts


def _collection_chunk_count(wiki_id: str, cache: Path, collection: str) -> int:
    return _collection_document_counts(wiki_id, cache).get(collection, 0)


def _update_index(wiki_id: str, cache: Path, index_path: Path) -> None:
    try:
        with _clean_on_signals():
            _run_qmd(wiki_id, cache, ["update"], budget_action="update")
    except BaseException:
        _remove_index(index_path)
        raise


def index(
    instance: Path,
    wiki_id: str,
    cache: Path,
    *,
    download: bool,
) -> dict[str, object]:
    """Build or refresh qmd's pages and evidence collections."""
    wiki_id = _component(wiki_id)
    instance = Path(instance)
    cache = Path(cache).resolve()
    _secure_cache(cache)
    wiki_root = instance / "wiki"
    evidence_root = (
        cache
        / "wiki-evidence"
        / wiki_id
        / f"markitdown-{evidence.CONVERTER_VERSION}"
    )
    if not wiki_root.is_dir():
        raise ValueError(f"Wiki pages directory is missing: {wiki_root}")
    evidence_root.mkdir(parents=True, exist_ok=True)
    qmd_root, index_path, _ = _paths(wiki_id, cache)
    _check_budget(qmd_root, "collection setup")
    _ensure_collections(
        wiki_id,
        cache,
        {"pages": wiki_root.resolve(), "evidence": evidence_root.resolve()},
    )
    _update_index(wiki_id, cache, index_path)

    model_cached = _model_is_cached(cache)
    embedding_attempted = model_cached or download
    semantic_error = None
    if embedding_attempted:
        try:
            with _clean_on_signals():
                _run_qmd(wiki_id, cache, ["embed"], budget_action="embed")
        except subprocess.CalledProcessError as error:
            detail = error.stderr or error.stdout or str(error)
            semantic_error = " ".join(str(detail).split()) or str(error)
    semantic = semantic_ready(wiki_id, cache)
    if embedding_attempted and not semantic and semantic_error is None:
        semantic_error = (
            "qmd embed completed but semantic search is still not ready"
        )
    counts = _collection_document_counts(wiki_id, cache)

    return {
        "pages": counts.get("pages", 0),
        "evidence": counts.get("evidence", 0),
        "semantic": semantic,
        "semantic_error": semantic_error,
    }


def _relative_path(filepath: str, collection: str, root: Path) -> str:
    filepath = filepath.split("?", 1)[0]
    prefix = f"qmd://{collection}/"
    if filepath.startswith(prefix):
        return Path(filepath[len(prefix) :]).as_posix()
    path = Path(filepath)
    if path.is_absolute():
        return path.resolve().relative_to(root.resolve()).as_posix()
    return path.as_posix()


def _mcp_parameters(wiki_id: str, cache: Path) -> StdioServerParameters:
    qmd = _qmd_path()
    if not qmd.is_file():
        raise FileNotFoundError(f"qmd is not installed at {qmd}")
    _secure_cache(cache)
    qmd_root, _, _ = _paths(wiki_id, cache)
    _check_budget(qmd_root, "MCP search")
    return StdioServerParameters(
        command="/bin/sh",
        args=[
            "-c",
            'umask 077; exec "$@"',
            "qmd",
            str(qmd),
            "--index",
            wiki_id,
            "mcp",
        ],
        cwd=str(qmd.parents[2]),
        env=_environment(cache),
    )


def _mcp_data(result: object, tool: str) -> dict[str, object]:
    if getattr(result, "is_error", False):
        detail = " ".join(
            str(getattr(item, "text", ""))
            for item in getattr(result, "content", [])
        ).strip()
        raise LookupError(detail or f"qmd MCP {tool} failed")
    data = getattr(result, "structured_content", None)
    if not isinstance(data, dict):
        raise LookupError(f"qmd MCP {tool} returned no structured result")
    return data


async def _mcp_search(
    parameters: StdioServerParameters,
    vector_queries: Sequence[Mapping[str, object]],
) -> tuple[bool, list[dict[str, object]]]:
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            status = _mcp_data(await session.call_tool("status", {}), "status")
            if status.get("needsEmbedding") != 0:
                return False, []
            results = [
                _mcp_data(await session.call_tool("query", query), "query")
                for query in vector_queries
            ]
            return True, results


def _run_mcp_search(
    wiki_id: str,
    cache: Path,
    vector_queries: Sequence[Mapping[str, object]],
) -> tuple[bool, list[dict[str, object]]]:
    parameters = _mcp_parameters(wiki_id, cache)
    with _clean_on_signals():
        return asyncio.run(_mcp_search(parameters, vector_queries))


def semantic_ready(wiki_id: str, cache: Path) -> bool:
    """Return whether qmd can run vector search with the cached model."""
    cache = Path(cache)
    if not _model_is_cached(cache):
        return False
    _, index_path, _ = _paths(wiki_id, cache)
    if not index_path.is_file():
        raise LookupError(
            f"qmd index is missing; run wiki-consistency index for {wiki_id}"
        )
    ready, _ = _run_mcp_search(wiki_id, cache, [])
    return ready


def _mapped_hits(
    raw_hits: Sequence[Mapping[str, object]],
    query: Mapping[str, object],
    root: Path,
    mode: str,
) -> list[dict[str, object]]:
    collection = str(query["collection"])
    allowed_paths = query.get("allowed_paths")
    allowed = set(allowed_paths) if isinstance(allowed_paths, list) else None
    hits = []
    for hit in raw_hits:
        try:
            path = _relative_path(str(hit["file"]), collection, root)
            document = (root / path).resolve()
            if not document.is_relative_to(root.resolve()):
                continue
        except KeyError, ValueError:
            continue
        if allowed is not None and path not in allowed:
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
                "line": int(hit["line"]),
                "score": float(hit["score"]),
                "mode": mode,
            }
        )
    return hits


def search(
    wiki_id: str,
    cache: Path,
    queries: Sequence[Mapping[str, object]],
    *,
    expected_pages_root: Path | None = None,
) -> list[dict[str, object]]:
    """Search all queries through qmd's CLI and one MCP server."""
    wiki_id = _component(wiki_id)
    cache = Path(cache)
    _, index_path, config_path = _paths(wiki_id, cache)
    if not index_path.is_file():
        raise LookupError(
            f"qmd index is missing; run wiki-consistency index for {wiki_id}"
        )
    for query in queries:
        if query.get("collection") not in {"pages", "evidence"}:
            raise ValueError("search collection must be pages or evidence")
        if not isinstance(query.get("text"), str) or not query["text"].strip():
            raise ValueError("search query text must be non-empty")
        allowed_paths = query.get("allowed_paths")
        if allowed_paths is not None:
            if query.get("collection") != "evidence":
                raise ValueError(
                    "allowed_paths is only valid for evidence searches"
                )
            if not isinstance(allowed_paths, list) or any(
                not isinstance(path, str) for path in allowed_paths
            ):
                raise ValueError(
                    "evidence allowed paths must be a list of strings"
                )

    configured = _collections(config_path)
    try:
        roots = {
            name: Path(str(configured[name]["path"]))
            for name in ("pages", "evidence")
        }
    except (KeyError, TypeError) as error:
        raise LookupError(
            "qmd collection config is missing; run wiki-consistency index "
            f"for {wiki_id}"
        ) from error
    if (
        expected_pages_root is not None
        and roots["pages"].resolve() != Path(expected_pages_root).resolve()
    ):
        raise LookupError(
            f"qmd pages collection uses a different Wiki root; "
            f"run wiki-consistency index for {wiki_id}"
        )
    expected_evidence_root = (
        cache
        / "wiki-evidence"
        / wiki_id
        / f"markitdown-{evidence.CONVERTER_VERSION}"
    ).resolve()
    if roots["evidence"].resolve() != expected_evidence_root:
        raise LookupError(
            f"qmd evidence collection uses a different markitdown version; "
            f"run wiki-consistency index for {wiki_id}"
        )

    _update_index(wiki_id, cache, index_path)
    hits_by_query: list[list[dict[str, object]]] = [[] for _ in queries]
    vector_queries = []
    vector_indexes = []
    if _model_is_cached(cache):
        for index, query in enumerate(queries):
            vector_queries.append(
                {
                    "searches": [{"type": "vec", "query": str(query["text"])}],
                    "collections": [str(query["collection"])],
                    "limit": (
                        100000
                        if query.get("allowed_paths") is not None
                        else query.get("limit", 10)
                    ),
                    "minScore": 0,
                    "rerank": False,
                }
            )
            vector_indexes.append(index)

    for index, query in enumerate(queries):
        args = [
            "search",
            str(query["text"]),
            "-c",
            str(query["collection"]),
            "--format",
            "json",
        ]
        if query.get("allowed_paths") is not None:
            args.append("--all")
        else:
            args.extend(["-n", str(query.get("limit", 20))])
        results = json.loads(
            _run_qmd(wiki_id, cache, args, budget_action="search").stdout
        )
        hits_by_query[index].extend(
            _mapped_hits(results, query, roots[str(query["collection"])], "lex")
        )

    if vector_queries:
        ready, results = _run_mcp_search(wiki_id, cache, vector_queries)
        if ready:
            for index, result in zip(vector_indexes, results, strict=True):
                hits_by_query[index].extend(
                    _mapped_hits(
                        result.get("results", []),
                        queries[index],
                        roots[str(queries[index]["collection"])],
                        "vec",
                    )
                )
    return [hit for query_hits in hits_by_query for hit in query_hits]
