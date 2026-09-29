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
from backfire.providers import _ProfileProvider
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

    def resolve(settings):
        seen.append(settings)
        return object()

    monkeypatch.setattr("backfire.providers.pymodel.resolve_provider", resolve)
    profile = {
        "name": "synthetic",
        "jev_provider": name,
        "base_url": "https://provider.invalid/v1",
    }
    if name == "cloudflare":
        profile["account_id"] = "synthetic-account"
    marker = _jev_provider(profile, "synthetic-key")
    assert marker is not None
    (settings,) = seen
    assert settings.jev_provider == name
    assert (
        getattr(settings, expected_field).get_secret_value() == "synthetic-key"
    )
    if name == "cloudflare":
        assert settings.cloudflare_account_id == "synthetic-account"


def test_profile_configuration_failure_is_a_pymodel_provider_error():
    with pytest.raises(ProviderConfigError, match="^backend_not_configured:"):
        provider_factory()(Settings.model_construct())


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
    wrapped = _ProfileProvider(Stub(), "profile-model", education=True)

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
