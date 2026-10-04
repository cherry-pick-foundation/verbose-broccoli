"""Prepare deterministic Jev requests for a Wiki scope."""

from difflib import SequenceMatcher
import json
import os
from pathlib import Path
import subprocess

from markdown_it import MarkdownIt
import yaml

from doc_regions.requests import classify_requests
from doc_regions.requests import verify_requests
from doc_regions.units import split
from wiki_consistency import citations
from wiki_consistency import evidence
from wiki_consistency import instance as storage
from wiki_consistency import search
from wiki_consistency.instance import mask_front_matter
from wiki_consistency.instance import pages
from wiki_consistency.instance import revisions
from wiki_consistency.lint import _link_targets

SPECIAL_NO_UNITS = {"wiki/index.qmd", "wiki/log.qmd"}
REQUEST_ORDER = {"evidence": 0, "pages": 1, "crossref": 2, "classify": 3}
# Upstream 0.13.0 truncates classify/find text at 2,000 UTF-16 code units.
MAX_SUGGESTION_TEXT_UNITS = 2000


def _text_units(text):
    """Count JavaScript string length without truncating exact text."""
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def _git(root, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    result.stdout = result.stdout.decode("utf-8")
    result.stderr = result.stderr.decode("utf-8", errors="replace")
    return result


def _head_metadata(root, path, text):
    merged = {}
    directory = Path("wiki")
    for folder in (None, *Path(path).parent.relative_to("wiki").parts):
        if folder is not None:
            directory /= folder
        result = _git(root, "show", f"HEAD:{directory}/_metadata.yml")
        if result.returncode == 0:
            value = yaml.safe_load(result.stdout)
            if not isinstance(value, dict):
                return {}, True
            merged = storage._merge_metadata(merged, value)  # noqa: SLF001
    local, problems = storage._front_matter_mapping(text)  # noqa: SLF001
    if problems:
        return {}, True
    return storage._validate_metadata(  # noqa: SLF001
        storage._merge_metadata(merged, local)  # noqa: SLF001
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
        text = (root / path).read_bytes().decode("utf-8")
        current = mask_front_matter(text)
        if head:
            base_result = _git(root, "show", f"HEAD:{path}")
            if base_result.returncode:
                base_result = _git(
                    root, "show", f"HEAD:{Path(path).with_suffix('.md')}"
                )
            base_text = (
                base_result.stdout if base_result.returncode == 0 else ""
            )
            base = mask_front_matter(base_text) if base_text else ""
        else:
            base = ""
        raw_units = split(path, current, base)
        units = raw_units if page["special"] else citations.sentences(raw_units)
        metadata_changed = False
        if not page["special"]:
            metadata, problems = storage.read_metadata(root, path)
            if problems:
                units = [
                    {
                        **unit,
                        "citation_problem": "invalid effective page metadata",
                    }
                    for unit in units
                ]
            if head:
                try:
                    old, old_problems = _head_metadata(root, path, base_text)
                except ValueError, yaml.YAMLError:
                    old, old_problems = {}, True
                metadata_changed = bool(old_problems) or old != metadata
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

        source_specs = sorted(source_specs)
        retained_changed = head is not None and any(
            _git(
                root,
                "diff",
                "--quiet",
                "HEAD",
                "--",
                f"text/{source_id}/{revision}.qmd",
            ).returncode
            or (
                _git(
                    root,
                    "cat-file",
                    "-e",
                    f"HEAD:text/{source_id}/{revision}.qmd",
                ).returncode
                and (root / "text" / source_id / f"{revision}.qmd").exists()
            )
            for source_id, revision in source_specs
        )
        linked = sorted(
            {
                f"wiki/{target}"
                for target in (_link_targets(root, page, markdown) or ())
            }
        )
        info = {
            "page": page,
            "units": units,
            "blocks": raw_units,
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
            in_scope = (
                scope == "lint"
                or head is None
                or stale
                or changed
                or metadata_changed
                or retained_changed
            )
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
        if (
            scope == "lint"
            or head is None
            or stale
            or metadata_changed
            or retained_changed
        ):
            scoped_pages.add(path)

    scoped_units.sort(
        key=lambda unit: (
            unit["page"],
            unit["first_line"],
            unit.get("start", 0),
            unit["id"],
        )
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


def _page_text(info):
    return "\n".join(unit["text"] for unit in info["blocks"])


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


def _request(kind, request):
    return {"kind": kind, **request}


def _prepare(
    instance,
    wiki_id,
    cache,
    *,
    scope,
    max_evidence_chars,
    candidates,
    collected,
    canonical_keys,
    reviews,
):
    head, page_info, units, scoped_pages, _ = collected
    by_page = {}
    for unit in units:
        by_page.setdefault(unit["page"], []).append(unit)

    unverifiable, evidence_groups, evidence_spans = [], [], {}
    for path in sorted(scoped_pages):
        info = page_info[path]
        page_units = by_page.get(path, [])
        declared = {
            f"{source_id}/{revision}"
            for source_id, revision in info["source_specs"]
        }
        for unit in page_units:
            evidence_items = []
            reason = unit.get("citation_problem")
            if path == "wiki/overview.qmd":
                evidence_items = [
                    {"id": target, "text": _page_text(page_info[target])}
                    for target in info["linked"]
                    if target in page_info
                    and target not in SPECIAL_NO_UNITS
                    and _page_text(page_info[target])
                ]
                source_ids = [item["id"] for item in evidence_items]
                reason = (
                    None
                    if evidence_items
                    else "overview has no linked English page evidence"
                )
            else:
                source_ids = [item["key"] for item in unit.get("citations", [])]
                if reason is None:
                    try:
                        for citation in unit["citations"]:
                            key = citation["key"]
                            if key not in declared or key not in canonical_keys:
                                raise ValueError(
                                    "citation is not an exact "
                                    "declared bag revision"
                                )
                            source_id, revision = key.split("/", 1)
                            located = evidence.read_located(
                                instance,
                                source_id,
                                revision,
                                citation["locator"],
                                max_chars=max_evidence_chars,
                                review=reviews.get(key),
                            )
                            evidence_id = (
                                f"{key}#{','.join(located['locator_ids'])}:"
                                f"{located['first_line']}-{located['last_line']}:"
                                f"{located['extraction-sha256']}"
                            )
                            evidence_items.append(
                                {"id": evidence_id, "text": located["text"]}
                            )
                            evidence_spans[evidence_id] = {
                                key: value
                                for key, value in located.items()
                                if key != "text"
                            }
                    except (
                        OSError,
                        UnicodeError,
                        ValueError,
                        LookupError,
                    ) as error:
                        reason = str(error)
            if (
                reason is None
                and sum(len(item["text"]) for item in evidence_items)
                > max_evidence_chars
            ):
                reason = "exact evidence set exceeds the evidence budget"
            if reason is not None or not evidence_items:
                unverifiable.append(
                    {
                        "unit": unit["id"],
                        "sources": sorted(source_ids),
                        "reason": reason or "missing sentence citation",
                    }
                )
                continue
            evidence_items = sorted(
                {item["id"]: item for item in evidence_items}.values(),
                key=lambda item: item["id"],
            )
            if evidence_groups and evidence_groups[-1][1] == evidence_items:
                evidence_groups[-1][0].append(unit)
            else:
                evidence_groups.append(([unit], evidence_items))

    queries = []
    # Status and candidate queries share the same qmd MCP session.
    model_cached = search._model_is_cached(cache)  # noqa: SLF001
    page_query_ids = {}
    for unit in units:
        page_query_ids[unit["id"]] = f"pages:{unit['id']}"
        if model_cached:
            queries.append(
                {
                    "id": page_query_ids[unit["id"]],
                    "text": unit["text"],
                    "collection": "pages",
                    "semantic_only": True,
                    "limit": min(249, max(20, candidates * 4)),
                }
            )

    crossref_query_ids = {}
    if scope == "lint" and model_cached:
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
                    "semantic_only": True,
                    "limit": 100,
                }
            )

    search_status = {}
    try:
        hits = search.search(
            wiki_id,
            cache,
            queries,
            expected_pages_root=Path(instance) / "wiki",
            search_status=search_status,
        )
    except LookupError as error:
        raise ValueError(f"prepare requires index: {error}") from error
    semantic = search_status.get("semantic", False)
    hits_by_query = {}
    for hit in hits:
        hits_by_query.setdefault(str(hit["query"]), []).append(hit)

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
                        "tool": "jev_find",
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
    for request in request_list:
        arguments = request["arguments"]
        if request["tool"] == "jev_classify" and any(
            _text_units(item["text"]) > MAX_SUGGESTION_TEXT_UNITS
            for item in arguments["items"]
        ):
            raise ValueError("classification item exceeds exact text limit")
        if request["tool"] == "jev_find" and any(
            _text_units(item["text"]) > MAX_SUGGESTION_TEXT_UNITS
            for item in arguments["candidates"]
        ):
            raise ValueError(
                "cross-reference candidate exceeds exact text limit"
            )
        if (
            request["tool"] == "jev_verify"
            and sum(len(item["text"]) for item in arguments["evidence"])
            > max_evidence_chars
        ):
            raise ValueError(
                "suggestion evidence exceeds caller evidence budget"
            )
    unverifiable.sort(key=lambda item: (item["unit"], item["sources"]))
    unit_order = {unit["id"]: index for index, unit in enumerate(units)}
    request_list.sort(
        key=lambda item: (
            REQUEST_ORDER[item["kind"]],
            tuple(unit_order[unit_id] for unit_id in item["units"]),
            item["tool"],
        )
    )
    calls = {
        tool: sum(request["tool"] == tool for request in request_list)
        for tool in ("jev_verify", "jev_find", "jev_classify")
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
                    "block_id",
                    "start",
                    "end",
                )
                if key in unit
            }
            for unit in units
        ],
        "unverifiable": unverifiable,
        "evidence_spans": evidence_spans,
        "segmentation": "candidate spans; unsupported or ambiguous prose "
        "needs review",
        "search": {
            "keyword": True,
            "semantic": semantic,
            "not_searched": [] if semantic else ["crossref", "pages"],
        },
        "calls": calls,
        "requests": request_list,
    }


