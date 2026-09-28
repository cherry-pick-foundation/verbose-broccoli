"""Fixed public errors and retries through the installed SDK's async runner."""

import asyncio
from email.utils import formatdate
from pathlib import Path
import random
import time
import tomllib

import httpx2
import openai
import pytest
from system_one_adapter.providers.openai import AsyncOpenAIProvider
from typesafe_sdk import (
    RetryPolicy,
    TypeSafeAPIConnectionError,
    TypeSafeAPIResponseValidationError,
    TypeSafeAPITimeoutError,
    TypeSafeError,
)
from typesafe_sdk._core.errors import api_error
from typesafe_sdk._core.retry import build_tenacity_async

from backfire.failures import JudgmentError, MESSAGES, map_error, retry_policy

PRIVATE = "synthetic-request-credential-and-provider-body"


@pytest.fixture
def profile():
    with (Path(__file__).parents[1] / "src/backfire/config.toml").open(
        "rb"
    ) as file:
        config = tomllib.load(file)
    return config["providers"][config["provider"]]


def http_error(status, headers=None):
    return api_error(status, {"error": PRIVATE}, httpx2.Headers(headers or {}))


async def failed_attempts(error, profile, remaining_seconds=118):
    attempts, waits = 0, []

    async def call():
        nonlocal attempts
        attempts += 1
        raise error

    async def sleep(delay):
        waits.append(float(delay))

    runner = build_tenacity_async(
        retry_policy(profile, remaining_seconds=remaining_seconds)
    )
    runner.sleep = sleep
    with pytest.raises(type(error)) as caught:
        await runner(call)
    assert caught.value is error
    return attempts, waits


def test_fixed_error_types_and_configuration_detail():
    expected = {
        "invalid_request",
        "request_limit_exceeded",
        "backend_not_configured",
        "pseudonym_conflict",
        "credential_rejected",
        "balance_exhausted",
        "request_rejected",
        "rate_limited",
        "provider_unavailable",
        "provider_error",
        "truncated_output",
        "malformed_output",
        "refused",
        "invalid_distribution",
        "thinking_not_confirmed",
        "model_not_confirmed",
    }
    assert set(MESSAGES) == expected
    for error_type in expected:
        error = JudgmentError(error_type)
        assert error.error_type == error_type
        assert str(error) == f"{error_type}: {error.message}"
        assert (
            "; " in error.message
        )  # Each fixed message gives a cause and an action.
    configured = JudgmentError(
        "backend_not_configured", "/synthetic/config.toml"
    )
    assert configured.message == MESSAGES["backend_not_configured"]
    assert str(configured).endswith(" (/synthetic/config.toml)")
    with pytest.raises(ValueError, match="Only configuration failures"):
        JudgmentError("provider_error", PRIVATE)


@pytest.mark.parametrize(
    "status, expected",
    [
        (400, "request_rejected"),
        (401, "credential_rejected"),
        (403, "provider_error"),
        (404, "provider_error"),
        (405, "balance_exhausted"),
        (408, "provider_error"),
        (422, "provider_error"),
        (429, "rate_limited"),
        (500, "provider_error"),
        (502, "provider_error"),
        (503, "provider_error"),
        (504, "provider_error"),
        (599, "provider_error"),
    ],
)
def test_sdk_status_classes_and_shipped_override(profile, status, expected):
    error = http_error(status, {"x-private": PRIVATE})
    error.debug = {"messages": PRIVATE}
    mapped = map_error(error, profile)
    assert mapped.error_type == expected
    assert mapped.message == MESSAGES[expected]
    assert PRIVATE not in str(mapped) + repr(mapped) + repr(vars(mapped))
    assert not hasattr(mapped, "debug")
    assert mapped.__cause__ is None


@pytest.mark.parametrize(
    "status, override",
    [
        (401, "rate_limited"),
        (429, "balance_exhausted"),
        (400, "credential_rejected"),
        (503, "request_rejected"),
    ],
)
def test_profile_overrides_precede_sdk_classes(status, override):
    assert (
        map_error(
            http_error(status), {"statuses": {str(status): override}}
        ).error_type
        == override
    )


