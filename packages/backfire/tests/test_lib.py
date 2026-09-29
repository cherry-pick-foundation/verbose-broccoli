"""Behavior checks adapted from the pinned upstream helpers and unit tests."""

import asyncio
from copy import deepcopy
import random
import re
import time

import pytest
from scripted_judge import ScriptedJudge

from backfire import lib
from backfire.judge import Judge


def original_ensure_unique_ids(items, fallback_prefix):
    """The original quadratic src/lib.ts algorithm, translated literally."""
    used = set()
    renamed = {}
    out = []
    for index, item in enumerate(items):
        raw = item.get("id") or ""
        cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_")
        base = cleaned[:64] or f"{fallback_prefix}{index}"
        identifier = base
        suffix = 1
        while identifier in used:
            identifier = f"{base}_{suffix}"
            suffix += 1
        used.add(identifier)
        if raw and raw != identifier:
            renamed[raw] = identifier
        out.append({**item, "id": identifier})
    return {"items": out, "renamed": renamed}


def test_unique_ids_match_original_and_preserve_inputs():
    randomizer = random.Random(69)
    identifiers = [
        None,
        "",
        "?",
        "한글",
        "x",
        "x_1",
        "x_2",
        "x_1_1",
        "x?",
        "x!",
        "x" * 65,
        "item0",
        "__a__",
    ]
    batches = [
        [],
        [{"id": "x"}] * 100,
        [
            {"id": "x_1"},
            {"id": "x"},
            {"id": "x"},
            {"id": "x_2"},
            {"id": "x"},
            {"id": "x_1"},
            {},
            {"id": "item6"},
        ],
    ]
    batches.extend(
        [
            {"id": randomizer.choice(identifiers), "text": str(index)}
            for index in range(100)
        ]
        for _ in range(50)
    )
    for items in batches:
        before = deepcopy(items)
        assert lib.ensure_unique_ids(
            items, "item"
        ) == original_ensure_unique_ids(items, "item")
        assert items == before


def test_unique_ids_100000_shared_ids_within_one_second():
    items = [{"id": "same", "text": "value"}] * 100_000
    started = time.perf_counter()
    result = lib.ensure_unique_ids(items, "item")
    elapsed = time.perf_counter() - started
    assert elapsed < 1, f"100,000 duplicate IDs took {elapsed:.3f}s"
    assert len({item["id"] for item in result["items"]}) == 100_000
    assert result["items"][0]["id"] == "same"
    assert result["items"][-1]["id"] == "same_99999"
    assert result["renamed"] == {"same": "same_99999"}


@pytest.mark.parametrize(
    "value, expected",
    [
        ("src/lib.ts", "src_lib.ts"),
        ("note: hello?!", "note_hello"),
        ("???", ""),
        ("a" * 100, "a" * 64),
        ("_-._", "-."),
    ],
)
def test_sanitize_id(value, expected):
    assert lib.sanitize_id(value) == expected


