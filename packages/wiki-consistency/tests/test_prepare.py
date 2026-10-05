from contextlib import asynccontextmanager
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

from conftest import REVISIONS
from conftest import SOURCE_ID
from conftest import add_revision
from conftest import commit_instance
from conftest import make_instance
from conftest import tree_hash
from conftest import update_regions
import jsonschema
import pytest
import yaml

from wiki_consistency import evidence
from wiki_consistency import instance as storage
from wiki_consistency import requests
from wiki_consistency import search

FIXTURES = Path(__file__).parent / "fixtures"
SCHEMAS = {
    name: json.loads(
        (FIXTURES / f"{name.replace('_', '-')}-input-schema.json").read_text()
    )
    for name in ("jev_verify", "jev_find", "jev_classify")
}
KEY = f"{SOURCE_ID}/{REVISIONS[-1]}"
BODY = (
    "First result [@" + KEY + ", p. 25]. Second result [@" + KEY + ", p. 26].\n"
)
TEXT = (
    "## Page 25 {#p-25}\nFirst result.\n\n"
    "## Page 26 {#p-26}\nSecond result.\n\n"
    "## Page 27 {#p-27}\nOUTSIDE-SENTINEL-4d9c.\n"
    "## Purpose {#sec-purpose}\nThe purpose holds.\n"
    "## Next section\nANOTHER-OUTSIDE-SENTINEL.\n"
)


def _retain(
    instance,
    revision=REVISIONS[-1],
    *,
    source_id=SOURCE_ID,
    body=TEXT,
    **overrides,
):
    record = next(
        item
        for item in storage.revisions(instance)[source_id]
        if item["revision"] == revision
    )
    _, digest, _ = evidence._raw_record(instance, record)
    metadata = {
        "source-id": source_id,
        "revision": revision,
        "sha256": digest,
        "converter": {"name": "synthetic", "version": "1"},
        "checked-against-original": False,
        "conversion-status": "extracted",
        **overrides,
    }
    path = instance / "text" / source_id / f"{revision}.qmd"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + body)
    return path


def _page(instance, body=BODY, *, name="alpha", sources=None):
    metadata = {
        "title": name.title(),
        "summary": "Synthetic evidence page.",
        "topics": ["Algebra"],
        "sources": sources or [{"id": SOURCE_ID, "revision": REVISIONS[-1]}],
    }
    path = instance / "wiki" / "concepts" / f"{name}.qmd"
    path.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + body)
    return path


def _ready(tmp_path, *, commit=False, wiki_id="work"):
    instance, env = make_instance(tmp_path, wiki_id=wiki_id)
    _page(instance)
    _retain(instance)
    assert update_regions(instance) == []
    if commit:
        _commit(instance)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    search.index(instance, wiki_id, cache, download=False)
    return instance, cache, env


def _commit(instance):
    commit_instance(instance)
    subprocess.run(
        ["git", "add", "text"], cwd=instance, check=True, capture_output=True
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=synthetic@example.invalid",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "synthetic retained evidence",
        ],
        cwd=instance,
        check=True,
        capture_output=True,
    )


def _prepare(
    instance,
    cache,
    *,
    scope="changed",
    max_evidence_chars=40000,
    candidates=3,
    reviews=None,
):
    return requests.prepare(
        instance,
        instance.name,
        cache,
        scope=scope,
        max_evidence_chars=max_evidence_chars,
        candidates=candidates,
        reviews=reviews,
    )


def _assert_schemas(result):
    for request in result["requests"]:
        jsonschema.validate(request["arguments"], SCHEMAS[request["tool"]])


def _evidence(result, page="wiki/concepts/alpha.qmd"):
    ids = {unit["id"] for unit in result["units"] if unit["page"] == page}
    return [
        r
        for r in result["requests"]
        if r["kind"] == "evidence" and ids.intersection(r["units"])
    ]


def _units(result, page="wiki/concepts/alpha.qmd"):
    return [unit for unit in result["units"] if unit["page"] == page]


