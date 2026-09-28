import ast
import json
from pathlib import Path

import jsonschema
import pytest

from conftest import REVISIONS, SOURCE_ID, add_revision, commit_instance, make_instance, tree_hash, update_regions
from wiki_consistency import evidence, requests, search
from wiki_consistency.instance import revisions


FIXTURES = Path(__file__).parent / "fixtures"
SCHEMAS = {
    name: json.loads((FIXTURES / f"{name}_input_schema.json").read_text(encoding="utf-8"))
    for name in ("backfire_verify", "backfire_find", "backfire_classify")
}


def _ready(tmp_path, *, commit=False, wiki_id="default"):
    instance, env = make_instance(tmp_path, commit=commit, wiki_id=wiki_id)
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, wiki_id, cache, revisions(instance))
    search.index(instance, wiki_id, cache, download=False)
    return instance, cache, env


def _prepare(instance, cache, *, scope="changed", max_evidence_chars=40000, candidates=3):
    return requests.prepare(
        instance, instance.name, cache, scope=scope,
        max_evidence_chars=max_evidence_chars, candidates=candidates,
    )


def _assert_schemas(result):
    for request in result["requests"]:
        jsonschema.validate(request["arguments"], SCHEMAS[request["tool"]])


def _evidence_units(result):
    return [unit for request in result["requests"] if request["kind"] == "evidence"
            for unit in request["units"]]


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
    return next(index for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
                if line == text)


def test_schema_fixtures_copy_backfire_verbatim():
    root = Path(__file__).resolve().parents[2]
    for name, schema in SCHEMAS.items():
        path = root / "backfire" / "src" / "backfire" / "tools" / f"{name.removeprefix('backfire_')}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == "INPUT_SCHEMA"
                                  for target in node.targets))
        assert schema == ast.literal_eval(assignment.value)


def test_changed_scope_uses_line_diff_and_classifies_added_units(tmp_path):
    instance, cache, _ = _ready(tmp_path, commit=True)
    page = instance / "wiki" / "concepts" / "alpha.md"
    page.write_text(page.read_text(encoding="utf-8").replace(
        "See [the source](../sources/source.md).", "The quadratic formula solves equations."),
        encoding="utf-8")
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache)

    alpha = [unit for unit in result["units"] if unit["page"] == "wiki/concepts/alpha.md"]
    assert len(alpha) == 1
    assert alpha[0]["kind"] == "paragraph"
    assert alpha[0]["added"] is True
    assert alpha[0]["outcome"] == "requested"
    classified = [unit for request in result["requests"] if request["kind"] == "classify"
                  for unit in request["units"]]
    assert alpha[0]["id"] in classified
    _assert_schemas(result)


def test_changed_page_request_can_use_unchanged_candidate_units(tmp_path):
    instance, env = make_instance(tmp_path)
    beta = instance / "wiki" / "concepts" / "beta.md"
    beta.write_text(
        f"---\ntitle: Beta\nsummary: A synthetic quadratic page.\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
        "# Beta\n\nQuadratic equations have roots.\n", encoding="utf-8")
    assert update_regions(instance) == []
    commit_instance(instance)
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    alpha.write_text(alpha.read_text(encoding="utf-8").replace(
        "See [the source](../sources/source.md).", "Quadratic equations have roots."),
        encoding="utf-8")
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache)

    alpha_unit = next(unit for unit in result["units"]
                      if unit["page"] == "wiki/concepts/alpha.md" and unit["kind"] == "paragraph")
    request = next(request for request in result["requests"]
                   if request["kind"] == "pages" and alpha_unit["id"] in request["units"])
    assert request["arguments"]["evidence"][0]["id"].startswith("wiki/concepts/beta.md:")


def test_changed_scope_includes_all_stale_page_units_and_latest_evidence(tmp_path):
    instance, cache, _ = _ready(tmp_path, commit=True)
    latest = "20260929T000000000000Z"
    add_revision(instance, latest, "A newer synthetic source revision.\n")
    assert update_regions(instance) == []
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache)

    alpha = [unit for unit in result["units"] if unit["page"] == "wiki/concepts/alpha.md"]
    assert {unit["kind"] for unit in alpha} == {"heading", "paragraph"}
    evidence_requests = [request for request in result["requests"]
                         if request["kind"] == "evidence" and alpha[0]["id"] in request["units"]]
    items = evidence_requests[0]["arguments"]["evidence"]
    assert [item["id"] for item in items] == [f"{SOURCE_ID}/{REVISIONS[-1]}", f"{SOURCE_ID}/{latest}"]
    assert "newer synthetic source revision" in items[1]["text"]


