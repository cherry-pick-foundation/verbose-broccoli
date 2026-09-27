"""Offline request shapes, known-answer scoring, and the live probe's bounds."""

import asyncio
from copy import deepcopy
import hashlib
import importlib
import json
import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backfire.failures import JudgmentError
from backfire.validate import validate_request
from backfire_tools.acceptance import probe_limits as probe
from fake_provider import FakeProvider, completion


def test_maximum_shapes_and_obvious_answers_pass_adapter_schema(monkeypatch):
    expected_sizes = {
        "choice-150": (1, 150, 150), "choice-200": (1, 200, 200), "choice-250": (1, 250, 250),
        "backfire_find": (2, 250, 251), "backfire_classify": (64, 125, 8000),
        "backfire_rerank": (250, 1, 250), "backfire_noul": (64, 1, 64),
        "backfire_extract": (32, 21, 672), "backfire_gate": (21, 3, 61),
        "backfire_verify": (2000, 5, 8000), "backfire_compare": (11, 3, 33),
        "backfire_decide": (19, 9, 63),
    }
    monkeypatch.setenv("BACKFIRE_TEST_REQUEST_LIMITS", "250,8000")
    cases = probe.synthetic_cases()
    assert cases.keys() == expected_sizes.keys()
    for name, case in cases.items():
        assert tuple(probe.request_size(case["questions"]).values()) == expected_sizes[name]
        assert len(validate_request(case["questions"])) == len(case["expected"])
        for key, question in case["questions"].items():
            if question["type"] == "choice":
                assert question["criteria"][case["expected"][key]] == "A star"
                assert list(question["criteria"].values()).count("A star") == 1


def test_checksum_precedes_parsing_and_sample_preserves_evidence(tmp_path, monkeypatch):
    rows = [{"id": f"case-{i}", "state": f"evidence {i}", "expected": "yes",
             "question": {"type": "noul", "instructions": "Is it true?"}}
            for i in range(111)]
    data = b"\n".join(json.dumps(row).encode() for row in rows)
    path = tmp_path / "hard.jsonl"
    path.write_bytes(data)
    with pytest.raises(ValueError, match="checksum mismatch"):
        probe.load_hard(path)
    monkeypatch.setattr(probe, "HARD_SHA256", hashlib.sha256(data).hexdigest())
    original = deepcopy(rows)
    cases = probe.hard_cases(probe.load_hard(path))
    assert rows == original
    assert cases == probe.hard_cases(rows)
    largest = cases["hard-16"]
    for size in (4, 8, 16):
        assert list(cases[f"hard-{size}"]["questions"]) == list(largest["questions"])[:size]
    for index, (key, question) in enumerate(largest["questions"].items()):
        single = cases[f"single-{index + 1}"]
        assert single["state"] == {key: largest["state"][key]}
        assert single["questions"] == {key: question}
        source = next(row for row in rows if row["id"] == key)
        assert single["state"][key] == source["state"]
        assert question["instructions"] == f"Use only state[{key!r}] as evidence for this question.\n" + source["question"]["instructions"]
        assert "expected" not in json.dumps(question)
        validate_request(single["questions"])
    scheduled = []

    async def no_billing(cases):
        scheduled.extend(cases)
        return 0

    monkeypatch.setattr(probe, "run_cases", no_billing)
    assert probe.main(["--hard-tier", str(path)]) == 0
    assert "hard-16" not in scheduled and "hard-8" in scheduled and "single-16" in scheduled
    with pytest.raises(SystemExit) as caught:
        probe.main(["--hard-tier", str(path), "--case", "hard-16"])
    assert caught.value.code == 2


def test_scoring_keeps_wrong_invalid_and_ties_separate():
    result = probe.score_answers({
        "choice": {"type": "choice", "probabilities": {"a": 0.1, "b": 0.9}},
        "score": {"type": "score", "probabilities": {"0": 0, "1": 0.2, "2": 0.8}},
        "tie": {"type": "choice", "probabilities": {"a": 0.5, "b": 0.5}},
        "yes": {"type": "noul", "noul": 0.8},
        "no": {"type": "noul", "noul": 0.1},
        "uncertain": {"type": "noul", "noul": 0.5},
    }, {"choice": "b", "score": 1, "tie": "a", "yes": "yes", "no": "no", "uncertain": "no", "missing": "yes"})
    assert result == {"correct": 3, "wrong": 3, "invalid": 1, "wrong_ids": ["score", "tie", "uncertain"]}


