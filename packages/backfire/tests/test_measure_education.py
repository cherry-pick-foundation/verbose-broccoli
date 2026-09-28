"""Offline checks for the education measurement runner."""

import asyncio
import json
import os
from pathlib import Path
import tomllib

import pytest
from scripted_judge import ScriptedJudge

from backfire.lib import DECIDE_ESCAPE_HATCHES
from backfire.lib import ensure_unique_ids
from backfire_tools.acceptance import measure_education as measurement

USAGE = {"input_tokens": 2, "output_tokens": 1}
XDG_KEYS = (
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
    "XDG_CACHE_HOME",
)
VERDICTS = {
    "verified": "supports",
    "contradicted": "contradicts",
    "unsupported": "says_nothing",
}


def choice(choice_id, choices):
    return {
        "type": "choice",
        "choice": choice_id,
        "confidence": 1.0,
        "probabilities": {key: float(key == choice_id) for key in choices},
    }


def result_for(case, *, noul_value=None):
    arguments = case["arguments"]
    expected = case["expect"]["result"]
    answers = {}
    if case["tool"] == "backfire_classify":
        class_ids = [f"c{index}" for index in range(len(arguments["classes"]))]
        answers.update(
            {
                f"i{index}": choice("c0", class_ids)
                for index in range(len(arguments["items"]))
            }
        )
    elif case["tool"] == "backfire_verify":
        keys = list(VERDICTS.values())
        answers["relation_claim0"] = choice(
            VERDICTS[expected["results.0.verdict"]], keys
        )
    elif case["tool"] == "backfire_compare":
        relation = expected["overall.relation"]
        keys = ["same_fact", "contradicts", "different_facts"]
        answers["overall"] = choice(relation, keys)
        for index in range(len(arguments.get("aspects", []))):
            answers[f"aspect_{index}"] = choice(relation, keys)
    elif case["tool"] == "backfire_noul":
        label = expected["results.0.label"]
        value = (
            noul_value
            if noul_value is not None
            else {"likely": 0.99, "unlikely": 0.01, "uncertain": 0.5}[label]
        )
        answers["p_proposition0"] = {"type": "noul", "noul": value}
    elif case["tool"] == "backfire_find":
        ids = [
            item["id"]
            for item in ensure_unique_ids(arguments["candidates"], "candidate")[
                "items"
            ]
        ]
        answers["best"] = choice(expected["top.0.id"], ids)
        answers["exists"] = {"type": "noul", "noul": 0.99}
    elif case["tool"] == "backfire_rerank":
        candidates = arguments["candidates"]
        selected = expected["ranked.0.id"]
        for index, candidate in enumerate(candidates):
            answers[f"rel_{index}"] = {
                "type": "noul",
                "noul": float(candidate["id"] == selected),
            }
    elif case["tool"] == "backfire_decide":
        candidate_ids = [
            f"option_{index}" for index in range(len(arguments["candidates"]))
        ]
        selected = candidate_ids[
            [candidate["id"] for candidate in arguments["candidates"]].index(
                expected["recommendation.selected"]
            )
        ]
        answers["recommendation"] = choice(
            selected, candidate_ids + list(DECIDE_ESCAPE_HATCHES)
        )
    elif case["tool"] == "backfire_extract":
        answers["f0"] = choice("c0", ["c0", "none_of_them"])
    else:
        raise AssertionError(case["tool"])
    return {"model": "scripted-model", "answers": answers, "usage": USAGE}


def fake_operator_credential(tmp_path, monkeypatch):
    provider = tomllib.loads(
        measurement.SHIPPED_CONFIG.read_text(encoding="utf-8")
    )["provider"]
    xdg_config = tmp_path / "operator-config"
    credential = (
        xdg_config / "verbose-broccoli" / "backfire" / f"{provider}.env"
    )
    credential.parent.mkdir(parents=True)
    credential.write_text("HIVE_API_KEY=synthetic-only\n", encoding="utf-8")
    credential.chmod(0o600)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config))
    return (
        credential,
        credential.read_bytes(),
        {key: os.environ.get(key) for key in XDG_KEYS},
    )


def check_temporary_config(credential):
    roots = {Path(os.environ[key]) for key in XDG_KEYS}
    assert len(roots) == 1
    root = roots.pop()
    link = root / "verbose-broccoli" / "backfire" / credential.name
    assert link.is_symlink()
    assert link.resolve() == credential
    assert link.read_bytes() == credential.read_bytes()
    config = tomllib.loads(
        (link.parent / "education.toml").read_text(encoding="utf-8")
    )
    assert config == {
        "roster": str(measurement.FIXTURES / "education-roster-v1.csv")
    }
    return root


