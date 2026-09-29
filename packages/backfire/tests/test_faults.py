"""Exercise judgment faults through the real adapter and a local provider."""

import asyncio

from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
import pytest

from backfire.config import load_profile
from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge

PINNED_MODEL = "deepseek-ai/deepseek-v4.1-flash"
PRIVATE = "synthetic-provider-diagnostic"
STATE = "synthetic state"
NOUL = {"q": {"type": "noul", "instructions": "synthetic proposition"}}
CHOICE = {
    "q": {
        "type": "choice",
        "instructions": "synthetic proposition",
        "criteria": {"yes": "yes", "no": "no"},
    }
}


@pytest.fixture
def configured(monkeypatch):
    for name in (
        "BACKFIRE_TEST_PROVIDER_BASE_URL",
        "BACKFIRE_TEST_REQUEST_LIMITS",
    ):
        monkeypatch.delenv(name, raising=False)
    directory = xdg_path("config") / "backfire"
    directory.mkdir(parents=True)
    credential = directory / "hive.env"
    credential.write_text("HIVE_API_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)
    return directory, credential


async def evaluate(*, questions=NOUL, seconds=10):
    loop = asyncio.get_running_loop()
    return await judge(STATE, questions, deadline=loop.time() + seconds)


@pytest.mark.parametrize(
    "questions, expected",
    [
        ({}, "invalid_request"),
        (
            {"q": {"type": "unknown", "instructions": "synthetic"}},
            "invalid_request",
        ),
        (
            {
                "q": {
                    "type": "choice",
                    "criteria": {str(i): "x" for i in range(251)},
                }
            },
            "request_limit_exceeded",
        ),
    ],
)
def test_bad_requests_fail_before_the_provider(
    configured, monkeypatch, questions, expected
):
    del configured  # Unused.
    with FakeProvider([]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(questions=questions))
    assert str(caught.value) == str(JudgmentError(expected))
    assert fake.requests == []


@pytest.mark.parametrize(
    "fault, filename",
    [
        ("selection", "config.toml"),
        ("profile", "config.toml"),
        ("credential", "hive.env"),
    ],
)
def test_invalid_configuration_names_its_file_and_skips_the_provider(
    configured,
    monkeypatch,
    fault,
    filename,
):
    del filename  # Unused.
    directory, credential = configured
    config = directory / "config.toml"
    if fault == "selection":
        config.write_text('provider = "missing"\n', encoding="utf-8")
    elif fault == "profile":
        config.write_text(
            '[providers.hive]\napi = "invalid"\n', encoding="utf-8"
        )
    else:
        credential.unlink()
    expected_path = credential if fault == "credential" else config

    with FakeProvider([]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate())

    assert caught.value.error_type == "backend_not_configured"
    assert str(expected_path) in str(caught.value)
    assert PRIVATE not in str(caught.value)
    assert fake.requests == []


@pytest.mark.parametrize(
    "status, expected, attempts",
    [
        (400, "request_rejected", 1),
        (401, "credential_rejected", 1),
        (403, "provider_error", 1),
        (404, "provider_error", 1),
        (405, "balance_exhausted", 1),
        (408, "provider_error", 1),
        (422, "provider_error", 1),
        (429, "rate_limited", 4),
        (500, "provider_error", 4),
        (502, "provider_error", 4),
        (503, "provider_error", 4),
        (504, "provider_error", 4),
        (599, "provider_error", 4),
    ],
)
def test_http_faults_retry_rate_limits_and_server_errors(
    configured,
    monkeypatch,
    status,
    expected,
    attempts,
):
    del configured  # Unused.
    profile = load_profile()
    assert profile["name"] == "hive"
    assert profile["statuses"]["405"] == "balance_exhausted"
    assert profile["model"] == PINNED_MODEL
    replies = [
        Reply({"error": PRIVATE}, status, {"Retry-After": "0"})
        for _ in range(attempts)
    ]

    with FakeProvider(replies) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate())

    assert str(caught.value) == str(JudgmentError(expected))
    assert PRIVATE not in str(caught.value)
    assert len(fake.requests) == attempts
    assert all(
        request["body"]["model"] == PINNED_MODEL for request in fake.requests
    )


def test_retry_after_that_exceeds_the_deadline_is_not_retried(
    configured, monkeypatch
):
    del configured  # Unused.
    with FakeProvider(
        [Reply({"error": PRIVATE}, 429, {"Retry-After": "10"})]
    ) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(seconds=0.5))

    assert str(caught.value) == str(JudgmentError("rate_limited"))
    assert len(fake.requests) == 1
    assert fake.requests[0]["body"]["model"] == PINNED_MODEL


@pytest.mark.parametrize(
    "fault, expected",
    [
        ("truncated_at_max_tokens", "truncated_output"),
        ("malformed_output", "malformed_output"),
        ("refusal", "refused"),
        ("all_zero", "invalid_distribution"),
        ("off_sum", "invalid_distribution"),
        ("missing_model", "model_not_confirmed"),
        ("missing_thinking", "thinking_not_confirmed"),
    ],
)
def test_response_faults_fail_once_without_answer_or_diagnostics(
    configured,
    monkeypatch,
    fault,
    expected,
):
    del configured  # Unused.
    body = completion({"q": {"yes": 0.0, "no": 1.0}})
    questions = CHOICE
    message = body["choices"][0]["message"]
    if fault == "truncated_at_max_tokens":
        body["usage"]["completion_tokens"] = load_profile()["request"][
            "max_tokens"
        ]
    elif fault == "malformed_output":
        message["content"] = PRIVATE
    elif fault == "refusal":
        message.update(refusal=PRIVATE, content=None)
    elif fault == "all_zero":
        message["content"] = '{"answers":{"q":{"yes":0,"no":0}}}'
    elif fault == "off_sum":
        message["content"] = '{"answers":{"q":{"yes":0.2,"no":0.2}}}'
    elif fault == "missing_model":
        body.pop("model")
    elif fault == "missing_thinking":
        message.pop("reasoning_content")
        body["usage"].pop("reasoning_tokens")

    with FakeProvider([body]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError) as caught:
            asyncio.run(evaluate(questions=questions))

    assert str(caught.value) == str(JudgmentError(expected))
    assert PRIVATE not in str(caught.value)
    assert len(fake.requests) == 1
    assert fake.requests[0]["body"]["model"] == PINNED_MODEL
    if fault == "truncated_at_max_tokens":
        assert body["choices"][0]["finish_reason"] == "stop"


@pytest.mark.parametrize("probability", [0.0, 0.5])
def test_valid_negative_or_low_confidence_answer_is_returned_once(
    configured,
    monkeypatch,
    probability,
):
    del configured  # Unused.
    with FakeProvider([completion({"q": probability})]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        result = asyncio.run(evaluate())

    assert result["answers"]["q"]["noul"] == probability
    assert len(fake.requests) == 1
    assert fake.requests[0]["body"]["model"] == PINNED_MODEL