def test_changed_scope_without_head_selects_every_agent_unit(tmp_path):
    instance, cache, _ = _ready(tmp_path)

    result = _prepare(instance, cache)

    assert result["head"] is None
    assert result["units"]
    assert all(unit["outcome"] in {"requested", "unverifiable"} for unit in result["units"])
    assert all(unit["page"] not in {"wiki/index.md", "wiki/log.md"} for unit in result["units"])
    assert "Source `" not in json.dumps(result["requests"], ensure_ascii=False)
    assert "1 admitted." not in json.dumps(result["requests"], ensure_ascii=False)
    expected = {unit["id"] for unit in result["units"]}
    accounted = set(_evidence_units(result)) | {item["unit"] for item in result["unverifiable"]}
    assert accounted == expected
    _assert_schemas(result)


def test_large_evidence_uses_matching_converted_passages(tmp_path):
    instance, env = make_instance(tmp_path, commit=True)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    assert update_regions(instance) == []
    source = instance / "raw" / "files" / SOURCE_ID / REVISIONS[-1] / "data" / "document.txt"
    source.write_text("Unrelated background. " + "padding " * 30
                      + "\n\nThe quadratic formula has two roots.\n", encoding="utf-8")
    page = instance / "wiki" / "concepts" / "alpha.md"
    page.write_text(page.read_text(encoding="utf-8").replace(
        "See [the source](../sources/source.md).", "The quadratic formula has two roots."),
        encoding="utf-8")
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache, max_evidence_chars=60)

    request = next(request for request in result["requests"]
                   if request["kind"] == "evidence" and "quadratic formula" in request["arguments"]["claims"][0])
    passage = request["arguments"]["evidence"][0]
    assert passage["id"] == f"{SOURCE_ID}/{REVISIONS[-1]}#1"
    assert passage["text"].strip() == "The quadratic formula has two roots."
    assert len(passage["text"]) <= 60
    _assert_schemas(result)


