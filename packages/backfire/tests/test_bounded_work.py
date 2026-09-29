"""Measure 10 MiB stdio requests against PyModel's event loop."""

import asyncio
import json
import os
from pathlib import Path
import sys
import time

from jev_judge_mcp.domain import Usage
from jev_judge_mcp.errors import Redactor
from jev_judge_mcp.providers import Evaluation
from jev_judge_mcp.providers import JevProvider
from jev_judge_mcp.tools import TOOLS
import pytest

MESSAGE_BYTES = 10 * 1024 * 1024
INTERVAL_SECONDS = 0.1
MAX_LAG_SECONDS = 1
TOOL_NAMES = tuple(tool.name for tool in TOOLS) + ("jev_noul",)


def encode(message):
    return json.dumps(
        message, ensure_ascii=False, separators=(",", ":")
    ).encode()


def bounded_case(tool):
    arguments, padding = {}, None
    if tool == "jev_verify":
        arguments = {
            "claims": ["synthetic claim"],
            "evidence": [{"id": "same", "text": "synthetic evidence"}] * 8_000,
        }
    elif tool == "jev_screen":
        arguments, padding = (
            {"text": "synthetic text", "purpose": "screen"},
            "text",
        )
    elif tool == "jev_find":
        arguments, padding = (
            {
                "query": "synthetic query",
                "candidates": [{"id": "one", "text": "candidate"}],
            },
            "query",
        )
    elif tool == "jev_classify":
        arguments, padding = (
            {
                "items": [{"text": "synthetic item"}],
                "classes": [
                    {"id": "first", "description": "first"},
                    {"id": "second", "description": "second"},
                ],
                "context": "synthetic context",
            },
            "context",
        )
    elif tool == "jev_decide":
        arguments = {
            "decision": "d" * 1500,
            "evidence": "e" * 12_000,
            "priorities": "p" * 2000,
            "candidates": [
                {"id": "first", "description": "c" * 2000},
                {"id": "second", "description": "d" * 2000},
            ],
            "requirements": ["r" * 500] * 3,
        }
    elif tool == "jev_rerank":
        arguments = {
            "query": "q" * 2000,
            "candidates": [{"id": "one", "text": "e" * 2000}],
        }
    elif tool == "jev_compare":
        arguments = {
            "passage_a": "a" * 20_000,
            "passage_b": "b" * 20_000,
            "aspects": ["aspect" * 30] * 10,
            "purpose": "compare",
        }
    elif tool == "jev_extract":
        arguments = {
            "document": "a" * 60 + "b",
            "purpose": "extract",
            "fields": [
                {
                    "id": "simple_match",
                    "pattern": "b",
                    "description": "matching candidate",
                },
                {
                    "id": "simple_miss",
                    "pattern": "not-present",
                    "description": "absent candidate",
                },
                {
                    "id": "runaway",
                    "pattern": "(a|aa)+$",
                    "description": "runaway candidate",
                },
            ],
        }
    elif tool in {"jev_review", "jev_gate"}:
        arguments, padding = (
            {
                "request": "synthetic request",
                "diff": "+ synthetic",
                "tests": "passed",
            },
            "request",
        )
        if tool == "jev_gate":
            arguments.update(
                claims=["synthetic claim"], evidence="synthetic evidence"
            )
    elif tool == "jev_score":
        arguments = {
            "subject": "synthetic subject",
            "levels": ["low", "high"],
            "context": "synthetic context",
        }
    elif tool == "jev_noul":
        arguments = {
            "propositions": ["synthetic proposition"],
            "context": "c" * 22_000,
        }
    else:
        raise AssertionError(f"Missing bounded input for {tool}")

    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    if padding is not None:
        arguments[padding] += "x" * (MESSAGE_BYTES - len(encode(message)))
    payload = encode(message)
    assert len(payload) <= MESSAGE_BYTES
    payload += b" " * (MESSAGE_BYTES - len(payload))
    return payload + b"\n"


class ScriptedProvider(JevProvider):
    name = "compatible"
    label = "synthetic"

    def __init__(self):
        super().__init__(Redactor(()))

    async def _send(self, state, questions, model, timeout):
        del state, model, timeout
        answers = {}
        for key, question in questions.items():
            kind, criteria = question.get("type"), question.get("criteria")
            if kind == "noul":
                answers[key] = {"noul": 0.9}
            elif kind == "score":
                answers[key] = {
                    "score": 0,
                    "probabilities": {
                        str(index): int(index == 0)
                        for index in range(len(criteria))
                    },
                }
            else:
                labels = list(criteria)
                answers[key] = {
                    "choice": labels[0],
                    "probabilities": {
                        label: int(label == labels[0]) for label in labels
                    },
                }
        return Evaluation(answers, Usage(1, 1), self.name, "scripted-model")

    async def aclose(self):
        return None


