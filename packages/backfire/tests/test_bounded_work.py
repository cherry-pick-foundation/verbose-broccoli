"""Gate 6: real stdio calls at 10 MiB, timed inside the server's event loop."""

import asyncio
import json
import os
from pathlib import Path
import sys
import time

import pytest

from backfire.server import TOOLS
from test_tools_part1 import pick, probability
from test_tools_part2 import strong_review

MESSAGE_BYTES = 10 * 1024 * 1024
INTERVAL_SECONDS = 0.1
MAX_LAG_SECONDS = 1


def encode(message):
    return json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode()


def bounded_case(tool):
    """Keep inputs valid so the measurement reaches preparation and projection."""
    name = tool.removeprefix("backfire_")
    padding = None
    if name == "verify":
        arguments = {"claims": ["claim"], "evidence": [
            {"id": "same", "text": "evidence"} for _ in range(100_000)
        ]}
        source_ids = ["same", *(f"same_{index}" for index in range(1, 100_000)), "none"]
        answers = {"relation_claim0": pick("supports", ("supports", "contradicts", "says_nothing")),
                   "source_claim0": pick("same", source_ids)}
        padding = arguments["evidence"][0], "text"
    elif name == "screen":
        arguments = {"text": "content", "purpose": "screen"}
        answers = {"injection": probability(0), "substance": probability(1), "relevance": probability(1)}
        padding = arguments, "text"
    elif name == "noul":
        arguments = {"propositions": ["p" * 2000] * 64,
                     "context": {"id": "context", "text": "e" * 22_000}}
        answers = {f"p_proposition{index}": probability(1) for index in range(64)}
        # The text budget is 150,000 characters; context IDs have no size cap.
        padding = arguments["context"], "id"
    elif name == "find":
        arguments = {"query": "query", "candidates": [
            {"id": f"candidate{index}", "text": "e" * 2000} for index in range(250)
        ], "top_k": 50}
        answers = {"best": pick("candidate0", [item["id"] for item in arguments["candidates"]]),
                   "exists": probability(1)}
        padding = arguments, "query"
    elif name == "classify":
        arguments = {"items": [{"text": "e" * 2000} for _ in range(32)],
                     "classes": [{"description": "c" * 2000} for _ in range(250)], "context": "context"}
        answers = {f"i{index}": pick("c0", [f"c{i}" for i in range(250)]) for index in range(32)}
        padding = arguments, "context"
    elif name == "rerank":
        arguments = {"query": "q" * 2000, "candidates": [
            {"id": f"candidate{index}", "text": "e" * 300} for index in range(250)
        ]}
        answers = {f"rel_{index}": probability(1) for index in range(250)}
        padding = arguments["candidates"][0], "text"
    elif name == "compare":
        arguments = {"passage_a": "a" * 20_000, "passage_b": "b" * 20_000,
                     "aspects": ["c" * 200] * 10, "purpose": "compare"}
        answers = {key: pick("same_fact", ("same_fact", "contradicts", "different_facts"))
                   for key in ("overall", *(f"aspect_{index}" for index in range(10)))}
        padding = arguments, "purpose"
    elif name == "extract":
        arguments = {"document": "a" * 49_999 + "!", "purpose": "extract", "fields": [
            {"id": "slow_a", "pattern": "(a+)+$", "description": "slow pattern"},
            {"id": "slow_b", "pattern": "(a|aa)+$", "description": "slow pattern"},
            {"id": "match", "pattern": "!", "description": "matching pattern"},
        ]}
        answers = {"f2": pick("c0", ("c0", "none_of_them"))}
        padding = arguments, "purpose"
    elif name in ("review", "gate"):
        arguments = {"request": "r" * 50_000, "diff": "diff", "tests": "t" * 50_000}
        answers = strong_review()
        if name == "gate":
            arguments.update(claims=["c" * 2000] * 16, evidence=[
                {"id": f"e{index}", "text": "e" * 12_500} for index in range(16)
            ])
            answers.update({f"claim_{index}": pick("verified", ("verified", "contradicted", "unsupported"))
                            for index in range(16)})
        padding = arguments, "diff"
    elif name == "decide":
        arguments = {"decision": "d" * 1500, "evidence": "e" * 12_000, "priorities": "p" * 2000,
                     "candidates": [{"id": f"option{index}".ljust(64, "x"), "description": "c" * 2000}
                                    for index in range(6)], "requirements": ["r" * 500] * 3}
        answers = {"recommendation": pick("option_0", [*(f"option_{index}" for index in range(6)),
                                                      "ask_user", "investigate", "none"]),
                   **{f"check_{i}_{j}": pick("supported", ("supported", "contradicted", "unknown"))
                      for i in range(6) for j in range(3)}}
    else:
        raise AssertionError(f"Missing bounded input for {tool}")

    message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}
    remaining = MESSAGE_BYTES - len(encode(message))
    assert remaining >= 0
    if padding is not None:
        container, key = padding
        container[key] += "x" * remaining
        payload = encode(message)
    else:
        # Every decide argument is capped, so fill the wire limit with JSON whitespace.
        payload = encode(message) + b" " * remaining
    assert len(payload) == MESSAGE_BYTES  # The newline is outside the contract's limit.
    return payload + b"\n", {"model": "scripted-model", "answers": answers,
                              "usage": {"input_tokens": 1, "output_tokens": 1}}