@pytest.mark.parametrize(
    "error, expected",
    [
        (
            TypeSafeAPIResponseValidationError(
                200, PRIVATE, httpx2.Headers(), "answers"
            ),
            "malformed_output",
        ),
        (TypeSafeAPIConnectionError(PRIVATE), "provider_unavailable"),
        (TypeSafeAPITimeoutError(1), "provider_unavailable"),
        (ValueError(PRIVATE), "invalid_request"),
        (TypeSafeError(PRIVATE), "provider_error"),
    ],
)
def test_non_status_errors_are_fixed(error, expected, profile):
    mapped = map_error(error, profile)
    assert mapped.error_type == expected
    assert PRIVATE not in str(mapped) + repr(vars(mapped))


def test_mapping_typed_error_discards_attached_diagnostics(profile):
    original = JudgmentError("backend_not_configured", "/synthetic/config.toml")
    original.debug = PRIVATE
    original.__cause__ = TypeSafeError(PRIVATE)
    mapped = map_error(original, profile)
    assert mapped is not original
    assert str(mapped) == str(original)
    assert not hasattr(mapped, "debug")
    assert mapped.__cause__ is None


@pytest.mark.parametrize(
    "status", [400, 401, 403, 404, 405, 408, 422, 500, 502, 503, 504, 599]
)
def test_shipped_profile_non_retryable_statuses_fail_once(profile, status):
    assert profile["statuses"]["405"] == "balance_exhausted"
    assert asyncio.run(failed_attempts(http_error(status), profile)) == (1, [])


@pytest.mark.parametrize(
    "overrides, status",
    [
        ({}, 429),
        ({"503": "rate_limited"}, 503),
        ({"401": "rate_limited"}, 401),
    ],
)
def test_rate_limits_have_four_total_attempts(overrides, status):
    profile = {"statuses": overrides}
    error = http_error(status, {"Retry-After": "0"})
    assert map_error(error, profile).error_type == "rate_limited"
    assert asyncio.run(failed_attempts(error, profile)) == (4, [0, 0, 0])


def test_override_can_disable_standard_rate_limit_retry():
    profile = {"statuses": {"429": "balance_exhausted"}}
    assert asyncio.run(failed_attempts(http_error(429), profile)) == (1, [])


@pytest.mark.parametrize(
    "name, retried",
    [
        ("ConnectError", True),
        ("ConnectTimeout", True),
        ("ReadError", False),
        ("ReadTimeout", False),
        ("WriteError", False),
        ("WriteTimeout", False),
        ("PoolTimeout", False),
        ("RemoteProtocolError", False),
    ],
)
def test_only_connect_phase_is_retried(profile, name, retried):
    cause = getattr(httpx2, name)(PRIVATE)
    wrapper = Exception(PRIVATE)
    wrapper.__cause__ = cause
    error = (
        TypeSafeAPITimeoutError(5)
        if isinstance(cause, httpx2.TimeoutException)
        else TypeSafeAPIConnectionError(PRIVATE)
    )
    error.__cause__ = wrapper
    assert map_error(error, profile).error_type == "provider_unavailable"
    attempts, waits = asyncio.run(failed_attempts(error, profile))
    assert attempts == (4 if retried else 1)
    assert len(waits) == (3 if retried else 0)


@pytest.mark.parametrize(
    "error", [TypeSafeAPIConnectionError(PRIVATE), TypeSafeAPITimeoutError(5)]
)
def test_unknown_transport_phase_is_not_retried(profile, error):
    assert asyncio.run(failed_attempts(error, profile)) == (1, [])


@pytest.mark.parametrize(
    "error_class, attempts",
    [
        (httpx2.ConnectError, 4),
        (httpx2.ConnectTimeout, 4),
        (httpx2.ReadError, 1),
        (httpx2.ReadTimeout, 1),
    ],
)
def test_real_adapter_preserves_connect_and_read_causes(
    profile, error_class, attempts
):
    async def exercise():
        def fail(request):
            raise error_class(PRIVATE, request=request)

        provider = AsyncOpenAIProvider(
            "synthetic-model",
            base_url="https://provider.invalid/v1",
            api_key="synthetic-key",
        )
        await provider.aclose()
        provider._client = openai.AsyncOpenAI(
            base_url="https://provider.invalid/v1",
            api_key="synthetic-key",
            max_retries=0,
            http_client=httpx2.AsyncClient(
                transport=httpx2.MockTransport(fail)
            ),
        )
        try:
            with pytest.raises(TypeSafeAPIConnectionError) as caught:
                await provider.request([], schema={}, structured=False)
            observed, _ = await failed_attempts(caught.value, profile)
            assert observed == attempts
        finally:
            await provider.aclose()

    asyncio.run(exercise())