def test_page_candidates_keep_best_search_rank_before_sorting(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    lexical = _add_candidate_page(instance, "aaa-lexical")
    vector = _add_candidate_page(instance, "zzz-vector")
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    target = next(unit for unit in requests._collect(instance, "changed")[2]
                  if unit["page"] == "wiki/concepts/alpha.md" and unit["kind"] == "paragraph")

    def stub_search(wiki_id, cache, queries):
        return [
            {"query": target["id"], "collection": "pages", "path": "concepts/alpha.md",
             "line": target["first_line"], "score": 0.0, "mode": "lex"},
            {"query": target["id"], "collection": "pages", "path": "concepts/aaa-lexical.md",
             "line": _line_of(lexical, "Synthetic candidate content."), "score": 10.0, "mode": "lex"},
            {"query": target["id"], "collection": "pages", "path": "concepts/zzz-vector.md",
             "line": _line_of(vector, "Synthetic candidate content."), "score": 0.01, "mode": "vec"},
        ]

    monkeypatch.setattr(requests.search, "search", stub_search)

    result = requests.prepare(instance, instance.name, cache, scope="changed",
                              max_evidence_chars=40000, candidates=1)

    request = next(request for request in result["requests"]
                   if request["kind"] == "pages" and target["id"] in request["units"])
    selected = request["arguments"]["evidence"]
    assert [item["id"] for item in selected] == [next(
        unit["id"] for unit in result["units"] if unit["page"] == "wiki/concepts/zzz-vector.md"
        and unit["kind"] == "paragraph"
    )]


def test_crossref_candidates_keep_best_search_rank_before_sorting(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    paths = [_add_candidate_page(instance, f"p{index:02}") for index in range(21)]
    best = _add_candidate_page(instance, "z-best")
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    hits = [
        {"query": "crossref:wiki/concepts/alpha.md", "collection": "pages",
         "path": f"concepts/{path.stem}.md", "line": _line_of(path, "Synthetic candidate content."),
         "score": float(21 - index), "mode": "lex"}
        for index, path in enumerate([best, *paths])
    ]
    monkeypatch.setattr(requests.search, "search", lambda wiki_id, cache, queries: hits)

    result = requests.prepare(instance, instance.name, cache, scope="lint",
                              max_evidence_chars=40000, candidates=3)

    alpha_units = {unit["id"] for unit in result["units"]
                   if unit["page"] == "wiki/concepts/alpha.md"}
    request = next(request for request in result["requests"]
                   if request["kind"] == "crossref" and alpha_units.intersection(request["units"]))
    selected = [item["id"] for item in request["arguments"]["candidates"]]
    assert len(selected) == 20
    assert "wiki/concepts/z-best.md" in selected
    assert "wiki/concepts/p19.md" not in selected
    assert selected == sorted(selected)


def test_passage_selection_uses_best_ranked_fitting_passage(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    latest = "20260929T000000000000Z"
    add_revision(instance, latest, "This oversized synthetic passage cannot fit this evidence budget.\n\n"
                 "Earlier matching synthetic passage.\n\nBest ranked passage.\n")
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    evidence.convert(instance, instance.name, cache, revisions(instance))
    target = next(unit for unit in requests._collect(instance, "changed")[2]
                  if unit["page"] == "wiki/concepts/alpha.md" and unit["kind"] == "paragraph")

    def stub_search(wiki_id, cache, queries):
        return [
            {"query": target["id"], "collection": "evidence", "path": f"{SOURCE_ID}/{latest}.md",
             "line": 1, "score": 100.0, "mode": "lex"},
            {"query": target["id"], "collection": "evidence", "path": f"{SOURCE_ID}/{latest}.md",
             "line": 3, "score": 100.0, "mode": "lex"},
            {"query": target["id"], "collection": "evidence", "path": f"{SOURCE_ID}/{latest}.md",
             "line": 5, "score": 0.01, "mode": "vec"},
        ]

    monkeypatch.setattr(requests.search, "search", stub_search)

    result = requests.prepare(instance, instance.name, cache, scope="changed",
                              max_evidence_chars=40, candidates=3)

    request = next(request for request in result["requests"]
                   if request["kind"] == "evidence" and target["id"] in request["units"])
    passage = request["arguments"]["evidence"][0]
    assert passage["text"].strip() == "Best ranked passage."


def test_overview_evidence_uses_linked_pages_and_path_ids(tmp_path):
    instance, cache, _ = _ready(tmp_path)

    result = _prepare(instance, cache)

    overview_units = [unit for unit in result["units"] if unit["page"] == "wiki/overview.md"]
    assert overview_units
    requests_for_overview = [request for request in result["requests"]
                             if request["kind"] == "evidence"
                             and overview_units[0]["id"] in request["units"]]
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

    overview_ids = {unit["id"] for unit in result["units"] if unit["page"] == "wiki/overview.md"}
    assert overview_ids
    assert {item["unit"] for item in result["unverifiable"] if item["unit"] in overview_ids} == overview_ids
    assert all(not item["sources"] for item in result["unverifiable"] if item["unit"] in overview_ids)


def test_unreadable_sources_are_listed_and_never_sent(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    source = instance / "raw" / "files" / SOURCE_ID / REVISIONS[-1] / "data" / "document.txt"
    source.rename(source.with_suffix(".hwp"))
    source.with_suffix(".hwp").write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache, scope="lint")

    alpha_ids = {unit["id"] for unit in result["units"]
                 if unit["page"] == "wiki/concepts/alpha.md"}
    unverifiable = [item for item in result["unverifiable"] if item["unit"] in alpha_ids]
    assert {item["unit"] for item in unverifiable} == alpha_ids
    assert all(item["sources"] == [f"{SOURCE_ID}/{REVISIONS[-1]}"] for item in unverifiable)
    assert not alpha_ids.intersection(
        unit for request in result["requests"] for unit in request["units"]
    )
    _assert_schemas(result)


def test_lint_scope_adds_crossrefs_only_with_two_unlinked_candidates(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    shared = "Synthetic quadratic formula roots"
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    alpha.write_text(alpha.read_text(encoding="utf-8").replace(
        "title: Alpha", "title: Quadratic").replace(
        "summary: A synthetic page.", f"summary: {shared}").replace(
            "See [the source](../sources/source.md).", f"{shared} describes a synthetic equation."),
        encoding="utf-8")
    for name in ("beta", "gamma"):
        (instance / "wiki" / "concepts" / f"{name}.md").write_text(
            f"---\ntitle: Quadratic\nsummary: {shared}\nsources:\n"
            f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
            f"# Quadratic\n\n{shared} describe a synthetic equation.\n",
            encoding="utf-8")
    (instance / "wiki" / "concepts" / "solo.md").write_text(
        f"---\ntitle: Solo\nsummary: Unique nebula observation\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n"
        "# Solo\n\nA unique nebula observation.\n", encoding="utf-8")
    search.index(instance, instance.name, cache, download=False)

    result = _prepare(instance, cache, scope="lint")

    expected_units = [unit["id"] for unit in result["units"]]
    accounted = _evidence_units(result) + [item["unit"] for item in result["unverifiable"]]
    assert sorted(accounted) == sorted(expected_units)
    crossrefs = [request for request in result["requests"] if request["kind"] == "crossref"]
    for name in ("alpha", "beta", "gamma"):
        page = f"wiki/concepts/{name}.md"
        unit = next(unit for unit in result["units"] if unit["page"] == page)
        request = next(request for request in crossrefs if unit["id"] in request["units"])
        paths = {candidate["id"] for candidate in request["arguments"]["candidates"]}
        assert len(paths) >= 2
        assert f"wiki/concepts/{({'alpha': 'beta', 'beta': 'alpha', 'gamma': 'alpha'}[name])}.md" in paths
        assert all("Synthetic quadratic formula roots" in candidate["text"]
                   for candidate in request["arguments"]["candidates"])
    solo = next(unit for unit in result["units"] if unit["page"] == "wiki/concepts/solo.md")
    assert all(solo["id"] not in request["units"] for request in crossrefs)
    assert result["calls"] == {
        "backfire_verify": sum(request["tool"] == "backfire_verify" for request in result["requests"]),
        "backfire_find": sum(request["tool"] == "backfire_find" for request in result["requests"]),
        "backfire_classify": sum(request["tool"] == "backfire_classify" for request in result["requests"]),
    }
    _assert_schemas(result)


def test_prepare_batches_verify_and_classify_with_deterministic_read_only_output(tmp_path, monkeypatch):
    instance, env = make_instance(tmp_path)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    body = "\n\n".join(f"Synthetic claim number {index} uses evidence." for index in range(230))
    page = instance / "wiki" / "concepts" / "many.md"
    page.write_text(
        f"---\ntitle: Many\nsummary: Many synthetic claims\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[-1]}\n---\n{body}\n",
        encoding="utf-8")
    assert update_regions(instance) == []
    evidence.convert(instance, instance.name, cache, revisions(instance))
    search.index(instance, instance.name, cache, download=False)
    monkeypatch.setattr(requests.search, "search", lambda wiki_id, cache, queries: [])
    before = tree_hash(instance), tree_hash(cache)

    first = _prepare(instance, cache)
    second = _prepare(instance, cache)

    assert json.dumps(first, ensure_ascii=False, sort_keys=True) == json.dumps(
        second, ensure_ascii=False, sort_keys=True)
    assert (tree_hash(instance), tree_hash(cache)) == before
    verify = [request for request in first["requests"] if request["kind"] == "evidence"]
    classify = [request for request in first["requests"] if request["kind"] == "classify"]
    assert len(verify) >= 2
    assert all(len(request["arguments"]["claims"]) * 3 <= 672 for request in verify)
    assert len(classify) >= 4
    assert all(len(request["arguments"]["items"]) <= 64 for request in classify)
    assert first["calls"] == {
        "backfire_verify": sum(request["tool"] == "backfire_verify" for request in first["requests"]),
        "backfire_find": sum(request["tool"] == "backfire_find" for request in first["requests"]),
        "backfire_classify": sum(request["tool"] == "backfire_classify" for request in first["requests"]),
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
