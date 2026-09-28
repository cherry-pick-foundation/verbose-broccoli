import ast
import json
import shutil
import sqlite3
from pathlib import Path

import jsonschema
import pytest

from conftest import (
    REVISIONS,
    SOURCE_ID,
    add_revision,
    commit_instance,
    make_instance,
    tree_hash,
    update_regions,
)
from wiki_consistency import evidence, requests, search
from wiki_consistency.instance import revisions


FIXTURES = Path(__file__).parent / "fixtures"
SCHEMAS = {
    name: json.loads(
        (FIXTURES / f"{name}_input_schema.json").read_text(encoding="utf-8")
    )
    for name in ("backfire_verify", "backfire_find", "backfire_classify")
}


def _ready(tmp_path, *, commit=False, wiki_id="work"):
    instance, env = make_instance(tmp_path, commit=commit, wiki_id=wiki_id)
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, wiki_id, cache, revisions(instance))
    search.index(instance, wiki_id, cache, download=False)
    return instance, cache, env


def _prepare(
    instance, cache, *, scope="changed", max_evidence_chars=40000, candidates=3
):
    return requests.prepare(
        instance,
        instance.name,
        cache,
        scope=scope,
        max_evidence_chars=max_evidence_chars,
        candidates=candidates,
    )


def _assert_schemas(result):
    for request in result["requests"]:
        jsonschema.validate(request["arguments"], SCHEMAS[request["tool"]])


def _evidence_units(result):
    return [
        unit
        for request in result["requests"]
        if request["kind"] == "evidence"
        for unit in request["units"]
    ]


def _add_candidate_page(instance, name):
    path = instance / "wiki" / "concepts" / f"{name}.md"
    path.write_text(
        f"---\ntitle: {name}\nsummary: Synthetic candidate {name}.\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
        f"# {name}\n\nSynthetic candidate content.\n",
        encoding="utf-8",
    )
    return path


def _line_of(path, text):
    return next(
        index
        for index, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        )
        if line == text
    )


def test_schema_fixtures_copy_backfire_verbatim():
    root = Path(__file__).resolve().parents[2]
    for name, schema in SCHEMAS.items():
        path = (
            root
            / "backfire"
            / "src"
            / "backfire"
            / "tools"
            / f"{name.removeprefix('backfire_')}.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assignment = next(
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "INPUT_SCHEMA"
                for target in node.targets
            )
        )
        assert schema == ast.literal_eval(assignment.value)


def test_changed_scope_uses_line_diff_and_classifies_added_units(tmp_path):
    instance, cache, _ = _ready(tmp_path, commit=True)
    page = instance / "wiki" / "concepts" / "alpha.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "See [the source](../sources/source.md).",
            "The quadratic formula solves equations.",
        ),
        encoding="utf-8",
    )
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache)

    alpha = [
        unit
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/alpha.md"
    ]
    assert len(alpha) == 1
    assert alpha[0]["kind"] == "paragraph"
    assert alpha[0]["added"] is True
    assert alpha[0]["outcome"] == "requested"
    classified = [
        unit
        for request in result["requests"]
        if request["kind"] == "classify"
        for unit in request["units"]
    ]
    assert alpha[0]["id"] in classified
    _assert_schemas(result)


