"""Run offline consistency checks and mechanical-region updates."""

from pathlib import Path
import subprocess
from urllib.parse import unquote, urlsplit

import bagit
from markdown_it import MarkdownIt

from doc_regions.config import files
from doc_regions.regions import check as check_regions
from doc_regions.regions import scan, shape, update as update_regions

from wiki_consistency.instance import mask_front_matter, pages, revisions


GENERATORS = "wiki_consistency.sources"
FIX_COMMAND = "wiki-consistency update"


def _problem(document, line, message):
    return {"document": document, "line": line, "message": message}


def _targets(root):
    return [
        path.relative_to(root).as_posix()
        for path in files(root, "wiki/**/*.md")
    ]


def _index_shape(root):
    path = root / "wiki" / "index.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [_problem("wiki/index.md", 1, str(error))]
    spans, marker_problems = scan("wiki/index.md", text)
    if marker_problems:
        return []
    if len(spans) != 1:
        return [
            _problem(
                "wiki/index.md",
                1,
                "index.md must contain one page_catalog region and nothing else",
            )
        ]
    span = spans[0]
    line_count = len(text.split("\n")) - text.endswith("\n")
    if span["start"] != 0 or span["end"] != line_count:
        return [
            _problem(
                "wiki/index.md",
                1,
                "index.md must contain one page_catalog region and nothing else",
            )
        ]
    try:
        function, sources = shape(span["code"], GENERATORS)
    except ValueError:
        return []
    if function != "page_catalog" or sources != ["wiki/**/*.md"]:
        return [
            _problem(
                "wiki/index.md",
                span["start"] + 1,
                'index.md must call page_catalog("wiki/**/*.md")',
            )
        ]
    return []


def _link_targets(root, page, markdown):
    page_path = root / page["path"]
    try:
        text = page_path.read_text(encoding="utf-8")
    except OSError, UnicodeError:
        return
    wiki = root / "wiki"
    for token in markdown.parse(mask_front_matter(text)):
        for child in token.children or ():
            if child.type != "link_open":
                continue
            href = child.attrGet("href")
            if not href:
                continue
            try:
                parsed = urlsplit(href)
                if (
                    parsed.scheme
                    or parsed.netloc
                    or not parsed.path
                    or parsed.path.startswith("/")
                ):
                    continue
                target = (page_path.parent / unquote(parsed.path)).resolve()
                if target.is_relative_to(wiki.resolve()):
                    yield target.relative_to(wiki.resolve()).as_posix()
            except OSError, ValueError:
                continue


def _page_findings(root, page_list, revision_map):
    problems = []
    stale = []
    validated = {}
    for page in page_list:
        if page["special"]:
            continue
        problems.extend(
            _problem(page["path"], item["line"], item["message"])
            for item in page["problems"]
        )
        for citation in page["sources"]:
            source_id = citation["id"]
            candidates = revision_map.get(source_id)
            if not candidates:
                problems.append(
                    _problem(
                        page["path"],
                        1,
                        f"citation names no source bag: {source_id}",
                    )
                )
                continue
            match = next(
                (
                    item
                    for item in candidates
                    if item["revision"] == citation["revision"]
                ),
                None,
            )
            if match is None:
                problems.append(
                    _problem(
                        page["path"],
                        1,
                        f"citation names no revision bag: {source_id}/{citation['revision']}",
                    )
                )
                continue
            bag_path = root / match["path"]
            key = bag_path.as_posix()
            if key not in validated:
                try:
                    bagit.Bag(str(bag_path)).validate(fast=True)
                except Exception as error:
                    validated[key] = str(error)
                else:
                    validated[key] = None
            if validated[key]:
                problems.append(
                    _problem(
                        page["path"],
                        1,
                        f"BagIt fast validation failed for {source_id}/{citation['revision']}: "
                        f"{validated[key]}",
                    )
                )
            latest = candidates[-1]["revision"]
            if citation["revision"] != latest:
                stale.append(
                    {
                        "page": page["path"],
                        "source_id": source_id,
                        "cited_revision": citation["revision"],
                        "latest_revision": latest,
                    }
                )
    return problems, stale


def _orphans(page_list, markdown, root):
    content_pages = [
        page["path"]
        for page in page_list
        if not page["special"] and page["path"] != "wiki/index.md"
    ]
    pages_by_path = set(content_pages)
    inbound = {path: set() for path in content_pages}
    for page in page_list:
        for target in _link_targets(root, page, markdown) or ():
            path = f"wiki/{target}"
            if path in pages_by_path and page["path"] != "wiki/index.md":
                inbound[path].add(page["path"])
    return sorted(
        path for path, sources in inbound.items() if not (sources - {path})
    )


def _log_prefix(root):
    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            text=True,
            capture_output=True,
        )
    except OSError as error:
        return [_problem("wiki/log.md", 1, f"git is unavailable: {error}")]
    if inside.returncode:
        return [
            _problem(
                "wiki/log.md",
                1,
                f"git repository check failed: {inside.stderr.strip()}",
            )
        ]
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if head.returncode:
        return []
    committed = subprocess.run(
        ["git", "show", "HEAD:wiki/log.md"], cwd=root, capture_output=True
    )
    if committed.returncode:
        message = committed.stderr.decode("utf-8", errors="replace").strip()
        return [
            _problem(
                "wiki/log.md", 1, f"git show HEAD:wiki/log.md failed: {message}"
            )
        ]
    try:
        current = (root / "wiki" / "log.md").read_bytes()
    except OSError as error:
        return [_problem("wiki/log.md", 1, str(error))]
    original = committed.stdout
    if current.startswith(original):
        return []
    before = original.splitlines(keepends=True)
    after = current.splitlines(keepends=True)
    line = next(
        (
            index + 1
            for index, (old, new) in enumerate(zip(before, after))
            if old != new
        ),
        min(len(before), len(after)) + 1,
    )
    return [
        _problem(
            "wiki/log.md",
            line,
            f"committed log.md is not a prefix of the current file at line {line}",
        )
    ]


def check(instance):
    root = Path(instance).resolve()
    problems = []
    try:
        targets = _targets(root)
    except (OSError, ValueError) as error:
        targets = []
        problems.append(_problem("wiki", 1, str(error)))
    if targets:
        try:
            problems.extend(
                check_regions(
                    root,
                    targets,
                    GENERATORS,
                    Path(__file__).resolve().parent.parent,
                    fix_command=FIX_COMMAND,
                )
            )
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            problems.append(_problem("wiki", 1, str(error)))

    problems.extend(_index_shape(root))
    page_list = pages(root)
    revision_map = revisions(root)
    page_problems, stale = _page_findings(root, page_list, revision_map)
    problems.extend(page_problems)
    problems.extend(_log_prefix(root))
    problems.sort(
        key=lambda item: (item["document"], item["line"], item["message"])
    )
    markdown = MarkdownIt("commonmark")
    return {
        "problems": problems,
        "orphans": _orphans(page_list, markdown, root),
        "stale_citations": sorted(
            stale,
            key=lambda item: (
                item["page"],
                item["source_id"],
                item["cited_revision"],
            ),
        ),
    }


def update(instance):
    root = Path(instance).resolve()
    problems = _index_shape(root)
    if problems:
        return {"problems": problems}
    try:
        targets = _targets(root)
        problems = update_regions(
            root, targets, GENERATORS, Path(__file__).resolve().parent.parent
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        problems = [_problem("wiki", 1, str(error))]
    return {"problems": problems}
