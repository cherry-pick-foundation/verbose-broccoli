import asyncio
from dataclasses import asdict
import json
import traceback

from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
import httpx2
import openai
import pytest
from system_one_adapter import AsyncSystemOneAdapterClient
from system_one_adapter.providers.base import Message

from backfire.config import load_credential
from backfire.config import load_profile
from backfire.failures import JudgmentError
from backfire.failures import map_error
from backfire.failures import retry_policy
from backfire.provider import ProfileProvider
from backfire.provider import ProviderCall
from backfire.provider import provider_call
from backfire.validate import validate_answers
from backfire.validate import validate_request

QUESTIONS = {
    "q": {"type": "noul", "instructions": "The synthetic document is complete."}
}
PRIVATE = "private synthetic document"


@pytest.fixture(params=["hive", "second-test"])
def profile(request, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("BACKFIRE_TEST_PROVIDER_BASE_URL", raising=False)
    directory = tmp_path / "verbose-broccoli" / "backfire"
    directory.mkdir(parents=True)
    if request.param == "second-test":
        (directory / "config.toml").write_text(
            (
                "\n"
                'provider = "second-test"\n'
                "[providers.second-test]\n"
                'api = "openai"\n'
                'base_url = "https://provider.invalid/v2"\n'
                'model = "another-requested-model"\n'
                'credential = "SYNTHETIC_KEY"\n'
                "request = {max_tokens = 64, temperature = 0.1, "
                "custom_option = {enabled = true}}\n"
                'thinking = {requested = "on", token_path = '
                '"completion_tokens_details.reasoning_tokens"}\n'
                'statuses = {409 = "rate_limited"}\n'
            ),
            encoding="utf-8",
        )
    profile = load_profile()
    credential = directory / f"{profile['name']}.env"
    credential.write_text(
        f"{profile['credential']}=synthetic-key\n", encoding="utf-8"
    )
    credential.chmod(0o600)
    return profile


@pytest.fixture
def body(profile):
    value = completion()
    if profile["name"] == "second-test":
        value["choices"][0]["message"].pop("reasoning_content")
        value["usage"].pop("reasoning_tokens")
        value["usage"]["completion_tokens_details"] = {"reasoning_tokens": 4}
    return value


async def evaluate(profile, *, call=None, questions=QUESTIONS):
    """Exercise the real adapter; T018 owns the public judge boundary."""
    call = call or ProviderCall(asyncio.get_running_loop().time() + 10)
    token = provider_call.set(call)
    provider = ProfileProvider(profile, load_credential(profile))
    try:
        validate_request(questions)
        async with AsyncSystemOneAdapterClient(
            model=provider,
            structured_outputs=False,
            llm_answer_mode="probabilities",
            normalize_probabilities=False,
            n_retry_malformed_structure=0,
            retry=retry_policy(
                profile,
                remaining_seconds=call.deadline
                - asyncio.get_running_loop().time(),
            ),
        ) as client:
            response = await client.system_one(PRIVATE, questions)
            validate_answers(response.answers)
            return response, call
    finally:
        provider_call.reset(token)
        await provider.aclose()


def test_profile_fields_and_reported_model_survive_real_adapter(
    profile, body, monkeypatch, capsys
):
    with FakeProvider([body]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        profile = load_profile()
        response, call = asyncio.run(evaluate(profile))
        assert len(fake.requests) == 1
        request = fake.requests[0]
        assert request["path"] == "/v1/chat/completions"
        assert request["headers"]["authorization"] == "Bearer synthetic-key"
        sent = request["body"]
        assert sent["model"] == profile["model"]
        assert all(
            sent[key] == value for key, value in profile["request"].items()
        )
        assert len(sent["messages"]) == 2
        assert QUESTIONS["q"]["instructions"] in sent["messages"][0]["content"]
        assert '"answers"' in sent["messages"][0]["content"]
        assert "private synthetic document" in sent["messages"][1]["content"]
        assert response.answers["q"].noul == 0.5
        assert (
            response.model == profile["model"]
        )  # This upstream field is not the answering model.
        assert call.model == "reported-model"
        assert call.usage == {"input_tokens": 11, "output_tokens": 7}
        assert call.metadata == {
            "attempts": 1,
            "latency_ms": None,
            "thinking_evidence": True,
            "reasoning_tokens": 3 if profile["name"] == "hive" else 4,
        }
        assert "private" not in json.dumps(asdict(call))
        assert "synthetic reasoning" not in json.dumps(asdict(call))
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "fault, expected",
    [
        ("empty_choices", "malformed_output"),
        ("missing_choices", "malformed_output"),
        ("null_choices", "malformed_output"),
        ("empty_content", "malformed_output"),
        ("blank_content", "malformed_output"),
        ("null_content", "malformed_output"),
        ("refusal", "refused"),
        ("finish_length", "truncated_output"),
        ("finish_filter", "truncated_output"),
        ("finish_tools", "truncated_output"),
        ("token_limit", "truncated_output"),
        ("over_token_limit", "truncated_output"),
        ("missing_usage", "malformed_output"),
        ("null_usage", "malformed_output"),
        ("missing_count", "malformed_output"),
        ("negative_count", "malformed_output"),
        ("boolean_count", "malformed_output"),
        ("missing_model", "model_not_confirmed"),
        ("null_model", "model_not_confirmed"),
        ("empty_model", "model_not_confirmed"),
        ("blank_model", "model_not_confirmed"),
        ("missing_thinking", "thinking_not_confirmed"),
    ],
)
def test_response_failures_are_fixed_and_never_retried(
    profile, body, fault, expected, capsys
):
    message = body["choices"][0]["message"]
    if fault == "empty_choices":
        body["choices"] = []
    elif fault == "missing_choices":
        body.pop("choices")
    elif fault == "null_choices":
        body["choices"] = None
    elif fault.endswith("_content"):
        message["content"] = {
            "empty_content": "",
            "blank_content": " \n",
            "null_content": None,
        }[fault]
    elif fault == "refusal":
        message.update(refusal="private refusal marker", content=None)
    elif fault.startswith("finish_"):
        body["choices"][0]["finish_reason"] = {
            "finish_length": "length",
            "finish_filter": "content_filter",
            "finish_tools": "tool_calls",
        }[fault]
    elif fault in ("token_limit", "over_token_limit"):
        body["usage"]["completion_tokens"] = profile["request"][
            "max_tokens"
        ] + (fault == "over_token_limit")
    elif fault == "missing_usage":
        body.pop("usage")
    elif fault == "null_usage":
        body["usage"] = None
    elif fault == "missing_count":
        body["usage"].pop("prompt_tokens")
    elif fault in ("negative_count", "boolean_count"):
        body["usage"]["prompt_tokens"] = (
            -1 if fault == "negative_count" else True
        )
    elif fault == "missing_model":
        body.pop("model")
    elif fault.endswith("_model"):
        body["model"] = {
            "null_model": None,
            "empty_model": "",
            "blank_model": " \n",
        }[fault]
    elif fault == "missing_thinking":
        message.pop("reasoning_content", None)
        body["usage"].pop("reasoning_tokens", None)
        body["usage"].pop("completion_tokens_details", None)
    with FakeProvider([body]) as fake:
        profile["base_url"] = fake.base_url
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(profile))
        assert caught.value.error_type == expected
        assert str(caught.value) == str(JudgmentError(expected))
        assert "private" not in "".join(
            traceback.format_exception(caught.value)
        )
        assert len(fake.requests) == 1
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("tokens", [None, 0, -1, True, 1.5, "3", {}, []])
def test_thinking_requires_positive_integer_tokens_or_nonblank_content(
    profile, body, tokens
):
    profile["thinking"] = {
        "requested": "on",
        "content_path": "reasoning.text",
        "token_path": "details.tokens",
    }
    body["choices"][0]["message"]["reasoning"] = {"text": " \n"}
    body["usage"]["details"] = {"tokens": tokens}
    with FakeProvider([body]) as fake:
        profile["base_url"] = fake.base_url

        async def run():
            call = ProviderCall(asyncio.get_running_loop().time() + 10)
            with pytest.raises(JudgmentError, match="^thinking_not_confirmed:"):
                await evaluate(profile, call=call)
            assert call.metadata["thinking_evidence"] is False
            assert call.metadata["reasoning_tokens"] == (
                0 if type(tokens) is int and tokens == 0 else None
            )

        asyncio.run(run())


