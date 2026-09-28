"""Measure synthetic education judgments in two arms; live use needs approval.

Run with ``python -m backfire_tools.acceptance.measure_education --runs 3``.
Only case IDs, correctness and error types reach stdout. Accuracy is evidence,
not a pass/fail gate. The shipped development profile supplies both arms.
"""

import argparse
import asyncio
from contextlib import contextmanager
from functools import partial
import json
import os
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
import tomllib

import jsonschema

from backfire.config import SHIPPED_CONFIG, xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge
from backfire.server import TOOLS

FIXTURES = Path(__file__).resolve().parents[5] / "scripts/backfire/fixtures"
ARMS = {"plain": False, "pseudonymized": True}
DEADLINE_SECONDS = 118


def load_cases():
    cases = [json.loads(line) for line in
             (FIXTURES / "education-v1.jsonl").read_text(encoding="utf-8").splitlines()]
    for case in cases:
        jsonschema.validate(case["arguments"], TOOLS[case["tool"]].INPUT_SCHEMA)
    return cases


def value_at_path(value, path):
    for key in path.split("."):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def matches(result, expected):
    try:
        return all(value_at_path(result, path) == value for path, value in expected.items())
    except (KeyError, IndexError, TypeError, ValueError):
        return False


@contextmanager
def temporary_environment():
    provider = tomllib.loads(SHIPPED_CONFIG.read_text(encoding="utf-8"))["provider"]
    credential = xdg_path("config") / "backfire" / f"{provider}.env"
    variables = ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME")
    previous = {key: os.environ.get(key) for key in variables}
    with TemporaryDirectory(prefix="backfire-education-") as temporary:
        directory = Path(temporary) / "verbose-broccoli/backfire"
        directory.mkdir(mode=0o700, parents=True)
        (directory / credential.name).symlink_to(credential)
        roster = str(FIXTURES / "education-roster-v1.csv")
        (directory / "education.toml").write_text(
            f"roster = {json.dumps(roster)}\n", encoding="utf-8",
        )
        try:
            os.environ.update(dict.fromkeys(variables, temporary))
            yield
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


async def measure(case, arm, run):
    correct, error_type = False, None
    deadline = asyncio.get_running_loop().time() + DEADLINE_SECONDS
    try:
        async with asyncio.timeout_at(deadline):
            result, is_error = await TOOLS[case["tool"]].call(
                case["arguments"], partial(judge, pseudonymize=ARMS[arm]),
                deadline=deadline, record_file=None,
            )
        if is_error:
            error_type = "tool_error"
        else:
            correct = matches(json.loads(result), case["expect"]["result"])
    except JudgmentError as error:
        error_type = error.error_type
    except TimeoutError:
        error_type = "deadline_exceeded"
    except Exception as error:
        error_type = type(error).__name__
    return {"id": case["id"], "tool": case["tool"], "arm": arm, "run": run,
            "correct": correct, "error_type": error_type}


async def run_cases(cases, runs):
    accuracy, differing = {}, set()
    for run in range(1, runs + 1):
        for case in cases:
            outcomes = []
            for arm in ARMS:
                row = await measure(case, arm, run)
                print(json.dumps(row), flush=True)
                counts = accuracy.setdefault(case["tool"], {}).setdefault(arm, {"correct": 0, "total": 0})
                counts["correct"] += int(row["correct"])
                counts["total"] += 1
                outcomes.append((row["correct"], row["error_type"]))
            if outcomes[0] != outcomes[1]:
                differing.add(case["id"])
    for arms in accuracy.values():
        for counts in arms.values():
            counts["accuracy"] = counts["correct"] / counts["total"]
    print(json.dumps({"summary": {"accuracy": accuracy, "differing_cases": sorted(differing)}}), flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    arguments = parser.parse_args(argv)
    if arguments.runs < 1:
        parser.error("--runs must be positive")
    cases = load_cases()
    previous_handler = signal.signal(signal.SIGTERM, signal.default_int_handler)
    try:
        with temporary_environment():
            asyncio.run(run_cases(cases, arguments.runs))
    finally:
        signal.signal(signal.SIGTERM, previous_handler)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Education measurement interrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception:
        print("Education measurement could not finish.", file=sys.stderr)
        sys.exit(1)