@pytest.mark.parametrize("error_type", list(MESSAGES))
def test_typed_failures_are_never_retried(profile, error_type):
    assert asyncio.run(failed_attempts(JudgmentError(error_type), profile)) == (
        1,
        [],
    )


def test_sdk_validation_failure_is_not_retried_even_with_success_status_override():
    profile = {"statuses": {"200": "rate_limited"}}
    error = TypeSafeAPIResponseValidationError(
        200, PRIVATE, httpx2.Headers(), "answers"
    )
    assert map_error(error, profile).error_type == "malformed_output"
    assert asyncio.run(failed_attempts(error, profile)) == (1, [])


def test_backoff_starts_at_one_and_doubles_with_sdk_jitter(
    profile, monkeypatch
):
    monkeypatch.setattr(random, "random", lambda: 0.5)
    policy = retry_policy(profile, remaining_seconds=17)
    assert isinstance(policy, RetryPolicy)
    assert policy.timeout == 17
    assert asyncio.run(failed_attempts(http_error(429), profile)) == (
        4,
        [0.875, 1.75, 3.5],
    )


@pytest.mark.parametrize(
    "headers, delay",
    [
        ({"Retry-After": "2"}, 2),
        ({"Retry-After": "0.125"}, 0.125),
        ({"retry-after-ms": "25", "Retry-After": "2"}, 0.025),
        ({"Retry-After": formatdate(1_000_002, usegmt=True)}, 2),
    ],
)
def test_sdk_retry_after_is_honored(profile, headers, delay, monkeypatch):
    monkeypatch.setattr(time, "time", lambda: 1_000_000)
    assert asyncio.run(failed_attempts(http_error(429, headers), profile)) == (
        4,
        [delay] * 3,
    )


@pytest.mark.parametrize(
    "status, headers, budget",
    [
        (429, {"Retry-After": "10"}, 1),
        (429, {"Retry-After": "1"}, 1),
        (503, {"retry-after-ms": "250"}, 0.1),
        (429, {}, 0.5),
    ],
)
def test_retry_wait_must_fit_remaining_budget(status, headers, budget):
    profile = {"statuses": {"503": "rate_limited"}}
    assert asyncio.run(
        failed_attempts(http_error(status, headers), profile, budget)
    ) == (1, [])


def test_attempt_time_reduces_remaining_retry_budget(profile):
    async def exercise():
        attempts = 0
        error = http_error(429, {"Retry-After": "0.1"})

        async def call():
            nonlocal attempts
            attempts += 1
            await asyncio.sleep(0.02)
            raise error

        runner = build_tenacity_async(
            retry_policy(profile, remaining_seconds=0.11)
        )
        with pytest.raises(type(error)) as caught:
            await runner(call)
        assert caught.value is error
        assert attempts == 1

    asyncio.run(exercise())


@pytest.mark.parametrize("answer", [0, 0.5, False])
def test_valid_low_confidence_or_negative_answer_is_final(profile, answer):
    async def exercise():
        attempts = 0

        async def call():
            nonlocal attempts
            attempts += 1
            return answer

        result = await build_tenacity_async(
            retry_policy(profile, remaining_seconds=118)
        )(call)
        assert result is answer
        assert attempts == 1

    asyncio.run(exercise())


def test_cancellation_ends_pending_sdk_retry(profile):
    async def exercise():
        waiting = asyncio.Event()
        attempts = 0

        async def call():
            nonlocal attempts
            attempts += 1
            raise http_error(429, {"Retry-After": "10"})

        async def sleep(delay):
            waiting.set()
            await asyncio.sleep(delay)

        runner = build_tenacity_async(
            retry_policy(profile, remaining_seconds=118)
        )
        runner.sleep = sleep
        task = asyncio.create_task(runner(call))
        await asyncio.wait_for(waiting.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert attempts == 1

    asyncio.run(exercise())
