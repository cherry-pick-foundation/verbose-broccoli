"""Read Wiki storage roots, pages, and raw revision folders."""

import json
import os
from pathlib import Path

import yaml

from doc_regions.config import files

SPECIAL_PAGES = {"wiki/index.qmd", "wiki/overview.qmd", "wiki/log.qmd"}


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


def _front_matter_mapping(text):
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
    return metadata, []


def _topic_names(values):
    problems = []
    topics = []
    seen_topics = set()
    for topic in values:
        if (
            not isinstance(topic, str)
            or not topic.strip()
            or "\n" in topic
            or "\r" in topic
        ):
            problems.append(
                {
                    "line": 1,
                    "message": (
                        "topics must contain non-empty single-line names"
                    ),
                }
            )
        elif topic in seen_topics:
            problems.append(
                {"line": 1, "message": "topics must not contain duplicates"}
            )
        else:
            seen_topics.add(topic)
            topics.append(topic)
    return (topics if not problems else []), problems


def _metadata(text):
    metadata, problems = _front_matter_mapping(text)
    if problems:
        return {}, problems
    return _validate_metadata(metadata)


def _validate_metadata(metadata):
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

    topic_values = metadata.get("topics")
    topics = []
    if not isinstance(topic_values, list) or not topic_values:
        problems.append(
            {"line": 1, "message": "topics must be a non-empty list"}
        )
    else:
        topics, topic_problems = _topic_names(topic_values)
        problems.extend(topic_problems)

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
        **metadata,
        "title": metadata.get("title"),
        "summary": metadata.get("summary"),
        "topics": topics,
        "sources": sources,
    }, problems


def _page_path(root, document):
    if not isinstance(document, str):
        raise ValueError("page must be a root-relative string")
    path = Path(document)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.parts[0] != "wiki"
        or path.suffix != ".qmd"
        or any(character in document for character in "*?[")
    ):
        raise ValueError(f"expected a literal wiki/*.qmd page: {document}")
    matches = files(root, document)
    page = matches[0]
    if not page.resolve().is_relative_to(root / "wiki"):
        raise ValueError(f"page leaves wiki/: {document}")
    if page.with_suffix(".md").exists():
        raise ValueError(f"page has a legacy .md collision: {document}")
    return page


def metadata_sources(instance, document):
    """List safe ancestor defaults, Wiki root first, without content reads."""
    root = Path(instance).resolve()
    page = _page_path(root, document)
    folders = list(page.parent.relative_to(root / "wiki").parts)
    directory = root / "wiki"
    result = []
    for folder in (None, *folders):
        if folder is not None:
            directory /= folder
        candidate = directory / "_metadata.yml"
        if candidate.exists() or candidate.is_symlink():
            name = candidate.relative_to(root).as_posix()
            files(root, name)
            if not candidate.resolve().is_relative_to(root / "wiki"):
                raise ValueError(f"metadata leaves wiki/: {name}")
            result.append(name)
    return result


def _merge_metadata(default, override):
    if isinstance(default, list) or isinstance(override, list):
        # Quarto combines sequences (including scalar/list pairs), uniquely.
        if default is None or default is False or default == "" or default == 0:
            return override
        if (
            override is None
            or override is False
            or override == ""
            or override == 0
        ):
            return default
        combined = (default if isinstance(default, list) else [default]) + (
            override if isinstance(override, list) else [override]
        )
        unique = {}
        for item in combined:
            unique.setdefault(json.dumps(item, default=str), item)
        return list(unique.values())
    if isinstance(override, dict):
        result = dict(default) if isinstance(default, dict) else {}
        for key, value in override.items():
            result[key] = (
                _merge_metadata(result[key], value) if key in result else value
            )
        return result
    return override


def read_metadata(instance, document, *, named_defaults=None):
    """Read and validate full page metadata with ancestor directory defaults.

    Args:
        instance: Wiki instance root.
        document: Literal root-relative Wiki .qmd page path.
        named_defaults: Optional allowed metadata source names. Cog supplies its
            literal arguments; missing ancestors are refused before any reads.

    Returns:
        The full merged mapping and validation problems with source and line.
    """
    root = Path(instance).resolve()
    source = document
    try:
        defaults = metadata_sources(root, document)
        if named_defaults is not None:
            missing = set(defaults) - set(named_defaults)
            if missing:
                raise ValueError(
                    f"unnamed metadata source: {', '.join(sorted(missing))}"
                )
        metadata = {}
        for source in defaults:
            value = yaml.safe_load((root / source).read_bytes().decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("directory metadata must be a mapping")
            metadata = _merge_metadata(metadata, value)
        source = document
        local, problems = _front_matter_mapping(
            (root / document).read_bytes().decode("utf-8")
        )
        if problems:
            return {}, [{"document": source, **item} for item in problems]
        metadata, problems = _validate_metadata(
            _merge_metadata(metadata, local)
        )
        return metadata, [{"document": source, **item} for item in problems]
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        mark = getattr(error, "problem_mark", None)
        return {}, [
            {
                "document": source,
                "line": mark.line + 1 if mark is not None else 1,
                "message": str(error),
            }
        ]


def declared_topics(root):
    """Read the topic names that a Wiki instance's schema declares.

    Args:
        root: The Wiki instance root, which holds the schema `AGENTS.md`.

    Returns:
        A pair of the declared topic names and the validation problems found.
    """
    path = Path(root) / "AGENTS.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [], [{"line": 1, "message": str(error)}]

    metadata, problems = _front_matter_mapping(text)
    if problems:
        return [], problems

    topics = metadata.get("topics")
    if not isinstance(topics, list):
        return [], [{"line": 1, "message": "topics must be a list"}]
    return _topic_names(topics)


def pages(instance):
    """Read page metadata and validation problems for a Wiki instance."""
    root = Path(instance).resolve()
    try:
        matches = files(root, "wiki/**/*.qmd")
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
            "topics": [],
            "special": special,
            "problems": [],
        }
        if not special:
            metadata, problems = read_metadata(root, relative)
            page.update(
                {
                    key: metadata[key]
                    for key in ("title", "summary", "topics", "sources")
                    if key in metadata
                }
            )
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