def test_changed_page_request_can_use_unchanged_candidate_units(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    beta = instance / "wiki" / "concepts" / "beta.md"
    beta.write_text(
        f"---\ntitle: Beta\nsummary: A synthetic quadratic page.\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
        "# Beta\n\nQuadratic equations have roots.\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []
    commit_instance(instance)
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    alpha.write_text(
        alpha.read_text(encoding="utf-8").replace(
            "See [the source](../sources/source.md).",
            "Quadratic equations have roots.",
        ),
        encoding="utf-8",
    )
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    alpha_unit = next(
        unit
        for unit in requests._collect(instance, "changed")[2]
        if unit["page"] == "wiki/concepts/alpha.md"
        and unit["kind"] == "paragraph"
    )

    def semantic_search(wiki_id, cache, queries, **kwargs):
        page_query = next(
            query for query in queries if query["collection"] == "pages"
        )
        return [
            {
                "query": page_query["id"],
                "collection": "pages",
                "path": "concepts/beta.md",
                "line": _line_of(beta, "Quadratic equations have roots."),
                "score": 0.0,
                "mode": "vec",
            }
        ]

    monkeypatch.setattr(search, "semantic_ready", lambda wiki_id, cache: True)
    monkeypatch.setattr(requests.search, "search", semantic_search)

    result = _prepare(instance, cache)

    request = next(
        request
        for request in result["requests"]
        if request["kind"] == "pages" and alpha_unit["id"] in request["units"]
    )
    assert request["arguments"]["evidence"][0]["id"].startswith(
        "wiki/concepts/beta.md:"
    )


def test_changed_scope_includes_all_stale_page_units_and_latest_evidence(
    tmp_path,
):
    instance, cache, _ = _ready(tmp_path, commit=True)
    latest = "20260929T000000000000Z"
    add_revision(instance, latest, "A newer synthetic source revision.\n")
    assert update_regions(instance) == []
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache)

    alpha = [
        unit
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/alpha.md"
    ]
    assert {unit["kind"] for unit in alpha} == {"heading", "paragraph"}
    evidence_requests = [
        request
        for request in result["requests"]
        if request["kind"] == "evidence" and alpha[0]["id"] in request["units"]
    ]
    items = evidence_requests[0]["arguments"]["evidence"]
    assert [item["id"] for item in items] == [
        f"{SOURCE_ID}/{REVISIONS[-1]}",
        f"{SOURCE_ID}/{latest}",
    ]
    assert "newer synthetic source revision" in items[1]["text"]


def test_changed_scope_without_head_selects_every_agent_unit(tmp_path):
    instance, cache, _ = _ready(tmp_path)

    result = _prepare(instance, cache)

    assert result["head"] is None
    assert result["units"]
    assert all(
        unit["outcome"] in {"requested", "unverifiable"}
        for unit in result["units"]
    )
    assert all(
        unit["page"] not in {"wiki/index.md", "wiki/log.md"}
        for unit in result["units"]
    )
    assert "Source `" not in json.dumps(result["requests"], ensure_ascii=False)
    assert "1 admitted." not in json.dumps(
        result["requests"], ensure_ascii=False
    )
    expected = {unit["id"] for unit in result["units"]}
    accounted = set(_evidence_units(result)) | {
        item["unit"] for item in result["unverifiable"]
    }
    assert accounted == expected
    _assert_schemas(result)


def test_prepare_without_model_skips_pages_and_crossrefs_but_searches_evidence(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    source = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    source.write_text("Synthetic supporting evidence. " * 100, encoding="utf-8")
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    captured = []

    def capture_queries(wiki_id, cache, queries, **kwargs):
        captured.extend(queries)
        return []

    monkeypatch.setattr(requests.search, "search", capture_queries)

    result = _prepare(instance, cache, scope="lint", max_evidence_chars=32)

    assert any(query["collection"] == "evidence" for query in captured)
    assert all(query["collection"] == "evidence" for query in captured)
    assert result["search"] == {
        "keyword": True,
        "semantic": False,
        "not_searched": ["crossref", "pages"],
    }
    assert not any(
        request["kind"] in {"pages", "crossref"}
        for request in result["requests"]
    )


def test_prepare_with_cached_model_and_pending_embeddings_skips_semantic_queries(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    monkeypatch.setattr(search, "EMBED_MODEL", "hf:synthetic/pending.gguf")
    model_dir = cache / "qmd" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "pending.gguf").touch()
    captured = []

    def capture_queries(wiki_id, cache, queries, **kwargs):
        captured.extend(queries)
        return []

    monkeypatch.setattr(requests.search, "search", capture_queries)

    result = _prepare(instance, cache, scope="lint", max_evidence_chars=32)

    assert result["search"] == {
        "keyword": True,
        "semantic": False,
        "not_searched": ["crossref", "pages"],
    }
    assert all(query["collection"] == "evidence" for query in captured)
    assert any(request["kind"] == "evidence" for request in result["requests"])
    assert not any(
        request["kind"] in {"pages", "crossref"}
        for request in result["requests"]
    )


def test_large_evidence_uses_matching_converted_passages(tmp_path):
    instance, env = make_instance(tmp_path, commit=True)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    assert update_regions(instance) == []
    source = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    source.write_text(
        "Unrelated background. "
        + "padding " * 30
        + "\n\nThe quadratic formula has two roots.\n",
        encoding="utf-8",
    )
    page = instance / "wiki" / "concepts" / "alpha.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "See [the source](../sources/source.md).",
            "The quadratic formula has two roots.",
        ),
        encoding="utf-8",
    )
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache, max_evidence_chars=60)

    request = next(
        request
        for request in result["requests"]
        if request["kind"] == "evidence"
        and "quadratic formula" in request["arguments"]["claims"][0]
    )
    passage = request["arguments"]["evidence"][0]
    assert passage["id"] == f"{SOURCE_ID}/{REVISIONS[-1]}#1"
    assert passage["text"].strip() == "The quadratic formula has two roots."
    assert len(passage["text"]) <= 60
    _assert_schemas(result)


