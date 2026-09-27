"""Exercise the in-process judge through the real adapter and a local provider."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys
import traceback

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import pytest

from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.validate import CELL_LIMIT, OPTION_LIMIT
from backfire.judge import judge
from backfire.provider import ProfileProvider, ProviderCall, provider_call
from backfire.records import RecordFile, RecordWriteError, digest, read_records
from fake_provider import FakeProvider, Reply, completion

PRIVATE = "synthetic-private-content"
QUESTIONS = {"q": {"type": "noul", "instructions": PRIVATE}}
CONFIG = '''
provider = "judge-test"
[providers.judge-test]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "requested-model"
credential = "SYNTHETIC_KEY"
request = {max_tokens = 64, response_format = {type = "json_object"}}
thinking = {requested = "on", token_path = "reasoning_tokens"}
statuses = {405 = "balance_exhausted", 409 = "rate_limited"}
'''


@pytest.fixture(autouse=True)
def configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    for name in ("BACKFIRE_TEST_PROVIDER_BASE_URL", "BACKFIRE_TEST_REQUEST_LIMITS", "BACKFIRE_TEST_JUDGE_SCRIPT"):
        monkeypatch.delenv(name, raising=False)
    directory = xdg_path("config") / "backfire"
    directory.mkdir(parents=True)
    (directory / "config.toml").write_text(CONFIG, encoding="utf-8")
    credential = directory / "judge-test.env"
    credential.write_text("SYNTHETIC_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)
    return directory


async def evaluate(*, state=PRIVATE, questions=QUESTIONS, seconds=10, record_file=None):
    return await judge(state, questions, deadline=asyncio.get_running_loop().time() + seconds,
                       record_file=record_file)


def test_direct_judgment_preserves_answers_and_exposes_only_safe_metadata(monkeypatch):
    questions = {
        **QUESTIONS,
        "choice": {"type": "choice", "criteria": {"second": "b", "first": "a"}},
        "score": {"type": "score", "criteria": ["low", "middle", "high"]},
    }
    answers = {"q": 0.5, "choice": {"second": 0.005, "first": 1},
               "score": {"0": 0, "1": 0.005, "2": 1}}
    state = {"document": [PRIVATE, "한글", {"n": 2}]}
    originals = deepcopy((state, questions))
    with FakeProvider([completion(answers)]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        result = asyncio.run(evaluate(state=state, questions=questions))
        assert set(result) == {"model", "answers", "usage", "metadata"}
        assert result["model"] == "reported-model"
        assert result["usage"] == {"input_tokens": 11, "output_tokens": 7}
        assert result["answers"]["q"] == {"type": "noul", "noul": 0.5}
        assert result["answers"]["choice"]["choice"] == "first"
        assert result["answers"]["choice"]["probabilities"] == answers["choice"]
        score = result["answers"]["score"]
        assert score["probabilities"] == answers["score"]
        assert score["score"] == pytest.approx(2.005 / 1.005)
        assert score["legend"] == {"0": "low", "1": "middle", "2": "high"}
        metadata = result["metadata"]
        assert metadata == {"attempts": 1, "latency_ms": metadata["latency_ms"],
                            "thinking_evidence": True, "reasoning_tokens": 3}
        assert metadata["latency_ms"] > 0
        assert len(fake.requests) == 1
        sent = fake.requests[0]["body"]
        assert sent["model"] == "requested-model"
        assert sent["response_format"] == {"type": "json_object"}
        assert '"answers"' in sent["messages"][0]["content"]
        assert PRIVATE in sent["messages"][1]["content"]
    assert (state, questions) == originals
    assert not xdg_path("state").exists()
    with pytest.raises(LookupError):
        provider_call.get()


def test_configuration_and_credential_are_read_for_every_judgment(configuration, monkeypatch):
    with FakeProvider([completion(), completion(model="next-reported-model")]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            first = await evaluate()
            (configuration / "config.toml").write_text(CONFIG.replace("requested-model", "next-model"))
            (configuration / "judge-test.env").write_text("SYNTHETIC_KEY=next-synthetic-key\n")
            second = await evaluate()
            (configuration / "judge-test.env").unlink()
            with pytest.raises(JudgmentError, match="^backend_not_configured:"):
                await evaluate()
            return first, second

        first, second = asyncio.run(run())
        assert first["model"] == "reported-model" and second["model"] == "next-reported-model"
        assert [item["body"]["model"] for item in fake.requests] == ["requested-model", "next-model"]
        assert [item["headers"]["authorization"] for item in fake.requests] == [
            "Bearer synthetic-key", "Bearer next-synthetic-key",
        ]


@pytest.mark.parametrize("questions, expected", [
    ({}, "invalid_request"),
    ({"q": {"type": "unknown", "instructions": PRIVATE}}, "invalid_request"),
    ({"q": {"type": "choice", "criteria": {"only": PRIVATE}}}, "invalid_request"),
    ({"q": {"type": "choice", "criteria": {str(i): PRIVATE for i in range(OPTION_LIMIT + 1)}}}, "request_limit_exceeded"),
    ({str(i): QUESTIONS["q"] for i in range(CELL_LIMIT + 1)}, "request_limit_exceeded"),
])
def test_bad_requests_fail_before_provider_and_are_recorded(monkeypatch, questions, expected):
    with FakeProvider([]) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(questions=questions, record_file=records))
        assert str(caught.value) == str(JudgmentError(expected))
        entry, = read_records(records.path)
        assert entry["outcome"] == expected and entry["results"] is None
        assert entry["payload_digest"] == digest({"model": None, "state": PRIVATE, "questions": questions})
        assert entry["attempts"] == 0 and entry["thinking_evidence"] is None
        assert fake.requests == []


@pytest.mark.parametrize("fault, model", [("config", None), ("missing-key", "requested-model"),
                                         ("key-mode", "requested-model")])
def test_configuration_failure_digest_uses_only_a_loaded_model(configuration, monkeypatch, fault, model):
    if fault == "config":
        (configuration / "config.toml").write_text("invalid TOML")
    elif fault == "missing-key":
        (configuration / "judge-test.env").unlink()
    else:
        (configuration / "judge-test.env").chmod(0o640)
    with FakeProvider([]) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError, match="^backend_not_configured:") as caught:
            asyncio.run(evaluate(record_file=records))
        assert str(configuration) in str(caught.value)
        assert "synthetic-key" not in str(caught.value)
        entry, = read_records(records.path)
        assert entry["payload_digest"] == digest({"model": model, "state": PRIVATE, "questions": QUESTIONS})
        assert entry["attempts"] == 0 and entry["outcome"] == "backend_not_configured"
        assert fake.requests == []


@pytest.mark.parametrize("status, expected", [(400, "request_rejected"), (401, "credential_rejected"),
                                             (405, "balance_exhausted"), (403, "provider_error"),
                                             (500, "provider_error")])
def test_provider_errors_have_fixed_text_and_no_retry(monkeypatch, status, expected, capsys):
    with FakeProvider([Reply({"error": PRIVATE}, status)]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate())
        assert str(caught.value) == str(JudgmentError(expected))
        assert PRIVATE not in "".join(traceback.format_exception(caught.value))
        assert not hasattr(caught.value, "debug")
        assert len(fake.requests) == 1
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("status", [429, 409])
@pytest.mark.parametrize("recover", [True, False])
def test_sdk_retry_policy_is_the_only_retry_layer(monkeypatch, status, recover):
    failure = Reply({"error": PRIVATE}, status, {"Retry-After": "0"})
    script = [failure, completion()] if recover else [failure] * 5
    with FakeProvider(script) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        if recover:
            result = asyncio.run(evaluate(record_file=records))
            assert result["metadata"]["attempts"] == 2
        else:
            with pytest.raises(JudgmentError, match="^rate_limited:"):
                asyncio.run(evaluate(record_file=records))
        entry, = read_records(records.path)
        assert entry["attempts"] == len(fake.requests) == (2 if recover else 4)
        assert entry["outcome"] == ("ok" if recover else "rate_limited")
        assert PRIVATE not in records.path.read_text()


def test_retry_wait_must_fit_time_left(monkeypatch):
    with FakeProvider([Reply({"error": PRIVATE}, 429, {"Retry-After": "10"})]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError, match="^rate_limited:"):
            asyncio.run(evaluate(seconds=0.5))
        assert len(fake.requests) == 1


@pytest.mark.parametrize("kind, value, expected", [
    ("noul", -0.1, "malformed_output"),
    ("choice", {"a": 1}, "malformed_output"),
    ("choice", {"a": 1, "b": 0, "extra": 0}, "malformed_output"),
    ("choice", {"a": 0, "b": 0}, "invalid_distribution"),
    ("choice", {"a": 0.2, "b": 0.2}, "invalid_distribution"),
    ("score", {"0": 0, "1": 0}, "invalid_distribution"),
    ("score", {"0": 1, "1": 1}, "invalid_distribution"),
])
def test_answer_validation_never_rescales_or_retries(monkeypatch, kind, value, expected):
    question = {"type": kind, "instructions": PRIVATE}
    if kind != "noul":
        question["criteria"] = {"a": "first", "b": "second"} if kind == "choice" else ["low", "high"]
    with FakeProvider([completion({"q": value})]) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(questions={"q": question}, record_file=records))
        assert str(caught.value) == str(JudgmentError(expected))
        assert PRIVATE not in "".join(traceback.format_exception(caught.value))
        entry, = read_records(records.path)
        assert entry["outcome"] == expected and entry["results"] is None
        assert entry["model"] == "reported-model"
        assert entry["usage"] == {"input_tokens": 11, "output_tokens": 7, "reasoning_tokens": 3}
        assert len(fake.requests) == 1


def test_records_precede_return_and_snapshot_open_calls(monkeypatch):
    with FakeProvider([Reply(completion(), delay=0.05)]) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        assert records.calls_in_flight == set()
        records.calls_in_flight.update({8, 2})

        async def run():
            task = asyncio.create_task(evaluate(record_file=records))
            assert await asyncio.to_thread(fake.received.wait, 2)
            records.calls_in_flight.clear()
            records.calls_in_flight.add(9)
            result = await task
            entry, = read_records(records.path)
            assert entry["calls_in_flight"] == [2, 8]
            assert entry["payload_digest"] == digest({"model": "requested-model", "state": PRIVATE, "questions": QUESTIONS})
            assert entry["results"] == [{"p": 0.5}]
            assert entry["latency_ms"] == result["metadata"]["latency_ms"]
            assert entry["outcome"] == "ok"
            assert PRIVATE not in records.path.read_text()

        asyncio.run(run())


def test_unwritable_record_withholds_valid_judgment(monkeypatch):
    with FakeProvider([completion()]) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        records.close()
        with pytest.raises(RecordWriteError, match="^record_write_failed:"):
            asyncio.run(evaluate(record_file=records))
        assert records.path.read_bytes() == b""
        assert len(fake.requests) == 1
        with pytest.raises(LookupError):
            provider_call.get()


@pytest.mark.parametrize("phase", ["provider", "retry"])
def test_cancellation_propagates_closes_provider_and_records_cancelled(monkeypatch, phase):
    closed = []
    close = ProfileProvider.aclose

    async def track_close(provider):
        await close(provider)
        closed.append(provider._client.is_closed())

    monkeypatch.setattr(ProfileProvider, "aclose", track_close)
    reply = Reply(completion(), stall=True) if phase == "provider" else Reply(
        {"error": PRIVATE}, 429, {"Retry-After": "5"},
    )
    with FakeProvider([reply]) as fake, RecordFile(xdg_path("state") / "backfire/records") as records:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            waiting = asyncio.Event()
            sleep = asyncio.sleep

            async def retry_sleep(delay, result=None):
                if delay == 5:
                    waiting.set()
                return await sleep(delay, result)

            monkeypatch.setattr(asyncio, "sleep", retry_sleep)
            task = asyncio.create_task(evaluate(record_file=records))
            if phase == "provider":
                assert await asyncio.to_thread(fake.received.wait, 2)
            else:
                await asyncio.wait_for(waiting.wait(), 2)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 1)
            entry, = read_records(records.path)
            assert entry["outcome"] == "cancelled" and entry["results"] is None
            assert entry["attempts"] == 1
            assert entry["thinking_evidence"] is (None if phase == "provider" else False)

        asyncio.run(run())
        assert len(fake.requests) == 1 and closed == [True]


def test_direct_deadline_bounds_stalled_provider_without_records(monkeypatch):
    with FakeProvider([Reply(completion(), stall=True)]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            with pytest.raises(JudgmentError, match="^provider_unavailable:"):
                await asyncio.wait_for(evaluate(seconds=0.15), 1)
            with pytest.raises(JudgmentError, match="^provider_unavailable:"):
                await evaluate(seconds=-1)

        asyncio.run(run())
        assert len(fake.requests) == 1
    assert not xdg_path("state").exists()


def test_concurrent_judgments_restore_context_and_keep_metadata_separate(monkeypatch):
    other = completion({"q": 0.8}, model="other-model")
    other["usage"].update(completion_tokens=9, reasoning_tokens=6)
    with FakeProvider([Reply(completion(), delay=0.08), other]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            outer = ProviderCall(123)
            token = provider_call.set(outer)
            try:
                first = asyncio.create_task(evaluate())
                assert await asyncio.to_thread(fake.received.wait, 2)
                results = await asyncio.gather(first, evaluate())
                assert provider_call.get() is outer
                return results
            finally:
                provider_call.reset(token)

        first, second = asyncio.run(run())
        assert [first["model"], second["model"]] == ["reported-model", "other-model"]
        assert [first["usage"]["output_tokens"], second["usage"]["output_tokens"]] == [7, 9]
        assert [first["metadata"]["reasoning_tokens"], second["metadata"]["reasoning_tokens"]] == [3, 6]
        assert first["metadata"] is not second["metadata"]


def test_serve_mcp_selects_real_judge_and_keeps_metadata_out_of_tool_result(tmp_path):
    with FakeProvider([completion({"p_proposition0": 0.5})]) as fake:
        parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "backfire", "serve-mcp"],
            cwd=Path(__file__).resolve().parents[1],
            env={"BACKFIRE_TEST_PROVIDER_BASE_URL": fake.base_url, "PYTHONDONTWRITEBYTECODE": "1",
                 "XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state")},
        )

        async def run():
            with anyio.fail_after(15):
                async with stdio_client(parameters) as streams:
                    async with ClientSession(*streams) as client:
                        await client.initialize()
                        result = await client.call_tool("backfire_noul", {"propositions": [PRIVATE]})
                        assert not result.is_error
                        payload = json.loads(result.content[0].text)
                        assert payload["model"] == "reported-model"
                        assert payload["results"][0]["probability"] == 0.5
                        assert '"metadata"' not in result.content[0].text

        asyncio.run(run())
        assert len(fake.requests) == 1