def test_records_and_truncation():
    assert lib.is_record({}) and lib.is_record({"answers": {}})
    assert not any(
        lib.is_record(value) for value in [None, [], "answers", 0, lambda: None]
    )
    assert lib.truncate("abc", 3) == "abc"
    assert lib.truncate("abcdef", 3) == "abc […truncated]"
    assert lib.truncate("가나다", 2) == "가나 […truncated]"
    assert lib.truncate("😀x", 2) == "😀 […truncated]"
    assert lib.truncate("😀", 1) == "\ud83d […truncated]"


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        (
            {"injection": 0.9},
            {
                "action": "block",
                "reason": "injection probability 0.90 >= block threshold 0.75",
            },
        ),
        (
            {"injection": 0.4},
            {
                "action": "review",
                "reason": "injection probability 0.40 >= review threshold 0.25",
            },
        ),
        (
            {"injection": 0.01},
            {"action": "pass", "reason": "no signals above thresholds"},
        ),
        (
            {"injection": 0.01, "substance": 0.1, "relevance": 0},
            {
                "action": "skip",
                "reason": "little substantive content (substance 0.10)",
            },
        ),
        (
            {"injection": 0.01, "relevance": 0.05},
            {
                "action": "skip",
                "reason": "not relevant to the stated purpose (relevance 0.05)",
            },
        ),
        (
            {"injection": 1.0, "block_at": 1.0},
            {
                "action": "block",
                "reason": "injection probability 1.00 >= block threshold 1",
            },
        ),
        (
            {"injection": 0.125, "review_at": 0.125},
            {
                "action": "review",
                "reason": (
                    "injection probability 0.13 >= review threshold 0.125"
                ),
            },
        ),
        (
            {"injection": -0.0, "review_at": 0.0},
            {
                "action": "review",
                "reason": "injection probability 0.00 >= review threshold 0",
            },
        ),
        (
            {"injection": 0.01, "substance": 0.3, "relevance": 0.3},
            {"action": "pass", "reason": "no signals above thresholds"},
        ),
    ],
)
def test_screen_recommendation(kwargs, expected):
    assert (
        lib.screen_recommendation(
            **{"block_at": 0.75, "review_at": 0.25, **kwargs}
        )
        == expected
    )


def test_verification_classification_and_ranking():
    assert lib.RELATION_TO_VERDICT == {
        "supports": "verified",
        "contradicts": "contradicted",
        "says_nothing": "unsupported",
    }
    assert [lib.verify_action(value, 0.8) for value in (0.8, 0.79, 0.99)] == [
        "auto",
        "review",
        "auto",
    ]
    assert [lib.exists_verdict(value) for value in (0.7, 0.35, 0.34)] == [
        "answered",
        "partial",
        "absent",
    ]
    assert lib.exists_verdict(0.6, 0.6, 0.1) == "answered"
    for top, margin, expected in [
        (0.9, 0.6, "auto"),
        (0.9, 0.4, "review"),
        (0.8, 0.8, "review"),
        (0.85, 0.5, "auto"),
    ]:
        assert lib.classification_decision(top, margin, 0.85, 0.5) == expected
    candidates = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
    before = deepcopy(candidates)
    assert lib.rank_candidates(candidates, {"a": 0.1, "b": 0.5, "c": 0.1}) == [
        {"id": "b", "probability": 0.5},
        {"id": "a", "probability": 0.1},
        {"id": "c", "probability": 0.1},
        {"id": "d", "probability": 0},
    ]
    assert lib.rerank_by_score(candidates, [0.2, 0.9, 0.2]) == [
        {"id": "b", "relevance": 0.9},
        {"id": "a", "relevance": 0.2},
        {"id": "c", "relevance": 0.2},
        {"id": "d", "relevance": 0},
    ]
    assert candidates == before
    assert lib.margin_of({"a": 0.7, "b": 0.2, "c": 0.1}) == pytest.approx(0.5)
    assert all(
        lib.margin_of(value) == 0
        for value in (None, {}, {"only": 0.8}, {"a": 0.5, "b": 0.5})
    )
    checks = [
        {"candidate": "a", "requirement": 0, "answer": "contradicted"},
        {"candidate": "a", "requirement": 1, "answer": "supported"},
        {"candidate": "b", "requirement": 2, "answer": "contradicted"},
    ]
    assert lib.contradicts_recommendation(checks, "a") == [0]
    assert lib.contradicts_recommendation(checks, "b") == [2]
    assert lib.contradicts_recommendation([], "a") == []


@pytest.mark.parametrize(
    "auto_accept, review_at",
    [
        (0.5, 0.8),
        (1.2, 0.5),
        (0.8, -0.1),
        (float("nan"), 0.5),
        (0.8, float("inf")),
        (True, 0.5),
    ],
)
def test_invalid_policy_thresholds(auto_accept, review_at):
    with pytest.raises(
        ValueError,
        match=r"^Thresholds must satisfy 0 <= review_at <= auto_accept <= 1\.$",
    ):
        lib.validate_policy_thresholds(auto_accept, review_at)


