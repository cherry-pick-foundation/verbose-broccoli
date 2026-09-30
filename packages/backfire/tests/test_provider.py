"""The profile adapter keeps retry ownership in PyModel."""

import asyncio

from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
from jev_judge_mcp.domain import NoulCriteria
from jev_judge_mcp.domain import NoulQuestion
from jev_judge_mcp.domain import Usage
from jev_judge_mcp.providers import Evaluation
from jev_judge_mcp.providers import ProviderConfigError
from jev_judge_mcp.providers.retry import RetryPolicy
from jev_judge_mcp.settings import Settings
import pytest

from backfire.providers import _jev_provider
from backfire.providers import _OpenAIProvider
from backfire.providers import _OrderProvider
from backfire.providers import provider_factory

QUESTIONS = {
    "q": NoulQuestion("synthetic proposition", NoulCriteria("true", "false"))
}


def provider(profile, script):
    fake = FakeProvider(script)
    fake.__enter__()
    profile["base_url"] = fake.base_url
    result = _OpenAIProvider(profile, "synthetic-key")
    result._retry = RetryPolicy(
        max_attempts=2,
        per_attempt_timeout=2,
        backoff_initial=0.001,
        backoff_max=0.001,
        backoff_jitter=0,
        budget=4,
    )
    return fake, result


def test_answerless_reply_gets_one_pymodel_retry():
    empty = completion({})
    fake, client = provider(
        {"model": "synthetic-model", "request": {}},
        [empty, completion({"q": 0.75})],
    )

    async def run():
        try:
            return await client.evaluate(
                {"claim": "synthetic"}, QUESTIONS, "model", 3
            )
        finally:
            await client.aclose()

    try:
        result = asyncio.run(run())
        assert result.answers["q"]["noul"] == 0.75
        assert len(fake.requests) == 2
    finally:
        fake.__exit__()


def test_status_retry_uses_pymodel_policy():
    fake, client = provider(
        {"model": "synthetic-model", "request": {}},
        [Reply({"error": "synthetic"}, status=503), completion({"q": 0.75})],
    )

    async def run():
        try:
            return await client.evaluate(
                {"claim": "synthetic"}, QUESTIONS, "model", 3
            )
        finally:
            await client.aclose()

    try:
        assert asyncio.run(run()).answers["q"]["noul"] == 0.75
        assert len(fake.requests) == 2
    finally:
        fake.__exit__()


def test_profile_retry_policy_allows_reply_after_default_attempt(monkeypatch):
    retry = {
        "max_attempts": 1,
        "per_attempt_timeout": 0.15,
        "budget": 0.2,
        "backoff_initial": 0.001,
        "backoff_max": 0.001,
        "backoff_jitter": 0,
    }
    policy = RetryPolicy(**retry)
    with FakeProvider([Reply(completion({"q": 0.75}), delay=0.04)]) as fake:
        profile = {
            "name": "synthetic",
            "api": "openai",
            "base_url": fake.base_url,
            "model": "synthetic-model",
            "request": {},
            "retry": retry,
        }
        monkeypatch.setattr(
            "backfire.providers.load_profiles", lambda **_: [profile]
        )
        monkeypatch.setattr(
            "backfire.providers.load_credential", lambda _: "synthetic-key"
        )
        monkeypatch.setattr(
            "jev_judge_mcp.providers.base.DEFAULT_RETRY_POLICY",
            RetryPolicy(
                max_attempts=1,
                per_attempt_timeout=0.01,
                backoff_initial=0.001,
                backoff_max=0.001,
                backoff_jitter=0,
                budget=0.02,
            ),
        )
        client = provider_factory()(Settings.model_construct())

        async def run():
            try:
                result = await client.evaluate(
                    {"claim": "synthetic"}, QUESTIONS, "model", 2
                )
                assert client._current[1]._retry == policy
                return result
            finally:
                await client.aclose()

        assert asyncio.run(run()).answers["q"]["noul"] == 0.75
        assert len(fake.requests) == 1


@pytest.mark.parametrize(
    "retry",
    [
        {"per_attempt_timout": 0.1},
        {"per_attempt_timeout": 0},
        {"budget": "118"},
    ],
)
def test_invalid_profile_retry_fails_before_key_load(monkeypatch, retry):
    profile = {
        "name": "synthetic-profile",
        "api": "openai",
        "retry": retry,
    }
    monkeypatch.setattr(
        "backfire.providers.load_profiles", lambda **_: [profile]
    )
    monkeypatch.setattr(
        "backfire.providers.load_credential",
        lambda _: pytest.fail("invalid retry reached credential loading"),
    )

    client = provider_factory()(Settings.model_construct())

    async def run():
        await client.evaluate({"claim": "synthetic"}, QUESTIONS, "model", 2)

    with pytest.raises(ProviderConfigError, match="synthetic-profile"):
        asyncio.run(run())