def test_schema_fixtures_match_pinned_upstream_capture():
    # SHA-256 of sorted JSON schemas captured from @jkudish/jev-mcp 0.13.0.
    expected = {
        "jev_verify": (
            "772d715a0a13c7560836909588cf888046669ec4cda8bcdc1386df2581864e48"
        ),
        "jev_find": (
            "8a66c80477a60d46d7139f1547deb4ce5af5b38bbb0b66d025bf67125c48f525"
        ),
        "jev_classify": (
            "4ce6e0c1ec7b1f002dab541398f288ac973b2b153565fb9fb15b3f7e0f0e54ab"
        ),
    }
    for name, schema in SCHEMAS.items():
        jsonschema.Draft202012Validator.check_schema(schema)
        assert (
            hashlib.sha256(
                json.dumps(schema, sort_keys=True).encode()
            ).hexdigest()
            == expected[name]
        )


def test_two_sentences_receive_distinct_exact_spans_and_no_sentinel(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    before = tree_hash(instance)
    result = _prepare(instance, cache)
    found = _evidence(result)
    assert len(found) == 2
    assert [r["arguments"]["claims"][0] for r in found] == [
        BODY[: BODY.index("Second")],
        BODY[BODY.index("Second") :],
    ]
    assert [r["arguments"]["evidence"][0]["text"] for r in found] == [
        "First result.\n\n",
        "Second result.\n\n",
    ]
    assert "OUTSIDE-SENTINEL" not in json.dumps(found)
    for request in found:
        item = request["arguments"]["evidence"][0]
        span = result["evidence_spans"][item["id"]]
        assert span["source-id"] == SOURCE_ID
        assert span["revision"] == REVISIONS[-1]
        assert len(span["sha256"]) == len(span["extraction-sha256"]) == 64
        assert span["first_line"] <= span["last_line"]
        assert span["locator_ids"] in [["p-25"], ["p-26"]]
    assert tree_hash(instance) == before
    assert not list(cache.rglob("sources.json"))
    _assert_schemas(result)


def test_uncited_opening_is_reported_while_cited_ending_is_requested(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    _page(
        instance, "Uncited opening. Supported ending [@" + KEY + ", p. 25].\n"
    )
    result = _prepare(instance, cache)
    assert [unit["outcome"] for unit in _units(result)] == [
        "unverifiable",
        "requested",
    ]
    assert any(
        item["reason"] == "missing sentence citation"
        for item in result["unverifiable"]
    )
    assert [r["arguments"]["claims"] for r in _evidence(result)] == [
        ["Supported ending [@" + KEY + ", p. 25].\n"]
    ]


def test_range_section_and_multi_source_forms_resolve_exactly(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    other = "0199a0e2-7c1b-7d3e-9f00-000000000001"
    add_revision(instance, "r2", "synthetic second original", source_id=other)
    _retain(instance, "r2", source_id=other)
    _page(
        instance,
        "Range [@" + KEY + ", pp. 25-26; @" + other + "/r2, sec. purpose].\n",
        sources=[
            {"id": SOURCE_ID, "revision": REVISIONS[-1]},
            {"id": other, "revision": "r2"},
        ],
    )
    result = _prepare(instance, cache)
    found = _evidence(result)
    assert len(found) == 1
    texts = [item["text"] for item in found[0]["arguments"]["evidence"]]
    assert len(texts) == 2
    assert any(
        "First result." in text and "Second result." in text for text in texts
    )
    assert "The purpose holds.\n" in texts
    assert "SENTINEL" not in json.dumps(found)
    _assert_schemas(result)


@pytest.mark.parametrize(
    "change",
    [
        "absent",
        "hash",
        "revision",
        "source",
        "partial",
        "converter",
        "unknown-review",
        "missing-locator",
        "duplicate",
        "range-gap",
        "section-missing",
        "range-reversed",
    ],
)
def test_evidence_failures_never_broaden_or_guess(
    tmp_path, change, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    retained = instance / "text" / SOURCE_ID / f"{REVISIONS[-1]}.qmd"
    if change == "absent":
        retained.unlink()
    elif change == "hash":
        _retain(instance, sha256="0" * 64)
    elif change == "revision":
        retained.write_text(
            retained.read_text().replace(
                "revision: " + REVISIONS[-1], "revision: wrong"
            )
        )
    elif change == "source":
        _retain(instance, **{"source-id": "wrong"})
    elif change == "partial":
        _retain(instance, **{"conversion-status": "partial"})
    elif change == "converter":
        _retain(instance, converter={"name": None, "version": None})
    elif change == "unknown-review":
        _retain(instance, **{"checked-against-original": None})
    elif change == "missing-locator":
        _retain(
            instance, body="Unlocated full extraction with OUTSIDE-SENTINEL.\n"
        )
    elif change == "duplicate":
        _retain(instance, body=TEXT + "## Duplicate {#p-25}\nDuplicate.\n")
    elif change == "range-gap":
        _retain(instance, body=TEXT.replace("{#p-26}", "{#p-99}"))
        _page(instance, "Result [@" + KEY + ", pp. 25-26].\n")
    elif change == "section-missing":
        _page(instance, "Result [@" + KEY + ", sec. absent].\n")
    else:
        _page(instance, "Result [@" + KEY + ", pp. 26-25].\n")
    # Proves no search-based evidence fallback exists even when one is offered.
    monkeypatch.setattr(
        search, "search", lambda *unused_args, **unused_kwargs: []
    )
    result = _prepare(instance, cache)
    assert all(unit["outcome"] == "unverifiable" for unit in _units(result))
    assert not _evidence(result)
    assert "OUTSIDE-SENTINEL" not in json.dumps(result["requests"])


@pytest.mark.parametrize(
    "key",
    ["unknown/r1", SOURCE_ID + "/missing", SOURCE_ID + "/" + REVISIONS[0]],
)
def test_citations_require_exact_declared_bag_revisions(tmp_path, key):
    instance, cache, _ = _ready(tmp_path)
    _page(instance, f"Result [@{key}, p. 25].\n")
    result = _prepare(instance, cache)
    assert not _evidence(result)
    assert "declared bag revision" in result["unverifiable"][0]["reason"]


def test_stale_citation_selects_units_without_adding_latest_evidence(tmp_path):
    instance, cache, _ = _ready(tmp_path, commit=True)
    latest = "20261001T000000000000Z"
    add_revision(instance, latest, "Newer raw revision.")
    _retain(instance, latest, body="## Page 25 {#p-25}\nLATEST-SENTINEL.\n")
    result = _prepare(instance, cache)
    assert len(_units(result)) == 2
    assert _evidence(result)
    assert "LATEST-SENTINEL" not in json.dumps(result["requests"])
    assert all(
        span["revision"] == REVISIONS[-1]
        for span in result["evidence_spans"].values()
    )
    selected = requests.revisions_for_scope(instance, "changed")
    assert [item["revision"] for item in selected[SOURCE_ID]] == [REVISIONS[-1]]


def test_original_review_requires_actual_byte_bound_receipt(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    path = _retain(instance, **{"checked-against-original": True})
    result = _prepare(instance, cache)
    assert not _evidence(result)
    assert any(
        "review evidence" in item["reason"] for item in result["unverifiable"]
    )
    record = storage.revisions(instance)[SOURCE_ID][-1]
    receipt = {
        "sha256": evidence._raw_record(instance, record)[1],
        "extraction-sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "evidence": "/private/review/SYNTHETIC-RECEIPT-REFERENCE",
    }
    result = _prepare(instance, cache, reviews={KEY: receipt})
    assert _evidence(result)
    assert "SYNTHETIC-RECEIPT-REFERENCE" not in json.dumps(result)
    receipt["extraction-sha256"] = "0" * 64
    assert not _evidence(_prepare(instance, cache, reviews={KEY: receipt}))


@pytest.mark.parametrize(
    "change",
    [
        "page-metadata",
        "ancestor-added",
        "ancestor-deleted",
        "ancestor-changed",
        "retained-correction",
    ],
)
def test_changed_scope_invalidates_metadata_and_retained_evidence(
    tmp_path, change
):
    instance, cache, _ = _ready(tmp_path)
    default = instance / "wiki" / "_metadata.yml"
    if change in {"ancestor-deleted", "ancestor-changed"}:
        default.write_text("custom:\n  status: old\n")
    _commit(instance)
    assert _prepare(instance, cache)["units"] == []
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    before_body = storage.mask_front_matter(page.read_text())
    if change == "page-metadata":
        page.write_text(
            page.read_text().replace(
                "summary: Synthetic evidence page.",
                "summary: Corrected metadata.",
            )
        )
    elif change == "ancestor-deleted":
        default.unlink()
    elif change in {"ancestor-added", "ancestor-changed"}:
        default.write_text("custom:\n  status: corrected\n")
    else:
        retained = instance / "text" / SOURCE_ID / f"{REVISIONS[-1]}.qmd"
        retained.write_text(
            retained.read_text().replace(
                "First result.", "Corrected first result."
            )
        )
    result = _prepare(instance, cache)
    assert len(_units(result)) == 2
    assert all(not unit["added"] for unit in _units(result))
    assert storage.mask_front_matter(page.read_text()) == before_body
    if change == "retained-correction":
        assert "Corrected first result." in json.dumps(_evidence(result))


def test_head_metadata_uses_historical_ancestors_and_same_merge_helpers(
    tmp_path,
):
    instance, cache, _ = _ready(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    metadata, _ = storage._front_matter_mapping(page.read_text())
    metadata.pop("sources")
    page.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + BODY)
    default = instance / "wiki" / "_metadata.yml"
    default.write_text(
        yaml.safe_dump(
            {
                "sources": [{"id": SOURCE_ID, "revision": REVISIONS[-1]}],
                "custom": {"x": [1, 2], "y": 1},
            }
        )
    )
    _commit(instance)
    old_text = page.read_text()
    default.write_text(
        yaml.safe_dump(
            {
                "sources": [{"id": SOURCE_ID, "revision": REVISIONS[0]}],
                "custom": {"x": [3], "y": 2},
            }
        )
    )
    old, problems = requests._head_metadata(
        instance, "wiki/concepts/alpha.qmd", old_text
    )
    assert not problems
    assert old["sources"] == [{"id": SOURCE_ID, "revision": REVISIONS[-1]}]
    assert old["custom"] == {"x": [1, 2], "y": 1}
    result = _prepare(instance, cache)
    assert len(_units(result)) == 2
    assert all(unit["outcome"] == "unverifiable" for unit in _units(result))


def test_md_to_qmd_rename_uses_old_body_and_head_defaults(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    old = page.with_suffix(".md")
    page.rename(old)
    _commit(instance)
    old.rename(page)
    result = _prepare(instance, cache)
    assert _units(result) == []
    page.write_text(
        page.read_text().replace("First result", "Corrected first result")
    )
    result = _prepare(instance, cache)
    assert len(_units(result)) == 2


def test_overview_uses_linked_english_pages_and_log_catalog_stay_out(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    result = _prepare(instance, cache)
    found = _evidence(result, "wiki/overview.qmd")
    assert found
    assert all(
        r["arguments"]["evidence"][0]["id"] == "wiki/concepts/alpha.qmd"
        for r in found
    )
    assert all(r["arguments"]["evidence"][0]["text"] == BODY for r in found)
    assert all(
        unit["page"] not in {"wiki/index.qmd", "wiki/log.qmd"}
        for unit in result["units"]
    )
    payload = json.dumps(result["requests"])
    assert "1 admitted." not in payload
    assert "Source `" not in payload


def test_overview_without_links_is_unverifiable(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    (instance / "wiki" / "overview.qmd").write_text("No linked pages.\n")
    result = _prepare(instance, cache)
    assert all(
        unit["outcome"] == "unverifiable"
        for unit in _units(result, "wiki/overview.qmd")
    )


def test_bibliography_is_fresh_private_cache_and_never_reused_after_exit(
    tmp_path, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "wrong-cache"))
    paths, entries = [], []
    real = evidence.bibliography

    @contextmanager
    def record(*args, **kwargs):
        with real(*args, **kwargs) as path:
            paths.append(path)
            entries.append(json.loads(path.read_text()))
            assert path.stat().st_mode & 0o777 == 0o600
            assert path.is_relative_to(cache)
            yield path

    monkeypatch.setattr(evidence, "bibliography", record)
    first = _prepare(instance, cache)
    second = _prepare(instance, cache)
    assert first == second
    assert len(paths) >= 2 and len(set(paths)) == len(paths)
    assert all(not path.exists() for path in paths)
    assert all(entry["type"] == "document" for run in entries for entry in run)
    assert not (tmp_path / "wrong-cache").exists()


def test_keyword_only_preparation_never_searches_for_citation_evidence(
    tmp_path, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    captured = []
    real = search.search

    def record(wiki_id, root, queries, **kwargs):
        captured.extend(queries)
        return real(wiki_id, root, queries, **kwargs)

    monkeypatch.setattr(search, "search", record)
    result = _prepare(instance, cache)
    assert captured == []
    assert result["search"] == {
        "keyword": True,
        "semantic": False,
        "not_searched": ["crossref", "pages"],
    }
    assert _evidence(result)


def test_cross_page_candidates_remain_separate_and_rank_before_sorting(
    tmp_path, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    _page(instance, "Best candidate [@" + KEY + ", p. 26].\n", name="z-best")
    _page(instance, "Later candidate [@" + KEY + ", p. 26].\n", name="a-later")
    monkeypatch.setattr(search, "_model_is_cached", lambda *unused_args: True)

    def hits(unused_wiki_id, unused_cache, queries, **kwargs):
        kwargs["search_status"]["semantic"] = True
        return [
            {
                "query": query["id"],
                "path": f"concepts/{name}.qmd",
                "line": 10,
                "mode": "lex",
            }
            for query in queries
            if query["id"].startswith("pages:wiki/concepts/alpha")
            for name in ("z-best", "a-later")
        ]

    monkeypatch.setattr(search, "search", hits)
    result = _prepare(instance, cache, candidates=1)
    source_evidence = _evidence(result)
    assert source_evidence
    assert all(
        "candidate" not in json.dumps(r["arguments"]["evidence"]).lower()
        for r in source_evidence
    )
    candidate_requests = [r for r in result["requests"] if r["kind"] == "pages"]
    assert candidate_requests
    assert all(
        "z-best.qmd" in r["arguments"]["evidence"][0]["id"]
        for r in candidate_requests
    )
    _assert_schemas(result)


def test_lint_crossrefs_keep_two_unlinked_candidates_and_metadata_titles(
    tmp_path, monkeypatch
):
    instance, cache, _ = _ready(tmp_path)
    for name in ("beta", "gamma"):
        _page(instance, BODY, name=name)
    monkeypatch.setattr(search, "_model_is_cached", lambda *unused_args: True)

    def hits(unused_wiki_id, unused_cache, queries, **kwargs):
        kwargs["search_status"]["semantic"] = True
        return [
            {
                "query": query["id"],
                "path": f"concepts/{name}.qmd",
                "line": 10,
                "mode": "lex",
            }
            for query in queries
            if query["id"] == "crossref:wiki/concepts/alpha.qmd"
            for name in ("beta", "gamma")
        ]

    monkeypatch.setattr(search, "search", hits)
    result = _prepare(instance, cache, scope="lint")
    found = [r for r in result["requests"] if r["kind"] == "crossref"]
    assert len(found) == 1
    assert [item["id"] for item in found[0]["arguments"]["candidates"]] == [
        "wiki/concepts/beta.qmd",
        "wiki/concepts/gamma.qmd",
    ]
    assert found[0]["arguments"]["candidates"][0]["text"].startswith("Beta\n")
    _assert_schemas(result)


def test_deterministic_packing_keeps_exact_evidence_sets_and_claim_order(
    tmp_path,
):
    instance, cache, _ = _ready(tmp_path)
    body = "\n\n".join(
        f"Result {index:03} [@{KEY}, p. 25]." for index in range(230)
    )
    _page(instance, body)
    first = _prepare(instance, cache)
    second = _prepare(instance, cache)
    assert first == second
    found = _evidence(first)
    claims = [
        claim for request in found for claim in request["arguments"]["claims"]
    ]
    assert len(claims) == 230
    assert [int(claim.split()[1]) for claim in claims] == list(range(230))
    assert all(len(request["arguments"]["claims"]) <= 110 for request in found)
    assert all(
        sum(len(claim) for claim in request["arguments"]["claims"]) <= 12000
        for request in found
    )
    _assert_schemas(first)


def test_exact_evidence_budget_is_unverifiable_without_search_fallback(
    tmp_path,
):
    instance, cache, _ = _ready(tmp_path)
    _retain(instance, body="## Page 25 {#p-25}\n" + "padding " * 100 + "\n")
    result = _prepare(instance, cache, max_evidence_chars=32)
    assert not _evidence(result)
    assert any(
        "oversized located span" in item["reason"]
        for item in result["unverifiable"]
    )


def test_prepare_requires_correct_index_root_and_reports_absent_evidence(
    tmp_path,
):
    instance, cache, _ = _ready(tmp_path)
    other = tmp_path / "other-instance"
    shutil.copytree(instance, other, ignore=shutil.ignore_patterns(".git"))
    search.index(other, instance.name, cache, download=False)
    with pytest.raises(ValueError, match="prepare requires index"):
        _prepare(instance, cache)
    (cache / "qmd" / f"{instance.name}.sqlite").unlink()
    with pytest.raises(ValueError, match="prepare requires index"):
        _prepare(instance, cache)


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_evidence_chars", 0),
        ("max_evidence_chars", True),
        ("candidates", 0),
        ("reviews", []),
    ],
)
def test_prepare_validates_boundary_inputs(tmp_path, field, value):
    with pytest.raises(ValueError):
        _prepare(tmp_path, tmp_path / "cache", **{field: value})


def test_alternating_evidence_sets_preserve_claim_order(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    body = " ".join(
        [
            f"First [@{KEY}, p. 25].",
            f"Second [@{KEY}, p. 26].",
            f"Third [@{KEY}, p. 25].",
        ]
    )
    _page(instance, body)
    result = _prepare(instance, cache)
    found = _evidence(result)
    assert [
        claim.split()[0]
        for item in found
        for claim in item["arguments"]["claims"]
    ] == ["First", "Second", "Third"]
    assert len(found) == 3


def test_full_serialized_payload_is_measured_without_inventing_a_cap(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    _retain(instance, body="## Page 25 {#p-25}\n" + "café " * 5000 + "\n")
    _page(instance, BODY.replace("p. 26", "p. 25"))
    found = _evidence(_prepare(instance, cache))
    assert found
    serialized = json.dumps(
        found[0]["arguments"], ensure_ascii=False, sort_keys=True
    )
    assert len(serialized) > 12000
    assert len(serialized.encode("utf-8")) > len(serialized)
    assert (
        sum(len(item["text"]) for item in found[0]["arguments"]["evidence"])
        <= 40000
    )


def test_oversized_suggestion_items_fail_without_upstream_truncation(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    _page(instance, "Long " + "word " * 410 + f"[@{KEY}, p. 25].\n")
    with pytest.raises(
        ValueError, match="classification item exceeds exact text limit"
    ):
        _prepare(instance, cache)


def test_ambiguous_bags_and_changed_raw_hash_fail_explicitly(tmp_path):
    instance, cache, _ = _ready(tmp_path)
    bag = instance / "raw" / "files" / SOURCE_ID / REVISIONS[-1]
    duplicate = instance / "raw" / "notes" / SOURCE_ID / REVISIONS[-1]
    shutil.copytree(bag, duplicate)
    with pytest.raises(ValueError, match="ambiguous raw revision"):
        _prepare(instance, cache)
    shutil.rmtree(duplicate)
    (bag / "data" / "document.txt").write_text("Altered synthetic raw bytes.")
    with pytest.raises(ValueError, match="raw SHA-256 changed"):
        _prepare(instance, cache)


def test_retained_symlink_cannot_send_outside_sentinel(tmp_path, monkeypatch):
    instance, cache, _ = _ready(tmp_path)
    outside = tmp_path / "outside.qmd"
    outside.write_text("OUTSIDE-PRIVATE-SENTINEL-948f")
    retained = instance / "text" / SOURCE_ID / f"{REVISIONS[-1]}.qmd"
    retained.unlink()
    retained.symlink_to(outside)
    monkeypatch.setattr(
        search, "search", lambda *unused_args, **unused_kwargs: []
    )
    result = _prepare(instance, cache)
    assert not _evidence(result)
    assert "OUTSIDE-PRIVATE-SENTINEL" not in json.dumps(result)
    assert any("symlink" in item["reason"] for item in result["unverifiable"])
    assert outside.read_text() == "OUTSIDE-PRIVATE-SENTINEL-948f"


@pytest.mark.parametrize("pending", [False, True])
def test_prepare_status_and_candidate_queries_use_one_mcp_session(
    tmp_path, monkeypatch, pending
):

    instance, cache, _ = _ready(tmp_path)
    calls, servers = [], []
    monkeypatch.setattr(search, "_model_is_cached", lambda *unused_args: True)

    class Session:
        def __init__(self, *unused_args):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *unused_args):
            return None

        async def initialize(self):
            return None

        async def call_tool(self, name, arguments):
            calls.append((name, arguments))
            value = (
                {"needsEmbedding": 1 if pending else 0}
                if name == "status"
                else {"results": []}
            )
            return SimpleNamespace(is_error=False, structured_content=value)

    @asynccontextmanager
    async def stdio(server):
        servers.append(server)
        yield object(), object()

    monkeypatch.setattr(search, "ClientSession", Session)
    monkeypatch.setattr(search, "stdio_client", stdio)
    result = _prepare(instance, cache, scope="lint")
    assert len(servers) == 1
    assert [name for name, _ in calls].count("status") == 1
    assert result["search"]["semantic"] is not pending
    assert bool([name for name, _ in calls if name == "query"]) is not pending
    assert all(not args["rerank"] for name, args in calls if name == "query")
    assert _evidence(result)


@pytest.mark.parametrize("text", ["한국어 근거.", "가나 ㄴ."])
def test_exact_korean_evidence_is_preserved(tmp_path, text):
    instance, cache, _ = _ready(tmp_path)
    _retain(instance, body=f"## Page 25 {{#p-25}}\n{text}\n")
    claim = f"The original supports this result [@{KEY}, p. 25].\n"
    _page(instance, claim)
    result = _prepare(instance, cache)
    found = _evidence(result)
    assert [r["arguments"]["claims"] for r in found] == [[claim]]
    assert found[0]["arguments"]["evidence"][0]["text"] == text + "\n"
    _assert_schemas(result)


@pytest.mark.parametrize(
    "text, expected", [("가" * 2000, 2000), ("😀" * 1000, 2000)]
)
def test_exact_suggestion_limit_counts_utf16_units(text, expected):
    assert requests._text_units(text) == expected
    assert requests._text_units(text + "가") > 2000