def test_page_candidates_keep_best_search_rank_before_sorting(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    lexical = _add_candidate_page(instance, "aaa-lexical")
    vector = _add_candidate_page(instance, "zzz-vector")
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    target = next(
        unit
        for unit in requests._collect(instance, "changed")[2]
        if unit["page"] == "wiki/concepts/alpha.md"
        and unit["kind"] == "paragraph"
    )
    monkeypatch.setattr(search, "semantic_ready", lambda wiki_id, cache: True)

    def stub_search(wiki_id, cache, queries, **kwargs):
        return [
            {
                "query": f"pages:{target['id']}",
                "collection": "pages",
                "path": "concepts/alpha.md",
                "line": target["first_line"],
                "score": 0.0,
                "mode": "lex",
            },
            {
                "query": f"pages:{target['id']}",
                "collection": "pages",
                "path": "concepts/aaa-lexical.md",
                "line": _line_of(lexical, "Synthetic candidate content."),
                "score": 10.0,
                "mode": "lex",
            },
            {
                "query": f"pages:{target['id']}",
                "collection": "pages",
                "path": "concepts/zzz-vector.md",
                "line": _line_of(vector, "Synthetic candidate content."),
                "score": 0.01,
                "mode": "vec",
            },
        ]

    monkeypatch.setattr(requests.search, "search", stub_search)

    result = requests.prepare(
        instance,
        instance.name,
        cache,
        scope="changed",
        max_evidence_chars=40000,
        candidates=1,
    )

    request = next(
        request
        for request in result["requests"]
        if request["kind"] == "pages" and target["id"] in request["units"]
    )
    selected = request["arguments"]["evidence"]
    assert [item["id"] for item in selected] == [
        next(
            unit["id"]
            for unit in result["units"]
            if unit["page"] == "wiki/concepts/zzz-vector.md"
            and unit["kind"] == "paragraph"
        )
    ]


def test_crossref_candidates_keep_best_search_rank_before_sorting(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    paths = [
        _add_candidate_page(instance, f"p{index:02}") for index in range(21)
    ]
    best = _add_candidate_page(instance, "z-best")
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    hits = [
        {
            "query": "crossref:wiki/concepts/alpha.md",
            "collection": "pages",
            "path": f"concepts/{path.stem}.md",
            "line": _line_of(path, "Synthetic candidate content."),
            "score": float(21 - index),
            "mode": "lex",
        }
        for index, path in enumerate([best, *paths])
    ]
    monkeypatch.setattr(search, "semantic_ready", lambda wiki_id, cache: True)
    monkeypatch.setattr(
        requests.search,
        "search",
        lambda wiki_id, cache, queries, **kwargs: hits,
    )

    result = requests.prepare(
        instance,
        instance.name,
        cache,
        scope="lint",
        max_evidence_chars=40000,
        candidates=3,
    )

    alpha_units = {
        unit["id"]
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/alpha.md"
    }
    request = next(
        request
        for request in result["requests"]
        if request["kind"] == "crossref"
        and alpha_units.intersection(request["units"])
    )
    selected = [item["id"] for item in request["arguments"]["candidates"]]
    assert len(selected) == 20
    assert "wiki/concepts/z-best.md" in selected
    assert "wiki/concepts/p19.md" not in selected
    assert selected == sorted(selected)


def test_passage_selection_uses_best_ranked_fitting_passage(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    latest = "20260929T000000000000Z"
    add_revision(
        instance,
        latest,
        "This oversized synthetic passage cannot fit this evidence budget.\n\n"
        "Earlier matching synthetic passage.\n\nBest ranked passage.\n",
    )
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    target = next(
        unit
        for unit in requests._collect(instance, "changed")[2]
        if unit["page"] == "wiki/concepts/alpha.md"
        and unit["kind"] == "paragraph"
    )

    def stub_search(wiki_id, cache, queries, **kwargs):
        return [
            {
                "query": f"evidence:{target['id']}",
                "collection": "evidence",
                "path": f"{SOURCE_ID}/{latest}.md",
                "line": 1,
                "score": 100.0,
                "mode": "lex",
            },
            {
                "query": f"evidence:{target['id']}",
                "collection": "evidence",
                "path": f"{SOURCE_ID}/{latest}.md",
                "line": 3,
                "score": 100.0,
                "mode": "lex",
            },
            {
                "query": f"evidence:{target['id']}",
                "collection": "evidence",
                "path": f"{SOURCE_ID}/{latest}.md",
                "line": 5,
                "score": 0.01,
                "mode": "vec",
            },
        ]

    monkeypatch.setattr(requests.search, "search", stub_search)

    result = requests.prepare(
        instance,
        instance.name,
        cache,
        scope="changed",
        max_evidence_chars=40,
        candidates=3,
    )

    request = next(
        request
        for request in result["requests"]
        if request["kind"] == "evidence" and target["id"] in request["units"]
    )
    passage = request["arguments"]["evidence"][0]
    assert passage["text"].strip() == "Best ranked passage."


def test_passage_selection_adds_more_ranked_passages_within_budget():
    passages = [
        "Oversized passage " + "padding " * 20,
        "Second ranked passage.",
        "Best ranked passage.",
    ]
    text = "\n\n".join(passages)
    job = {
        "texts": {(SOURCE_ID, "r1"): text},
        "units": [{"id": "unit", "text": "synthetic claim"}],
    }
    hits = [
        {
            "query": "evidence:unit",
            "path": f"{SOURCE_ID}/r1.md",
            "line": line,
            "mode": "lex",
        }
        for line in (1, 3, 5)
    ]

    groups, assigned = requests._passages_for_group(job, hits, 60)

    assert assigned == {"unit"}
    assert [item["text"].strip() for item in groups[0][1]] == [
        "Second ranked passage.",
        "Best ranked passage.",
    ]


def test_passage_groups_pack_units_at_249_evidence_items_without_loss():
    passages = [
        f"Synthetic evidence passage {index:03}." for index in range(250)
    ]
    text = "\n\n".join(passages)
    units = [
        {"id": f"unit-{index:03}", "text": f"synthetic claim {index}"}
        for index in range(250)
    ]
    job = {"texts": {(SOURCE_ID, "r1"): text}, "units": units}
    hits = [
        {
            "query": f"evidence:unit-{index:03}",
            "path": f"{SOURCE_ID}/r1.md",
            "line": index * 2 + 1,
            "mode": "lex",
        }
        for index in range(250)
    ]

    groups, assigned = requests._passages_for_group(job, hits, 20000)

    assert [len(evidence_items) for _, evidence_items in groups] == [249, 1]
    assert all(len(evidence_items) <= 249 for _, evidence_items in groups)
    grouped_units = [
        unit["id"] for group_units, _ in groups for unit in group_units
    ]
    assert grouped_units == [unit["id"] for unit in units]
    assert len(grouped_units) == len(set(grouped_units))
    assert assigned == {unit["id"] for unit in units}


def test_one_unit_keeps_its_249_best_ranked_passages():
    passages = [
        f"Synthetic evidence passage {index:03}." for index in range(250)
    ]
    text = "\n\n".join(passages)
    job = {
        "texts": {(SOURCE_ID, "r1"): text},
        "units": [{"id": "unit", "text": "synthetic claim"}],
    }
    hits = [
        {
            "query": "evidence:unit",
            "path": f"{SOURCE_ID}/r1.md",
            "line": index * 2 + 1,
            "mode": "lex",
        }
        for index in reversed(range(250))
    ]

    groups, assigned = requests._passages_for_group(job, hits, 20000)

    assert len(groups) == 1
    assert len(groups[0][1]) == 249
    assert [unit["id"] for unit in groups[0][0]] == ["unit"]
    assert assigned == {"unit"}
    assert "Synthetic evidence passage 000." not in [
        item["text"] for item in groups[0][1]
    ]
    assert "Synthetic evidence passage 249." in [
        item["text"] for item in groups[0][1]
    ]


def test_shared_passage_is_in_each_batch_that_uses_it():
    passages = ["Shared passage.", "Unique first passage."]
    passages.extend(f"Filler passage {index:03}." for index in range(247))
    passages.append("New passage for final unit.")
    text = "\n\n".join(passages)
    units = [
        {"id": f"unit-{index:03}", "text": f"synthetic claim {index}"}
        for index in range(1, 250)
    ]
    hits = [
        {
            "query": "evidence:unit-001",
            "path": f"{SOURCE_ID}/r1.md",
            "line": 1,
            "mode": "lex",
        },
        {
            "query": "evidence:unit-001",
            "path": f"{SOURCE_ID}/r1.md",
            "line": 3,
            "mode": "lex",
        },
    ]
    hits.extend(
        {
            "query": f"evidence:unit-{index:03}",
            "path": f"{SOURCE_ID}/r1.md",
            "line": index * 2 + 1,
            "mode": "lex",
        }
        for index in range(2, 249)
    )
    hits.extend(
        [
            {
                "query": "evidence:unit-249",
                "path": f"{SOURCE_ID}/r1.md",
                "line": 1,
                "mode": "lex",
            },
            {
                "query": "evidence:unit-249",
                "path": f"{SOURCE_ID}/r1.md",
                "line": 499,
                "mode": "lex",
            },
        ]
    )
    job = {"texts": {(SOURCE_ID, "r1"): text}, "units": units}

    groups, assigned = requests._passages_for_group(job, hits, 20000)

    assert [len(evidence_items) for _, evidence_items in groups] == [249, 2]
    assert [len(group_units) for group_units, _ in groups] == [248, 1]
    assert all(
        any(
            item["text"].strip() == "Shared passage." for item in evidence_items
        )
        for _, evidence_items in groups
    )
    assert assigned == {unit["id"] for unit in units}


def test_passage_search_splits_each_evidence_file_once(monkeypatch):
    job = {
        "texts": {(SOURCE_ID, "r1"): "First passage.\n\nSecond passage."},
        "units": [{"id": "unit", "text": "synthetic claim"}],
    }
    real_split = requests.split
    calls = []

    def count_split(*args, **kwargs):
        calls.append(args[0])
        return real_split(*args, **kwargs)

    monkeypatch.setattr(requests, "split", count_split)
    requests._passages_for_group(
        job,
        [
            {
                "query": "evidence:unit",
                "path": f"{SOURCE_ID}/r1.md",
                "line": 1,
                "mode": "lex",
            },
            {
                "query": "evidence:unit",
                "path": f"{SOURCE_ID}/r1.md",
                "line": 3,
                "mode": "lex",
            },
        ],
        100,
    )

    assert calls == [f"{SOURCE_ID}/r1.md"]


def test_collection_query_ids_keep_page_candidate_ranks_independent(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    lexical = _add_candidate_page(instance, "aaa-lexical")
    vector = _add_candidate_page(instance, "zzz-vector")
    source = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    source.write_text(
        "Oversized "
        + "padding " * 30
        + "\n\nFirst supporting passage.\n\nSecond supporting passage.\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    target = next(
        unit
        for unit in requests._collect(instance, "changed")[2]
        if unit["page"] == "wiki/concepts/alpha.md"
        and unit["kind"] == "paragraph"
    )
    captured = []
    monkeypatch.setattr(search, "semantic_ready", lambda wiki_id, cache: True)

    def stub_search(wiki_id, cache, queries, **kwargs):
        captured.extend(queries)
        evidence_id = f"evidence:{target['id']}"
        page_id = f"pages:{target['id']}"
        evidence_query = next(
            query for query in queries if query["id"] == evidence_id
        )
        page_query = next(query for query in queries if query["id"] == page_id)
        assert evidence_query["collection"] == "evidence"
        assert page_query["collection"] == "pages"
        return [
            {
                "query": query["id"],
                "collection": "evidence",
                "path": f"{SOURCE_ID}/{REVISIONS[-1]}.md",
                "line": line,
                "mode": "lex",
            }
            for query in queries
            if query["collection"] == "evidence"
            for line in (1, 3, 5)
        ] + [
            {
                "query": page_id,
                "collection": "pages",
                "path": "concepts/aaa-lexical.md",
                "line": _line_of(lexical, "Synthetic candidate content."),
                "mode": "lex",
            },
            {
                "query": page_id,
                "collection": "pages",
                "path": "concepts/zzz-vector.md",
                "line": _line_of(vector, "Synthetic candidate content."),
                "mode": "vec",
            },
        ]

    monkeypatch.setattr(requests.search, "search", stub_search)
    result = requests.prepare(
        instance,
        instance.name,
        cache,
        scope="changed",
        max_evidence_chars=100,
        candidates=1,
    )

    request = next(
        request
        for request in result["requests"]
        if request["kind"] == "pages" and target["id"] in request["units"]
    )
    expected = next(
        unit["id"]
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/aaa-lexical.md"
        and unit["kind"] == "paragraph"
    )
    assert request["arguments"]["evidence"][0]["id"] == expected
    assert any(query["id"] == f"evidence:{target['id']}" for query in captured)
    assert any(query["id"] == f"pages:{target['id']}" for query in captured)


def test_evidence_queries_cover_the_full_collection_limit(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    source = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    source.write_text(
        "Oversized " + "padding " * 30 + "\n\nCited supporting passage.\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    evidence_root = (
        cache
        / "wiki-evidence"
        / instance.name
        / f"markitdown-{evidence.CONVERTER_VERSION}"
    )
    decoys = evidence_root / "unrelated"
    decoys.mkdir(parents=True)
    for index in range(25):
        (decoys / f"decoy-{index:02}.md").write_text(
            f"Synthetic unrelated evidence {index}.\n", encoding="utf-8"
        )
    search.index(instance, instance.name, cache, download=False)
    document_count = sum(path.is_file() for path in evidence_root.rglob("*.md"))
    captured = []

    def stub_search(wiki_id, cache, queries, **kwargs):
        captured.extend(queries)
        return [
            {
                "query": query["id"],
                "collection": "evidence",
                "path": f"{SOURCE_ID}/{REVISIONS[-1]}.md",
                "line": 3,
                "mode": "lex",
            }
            for query in queries
            if query["collection"] == "evidence"
        ]

    monkeypatch.setattr(requests.search, "search", stub_search)
    requests.prepare(
        instance,
        instance.name,
        cache,
        scope="changed",
        max_evidence_chars=100,
        candidates=3,
    )

    evidence_queries = [
        query for query in captured if query["collection"] == "evidence"
    ]
    assert evidence_queries
    assert all(query["limit"] >= document_count for query in evidence_queries)


def test_evidence_query_limit_covers_qmd_embedding_chunks(
    tmp_path, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    index_path = cache / "qmd" / f"{instance.name}.sqlite"
    with sqlite3.connect(index_path) as database:
        content_hash = database.execute(
            "SELECT hash FROM documents WHERE collection = 'evidence' AND active = 1 LIMIT 1"
        ).fetchone()[0]
        database.executemany(
            "INSERT INTO content_vectors "
            "(hash, seq, pos, model, embed_fingerprint, total_chunks, embedded_at) "
            "VALUES (?, ?, 0, 'synthetic', 'synthetic', 50, 'synthetic')",
            [(content_hash, sequence) for sequence in range(50)],
        )
    database.close()
    captured = []

    def capture_search(wiki_id, cache_root, queries, **kwargs):
        captured.extend(queries)
        return []

    monkeypatch.setattr(requests.search, "search", capture_search)

    requests.prepare(
        instance,
        instance.name,
        cache,
        scope="changed",
        max_evidence_chars=1,
        candidates=3,
    )

    evidence_queries = [
        query for query in captured if query["collection"] == "evidence"
    ]
    assert evidence_queries
    assert all(query["limit"] >= 50 for query in evidence_queries)


def test_evidence_query_limit_includes_chunks_in_qmd_wal(tmp_path, monkeypatch):
    instance, cache, _ = _ready(tmp_path)
    index_path = cache / "qmd" / f"{instance.name}.sqlite"
    database = sqlite3.connect(index_path)
    database.execute("PRAGMA journal_mode = WAL")
    content_hash = database.execute(
        "SELECT hash FROM documents WHERE collection = 'evidence' AND active = 1 LIMIT 1"
    ).fetchone()[0]
    database.executemany(
        "INSERT INTO content_vectors "
        "(hash, seq, pos, model, embed_fingerprint, total_chunks, embedded_at) "
        "VALUES (?, ?, 0, 'synthetic', 'synthetic', 50, 'synthetic')",
        [(content_hash, sequence) for sequence in range(50)],
    )
    database.commit()
    captured = []
    monkeypatch.setattr(
        requests.search,
        "search",
        lambda wiki_id, cache_root, queries, **kwargs: (
            captured.extend(queries) or []
        ),
    )

    try:
        requests.prepare(
            instance,
            instance.name,
            cache,
            scope="changed",
            max_evidence_chars=1,
            candidates=3,
        )
    finally:
        database.close()

    evidence_queries = [
        query for query in captured if query["collection"] == "evidence"
    ]
    assert evidence_queries
    assert all(query["limit"] >= 50 for query in evidence_queries)


def test_evidence_search_is_limited_to_cited_files(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    source = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    source.write_text("Synthetic cited claim. " * 100, encoding="utf-8")
    page = instance / "wiki" / "concepts" / "alpha.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(
            "See [the source](../sources/source.md).", "Synthetic cited claim."
        ),
        encoding="utf-8",
    )
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    evidence_root = (
        cache
        / "wiki-evidence"
        / instance.name
        / f"markitdown-{evidence.CONVERTER_VERSION}"
    )
    decoy = evidence_root / "decoy" / "extra.md"
    decoy.parent.mkdir(parents=True)
    decoy.write_text("Synthetic cited claim. " * 100, encoding="utf-8")
    search.index(instance, instance.name, cache, download=False)
    captured = []
    real_search = search.search

    def capture_search(wiki_id, cache, queries, **kwargs):
        captured.extend(queries)
        return real_search(wiki_id, cache, queries, **kwargs)

    monkeypatch.setattr(requests.search, "search", capture_search)

    requests.prepare(
        instance,
        instance.name,
        cache,
        scope="changed",
        max_evidence_chars=10,
        candidates=3,
    )

    evidence_queries = [
        query for query in captured if query["collection"] == "evidence"
    ]
    cited_path = f"{SOURCE_ID}/{REVISIONS[-1]}.md"
    assert evidence_queries
    assert all(
        query["allowed_paths"] == [cited_path] for query in evidence_queries
    )
    hits = real_search(instance.name, cache, evidence_queries)
    assert hits
    assert {hit["path"] for hit in hits} == {cited_path}


def test_overview_evidence_uses_linked_pages_and_path_ids(tmp_path):
    instance, cache, _ = _ready(tmp_path)

    result = _prepare(instance, cache)

    overview_units = [
        unit for unit in result["units"] if unit["page"] == "wiki/overview.md"
    ]
    assert overview_units
    requests_for_overview = [
        request
        for request in result["requests"]
        if request["kind"] == "evidence"
        and overview_units[0]["id"] in request["units"]
    ]
    assert requests_for_overview
    evidence_items = requests_for_overview[0]["arguments"]["evidence"]
    assert [item["id"] for item in evidence_items] == ["wiki/concepts/alpha.md"]
    assert "# Alpha" in evidence_items[0]["text"]


def test_overview_without_links_is_unverifiable_with_no_sources(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    overview = instance / "wiki" / "overview.md"
    overview.write_text("# Overview\n\nNo linked pages.\n", encoding="utf-8")
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache)

    overview_ids = {
        unit["id"]
        for unit in result["units"]
        if unit["page"] == "wiki/overview.md"
    }
    assert overview_ids
    assert {
        item["unit"]
        for item in result["unverifiable"]
        if item["unit"] in overview_ids
    } == overview_ids
    assert all(
        not item["sources"]
        for item in result["unverifiable"]
        if item["unit"] in overview_ids
    )


def test_unreadable_sources_are_listed_and_never_sent(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    source = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    source.rename(source.with_suffix(".hwp"))
    source.with_suffix(".hwp").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache, scope="lint")

    alpha_ids = {
        unit["id"]
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/alpha.md"
    }
    unverifiable = [
        item for item in result["unverifiable"] if item["unit"] in alpha_ids
    ]
    assert {item["unit"] for item in unverifiable} == alpha_ids
    assert all(
        item["sources"] == [f"{SOURCE_ID}/{REVISIONS[-1]}"]
        for item in unverifiable
    )
    assert not alpha_ids.intersection(
        unit for request in result["requests"] for unit in request["units"]
    )
    _assert_schemas(result)


def test_lint_scope_adds_crossrefs_only_with_two_unlinked_candidates(
    tmp_path, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    shared = "Synthetic quadratic formula roots"
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    alpha.write_text(
        alpha.read_text(encoding="utf-8")
        .replace("title: Alpha", "title: Quadratic")
        .replace("summary: A synthetic page.", f"summary: {shared}")
        .replace(
            "See [the source](../sources/source.md).",
            f"{shared} describes a synthetic equation.",
        ),
        encoding="utf-8",
    )
    for name in ("beta", "gamma"):
        (instance / "wiki" / "concepts" / f"{name}.md").write_text(
            f"---\ntitle: Quadratic\nsummary: {shared}\nsources:\n"
            f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
            f"# Quadratic\n\n{shared} describe a synthetic equation.\n",
            encoding="utf-8",
        )
    (instance / "wiki" / "concepts" / "solo.md").write_text(
        f"---\ntitle: Solo\nsummary: Unique nebula observation\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
        "# Solo\n\nA unique nebula observation.\n",
        encoding="utf-8",
    )
    search.index(instance, instance.name, cache, download=False)

    def semantic_search(wiki_id, cache, queries, **kwargs):
        hits = []
        for query in queries:
            if not query["id"].startswith("crossref:"):
                continue
            page = query["id"].rsplit("/", 1)[-1].removesuffix(".md")
            if page == "solo":
                continue
            for candidate in ("alpha", "beta", "gamma"):
                if candidate != page:
                    hits.append(
                        {
                            "query": query["id"],
                            "collection": "pages",
                            "path": f"concepts/{candidate}.md",
                            "line": 1,
                            "score": 1.0,
                            "mode": "vec",
                        }
                    )
        return hits

    monkeypatch.setattr(search, "semantic_ready", lambda wiki_id, cache: True)
    monkeypatch.setattr(requests.search, "search", semantic_search)

    result = _prepare(instance, cache, scope="lint")

    assert result["search"] == {
        "keyword": True,
        "semantic": True,
        "not_searched": [],
    }
    expected_units = [unit["id"] for unit in result["units"]]
    accounted = _evidence_units(result) + [
        item["unit"] for item in result["unverifiable"]
    ]
    assert sorted(accounted) == sorted(expected_units)
    crossrefs = [
        request
        for request in result["requests"]
        if request["kind"] == "crossref"
    ]
    for name in ("alpha", "beta", "gamma"):
        page = f"wiki/concepts/{name}.md"
        unit = next(unit for unit in result["units"] if unit["page"] == page)
        request = next(
            request for request in crossrefs if unit["id"] in request["units"]
        )
        paths = {
            candidate["id"] for candidate in request["arguments"]["candidates"]
        }
        assert len(paths) >= 2
        assert (
            f"wiki/concepts/{ ({'alpha': 'beta', 'beta': 'alpha', 'gamma': 'alpha'}[name]) }.md"
            in paths
        )
        assert all(
            "Synthetic quadratic formula roots" in candidate["text"]
            for candidate in request["arguments"]["candidates"]
        )
    solo = next(
        unit
        for unit in result["units"]
        if unit["page"] == "wiki/concepts/solo.md"
    )
    assert all(solo["id"] not in request["units"] for request in crossrefs)
    assert result["calls"] == {
        "backfire_verify": sum(
            request["tool"] == "backfire_verify"
            for request in result["requests"]
        ),
        "backfire_find": sum(
            request["tool"] == "backfire_find" for request in result["requests"]
        ),
        "backfire_classify": sum(
            request["tool"] == "backfire_classify"
            for request in result["requests"]
        ),
    }
    _assert_schemas(result)


def test_prepare_batches_verify_and_classify_with_deterministic_read_only_output(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    body = "\n\n".join(
        f"Synthetic claim number {index} uses evidence." for index in range(230)
    )
    page = instance / "wiki" / "concepts" / "many.md"
    page.write_text(
        f"---\ntitle: Many\nsummary: Many synthetic claims\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n{body}\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    monkeypatch.setattr(
        requests.search, "search", lambda wiki_id, cache, queries, **kwargs: []
    )
    before = tree_hash(instance), tree_hash(cache)

    first = _prepare(instance, cache)
    second = _prepare(instance, cache)

    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True
    )
    assert (tree_hash(instance), tree_hash(cache)) == before
    verify = [
        request
        for request in first["requests"]
        if request["kind"] == "evidence"
    ]
    classify = [
        request
        for request in first["requests"]
        if request["kind"] == "classify"
    ]
    assert len(verify) >= 2
    assert all(
        len(request["arguments"]["claims"]) * 3 <= 672 for request in verify
    )
    assert len(classify) >= 4
    assert all(len(request["arguments"]["items"]) <= 64 for request in classify)
    assert first["calls"] == {
        "backfire_verify": sum(
            request["tool"] == "backfire_verify"
            for request in first["requests"]
        ),
        "backfire_find": sum(
            request["tool"] == "backfire_find" for request in first["requests"]
        ),
        "backfire_classify": sum(
            request["tool"] == "backfire_classify"
            for request in first["requests"]
        ),
    }
    _assert_schemas(first)


def test_prepare_names_missing_convert_and_index_steps(tmp_path):
    instance, env = make_instance(tmp_path)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    with pytest.raises(ValueError, match="convert"):
        _prepare(instance, cache)

    evidence.convert(instance, instance.name, cache, revisions(instance))
    with pytest.raises(ValueError, match="index"):
        _prepare(instance, cache)


def test_prepare_refuses_missing_index_when_model_is_cached(
    tmp_path, monkeypatch
):
    instance, env = make_instance(tmp_path)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    model_name = "synthetic-pending.gguf"
    model_dir = cache / "qmd" / "models"
    model_dir.mkdir(parents=True)
    (model_dir / model_name).touch()
    monkeypatch.setattr(search, "EMBED_MODEL", f"hf:synthetic/{model_name}")

    with pytest.raises(ValueError, match="prepare requires index"):
        _prepare(instance, cache)


def test_prepare_refuses_index_from_another_pages_root(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    old_instance = tmp_path / "old-instance"
    shutil.copytree(instance / "wiki", old_instance / "wiki")
    search.index(old_instance, instance.name, cache, download=False)

    with pytest.raises(ValueError, match="index"):
        _prepare(instance, cache)
