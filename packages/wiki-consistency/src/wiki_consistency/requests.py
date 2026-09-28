"""Prepare deterministic Backfire requests for a Wiki scope."""

from difflib import SequenceMatcher
import os
from pathlib import Path
import subprocess

from markdown_it import MarkdownIt

from doc_regions.requests import classify_requests
from doc_regions.requests import verify_requests
from doc_regions.units import split
from wiki_consistency import evidence
from wiki_consistency import search
from wiki_consistency.instance import mask_front_matter
from wiki_consistency.instance import pages
from wiki_consistency.instance import revisions
from wiki_consistency.lint import _link_targets
from wiki_consistency.search import _collection_chunk_count
from wiki_consistency.search import _markdown_count

SPECIAL_NO_UNITS = {"wiki/index.md", "wiki/log.md"}
REQUEST_ORDER = {"evidence": 0, "pages": 1, "crossref": 2, "classify": 3}


def _git(root, *args):
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def _collect(instance, scope):
    if scope not in {"changed", "lint"}:
        raise ValueError("scope must be changed or lint")
    root = Path(instance).resolve()
    head_result = _git(root, "rev-parse", "--verify", "HEAD")
    head = head_result.stdout.strip() if head_result.returncode == 0 else None
    revision_map = revisions(root)
    revision_by_key = {
        (source_id, item["revision"]): item
        for source_id, items in revision_map.items()
        for item in items
    }
    markdown = MarkdownIt("commonmark")
    page_info = {}
    scoped_units = []
    scoped_pages = set()

    for page in pages(root):
        path = page["path"]
        if path in SPECIAL_NO_UNITS:
            continue
        text = (root / path).read_text(encoding="utf-8")
        current = mask_front_matter(text)
        if head:
            base_result = _git(root, "show", f"HEAD:{path}")
            base = mask_front_matter(
                base_result.stdout if base_result.returncode == 0 else ""
            )
        else:
            base = ""
        units = split(path, current, base)
        changed_lines = set()
        changed_boundaries = set()
        if head:
            for tag, _, _, first, end in SequenceMatcher(
                None,
                base.splitlines(keepends=True),
                current.splitlines(keepends=True),
                autojunk=False,
            ).get_opcodes():
                if tag in {"insert", "replace"}:
                    changed_lines.update(range(first + 1, end + 1))
                elif tag == "delete":
                    changed_boundaries.add(first)

        cited = {(item["id"], item["revision"]) for item in page["sources"]}
        source_specs = set(cited)
        stale = False
        for source_id, cited_revision in cited:
            available = revision_map.get(source_id, [])
            if available and cited_revision != available[-1]["revision"]:
                stale = True
                source_specs.add((source_id, available[-1]["revision"]))
        source_specs = sorted(source_specs)
        linked = sorted(
            {
                f"wiki/{target}"
                for target in (_link_targets(root, page, markdown) or ())
            }
        )
        info = {
            "page": page,
            "units": units,
            "source_specs": source_specs,
            "linked": linked,
        }
        page_info[path] = info

        for raw_unit in units:
            changed = any(
                line in changed_lines
                for line in range(
                    raw_unit["first_line"], raw_unit["last_line"] + 1
                )
            ) or any(
                raw_unit["first_line"] - 1 <= boundary <= raw_unit["last_line"]
                for boundary in changed_boundaries
            )
            in_scope = scope == "lint" or head is None or stale or changed
            if not in_scope:
                continue
            unit = {
                key: value
                for key, value in raw_unit.items()
                if key != "document"
            }
            unit.update({"page": path, "outcome": None})
            scoped_units.append(unit)
            scoped_pages.add(path)
        if scope == "lint" or head is None or stale:
            scoped_pages.add(path)

    scoped_units.sort(
        key=lambda unit: (unit["page"], unit["first_line"], unit["id"])
    )
    return (
        head,
        page_info,
        scoped_units,
        scoped_pages,
        revision_by_key,
    )