async def observe_loop(serve, judge, report):
    """Arm before serving; sample after shutdown so a last synchronous stall counts."""
    loop = asyncio.get_running_loop()
    sampled = asyncio.Event()
    lags = []
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
        await serve(judge)
    finally:
        sampled.clear()
        await sampled.wait()
        handle.cancel()
        report.write_text(json.dumps({"interval_seconds": INTERVAL_SECONDS,
                                      "samples": len(lags), "worst_lag_seconds": max(lags)}))


async def call_server(tmp_path, payload, answer):
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"script": [answer], "requests_file": "requests.jsonl"}))
    report = tmp_path / "lag.json"
    process = await asyncio.create_subprocess_exec(
        sys.executable, str(Path(__file__).resolve()), str(report),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        limit=3 * MESSAGE_BYTES,
        env={**os.environ, "BACKFIRE_TEST_JUDGE_SCRIPT": str(script), "PYTHONDONTWRITEBYTECODE": "1",
             "XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state")},
    )
    errors = asyncio.create_task(process.stderr.read())

    async def send(message):
        process.stdin.write(message)
        await process.stdin.drain()

    async def receive(identifier):
        message = json.loads(await process.stdout.readline())
        assert message["id"] == identifier
        assert "error" not in message, message
        return message["result"]

    try:
        async with asyncio.timeout(130):
            await send(encode({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "bounded-work-test", "version": "1"},
            }}) + b"\n")
            assert (await receive(0))["serverInfo"]["name"] == "backfire"
            await send(encode({"jsonrpc": "2.0", "method": "notifications/initialized"}) + b"\n")
            await send(payload)
            result = await receive(1)
            await send(encode({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}) + b"\n")
            assert {tool["name"] for tool in (await receive(2))["tools"]} == set(TOOLS)
            process.stdin.close()
            assert await process.wait() == 0
            stderr = (await errors).decode()
            assert "Traceback" not in stderr, stderr
            return result, json.loads(report.read_text())
    finally:
        if process.returncode is None:
            process.kill()
        await process.wait()
        process.stdin.close()
        await errors


@pytest.mark.parametrize("tool", tuple(TOOLS))
def test_each_tool_keeps_event_loop_lag_below_one_second(tmp_path, tool, record_property):
    payload, answer = bounded_case(tool)
    result, timing = asyncio.run(call_server(tmp_path, payload, answer))
    lag = timing["worst_lag_seconds"]
    print(f"{tool}: message_bytes={len(payload) - 1}, samples={timing['samples']}, worst_lag_ms={lag * 1000:.3f}")
    record_property("message_bytes", len(payload) - 1)
    record_property("worst_lag_ms", lag * 1000)
    assert timing["interval_seconds"] == 0.1 and timing["samples"] >= 2
    assert not result.get("isError"), result
    assert ': "invalid_response"' not in result["content"][0]["text"]
    output = json.loads(result["content"][0]["text"])
    assert output["tool"] == tool and output["model"] == "scripted-model"
    captured = [json.loads(line) for line in (tmp_path / "requests.jsonl").read_text().splitlines()]
    assert len(captured) == 1, "Every input must reach the immediate scripted judge."
    if tool == "backfire_verify":
        evidence = captured[0]["state"]["evidence"]
        assert len(evidence) == len({item["id"] for item in evidence}) == 100_000
        assert evidence[0]["id"] == "same" and evidence[-1]["id"] == "same_99999"
        assert output["results"][0]["verdict"] == "verified"
    if tool == "backfire_extract":
        for field in output["results"][:2]:
            assert field["status"] == "invalid_pattern"
            assert field["reason"] == "regex timed out after 1000ms; simplify the pattern"
        assert output["results"][2]["value"] == "!"
    assert lag < MAX_LAG_SECONDS, f"{tool} stalled the server event loop for {lag:.6f}s (must be < 1s)"


def test_timer_captures_a_stall_even_when_server_returns_without_yielding(tmp_path):
    async def blocking_server(judge):
        time.sleep(1.2)

    report = tmp_path / "control.json"
    asyncio.run(observe_loop(blocking_server, None, report))
    lag = json.loads(report.read_text())["worst_lag_seconds"]
    print(f"timer_control: worst_lag_ms={lag * 1000:.3f}")
    assert lag >= MAX_LAG_SECONDS


if __name__ == "__main__":
    # Instrument the real CLI entry without changing the server, boundary or tools.
    from backfire import __main__, server

    report = Path(sys.argv[1])
    original_serve = server.serve

    async def measured_serve(judge):
        await observe_loop(original_serve, judge, report)

    server.serve = measured_serve
    sys.argv = ["backfire", "serve-mcp"]
    __main__.main()
