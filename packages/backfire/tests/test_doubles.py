import asyncio
from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from backfire import __main__, server
from scripted_judge import ScriptedJudge

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = {"q": {"type": "noul", "instructions": "Is it true?"}}
RESULT = {"model": "scripted-model", "answers": {"q": {"type": "noul", "noul": 0.5}},
          "usage": {"input_tokens": 1, "output_tokens": 2}}
ERROR_TYPES = (
    "invalid_request", "request_limit_exceeded", "backend_not_configured",
    "credential_rejected", "balance_exhausted", "request_rejected", "rate_limited",
    "provider_unavailable", "provider_error", "truncated_output", "malformed_output",
    "refused", "invalid_distribution", "thinking_not_confirmed", "model_not_confirmed",
)


def script_file(tmp_path, script, requests_file="requests.jsonl"):
    path = tmp_path / "script.json"
    path.write_text(json.dumps({"script": script, "requests_file": requests_file}), encoding="utf-8")
    return path


def requests(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_file_script_preserves_order_snapshots_and_existing_log(tmp_path, monkeypatch):
    log = tmp_path / "requests.jsonl"
    previous = {"state": "previous", "questions": {}}
    log.write_text(json.dumps(previous) + "\n", encoding="utf-8")
    path = script_file(tmp_path, [RESULT, {"result": {"answers": "malformed"}}])
    monkeypatch.chdir(tmp_path.parent)
    judge = ScriptedJudge.from_file(path)
    original = path.read_bytes()

    async def run():
        deadline = asyncio.get_running_loop().time() + 118
        record_file = tmp_path / "session.jsonl"
        state, questions = {"document": "한글\nsecond line"}, deepcopy(QUESTIONS)
        assert await judge(state, questions, deadline=deadline, record_file=record_file) == RESULT
        state["document"] = "changed"
        questions["q"]["instructions"] = "Changed?"
        assert judge.requests[0] == {
            "state": {"document": "한글\nsecond line"}, "questions": QUESTIONS,
            "deadline": deadline, "record_file": record_file,
        }
        assert await judge(["second"], {}, deadline=deadline) == {"answers": "malformed"}
        with pytest.raises(AssertionError, match="no answer left"):
            await judge("exhausted", {}, deadline=deadline)
        assert not record_file.exists()

    asyncio.run(run())
    assert requests(log) == [previous, {"state": {"document": "한글\nsecond line"}, "questions": QUESTIONS},
                             {"state": ["second"], "questions": {}}, {"state": "exhausted", "questions": {}}]
    assert path.read_bytes() == original


@pytest.mark.parametrize("error_type", ERROR_TYPES)
def test_any_judgment_error_is_raised_after_logging(tmp_path, error_type):
    message = f"{error_type}: synthetic judgment failure"
    judge = ScriptedJudge.from_file(script_file(tmp_path, [{"error": message}, RESULT]))

    async def run():
        with pytest.raises(RuntimeError) as error:
            await judge("failed", QUESTIONS, deadline=1)
        assert str(error.value) == message
        assert requests(tmp_path / "requests.jsonl") == [{"state": "failed", "questions": QUESTIONS}]
        assert await judge("next", QUESTIONS, deadline=1) == RESULT

    asyncio.run(run())


@pytest.mark.parametrize("malformed", [None, "not an answer", [], {"answers": None},
                                       {"error": "literal result, not an instruction"}])
def test_result_step_returns_malformed_values_unchanged(malformed):
    judge = ScriptedJudge([{"result": malformed}])
    assert asyncio.run(judge(None, {}, deadline=1)) == malformed


def test_numeric_one_is_a_malformed_result_not_a_stall():
    judge = ScriptedJudge([{"stall": 1}])

    async def run():
        task = asyncio.create_task(judge(None, {}, deadline=1))
        try:
            await asyncio.sleep(0)
            assert task.done(), "Only JSON true may stall the judge."
            assert task.result() == {"stall": 1}
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    asyncio.run(run())


def test_stall_logs_before_waiting_allows_other_calls_and_cancels(tmp_path):
    log = tmp_path / "requests.jsonl"
    judge = ScriptedJudge.from_file(script_file(tmp_path, [{"stall": True}, RESULT]))

    async def run():
        stalled = asyncio.create_task(judge("stalled", QUESTIONS, deadline=1))
        try:
            await asyncio.sleep(0)
            assert not stalled.done()
            assert requests(log) == [{"state": "stalled", "questions": QUESTIONS}]
            assert await asyncio.wait_for(judge("next", {}, deadline=1), 1) == RESULT
        finally:
            stalled.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(stalled, 1)

    asyncio.run(run())
    assert requests(log) == [{"state": "stalled", "questions": QUESTIONS}, {"state": "next", "questions": {}}]


def test_empty_script_creates_an_empty_log_with_an_absolute_path(tmp_path):
    log = tmp_path / "absolute.jsonl"
    ScriptedJudge.from_file(script_file(tmp_path, [], str(log)))
    assert log.read_bytes() == b""


@pytest.mark.parametrize("payload", [[], {}, {"script": [], "requests_file": ""},
                                    {"script": {}, "requests_file": "requests.jsonl"},
                                    {"script": [], "requests_file": 1}])
def test_invalid_script_configuration_fails_before_creating_log(tmp_path, payload):
    path = tmp_path / "script.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="script.*requests_file"):
        ScriptedJudge.from_file(path)
    assert sorted(item.name for item in tmp_path.iterdir()) == ["script.json"]


def test_request_log_cannot_be_the_script_file(tmp_path):
    path = script_file(tmp_path, [], "script.json")
    original = path.read_bytes()
    with pytest.raises(ValueError, match="different"):
        ScriptedJudge.from_file(path)
    assert path.read_bytes() == original


def test_serve_without_override_does_not_load_test_helper(monkeypatch):
    calls = []

    async def serve(judge):
        calls.append(judge)

    def unexpected_load(*args, **kwargs):
        pytest.fail("Test helper loaded without BACKFIRE_TEST_JUDGE_SCRIPT")

    monkeypatch.delenv("BACKFIRE_TEST_JUDGE_SCRIPT", raising=False)
    monkeypatch.setattr(sys, "argv", ["backfire", "serve-mcp"])
    monkeypatch.setattr(runpy, "run_path", unexpected_load)
    monkeypatch.setattr(server, "serve", serve)
    __main__.main()
    assert len(calls) == 1
    assert callable(calls[0])


@pytest.mark.parametrize("entry_point", [[sys.executable, "-m", "backfire"],
                                      ["uv", "run", "--frozen", "--offline", "--no-sync", "backfire"]],
                         ids=["module", "console"])
def test_real_serve_mcp_uses_script_and_logs_only_judgments(tmp_path, entry_point):
    answer = {**RESULT, "answers": {"p_proposition0": {"type": "noul", "noul": 0.97}}}
    failure = "refused: synthetic judgment failure"
    path = script_file(tmp_path, [answer, {**answer, "answers": {}}, {"error": failure}])
    parameters = StdioServerParameters(
        command=entry_point[0], args=[*entry_point[1:], "serve-mcp"], cwd=PACKAGE_ROOT,
        env={"BACKFIRE_TEST_JUDGE_SCRIPT": str(path), "PYTHONDONTWRITEBYTECODE": "1",
             "XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state")},
    )

    async def run():
        with anyio.fail_after(15):
            async with stdio_client(parameters) as streams:
                async with ClientSession(*streams) as client:
                    assert (await client.initialize()).server_info.name == "backfire"
                    result = await client.call_tool("backfire_noul", {"propositions": ["첫 문장"]})
                    assert not result.is_error
                    payload = json.loads(result.content[0].text)
                    assert payload["model"] == "scripted-model"
                    assert payload["results"][0]["probability"] == 0.97
                    malformed = await client.call_tool("backfire_noul", {"propositions": ["second"]})
                    assert json.loads(malformed.content[0].text)["results"][0]["probability"] is None
                    failed = await client.call_tool("backfire_noul", {"propositions": ["third"]})
                    assert failed.is_error and failed.content[0].text == failure
                    local = await client.call_tool("backfire_extract", {
                        "document": "no digits", "fields": [{"id": "number", "pattern": r"\d+", "description": "number"}],
                    })
                    assert json.loads(local.content[0].text)["provider"] == "none"
                    assert len((await client.list_tools()).tools) == 11

    asyncio.run(run())
    logged = requests(tmp_path / "requests.jsonl")
    assert [item["state"] for item in logged] == [
        {"propositions": [{"id": "proposition0", "text": proposition}], "context": None}
        for proposition in ("첫 문장", "second", "third")
    ]
    for item, proposition in zip(logged, ("첫 문장", "second", "third")):
        assert set(item) == {"state", "questions"}
        assert item["questions"] == {"p_proposition0": {
            "type": "noul", "instructions": f"proposition `proposition0`: {proposition}",
            "criteria": {"true": "The proposition is likely true, given the supplied context (when present) and general knowledge",
                         "false": "The proposition is likely not true"},
        }}