@pytest.mark.parametrize("failure", [None, "wrong", "invalid_distribution", "provider_error", "rate_limited", "retried"])
def test_three_runs_or_stop_without_retry_and_restore_override(monkeypatch, capsys, failure):
    case = probe.synthetic_cases()["choice-200"]
    calls = []
    monkeypatch.setenv("BACKFIRE_TEST_REQUEST_LIMITS", "2,3")

    async def fake(state, questions, *, deadline):
        calls.append(questions)
        assert 117 < deadline - asyncio.get_running_loop().time() <= 118
        assert os.environ["BACKFIRE_TEST_REQUEST_LIMITS"] == "200,200"
        validate_request(questions)
        if failure not in (None, "wrong", "retried"):
            raise JudgmentError(failure)
        target = "o0" if failure == "wrong" else case["expected"]["q0"]
        return {"model": "synthetic-model", "usage": {}, "metadata": {"attempts": 2 if failure == "retried" else 1},
                "answers": {"q0": {"type": "choice", "probabilities": {
                    key: float(key == target) for key in questions["q0"]["criteria"]}}}}

    monkeypatch.setattr(probe, "judge", fake)
    stopped = failure in ("provider_error", "rate_limited", "retried")
    assert asyncio.run(probe.run_cases({"choice-200": case})) == int(stopped)
    output = capsys.readouterr()
    rows = [json.loads(line) for line in output.out.splitlines()]
    assert len(calls) == (3 if failure is None else 1)
    assert len(rows) == (1 if stopped else 3)
    assert [row["run"] for row in rows] == list(range(1, len(rows) + 1))
    assert rows[0]["invalid"] == int(failure not in (None, "wrong", "retried"))
    if failure in ("wrong", "invalid_distribution"):
        assert all(row["skipped"] and row["latency_ms"] is None for row in rows[1:])
    assert os.environ["BACKFIRE_TEST_REQUEST_LIMITS"] == "2,3"
    assert bool(output.err) == stopped


def test_deadline_cancels_judge_and_external_cancellation_propagates(monkeypatch):
    cancelled = []

    async def stall(*args, **kwargs):
        try:
            await asyncio.Future()
        finally:
            cancelled.append(True)

    monkeypatch.setattr(probe, "judge", stall)
    monkeypatch.setattr(probe, "DEADLINE_SECONDS", 0.01)
    monkeypatch.delenv("BACKFIRE_TEST_REQUEST_LIMITS", raising=False)
    case = probe.synthetic_cases()["choice-150"]
    row = asyncio.run(probe.measure("deadline", case, 1))
    assert row["error"] == "deadline_exceeded" and row["invalid"] == 1 and not row["passed"]
    assert cancelled == [True] and "BACKFIRE_TEST_REQUEST_LIMITS" not in os.environ

    async def cancel():
        task = asyncio.create_task(probe.measure("cancel", case, 1))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    assert cancelled == [True, True] and "BACKFIRE_TEST_REQUEST_LIMITS" not in os.environ


def test_failed_size_skips_its_remaining_runs_but_continues_next_size(monkeypatch, capsys):
    calls = []
    case = {"questions": {"q": {"type": "noul"}}}

    async def fake(name, case, run):
        calls.append((name, run))
        return {"case": name, "run": run, "error": None, "passed": name == "later"}

    monkeypatch.setattr(probe, "measure", fake)
    assert asyncio.run(probe.run_cases({"failed": case, "later": case})) == 0
    assert calls == [("failed", 1), ("later", 1), ("later", 2), ("later", 3)]
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(rows) == 6
    assert [row["run"] for row in rows if row.get("skipped")] == [2, 3]
    calls.clear()
    assert asyncio.run(probe.run_cases({"later": case}, first_run=2)) == 0
    assert calls == [("later", 2), ("later", 3)]
    calls.clear()
    assert asyncio.run(probe.run_cases({"single-1": case})) == 0
    assert calls == [("single-1", 1)]


@pytest.mark.parametrize("seconds, passed", [(59, True), (61, False)])
def test_correct_answer_still_has_to_finish_within_sixty_seconds(monkeypatch, seconds, passed):
    case = {"state": "synthetic", "questions": {"q": {"type": "noul"}}, "expected": {"q": "yes"}}

    async def fake(*args, **kwargs):
        return {"model": "synthetic", "usage": {}, "metadata": {"attempts": 1},
                "answers": {"q": {"type": "noul", "noul": 1}}}

    async def run():
        started = asyncio.get_running_loop().time()
        clock = SimpleNamespace(time=Mock(side_effect=[started, started + seconds]))
        monkeypatch.setattr(probe.asyncio, "get_running_loop", lambda: clock)
        return await probe.measure("timing", case, 1)

    monkeypatch.setattr(probe, "judge", fake)
    row = asyncio.run(run())
    assert row["correct"] == 1 and row["latency_ms"] == seconds * 1000
    assert row["passed"] is passed


@pytest.mark.parametrize("invalid", [False, True])
def test_real_judge_validates_answers_without_a_record(monkeypatch, tmp_path, invalid):
    module = importlib.import_module("backfire.judge")
    case = probe.synthetic_cases()["choice-150"]
    probabilities = {key: float(key == case["expected"]["q0"]) * (0.5 if invalid else 1)
                     for key in case["questions"]["q0"]["criteria"]}
    with FakeProvider([completion({"q0": probabilities})]) as fake:
        monkeypatch.setattr(module, "load_profile", lambda: {
            "api": "openai", "base_url": fake.base_url, "model": "synthetic-model",
            "request": {"max_tokens": 1000}, "thinking": {"requested": "on", "token_path": "reasoning_tokens"},
        })
        monkeypatch.setattr(module, "load_credential", lambda profile: "synthetic-test-key")
        row = asyncio.run(probe.measure("choice-150", case, 1))
    assert row["invalid"] == int(invalid) and row["correct"] == int(not invalid)
    assert row["error"] == ("invalid_distribution" if invalid else None)
    assert len(fake.requests) == 1
    assert not (tmp_path / "state").exists()
