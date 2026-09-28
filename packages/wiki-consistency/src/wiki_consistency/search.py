"""qmd indexing and batched local search for Wiki Markdown."""

from __future__ import annotations

from contextlib import closing
import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from wiki_consistency import evidence
from wiki_consistency.evidence import _clean_on_signals, _component, _tree_size


QMD_BUDGET_BYTES = 3 * 1024**3
EMBED_MODEL = "hf:Qwen/Qwen3-Embedding-0.6B-GGUF/Qwen3-Embedding-0.6B-Q8_0.gguf"


def _paths(wiki_id: str, cache: Path) -> tuple[Path, Path, Path]:
    wiki_id = _component(wiki_id)
    qmd_root = Path(cache) / "qmd"
    index_path = qmd_root / f"{wiki_id}.sqlite"
    config_path = qmd_root / "config" / f"{wiki_id}.yml"
    if not index_path.resolve().is_relative_to(qmd_root.resolve()):
        raise ValueError("qmd index path escapes the cache")
    return qmd_root, index_path, config_path


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
    qmd_root = Path(cache) / "qmd"
    environment = os.environ.copy()
    environment.update(
        {
            "XDG_CACHE_HOME": str(Path(cache).resolve()),
            "QMD_CONFIG_DIR": str((qmd_root / "config").resolve()),
            "QMD_EMBED_MODEL": EMBED_MODEL,
            "MESA_SHADER_CACHE_DIR": str((qmd_root / "mesa_shader_cache").resolve()),
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
    qmd_root, _, _ = _paths(wiki_id, cache)
    _check_budget(qmd_root, budget_action)
    return subprocess.run(
        [str(qmd), "--index", wiki_id, *args],
        cwd=qmd.parents[2],
        env=_environment(cache),
        check=True,
        capture_output=True,
        text=True,
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
    qmd_root, _, config_path = _paths(wiki_id, cache)
    (qmd_root / "config").mkdir(parents=True, exist_ok=True)
    configured = _collections(config_path)
    for name in sorted(configured):
        value = configured[name]
        path = Path(str(value.get("path", ""))).resolve() if isinstance(value, dict) else None
        if name not in expected or path != expected[name].resolve():
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
    return sum(path.is_file() for path in root.rglob("*.md")) if root.is_dir() else 0


def _collection_chunk_count(wiki_id: str, cache: Path, collection: str) -> int:
    _, index_path, _ = _paths(wiki_id, cache)
    if not index_path.is_file():
        return 0
    try:
        with closing(sqlite3.connect(
            f"{index_path.resolve().as_uri()}?mode=ro&immutable=1", uri=True
        )) as database:
            return int(database.execute(
                "SELECT COUNT(DISTINCT vectors.hash || '_' || vectors.seq) "
                "FROM content_vectors AS vectors "
                "JOIN documents ON documents.hash = vectors.hash AND documents.active = 1 "
                "WHERE documents.collection = ?",
                (collection,),
            ).fetchone()[0])
    except sqlite3.Error:
        return 0


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
    cache = Path(cache)
    wiki_root = instance / "wiki"
    evidence_root = cache / "wiki-evidence" / wiki_id / f"markitdown-{evidence.CONVERTER_VERSION}"
    if not wiki_root.is_dir():
        raise ValueError(f"Wiki pages directory is missing: {wiki_root}")
    evidence_root.mkdir(parents=True, exist_ok=True)
    qmd_root, index_path, _ = _paths(wiki_id, cache)
    qmd_root.mkdir(parents=True, exist_ok=True)
    _check_budget(qmd_root, "collection setup")
    _ensure_collections(
        wiki_id,
        cache,
        {"pages": wiki_root.resolve(), "evidence": evidence_root.resolve()},
    )

    try:
        with _clean_on_signals():
            _run_qmd(wiki_id, cache, ["update"], budget_action="update")
    except BaseException:
        _remove_index(index_path)
        raise

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
        semantic_error = "qmd embed completed but semantic search is still not ready"
    counts = _run_search_mjs(
        wiki_id,
        cache,
        {
            "operation": "counts",
            "roots": {
                "pages": str(wiki_root.resolve()),
                "evidence": str(evidence_root.resolve()),
            },
        },
    )

    return {
        "pages": counts["pages"],
        "evidence": counts["evidence"],
        "semantic": semantic,
        "semantic_error": semantic_error,
    }


def _relative_path(filepath: str, collection: str, root: Path) -> str:
    prefix = f"qmd://{collection}/"
    if filepath.startswith(prefix):
        return Path(filepath[len(prefix) :]).as_posix()
    path = Path(filepath)
    if path.is_absolute():
        return path.resolve().relative_to(root.resolve()).as_posix()
    return path.as_posix()


def _run_search_mjs(wiki_id: str, cache: Path, payload: Mapping[str, object]) -> dict[str, object]:
    _, index_path, _ = _paths(wiki_id, cache)
    if not index_path.is_file():
        raise LookupError(f"qmd index is missing; run wiki-consistency index for {wiki_id}")
    environment = _environment(cache)
    environment["QMD_SEMANTIC_AVAILABLE"] = "1" if _model_is_cached(cache) else "0"
    process = subprocess.run(
        ["node", str(Path(__file__).with_name("search.mjs")), str(index_path.resolve())],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        input=json.dumps(payload, ensure_ascii=False),
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(process.stdout)
    if "error" in result:
        raise LookupError(result["error"])
    return result


def semantic_ready(wiki_id: str, cache: Path) -> bool:
    """Return whether the cached model and qmd index health allow vector search."""
    cache = Path(cache)
    if not _model_is_cached(cache):
        return False
    return bool(_run_search_mjs(wiki_id, cache, {"operation": "semantic"})["semantic"])


def search(
    wiki_id: str,
    cache: Path,
    queries: Sequence[Mapping[str, object]],
    *,
    expected_pages_root: Path | None = None,
) -> list[dict[str, object]]:
    """Search all queries in one qmd library process and map hits to lines."""
    wiki_id = _component(wiki_id)
    cache = Path(cache)
    _, index_path, config_path = _paths(wiki_id, cache)
    if not index_path.is_file():
        raise LookupError(f"qmd index is missing; run wiki-consistency index for {wiki_id}")
    for query in queries:
        if query.get("collection") not in {"pages", "evidence"}:
            raise ValueError("search collection must be pages or evidence")
        if not isinstance(query.get("text"), str) or not query["text"].strip():
            raise ValueError("search query text must be non-empty")
        allowed_paths = query.get("allowed_paths")
        if allowed_paths is not None:
            if query.get("collection") != "evidence":
                raise ValueError("allowed_paths is only valid for evidence searches")
            if not isinstance(allowed_paths, list) or any(
                not isinstance(path, str) for path in allowed_paths
            ):
                raise ValueError("evidence allowed paths must be a list of strings")

    configured = _collections(config_path)
    try:
        roots = {
            name: Path(str(configured[name]["path"]))
            for name in ("pages", "evidence")
        }
    except (KeyError, TypeError) as error:
        raise LookupError(
            f"qmd collection config is missing; run wiki-consistency index for {wiki_id}"
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
        cache / "wiki-evidence" / wiki_id / f"markitdown-{evidence.CONVERTER_VERSION}"
    ).resolve()
    if roots["evidence"].resolve() != expected_evidence_root:
        raise LookupError(
            f"qmd evidence collection uses a different markitdown version; "
            f"run wiki-consistency index for {wiki_id}"
        )

    result = _run_search_mjs(
        wiki_id,
        cache,
        {
            "queries": queries,
            "roots": {name: str(root.resolve()) for name, root in roots.items()},
        },
    )
    raw_hits = result["hits"]
    hits: list[dict[str, object]] = []
    for hit in raw_hits:
        collection = str(hit["collection"])
        path = _relative_path(str(hit["filepath"]), collection, roots[collection])
        document = roots[collection] / path
        if not document.is_file():
            continue
        hits.append(
            {
                "query": hit["query"],
                "collection": collection,
                "path": path,
                "line": int(hit["line"]),
                "score": float(hit["score"]),
                "mode": hit["mode"],
            }
        )
    return hits
