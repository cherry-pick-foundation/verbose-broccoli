"""Gate 3: up to three sequential judgments per size, with no judgment records.

Run with ``python -m backfire_tools.acceptance.probe_limits``. The public hard
tier is downloaded into a temporary directory, or read from --hard-tier after
the same checksum check. --case selects named cases when resuming an approved
run; the probe adds no retry layer. JSON lines contain counts and timing,
not prompts, credentials, provider errors, or reasoning text.
After a size fails once, its remaining runs are reported as skipped: it cannot
meet the requirement to pass all three runs.
Limits use the synthetic cases only. Hard-tier batches are quality guidance;
16-question batches are disabled and individual baselines run once.
"""

import argparse
import asyncio
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from backfire.failures import JudgmentError
from backfire.judge import judge

REVISION = "3749b4fc1b88e4f5f02a3c0b9766c4ffa57891c0"
HARD_URL = f"https://raw.githubusercontent.com/fstandhartinger/jevbench/{REVISION}/datasets/public/hard.jsonl"
HARD_SHA256 = "89e9e6becb33ed88c1de7d42dcc87531b2fb64cfaef4e1986faf7c37b3f80ebb"
DEADLINE_SECONDS = 118
QUALITY_FAILURES = {
    "truncated_output",
    "malformed_output",
    "invalid_distribution",
    "refused",
    "deadline_exceeded",
}