def restore_environment(previous):
    for key, value in previous.items():
        assert os.environ.get(key) == value


def test_main_measures_all_cases_with_scripted_judge_and_links_key(
    tmp_path, monkeypatch, capsys
):
    credential, original_key, previous = fake_operator_credential(
        tmp_path, monkeypatch
    )
    cases = measurement.load_cases()
    scripted = ScriptedJudge(
        [{"result": result_for(case)} for case in cases for _ in range(2)]
    )
    flags, temporary_roots = [], set()

    async def scripted_judge(
        state,
        questions,
        *,
        deadline,
        record_file=None,
        pseudonymize: bool | None = None,
    ):
        flags.append(pseudonymize)
        temporary_roots.add(check_temporary_config(credential))
        return await scripted(
            state, questions, deadline=deadline, record_file=record_file
        )

    monkeypatch.setattr(measurement, "judge", scripted_judge)
    assert measurement.main(["--runs", "1"]) == 0

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    rows, summary = lines[:-1], lines[-1]["summary"]
    assert len(rows) == 2 * len(cases)
    assert all(row["correct"] and row["error_type"] is None for row in rows)
    assert flags == [False, True] * len(cases)
    assert len(scripted.requests) == 2 * len(cases)
    assert set(summary["accuracy"]) == {case["tool"] for case in cases}
    for arms in summary["accuracy"].values():
        assert arms == {
            "plain": {"correct": 3, "total": 3, "accuracy": 1.0},
            "pseudonymized": {"correct": 3, "total": 3, "accuracy": 1.0},
        }
    assert summary["differing_cases"] == []
    assert temporary_roots and all(
        not root.exists() for root in temporary_roots
    )
    assert credential.read_bytes() == original_key
    restore_environment(previous)


def test_failed_calls_count_wrong_and_differing_cases_are_listed(
    monkeypatch, capsys
):
    by_id = {case["id"]: case for case in measurement.load_cases()}
    cases = [
        by_id[case_id]
        for case_id in (
            "noul-claim-supported",
            "verify-progress-claim-supported",
        )
    ]
    scripted = ScriptedJudge(
        [
            {"result": result_for(cases[0])},
            {"result": result_for(cases[0], noul_value=0.6)},
            {"result": result_for(cases[1])},
            {"error": "synthetic scripted provider failure"},
        ]
    )
    flags = []

    async def scripted_judge(
        state,
        questions,
        *,
        deadline,
        record_file=None,
        pseudonymize: bool | None = None,
    ):
        flags.append(pseudonymize)
        return await scripted(
            state, questions, deadline=deadline, record_file=record_file
        )

    monkeypatch.setattr(measurement, "judge", scripted_judge)
    asyncio.run(measurement.run_cases(cases, 1))

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    rows, summary = lines[:-1], lines[-1]["summary"]
    assert [row["correct"] for row in rows] == [True, False, True, False]
    assert rows[-1]["error_type"] == "RuntimeError"
    assert flags == [False, True, False, True]
    assert summary["accuracy"]["backfire_noul"] == {
        "plain": {"correct": 1, "total": 1, "accuracy": 1.0},
        "pseudonymized": {"correct": 0, "total": 1, "accuracy": 0.0},
    }
    assert summary["accuracy"]["backfire_verify"]["pseudonymized"] == {
        "correct": 0,
        "total": 1,
        "accuracy": 0.0,
    }
    assert summary["differing_cases"] == [
        "noul-claim-supported",
        "verify-progress-claim-supported",
    ]


@pytest.mark.parametrize("interruption", [False, True])
def test_main_removes_temporary_directory_after_failure_or_interruption(
    tmp_path,
    monkeypatch,
    interruption,
):
    credential, original_key, previous = fake_operator_credential(
        tmp_path, monkeypatch
    )
    temporary_roots = set()

    async def stop(cases, runs):
        del cases, runs  # Unused.
        temporary_roots.add(check_temporary_config(credential))
        if interruption:
            raise KeyboardInterrupt
        raise RuntimeError("synthetic runner failure")

    monkeypatch.setattr(measurement, "run_cases", stop)
    failure = KeyboardInterrupt if interruption else RuntimeError
    with pytest.raises(failure):
        measurement.main(["--runs", "1"])

    assert temporary_roots and all(
        not root.exists() for root in temporary_roots
    )
    assert credential.read_bytes() == original_key
    restore_environment(previous)