@pytest.mark.parametrize("mode", ["content", "tokens", "off"])
def test_each_thinking_source_and_explicit_off(profile, body, mode):
    profile["thinking"] = (
        {"requested": "off"}
        if mode == "off"
        else {
            "requested": "on",
            "content_path": "reasoning.text",
            "token_path": "details.tokens",
        }
    )
    body["choices"][0]["message"]["reasoning"] = {
        "text": "synthetic reasoning" if mode == "content" else ""
    }
    body["usage"]["details"] = {"tokens": 2 if mode == "tokens" else 0}
    with FakeProvider([body]) as fake:
        profile["base_url"] = fake.base_url
        _, call = asyncio.run(evaluate(profile))
        assert call.metadata["thinking_evidence"] is (mode != "off")
        assert (
            call.metadata["reasoning_tokens"]
            == {"off": None, "content": 0, "tokens": 2}[mode]
        )


@pytest.mark.parametrize("status", [401, 400, 403, 405, 500, 429, 409])
def test_sdk_status_mapping_and_one_retry_layer(profile, body, status):
    retried = (
        status == 429 or profile["statuses"].get(str(status)) == "rate_limited"
    )
    with FakeProvider(
        [
            Reply(
                {"error": "private provider diagnostic"},
                status,
                {"Retry-After": "0"},
            ),
            body,
        ]
    ) as fake:
        profile["base_url"] = fake.base_url
        if retried:
            _, call = asyncio.run(evaluate(profile))
            assert call.metadata["attempts"] == 2
        else:
            with pytest.raises(Exception) as caught:
                asyncio.run(evaluate(profile))
            expected = profile["statuses"].get(
                str(status),
                {
                    401: "credential_rejected",
                    400: "request_rejected",
                }.get(status, "provider_error"),
            )
            assert map_error(caught.value, profile).error_type == expected
        assert len(fake.requests) == (2 if retried else 1)
        assert all(
            request["body"]["model"] == profile["model"]
            for request in fake.requests
        )