@pytest.mark.parametrize(
    ("name", "expected_field"),
    [
        ("typesafe", "typesafe_api_key"),
        ("openrouter", "openrouter_api_key"),
        ("cloudflare", "cloudflare_api_token"),
        ("compatible", "jev_api_key"),
    ],
)
def test_jev_profiles_use_pymodel_resolver(monkeypatch, name, expected_field):
    seen = []

    def resolve(settings, *, retry):
        seen.append((settings, retry))
        return object()

    monkeypatch.setattr("backfire.providers.pymodel.resolve_provider", resolve)
    profile = {
        "name": "synthetic",
        "jev_provider": name,
        "base_url": "https://provider.invalid/v1",
    }
    if name == "cloudflare":
        profile["account_id"] = "synthetic-account"
    policy = RetryPolicy(max_attempts=1)
    marker = _jev_provider(profile, "synthetic-key", retry=policy)
    assert marker is not None
    settings, retry = seen[0]
    assert retry is policy
    assert settings.jev_provider == name
    assert (
        getattr(settings, expected_field).get_secret_value() == "synthetic-key"
    )
    if name == "cloudflare":
        assert settings.cloudflare_account_id == "synthetic-account"


@pytest.mark.parametrize("name", ["cloudflare", "compatible"])
def test_jev_profiles_require_provider_fields_before_key_load(
    monkeypatch, name
):
    monkeypatch.setattr(
        "backfire.providers.load_profiles",
        lambda **_: [
            {
                "name": "synthetic-profile",
                "api": "jev",
                "jev_provider": name,
            }
        ],
    )
    monkeypatch.setattr(
        "backfire.providers.load_credential",
        lambda _: pytest.fail("incomplete profile reached credential loading"),
    )

    client = provider_factory()(Settings.model_construct())

    async def run():
        await client.evaluate({"claim": "synthetic"}, QUESTIONS, "model", 2)

    with pytest.raises(
        ProviderConfigError, match="^backend_not_configured:"
    ) as caught:
        asyncio.run(run())
    assert "synthetic-profile" in str(caught.value)


def test_vercel_profile_receives_pymodel_retry():
    policy = RetryPolicy(max_attempts=1)
    marker = _jev_provider(
        {
            "name": "synthetic",
            "jev_provider": "vercel",
            "base_url": "https://provider.invalid/v1",
        },
        "synthetic-key",
        retry=policy,
    )

    assert marker._retry is policy


def test_profile_configuration_failure_is_a_pymodel_provider_error():
    client = provider_factory()(Settings.model_construct())

    async def run():
        try:
            await client.evaluate({"claim": "synthetic"}, QUESTIONS, "model", 2)
        finally:
            await client.aclose()

    with pytest.raises(ProviderConfigError, match="^backend_not_configured:"):
        asyncio.run(run())


def test_education_wrapper_pseudonymizes_before_delegating(monkeypatch):
    seen = {}

    class Stub:
        name = "compatible"
        label = "stub"

        async def evaluate(self, state, questions, model, timeout):
            seen.update(
                state=state, questions=questions, model=model, timeout=timeout
            )
            return Evaluation({"masked": 0.8}, Usage(1, 2), "compatible", model)

        async def aclose(self):
            return None

    def pseudonymize(state, questions):
        assert state == {"record": "synthetic source"}
        return (
            {"record": "masked source"},
            {"masked": questions["q"]},
            lambda answers: {"q": answers["masked"]},
        )

    monkeypatch.setattr("backfire.providers.pseudonymize", pseudonymize)
    monkeypatch.setattr(
        "backfire.providers.load_credential", lambda _: "synthetic-key"
    )
    monkeypatch.setattr("backfire.providers._build_provider", lambda *_: Stub())
    wrapped = _OrderProvider(
        [
            {
                "name": "synthetic-profile",
                "credential": "SYNTHETIC_KEY",
                "model": "profile-model",
            }
        ],
        education=True,
    )

    async def run():
        return await wrapped.evaluate(
            {"record": "synthetic source"}, {"q": "question"}, "default", 2
        )

    result = asyncio.run(run())
    assert seen == {
        "state": {"record": "masked source"},
        "questions": {"masked": "question"},
        "model": "profile-model",
        "timeout": 2,
    }
    assert result.answers == {"q": 0.8}