def test_review_policy_and_composite():
    assert lib.resolve_policy_thresholds() == {
        "auto_accept": 0.8,
        "review_at": 0.5,
    }
    assert lib.resolve_policy_thresholds(0.3) == {
        "auto_accept": 0.3,
        "review_at": 0.3,
    }
    assert lib.resolve_policy_thresholds(0.9, 0.6) == {
        "auto_accept": 0.9,
        "review_at": 0.6,
    }
    assert lib.resolve_policy_thresholds(0, 0) == {
        "auto_accept": 0,
        "review_at": 0,
    }
    with pytest.raises(ValueError):
        lib.resolve_policy_thresholds(0.5, 0.8)
    for scores, expected in [
        ((2, 2, 0, 0), 1),
        ((0, 0, 2, 2), 0),
        ((9, 3, -1, -5), 1),
        ((2, 0, 2, 2), 0.4),
    ]:
        assert lib.review_composite(
            **dict(
                zip(
                    ("correctness", "spec_match", "test_gap", "blast_radius"),
                    scores,
                )
            )
        ) == pytest.approx(expected)
    passing = {
        "composite": 0.9,
        "safe_to_apply": 0.95,
        "min_confidence": 0.9,
        "auto_accept": 0.8,
        "review_at": 0.5,
        "composite_floor": 0.7,
    }
    for overrides, expected in [
        ({}, "auto"),
        ({"composite": 0.5}, "review"),
        ({"composite_floor": 1}, "review"),
        ({"safe_to_apply": 0.4}, "escalate"),
        ({"min_confidence": 0.2}, "escalate"),
        ({"safe_to_apply": 0.6}, "review"),
        (
            {"min_confidence": None, "auto_accept": 0, "review_at": 0},
            "escalate",
        ),
    ]:
        assert lib.review_action(**{**passing, **overrides}) == expected
    for verdict, confidence, expected in [
        ("verified", 0.95, "auto"),
        ("verified", 0.6, "review"),
        ("verified", 0.3, "escalate"),
        ("contradicted", 0.95, "escalate"),
        ("contradicted", 0.6, "review"),
        ("unsupported", 0.95, "review"),
    ]:
        assert lib.claim_action(verdict, confidence, 0.8, 0.5) == expected
    assert lib.claim_action("verified", None, 0, 0) == "escalate"
    for actions, expected in [
        (["auto", "review"], "review"),
        (["review", "escalate"], "escalate"),
        (["auto"], "auto"),
        ([], "auto"),
    ]:
        assert lib.worst_action(actions) == expected
    for action in ("auto", "review", "escalate"):
        assert lib.require_complete_context(action, False) == action
        assert lib.require_complete_context(action, True) == (
            "review" if action == "auto" else action
        )


def test_evidence_shapes_and_js_whitespace():
    assert lib.normalize_evidence("text") == [
        {"id": "evidence", "text": "text"}
    ]
    assert lib.normalize_evidence({"text": "single"}) == [
        {"id": "evidence0", "text": "single"}
    ]
    assert lib.normalize_evidence(
        [{"id": "a", "text": "one"}, {"id": "a", "text": "two"}]
    ) == [
        {"id": "a", "text": "one"},
        {"id": "a_1", "text": "two"},
    ]
    assert not lib.has_non_empty_evidence([])
    assert not lib.has_non_empty_evidence(
        [{"id": "x", "text": " \n\t\ufeff\u2029"}]
    )
    assert lib.has_non_empty_evidence([{"id": "x", "text": "\u0085"}])
    assert lib.has_non_empty_evidence([{"id": "x", "text": "확인"}])