def test_sdk_retry_limit_and_failure_metadata(profile):
    with FakeProvider(
        [
            Reply({"error": "private error"}, 429, {"Retry-After": "0"})
            for _ in range(5)
        ]
    ) as fake:
        profile["base_url"] = fake.base_url

        async def run():
            call = ProviderCall(asyncio.get_running_loop().time() + 10)
            with pytest.raises(Exception) as caught:
                await evaluate(profile, call=call)
            assert map_error(caught.value, profile).error_type == "rate_limited"
            assert call.model is call.usage is None
            assert call.metadata == {
                "attempts": 4,
                "latency_ms": None,
                "thinking_evidence": False,
                "reasoning_tokens": None,
            }

        asyncio.run(run())
        assert len(fake.requests) == 4


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"answers": {"q": -0.1}}, "malformed_output"),
        ({"answers": {"wrong": 0.5}}, "malformed_output"),
        ({"answers": {"q": 0.5, "extra": 1}}, "malformed_output"),
        ("private not-json", "malformed_output"),
    ],
)
def test_answer_schema_stays_in_adapter(profile, body, payload, expected):
    body["choices"][0]["message"]["content"] = (
        payload if isinstance(payload, str) else json.dumps(payload)
    )
    with FakeProvider([body]) as fake:
        profile["base_url"] = fake.base_url
        with pytest.raises(Exception) as caught:
            asyncio.run(evaluate(profile))
        assert map_error(caught.value, profile).error_type == expected
        assert len(fake.requests) == 1


def test_timeout_shrinks_and_unknown_fields_stay_in_json(profile, body):
    async def run():
        seen = []

        async def respond(request):
            seen.append(request)
            return httpx2.Response(200, json=body)

        provider = ProfileProvider(profile, "synthetic-key")
        await provider.aclose()
        provider._client = openai.AsyncOpenAI(
            base_url="https://provider.invalid/v1",
            api_key="synthetic-key",
            max_retries=0,
            http_client=httpx2.AsyncClient(
                transport=httpx2.MockTransport(respond)
            ),
        )
        # A request field named timeout is body data, never an SDK timeout
        # override.
        profile["request"]["timeout"] = 999
        call = ProviderCall(asyncio.get_running_loop().time() + 2)
        token = provider_call.set(call)
        try:
            for _ in range(2):
                await provider.request(
                    [Message("user", "synthetic")], schema={}, structured=False
                )
                await asyncio.sleep(0.01)
            timeouts = [request.extensions["timeout"] for request in seen]
            assert all(
                0 < timeout < 2
                for values in timeouts
                for timeout in values.values()
            )
            assert timeouts[1]["read"] < timeouts[0]["read"]
            assert all(
                json.loads(request.content)["timeout"] == 999
                for request in seen
            )
            call.deadline = asyncio.get_running_loop().time() - 1
            with pytest.raises(TimeoutError):
                await provider.request([], schema={}, structured=False)
            assert len(seen) == call.metadata["attempts"] == 2
        finally:
            provider_call.reset(token)
            await provider.aclose()

    asyncio.run(run())


def test_timeout_after_send_and_cancellation_are_not_retried(profile, body):
    with FakeProvider([Reply(body, stall=True)]) as fake:
        profile["base_url"] = fake.base_url

        async def run():
            call = ProviderCall(asyncio.get_running_loop().time() + 0.1)
            with pytest.raises(Exception) as caught:
                await evaluate(profile, call=call)
            assert (
                map_error(caught.value, profile).error_type
                == "provider_unavailable"
            )
            assert call.metadata["attempts"] == 1

        asyncio.run(run())
        assert len(fake.requests) == 1
    with FakeProvider([Reply(body, stall=True)]) as fake:
        profile["base_url"] = fake.base_url

        async def run():
            call = ProviderCall(asyncio.get_running_loop().time() + 10)
            task = asyncio.create_task(evaluate(profile, call=call))
            assert await asyncio.to_thread(fake.received.wait, 2)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert call.metadata["attempts"] == 1
            assert call.metadata["thinking_evidence"] is None

        asyncio.run(run())
        assert len(fake.requests) == 1


