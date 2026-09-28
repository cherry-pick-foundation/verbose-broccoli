"""Read Wiki storage roots, pages, and raw revision folders."""

import os
from pathlib import Path

import yaml

from doc_regions.config import files

SPECIAL_PAGES = {"wiki/index.md", "wiki/overview.md", "wiki/log.md"}


def roots(env=None):
    """Return namespaced data and cache roots from the environment."""
    env = os.environ if env is None else env
    home = Path(env.get("HOME") or Path.home())
    result = {}
    for name, default in (("data", ".local/share"), ("cache", ".cache")):
        configured = env.get(f"XDG_{name.upper()}_HOME")
        path = Path(configured) if configured else home / default
        if not path.is_absolute():
            path = home / default
        result[name] = (path / "verbose-broccoli").resolve()
    return result


def instance_path(wiki_id, env=None):
    """Return a Wiki instance path after validating its name."""
    if (
        not isinstance(wiki_id, str)
        or wiki_id in ("", ".", "..")
        or "/" in wiki_id
        or "\0" in wiki_id
    ):
        raise ValueError("wiki must be a single folder name")
    return roots(env)["data"] / "vaults" / wiki_id


def _front_matter(text):
    lines = text.split("\n")
    if not lines or lines[0].removesuffix("\r") != "---":
        return None, None, "missing YAML front matter"
    end = next(
        (
            index
            for index in range(1, len(lines))
            if lines[index].removesuffix("\r") == "---"
        ),
        None,
    )
    if end is None:
        return None, None, "unclosed YAML front matter"
    return (
        "\n".join(line.removesuffix("\r") for line in lines[1:end]),
        end,
        None,
    )


def _metadata(text):
    source, _, error = _front_matter(text)
    if error:
        return {}, [{"line": 1, "message": error}]
    try:
        metadata = yaml.safe_load(source)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        line = 2 + mark.line if mark is not None else 1
        return {}, [
            {"line": line, "message": f"invalid YAML front matter: {error}"}
        ]
    if not isinstance(metadata, dict):
        return {}, [{"line": 2, "message": "front matter must be a mapping"}]

    problems = []
    for field in ("title", "summary"):
        value = metadata.get(field)
        if (
            not isinstance(value, str)
            or not value.strip()
            or "\n" in value
            or "\r" in value
        ):
            problems.append(
                {
                    "line": 1,
                    "message": f"{field} must be a non-empty single line",
                }
            )

    citations = metadata.get("sources")
    sources = []
    if not isinstance(citations, list) or not citations:
        problems.append(
            {"line": 1, "message": "sources must be a non-empty list"}
        )
    else:
        for citation in citations:
            if not isinstance(citation, dict) or any(
                not isinstance(citation.get(field), str)
                or not citation[field].strip()
                for field in ("id", "revision")
            ):
                problems.append(
                    {
                        "line": 1,
                        "message": "source citation needs a non-empty "
                        "id and revision",
                    }
                )
                continue
            sources.append(
                {"id": citation["id"], "revision": citation["revision"]}
            )

    return {
        "title": metadata.get("title"),
        "summary": metadata.get("summary"),
        "sources": sources,
    }, problems


def pages(instance):
    """Read page metadata and validation problems for a Wiki instance."""
    root = Path(instance).resolve()
    try:
        matches = files(root, "wiki/**/*.md")
    except ValueError as error:
        if str(error).startswith("No files match:"):
            return []
        raise

    result = []
    for path in matches:
        relative = path.relative_to(root).as_posix()
        special = relative in SPECIAL_PAGES
        page = {
            "path": relative,
            "title": None,
            "summary": None,
            "sources": [],
            "special": special,
            "problems": [],
        }
        if not special:
            try:
                metadata, problems = _metadata(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as error:
                problems = [{"line": 1, "message": str(error)}]
            else:
                page.update(metadata)
            page["problems"] = problems
        result.append(page)
    return result


def mask_front_matter(text):
    """Replace front matter with blank lines while preserving line numbers."""
    _, end, error = _front_matter(text)
    if error:
        return text
    lines = text.split("\n")
    for index in range(end + 1):
        lines[index] = "\r" if lines[index].endswith("\r") else ""
    return "\n".join(lines)


def revisions(instance):
    """Return raw BagIt revisions grouped by source identifier."""
    root = Path(instance).resolve()
    raw = root / "raw"
    result = {}
    if not raw.is_dir():
        return result
    paths = sorted(
        path
        for path in raw.glob("*/*/*")
        if path.is_dir() and not path.is_symlink()
    )
    for path in paths:
        kind, source_id, revision = path.relative_to(raw).parts
        result.setdefault(source_id, []).append(
            {
                "kind": kind,
                "id": source_id,
                "revision": revision,
                "path": path.relative_to(root).as_posix(),
            }
        )
    return dict(sorted(result.items()))