def test_upstream_limits_and_criteria():
    expected = {
        "MAX_CANDIDATES": 250,
        "MAX_CANDIDATE_CHARS": 2000,
        "MAX_CLASSES": 250,
        "MAX_ITEMS": 64,
        "MAX_ITEM_CHARS": 2000,
        "MAX_CANDIDATES_DECIDE": 6,
        "MAX_REQUIREMENTS": 3,
        "MAX_RERANK_CANDIDATES": 250,
        "MAX_RERANK_TOTAL_CHARS": 100_000,
        "MAX_PROPOSITIONS": 64,
        "MAX_PROPOSITION_CHARS": 2000,
        "MAX_NOUL_TOTAL_CHARS": 150_000,
        "MAX_COMPARE_ASPECTS": 10,
        "MAX_EXTRACT_FIELDS": 32,
        "MAX_EXTRACT_CANDIDATES": 20,
        "MAX_EXTRACT_CANDIDATE_CHARS": 2000,
        "MAX_EXTRACT_TOTAL_CHARS": 50_000,
        "REGEX_TIMEOUT_MS": 1000,
        "MAX_GATE_CLAIMS": 16,
        "MAX_GATE_EVIDENCE_ITEMS": 16,
        "MAX_GATE_EVIDENCE_CHARS": 200_000,
        "MAX_REVIEW_DOC_CHARS": 50_000,
        "MAX_CLAIM_CHARS": 2000,
        "PROBABILITY_SUM_TOLERANCE": 0.01 + 1e-12,
        "SCORE_MEAN_TOLERANCE": 0.02 + 1e-12,
        "DEFAULT_COMPOSITE_FLOOR": 0.7,
    }
    assert {key: getattr(lib, key) for key in expected} == expected
    assert list(lib.DECIDE_ESCAPE_HATCHES) == [
        "ask_user",
        "investigate",
        "none",
    ]
    assert (
        list(lib.COMPARE_RELATIONS)
        == list(lib.ASPECT_RELATIONS)
        == ["same_fact", "contradicts", "different_facts"]
    )
    assert (
        "at least one does not address it"
        in lib.ASPECT_RELATIONS["different_facts"]
    )
    assert lib.VERIFY_CLAIM_CRITERIA == {
        "verified": "The evidence clearly supports the claim",
        "contradicted": "The evidence contradicts the claim",
        "unsupported": (
            "The evidence neither supports nor contradicts the claim"
        ),
    }


def test_scripted_judge_preserves_requests_answers_and_deadlines(tmp_path):
    async def exercise():
        responses = [
            {
                "model": "scripted-model",
                "answers": {"q": {"type": "noul", "noul": 0.5}},
                "usage": {"input_tokens": 1, "output_tokens": 2},
            },
            {
                "model": "scripted-model",
                "answers": {
                    "q": {
                        "type": "choice",
                        "choice": "a",
                        "confidence": 0.8,
                        "probabilities": {"a": 0.9, "b": 0.1},
                    }
                },
                "usage": {"input_tokens": 2, "output_tokens": 3},
            },
        ]
        stand_in = ScriptedJudge(responses)
        judge: Judge = stand_in
        deadline = asyncio.get_running_loop().time() + 118
        state = {"text": "synthetic"}
        questions = {"q": {"type": "noul", "instructions": "True?"}}
        record_file = tmp_path / "session.jsonl"
        assert (
            await judge(
                state, questions, deadline=deadline, record_file=record_file
            )
            == responses[0]
        )
        state["text"] = "changed"
        questions["q"]["instructions"] = "Changed?"
        assert stand_in.requests[0] == {
            "state": {"text": "synthetic"},
            "questions": {"q": {"type": "noul", "instructions": "True?"}},
            "deadline": deadline,
            "record_file": record_file,
        }
        direct_questions = {
            "q": {
                "type": "choice",
                "instructions": "Which?",
                "criteria": {"a": "First", "b": "Second"},
            }
        }
        assert (
            await judge(["direct"], direct_questions, deadline=deadline)
            == responses[1]
        )
        assert stand_in.requests[1]["record_file"] is None
        assert stand_in.requests[1]["state"] == ["direct"]
        with pytest.raises(AssertionError, match="no answer left"):
            await judge("empty script", questions, deadline=deadline)
        assert not record_file.exists()

    asyncio.run(exercise())