def revisions_for_scope(instance, scope):
    """Return revisions to convert for the selected scope."""
    _, page_info, _, scoped_pages, revision_by_key = _collect(instance, scope)
    selected = {}
    for path in sorted(scoped_pages):
        for source_id, revision in page_info[path]["source_specs"]:
            item = revision_by_key.get((source_id, revision))
            if item is not None:
                selected.setdefault(source_id, {})[revision] = item
    return {
        source_id: [
            selected[source_id][revision]
            for revision in sorted(selected[source_id])
        ]
        for source_id in sorted(selected)
    }


def _read_evidence(cache, wiki_id, source_specs):
    result = []
    texts = {}
    for source_id, revision in source_specs:
        try:
            item = evidence.read(cache, wiki_id, source_id, revision)
        except LookupError as error:
            raise ValueError(f"prepare requires convert: {error}") from error
        if "text" in item:
            result.append(
                {"id": f"{source_id}/{revision}", "text": item["text"]}
            )
            texts[(source_id, revision)] = item["text"]
    return result, texts


def _page_text(info):
    return "\n".join(unit["text"] for unit in info["units"])


def _unit_at(page_info, path, line):
    info = page_info.get(path)
    if info is None:
        return None
    return next(
        (
            unit
            for unit in info["units"]
            if unit["first_line"] <= line <= unit["last_line"]
        ),
        None,
    )


def _ranked_hits(hits):
    positions = {}
    for hit in hits:
        key = (str(hit["query"]), str(hit["mode"]))
        position = positions.get(key, 0)
        positions[key] = position + 1
        yield hit, position


def _passages_for_group(job, hits, max_evidence_chars):
    allowed = job["texts"]
    path_keys = {
        f"{source_id}/{revision}.md": (source_id, revision)
        for source_id, revision in allowed
    }
    passage_units = {}
    units_by_file = {}
    query_units = {
        f"evidence:{unit['id']}": unit["id"] for unit in job["units"]
    }
    unit_passages = {unit["id"]: {} for unit in job["units"]}
    for hit, position in _ranked_hits(hits):
        path = Path(str(hit["path"])).as_posix()
        source_key = path_keys.get(path)
        if source_key is None:
            continue
        if path not in units_by_file:
            units_by_file[path] = split(path, allowed[source_key])
        units = units_by_file[path]
        unit = next(
            (
                item
                for item in units
                if item["first_line"] <= int(hit["line"]) <= item["last_line"]
            ),
            None,
        )
        if unit is None:
            continue
        key = (source_key, unit["first_line"], unit["last_line"])
        passage_units[key] = {
            "text": unit["text"],
            "source": source_key,
            "first_line": unit["first_line"],
        }
        query_unit = query_units.get(str(hit["query"]))
        if query_unit is None:
            continue
        rank = (position, path, int(hit["line"]))
        if (
            key not in unit_passages[query_unit]
            or rank < unit_passages[query_unit][key]
        ):
            unit_passages[query_unit][key] = rank

    ranked_passages = {
        unit_id: sorted(passages, key=passages.get)[:249]
        for unit_id, passages in unit_passages.items()
    }
    selected_by_unit = {unit["id"]: set() for unit in job["units"]}
    selected = set()
    selected_chars = 0
    for unit in job["units"]:
        unit_id = unit["id"]
        for key in ranked_passages[unit_id]:
            if (
                key not in selected
                and selected_chars + len(passage_units[key]["text"])
                > max_evidence_chars
            ):
                continue
            if key not in selected:
                selected.add(key)
                selected_chars += len(passage_units[key]["text"])
            selected_by_unit[unit_id].add(key)
            break

    cursors = {
        unit_id: next(
            (
                index + 1
                for index, key in enumerate(ranked_passages[unit_id])
                if key in selected_by_unit[unit_id]
            ),
            0,
        )
        for unit_id in ranked_passages
    }
    while True:
        progressed = False
        for unit in job["units"]:
            unit_id = unit["id"]
            while cursors[unit_id] < len(ranked_passages[unit_id]):
                key = ranked_passages[unit_id][cursors[unit_id]]
                cursors[unit_id] += 1
                if key in selected_by_unit[unit_id]:
                    continue
                if (
                    key not in selected
                    and selected_chars + len(passage_units[key]["text"])
                    > max_evidence_chars
                ):
                    continue
                if key not in selected:
                    selected.add(key)
                    selected_chars += len(passage_units[key]["text"])
                selected_by_unit[unit_id].add(key)
                progressed = True
                break
        if not progressed:
            break

    assigned = {unit_id for unit_id, keys in selected_by_unit.items() if keys}
    ordered_keys = sorted(
        selected,
        key=lambda key: (
            key[0],
            passage_units[key]["first_line"],
            passage_units[key]["text"],
        ),
    )
    counts = {}
    evidence_by_key = {}
    for key in ordered_keys:
        item = passage_units[key]
        source_id, revision = item["source"]
        counts[(source_id, revision)] = counts.get((source_id, revision), 0) + 1
        evidence_by_key[key] = {
            "id": f"{source_id}/{revision}#{counts[(source_id, revision)]}",
            "text": item["text"],
        }

    packed = []
    group_units = []
    group_keys = set()
    for unit in job["units"]:
        unit_id = unit["id"]
        keys = set(selected_by_unit[unit_id])
        if not keys:
            continue
        if group_units and len(group_keys | keys) > 249:
            packed.append((group_units, group_keys))
            group_units = []
            group_keys = set()
        group_units.append(unit)
        group_keys.update(keys)
    if group_units:
        packed.append((group_units, group_keys))
    order = {key: index for index, key in enumerate(ordered_keys)}
    groups = [
        (
            units,
            [
                evidence_by_key[key]
                for key in sorted(keys, key=order.__getitem__)
            ],
        )
        for units, keys in packed
    ]
    return groups, assigned