def test_concurrent_calls_keep_model_usage_and_metadata_separate(profile, body):
    other = completion(model="other-reported-model")
    other["usage"]["completion_tokens"] = 9
    other["usage"]["completion_tokens_details"] = {"reasoning_tokens": 6}
    other["usage"]["reasoning_tokens"] = 6
    with FakeProvider([Reply(body, delay=0.05), other]) as fake:
        profile["base_url"] = fake.base_url

        async def run():
            first = asyncio.create_task(evaluate(profile))
            assert await asyncio.to_thread(fake.received.wait, 2)
            return await asyncio.gather(first, evaluate(profile))

        (_, first), (_, second) = asyncio.run(run())
        assert first.model == "reported-model"
        assert second.model == "other-reported-model"
        assert first.usage["output_tokens"] == 7
        assert second.usage["output_tokens"] == 9
        assert second.metadata["reasoning_tokens"] == 6
        assert first.metadata is not second.metadata
        assert first.metadata["attempts"] == second.metadata["attempts"] == 1
        with pytest.raises(LookupError):
            provider_call.get()


@pytest.mark.parametrize(
    "payload", [b"private invalid JSON", [], None, {"choices": [None]}]
)
def test_malformed_envelopes_fail_without_raw_diagnostics(
    profile, payload, capsys
):
    with FakeProvider([payload]) as fake:
        profile["base_url"] = fake.base_url
        with pytest.raises(JudgmentError, match="^malformed_output:"):
            asyncio.run(evaluate(profile))
        assert len(fake.requests) == 1
    assert capsys.readouterr() == ("", "")


def test_optional_token_limit_and_adapter_null_finish_reason(profile, body):
    profile["request"].pop("max_tokens")
    body["choices"][0]["finish_reason"] = None
    body["usage"]["completion_tokens"] = 100000
    with FakeProvider([body]) as fake:
        profile["base_url"] = fake.base_url
        _, call = asyncio.run(evaluate(profile))
        assert call.usage["output_tokens"] == 100000


@pytest.mark.parametrize("outcome", ["completed", "incomplete", "refusal"])
def test_inherited_responses_route_keeps_adapter_handling(
    profile, monkeypatch, outcome
):
    profile["base_url"] = "https://api.openai.com/v1"
    profile["thinking"] = {
        "requested": "on",
        "token_path": "output_tokens_details.reasoning_tokens",
    }
    body = {
        "id": "synthetic-response",
        "object": "response",
        "created_at": 0,
        "model": "reported-model",
        "status": "incomplete" if outcome == "incomplete" else "completed",
        "error": None,
        "incomplete_details": {"reason": "max_output_tokens"}
        if outcome == "incomplete"
        else None,
        "output": []
        if outcome == "incomplete"
        else [
            {
                "id": "synthetic-message",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": (
                    [{"type": "refusal", "refusal": "private refusal"}]
                    if outcome == "refusal"
                    else [
                        {
                            "type": "output_text",
                            "text": '{"answers":{"q":0.5}}',
                            "annotations": [],
                        }
                    ]
                ),
            }
        ],
        "usage": {
            "input_tokens": 11,
            "output_tokens": 7,
            "total_tokens": 18,
            "output_tokens_details": {"reasoning_tokens": 3},
        },
    }
    sent = []

    async def respond(request):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        sent.append(json.loads(request.content))
        return httpx2.Response(200, json=body)

    client_type = openai.AsyncOpenAI
    monkeypatch.setattr(
        openai,
        "AsyncOpenAI",
        lambda **kwargs: client_type(
            **kwargs,
            http_client=httpx2.AsyncClient(
                transport=httpx2.MockTransport(respond)
            ),
        ),
    )
    if outcome == "completed":
        response, call = asyncio.run(evaluate(profile))
        assert response.answers["q"].noul == 0.5
        assert call.model == "reported-model"
        assert call.usage == {"input_tokens": 11, "output_tokens": 7}
        assert call.metadata["reasoning_tokens"] == 3
    else:
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(profile))
        assert (
            caught.value.error_type
            == {"incomplete": "truncated_output", "refusal": "refused"}[outcome]
        )
    assert len(sent) == 1
    assert sent[0]["model"] == profile["model"]
    assert sent[0]["store"] is False
    assert sent[0]["text"]["format"] == {"type": "json_object"}
    assert len(sent[0]["input"]) == 2
    assert all(
        sent[0][key] == value for key, value in profile["request"].items()
    )