def load_hard(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != HARD_SHA256:
        raise ValueError("Public hard-tier checksum mismatch.")
    return [json.loads(line) for line in data.splitlines()]


def synthetic_cases():
    # Research's maximum-cell classification uses all 64 items and 125 classes.
    shapes = {
        **{f"choice-{size}": [("choice", size)] for size in (150, 200, 250)},
        "backfire_find": [("choice", 250), ("noul", 1)],
        "backfire_classify": [("choice", 125)] * 64,
        "backfire_rerank": [("noul", 1)] * 250,
        "backfire_noul": [("noul", 1)] * 64,
        "backfire_extract": [("choice", 21)] * 32,
        "backfire_gate": [("score", 3)] * 4
        + [("noul", 1)]
        + [("choice", 3)] * 16,
        # 1,000 claims: relation (3) + four evidence items and none (5) = 8,000.
        "backfire_verify": [("choice", 3), ("choice", 5)] * 1000,
        "backfire_compare": [("choice", 3)] * 11,
        "backfire_decide": [("choice", 9)] + [("choice", 3)] * 18,
    }
    cases = {}
    for name, shape in shapes.items():
        questions, expected = {}, {}
        for index, (kind, size) in enumerate(shape):
            key = f"q{index}"
            question = {"type": kind}
            if kind == "choice":
                target = f"o{(size // 2 + 17 * index) % size}"
                question.update(
                    instructions="Which option describes the Sun?",
                    criteria={
                        f"o{i}": "A star"
                        if f"o{i}" == target
                        else f"A kitchen utensil, catalog item {i}"
                        for i in range(size)
                    },
                )
            elif kind == "score":
                question.update(
                    instructions="How many moons does the synthetic planet have?",
                    criteria=["No moons", "One moon", "Two moons"],
                )
                target = "2"
            else:
                question["instructions"] = "The Sun is " + (
                    "a star." if index % 2 else "a kitchen utensil."
                )
                target = "yes" if index % 2 else "no"
            questions[key], expected[key] = question, target
        cases[name] = {
            "state": "The Sun is a star. The synthetic planet has exactly two moons.",
            "questions": questions,
            "expected": expected,
        }
    return cases


def hard_cases(rows):
    # Fixed before any answers: nested samples permit shared single-call baselines.
    selected = random.Random(36).sample(rows, 16)
    questions, expected, states = {}, {}, {}
    for row in selected:
        question = deepcopy(row["question"])
        question["instructions"] = (
            f"Use only state[{row['id']!r}] as evidence for this question.\n"
            + question.get("instructions", "")
        )
        questions[row["id"]], expected[row["id"]] = question, row["expected"]
        states[row["id"]] = row["state"]
    groups = {f"hard-{size}": list(questions)[:size] for size in (4, 8, 16)}
    groups.update(
        {f"single-{index + 1}": [key] for index, key in enumerate(questions)}
    )
    return {
        name: {
            "state": {key: states[key] for key in keys},
            "questions": {key: questions[key] for key in keys},
            "expected": {key: expected[key] for key in keys},
        }
        for name, keys in groups.items()
    }


def request_size(questions):
    options = [
        len(q["criteria"]) for q in questions.values() if q["type"] == "choice"
    ]
    cells = sum(
        1 if q["type"] == "noul" else len(q["criteria"])
        for q in questions.values()
    )
    return {
        "questions": len(questions),
        "options": max(options, default=1),
        "cells": cells,
    }


def score_answers(answers, expected):
    counts = {"correct": 0, "wrong": 0, "invalid": 0}
    wrong_ids = []
    for key, target in expected.items():
        answer = answers.get(key)
        if answer is None:
            counts["invalid"] += 1
            continue
        probabilities = (
            {"yes": answer["noul"], "no": 1 - answer["noul"]}
            if answer["type"] == "noul"
            else answer["probabilities"]
        )
        # A tie (including a uniform distribution) is not a known-answer pass.
        correct = probabilities[str(target)] > max(
            value
            for label, value in probabilities.items()
            if label != str(target)
        )
        counts["correct" if correct else "wrong"] += 1
        if not correct:
            wrong_ids.append(key)
    return {**counts, "wrong_ids": wrong_ids}


async def measure(name, case, run):
    size = request_size(case["questions"])
    previous = os.environ.get("BACKFIRE_TEST_REQUEST_LIMITS")
    os.environ["BACKFIRE_TEST_REQUEST_LIMITS"] = (
        f"{size['options']},{size['cells']}"
    )
    loop = asyncio.get_running_loop()
    started = loop.time()
    result, error = None, None
    try:
        deadline = started + DEADLINE_SECONDS
        async with asyncio.timeout_at(deadline):
            result = await judge(
                case["state"], case["questions"], deadline=deadline
            )
    except JudgmentError as failure:
        error = failure.error_type
    except TimeoutError:
        error = "deadline_exceeded"
    finally:
        if previous is None:
            os.environ.pop("BACKFIRE_TEST_REQUEST_LIMITS", None)
        else:
            os.environ["BACKFIRE_TEST_REQUEST_LIMITS"] = previous
    elapsed = (loop.time() - started) * 1000
    counts = score_answers(
        result["answers"] if result else {}, case["expected"]
    )
    row = {
        "case": name,
        "run": run,
        **size,
        **counts,
        "latency_ms": round(elapsed, 3),
        "error": error,
    }
    if result is not None:
        row.update(
            model=result["model"],
            usage=result["usage"],
            metadata=result["metadata"],
        )
    row["passed"] = counts["correct"] == size["questions"] and elapsed < 60_000
    return row


async def run_cases(cases, *, first_run=1):
    for name, case in cases.items():
        last_run = 1 if name.startswith("single-") else 3
        for run in range(first_run, last_run + 1):
            row = await measure(name, case, run)
            print(json.dumps(row), flush=True)
            if (
                row["error"] is not None
                and row["error"] not in QUALITY_FAILURES
            ) or row.get("metadata", {}).get("attempts", 0) > 1:
                print(
                    "Probe stopped; ask the coordinator before more billed requests.",
                    file=sys.stderr,
                )
                return 1
            if not row["passed"]:
                for skipped in range(run + 1, last_run + 1):
                    print(
                        json.dumps(
                            {
                                "case": name,
                                "run": skipped,
                                **request_size(case["questions"]),
                                "skipped": "Earlier run failed correctness, answer validation, or the 60-second bound.",
                                "correct": None,
                                "wrong": None,
                                "invalid": None,
                                "latency_ms": None,
                            }
                        ),
                        flush=True,
                    )
                break
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hard-tier",
        type=Path,
        help="Previously downloaded, checksum-pinned public hard tier.",
    )
    parser.add_argument(
        "--case", action="append", help="Run only this named case (repeatable)."
    )
    arguments = parser.parse_args(argv)
    with TemporaryDirectory(prefix="backfire-limits-") as temporary:
        path = arguments.hard_tier
        if path is None:
            path = Path(temporary) / "hard.jsonl"
            with urlopen(HARD_URL, timeout=30) as response:
                # The fixed download has a 4 MiB budget and is deleted on exit.
                data = response.read(4 * 1024 * 1024 + 1)
                if len(data) > 4 * 1024 * 1024:
                    raise ValueError(
                        "Public hard tier exceeds the download budget."
                    )
                path.write_bytes(data)
        hard = hard_cases(load_hard(path))
        cases = {
            **synthetic_cases(),
            **{name: case for name, case in hard.items() if name != "hard-16"},
        }
        if arguments.case:
            if set(arguments.case) - cases.keys():
                parser.error("Unknown probe case.")
            cases = {
                name: cases[name] for name in dict.fromkeys(arguments.case)
            }
        print(
            json.dumps(
                {
                    "hard_revision": REVISION,
                    "hard_sha256": HARD_SHA256,
                    "hard_ids": list(hard["hard-16"]["questions"]),
                    "cases": {
                        name: request_size(case["questions"])
                        for name, case in cases.items()
                    },
                    "runs_per_case": {
                        "synthetic": 3,
                        "hard_batch": 3,
                        "single": 1,
                    },
                    "disabled_cases": ["hard-16"],
                    "skip_after_failure": True,
                }
            ),
            flush=True,
        )
        return asyncio.run(run_cases(cases))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        print(
            "Request-limit probe failed; no further requests sent.",
            file=sys.stderr,
        )
        sys.exit(1)