def _request(kind, request):
    return {"kind": kind, **request}


def prepare(instance, wiki_id, cache, *, scope, max_evidence_chars, candidates):
    """Build the sorted, ready-to-send request object for one Wiki scope."""
    if not isinstance(max_evidence_chars, int) or max_evidence_chars < 1:
        raise ValueError("max-evidence-chars must be a positive integer")
    if not isinstance(candidates, int) or candidates < 1:
        raise ValueError("candidates must be a positive integer")
    head, page_info, units, scoped_pages, _ = _collect(instance, scope)
    cache = Path(cache)
    by_page = {}
    for unit in units:
        by_page.setdefault(unit["page"], []).append(unit)

    unverifiable = []
    evidence_groups = []
    passage_jobs = []
    for path in sorted(scoped_pages):
        info = page_info[path]
        page_units = by_page.get(path, [])
        if path == "wiki/overview.md":
            linked = [
                target
                for target in info["linked"]
                if target in page_info and target not in SPECIAL_NO_UNITS
            ]
            evidence_items = [
                {"id": target, "text": _page_text(page_info[target])}
                for target in linked
                if _page_text(page_info[target])
            ]
            source_ids = linked
            evidence_texts = {}
        else:
            evidence_items, evidence_texts = _read_evidence(
                cache, wiki_id, info["source_specs"]
            )
            source_ids = [
                f"{source_id}/{revision}"
                for source_id, revision in info["source_specs"]
            ]
        if not page_units:
            continue
        if not evidence_items:
            unverifiable.extend(
                {"unit": unit["id"], "sources": sorted(source_ids)}
                for unit in page_units
            )
            continue
        if (
            sum(len(item["text"]) for item in evidence_items)
            <= max_evidence_chars
        ):
            evidence_groups.append((page_units, evidence_items))
        elif path == "wiki/overview.md":
            unverifiable.extend(
                {"unit": unit["id"], "sources": sorted(source_ids)}
                for unit in page_units
            )
        else:
            passage_jobs.append(
                {
                    "page": path,
                    "units": page_units,
                    "texts": evidence_texts,
                    "sources": [
                        f"{source_id}/{revision}"
                        for source_id, revision in info["source_specs"]
                    ],
                }
            )

    queries = []
    try:
        evidence_chunks = _collection_chunk_count(wiki_id, cache, "evidence")
    except LookupError as error:
        raise ValueError(f"prepare requires index: {error}") from error
    evidence_limit = max(
        20,
        candidates * 4,
        _markdown_count(
            cache
            / "wiki-evidence"
            / wiki_id
            / f"markitdown-{evidence.CONVERTER_VERSION}"
        ),
        evidence_chunks,
    )
    for job in passage_jobs:
        for unit in job["units"]:
            queries.append(
                {
                    "id": f"evidence:{unit['id']}",
                    "text": unit["text"],
                    "collection": "evidence",
                    "limit": evidence_limit,
                    "allowed_paths": sorted(
                        f"{source_id}/{revision}.md"
                        for source_id, revision in job["texts"]
                    ),
                }
            )
    try:
        semantic = search.semantic_ready(wiki_id, cache)
    except LookupError as error:
        raise ValueError(f"prepare requires index: {error}") from error
    page_query_ids = {}
    for unit in units:
        page_query_ids[unit["id"]] = f"pages:{unit['id']}"
        if semantic:
            queries.append(
                {
                    "id": page_query_ids[unit["id"]],
                    "text": unit["text"],
                    "collection": "pages",
                    "limit": min(249, max(20, candidates * 4)),
                }
            )

    crossref_query_ids = {}
    if scope == "lint" and semantic:
        for path, info in sorted(page_info.items()):
            page = info["page"]
            if page["special"] or not page["title"] or not page["summary"]:
                continue
            query_id = f"crossref:{path}"
            crossref_query_ids[path] = query_id
            queries.append(
                {
                    "id": query_id,
                    "text": f"{page['title']}\n{page['summary']}",
                    "collection": "pages",
                    "limit": 100,
                }
            )

    try:
        hits = search.search(
            wiki_id, cache, queries, expected_pages_root=Path(instance) / "wiki"
        )
    except LookupError as error:
        raise ValueError(f"prepare requires index: {error}") from error
    hits_by_query = {}
    for hit in hits:
        hits_by_query.setdefault(str(hit["query"]), []).append(hit)

    for job in passage_jobs:
        passage_groups, assigned = _passages_for_group(
            job,
            [
                hit
                for unit in job["units"]
                for hit in hits_by_query.get(f"evidence:{unit['id']}", [])
            ],
            max_evidence_chars,
        )
        unverifiable.extend(
            {"unit": unit["id"], "sources": sorted(job["sources"])}
            for unit in job["units"]
            if unit["id"] not in assigned
        )
        evidence_groups.extend(passage_groups)

    request_list = [
        _request("evidence", item) for item in verify_requests(evidence_groups)
    ]
    requestable = {
        unit_id for request in request_list for unit_id in request["units"]
    }
    unverifiable_ids = {item["unit"] for item in unverifiable}

    page_groups = []
    for unit in units:
        if unit["id"] not in requestable:
            continue
        found = {}
        ranks = {}
        for hit, position in _ranked_hits(
            hits_by_query.get(page_query_ids[unit["id"]], [])
        ):
            path = f"wiki/{Path(str(hit['path'])).as_posix()}"
            candidate = _unit_at(page_info, path, int(hit["line"]))
            if (
                candidate is not None
                and path != unit["page"]
                and candidate["id"] not in unverifiable_ids
            ):
                found[candidate["id"]] = candidate
                rank = (
                    position,
                    Path(str(hit["path"])).as_posix(),
                    int(hit["line"]),
                )
                if (
                    candidate["id"] not in ranks
                    or rank < ranks[candidate["id"]]
                ):
                    ranks[candidate["id"]] = rank
        chosen = sorted(
            found, key=lambda candidate_id: (*ranks[candidate_id], candidate_id)
        )[: min(candidates, 249)]
        candidates_for_unit = sorted(
            (found[candidate_id] for candidate_id in chosen),
            key=lambda item: (item["document"], item["first_line"], item["id"]),
        )
        if candidates_for_unit:
            page_groups.append(
                (
                    [unit],
                    [
                        {"id": candidate["id"], "text": candidate["text"]}
                        for candidate in candidates_for_unit
                    ],
                )
            )
    request_list.extend(
        _request("pages", item) for item in verify_requests(page_groups)
    )

    if scope == "lint":
        for path, query_id in sorted(crossref_query_ids.items()):
            info = page_info[path]
            linked = set(info["linked"])
            candidates_by_path = {}
            ranks = {}
            for hit, position in _ranked_hits(hits_by_query.get(query_id, [])):
                candidate_path = f"wiki/{Path(str(hit['path'])).as_posix()}"
                candidate = page_info.get(candidate_path)
                if (
                    candidate is None
                    or candidate["page"]["special"]
                    or candidate_path == path
                    or candidate_path in linked
                ):
                    continue
                page = candidate["page"]
                paragraph = next(
                    (
                        unit["text"]
                        for unit in candidate["units"]
                        if unit["kind"] == "paragraph"
                        and unit["id"] in requestable
                    ),
                    "",
                )
                text = "\n".join(
                    part
                    for part in (page["title"], page["summary"], paragraph)
                    if part
                )
                candidates_by_path[candidate_path] = {
                    "id": candidate_path,
                    "text": text,
                }
                rank = (
                    position,
                    Path(str(hit["path"])).as_posix(),
                    int(hit["line"]),
                )
                if candidate_path not in ranks or rank < ranks[candidate_path]:
                    ranks[candidate_path] = rank
            selected_paths = sorted(
                candidates_by_path,
                key=lambda candidate_path: ranks[candidate_path],
            )[:20]
            selected = [
                candidates_by_path[key] for key in sorted(selected_paths)
            ]
            if len(selected) >= 2:
                request_list.append(
                    {
                        "kind": "crossref",
                        "tool": "backfire_find",
                        "units": [
                            unit["id"]
                            for unit in by_page.get(path, [])
                            if unit["id"] in requestable
                        ],
                        "arguments": {
                            "query": f"{info['page']['title']}\n"
                            f"{info['page']['summary']}",
                            "candidates": selected,
                        },
                    }
                )

    for path in sorted(by_page):
        added = [
            unit
            for unit in by_page[path]
            if unit["added"] and unit["id"] in requestable
        ]
        request_list.extend(
            _request("classify", item)
            for item in classify_requests(
                added, f"Find mechanical region candidates in {path}."
            )
        )

    for unit in units:
        unit["outcome"] = (
            "requested" if unit["id"] in requestable else "unverifiable"
        )
    unverifiable.sort(key=lambda item: (item["unit"], item["sources"]))
    request_list.sort(
        key=lambda item: (
            REQUEST_ORDER[item["kind"]],
            tuple(item["units"]),
            item["tool"],
        )
    )
    calls = {
        tool: sum(request["tool"] == tool for request in request_list)
        for tool in ("backfire_verify", "backfire_find", "backfire_classify")
    }
    return {
        "wiki": wiki_id,
        "scope": scope,
        "head": head,
        "units": [
            {
                key: unit[key]
                for key in (
                    "id",
                    "page",
                    "heading_path",
                    "kind",
                    "first_line",
                    "last_line",
                    "added",
                    "outcome",
                )
            }
            for unit in units
        ],
        "unverifiable": unverifiable,
        "search": {
            "keyword": True,
            "semantic": semantic,
            "not_searched": [] if semantic else ["crossref", "pages"],
        },
        "calls": calls,
        "requests": request_list,
    }