def prepare(
    instance,
    wiki_id,
    cache,
    *,
    scope,
    max_evidence_chars,
    candidates,
    reviews=None,
):
    """Prepare exact candidate claims with optional caller-supplied receipts.

    Each receipt uses a canonical source/revision key and contains actual raw
    and extraction hashes plus its private evidence reference. The reference is
    used only by the evidence reader and is never included in request text.
    """
    if type(max_evidence_chars) is not int or max_evidence_chars < 1:
        raise ValueError("max-evidence-chars must be a positive integer")
    if type(candidates) is not int or candidates < 1:
        raise ValueError("candidates must be a positive integer")
    if reviews is not None and not isinstance(reviews, dict):
        raise ValueError("review receipts must be a canonical-key mapping")
    root, cache = Path(instance).resolve(), Path(cache).resolve()
    collected = _collect(root, scope)
    _, page_info, _, scoped_pages, revision_by_key = collected
    selected = {}
    for path in sorted(scoped_pages):
        for key in page_info[path]["source_specs"]:
            if key in revision_by_key:
                selected.setdefault(key[0], {})[key[1]] = revision_by_key[key]
    selected = {
        source: list(items.values()) for source, items in selected.items()
    }
    with evidence.bibliography(
        root,
        selected,
        budget_bytes=evidence.EVIDENCE_BUDGET_BYTES,
        env={"XDG_CACHE_HOME": str(cache)},
    ) as bibliography:
        canonical_keys = {
            item["id"] for item in json.loads(bibliography.read_text())
        }
        return _prepare(
            root,
            wiki_id,
            cache,
            scope=scope,
            max_evidence_chars=max_evidence_chars,
            candidates=candidates,
            collected=collected,
            canonical_keys=canonical_keys,
            reviews=reviews or {},
        )