async def observe_loop(serve, report):
    loop, lags, sampled = asyncio.get_running_loop(), [], asyncio.Event()
    handle = None

    def tick(expected):
        nonlocal handle
        now = loop.time()
        lags.append(max(0, now - expected))
        sampled.set()
        following = now + INTERVAL_SECONDS
        handle = loop.call_at(following, tick, following)

    first = loop.time() + INTERVAL_SECONDS
    handle = loop.call_at(first, tick, first)
    await sampled.wait()
    try:
        await serve()
    finally:
        sampled.clear()
        await sampled.wait()
        handle.cancel()
        report.write_text(
            json.dumps(
                {
                    "interval_seconds": INTERVAL_SECONDS,
                    "samples": len(lags),
                    "worst_lag_seconds": max(lags),
                }
            )
        )


async def call_server(tmp_path, payload):
    report = tmp_path / "lag.json"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(Path(__file__).resolve()),
        str(report),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=3 * MESSAGE_BYTES,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
        },
    )
    errors = asyncio.create_task(process.stderr.read())

    async def send(message):
        process.stdin.write(message)
        await process.stdin.drain()

    async def receive(identifier):
        message = json.loads(await process.stdout.readline())
        assert message["id"] == identifier, message
        assert "error" not in message, message
        return message["result"]

    try:
        async with asyncio.timeout(130):
            await send(
                encode(
                    {
                        "jsonrpc": "2.0",
                        "id": 0,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-11-25",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "bounded-work-test",
                                "version": "1",
                            },
                        },
                    }
                )
                + b"\n"
            )
            assert (await receive(0))["serverInfo"]["name"] == "jev-mcp"
            await send(
                encode(
                    {"jsonrpc": "2.0", "method": "notifications/initialized"}
                )
                + b"\n"
            )
            await send(
                encode({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
                + b"\n"
            )
            assert [
                tool["name"] for tool in (await receive(2))["tools"]
            ] == list(TOOL_NAMES)
            await send(payload)
            result = await receive(1)
            process.stdin.close()
            assert await process.wait() == 0, (await errors).decode()
            assert "Traceback" not in (await errors).decode()
            return result, json.loads(report.read_text())
    finally:
        if process.returncode is None:
            process.kill()
        await process.wait()
        process.stdin.close()
        await errors


@pytest.mark.parametrize(
    "tool",
    [
        pytest.param(
            "jev_verify",
            marks=pytest.mark.xfail(
                reason=(
                    "CHE-38: verify stalls on duplicate evidence identifiers"
                ),
                strict=True,
            ),
        ),
        *TOOL_NAMES[1:],
    ],
)
def test_each_tool_keeps_event_loop_lag_below_one_second(
    tmp_path, tool, record_property
):
    result, timing = asyncio.run(call_server(tmp_path, bounded_case(tool)))
    lag = timing["worst_lag_seconds"]
    print(
        f"{tool}: message_bytes={MESSAGE_BYTES}, "
        f"samples={timing['samples']}, worst_lag_ms={lag * 1000:.3f}"
    )
    record_property("message_bytes", MESSAGE_BYTES)
    record_property("worst_lag_ms", lag * 1000)
    assert (
        timing["interval_seconds"] == INTERVAL_SECONDS
        and timing["samples"] >= 2
    )
    assert not result.get("isError"), result
    content = result["content"][0]["text"]
    payload = json.loads(content)
    assert payload["model"] == "scripted-model"
    if tool == "jev_extract":
        rows = {row["id"]: row for row in payload["results"]}
        false_timeouts = sum(
            "timed out" in (rows[name].get("reason") or "")
            for name in ("simple_match", "simple_miss")
        )
        print(f"jev_extract: false_simple_timeouts={false_timeouts}")
        assert rows["runaway"]["status"] == "invalid_pattern"
    assert lag < MAX_LAG_SECONDS, (
        f"{tool} stalled the server event loop for {lag:.6f}s"
    )


def test_timer_captures_a_stall_even_when_server_returns_without_yielding(
    tmp_path,
):
    async def blocking_server():
        time.sleep(1.2)

    report = tmp_path / "control.json"
    asyncio.run(observe_loop(blocking_server, report))
    assert (
        json.loads(report.read_text())["worst_lag_seconds"] >= MAX_LAG_SECONDS
    )


if __name__ == "__main__":
    from backfire import __main__ as entry

    report = Path(sys.argv[1])
    original_serve = entry.pymodel.serve
    entry.providers.provider_factory = lambda **_: lambda _: ScriptedProvider()

    async def measured_serve(server, settings):
        await observe_loop(lambda: original_serve(server, settings), report)

    entry.pymodel.serve = measured_serve
    sys.argv = ["backfire", "serve-mcp"]
    entry.main()
