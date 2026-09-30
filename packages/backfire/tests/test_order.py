"""The profile order skips empty credit and switches on configured statuses."""

import asyncio
import csv
import json

from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
from jev_judge_mcp.domain import NoulCriteria
from jev_judge_mcp.domain import NoulQuestion
from jev_judge_mcp.domain import Usage
from jev_judge_mcp.errors import Redactor
from jev_judge_mcp.providers import Evaluation
from jev_judge_mcp.providers import JevProvider
from jev_judge_mcp.providers import ProviderConfigError
from jev_judge_mcp.providers import ProviderError
import pytest

from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.providers import _OrderProvider
from backfire_education.pseudonymize import (
    pseudonymize as education_pseudonymize,
)

QUESTIONS = {
    "q": NoulQuestion("synthetic proposition", NoulCriteria("true", "false"))
}


def openai_profile(name, fake, **fields):
    return {
        "name": name,
        "api": "openai",
        "base_url": fake.base_url,
        "model": "synthetic-model",
        "credential": "SYNTHETIC_API_KEY",
        "request": {},
        **fields,
    }


def wrapper(monkeypatch, profiles, *, credit=None):
    monkeypatch.setattr(
        "backfire.providers.load_credential", lambda _: "synthetic-key"
    )
    if credit is not None:
        monkeypatch.setattr("backfire.providers.check_credit", credit)
    return _OrderProvider(profiles, education=False)


async def ask(provider, state=None, questions=None):
    return await provider.evaluate(
        {"claim": "synthetic"} if state is None else state,
        QUESTIONS if questions is None else questions,
        "default-model",
        3,
    )


def test_skip_zero_credit_profile_without_sending_a_request(monkeypatch):
    with FakeProvider([]) as empty:
        with FakeProvider([completion({"q": 0.75})]) as full:
            checked = []

            def credit(provider, credential, key):
                checked.append((provider, credential, key))
                return False

            client = wrapper(
                monkeypatch,
                [
                    openai_profile("empty", empty, codexbar="openrouter"),
                    openai_profile("available", full),
                ],
                credit=credit,
            )

            async def run():
                try:
                    return await ask(client)
                finally:
                    await client.aclose()

            result = asyncio.run(run())

    assert checked == [("openrouter", "SYNTHETIC_API_KEY", "synthetic-key")]
    assert empty.requests == []
    assert len(full.requests) == 1
    assert result.provider == "available"


def test_unknown_credit_uses_the_profile(monkeypatch, caplog):
    with FakeProvider([completion({"q": 0.75})]) as provider:
        client = wrapper(
            monkeypatch,
            [openai_profile("unknown", provider, codexbar="openrouter")],
            credit=lambda *_: None,
        )

        async def run():
            try:
                return await ask(client)
            finally:
                await client.aclose()

        result = asyncio.run(run())

    assert len(provider.requests) == 1
    assert result.provider == "unknown"
    assert "credit unknown for profile unknown" in caplog.text


def test_mid_run_switch_reuses_the_target_for_later_judgments(monkeypatch):
    with FakeProvider([Reply({"error": "synthetic"}, status=402)]) as first:
        with FakeProvider(
            [completion({"q": 0.75}), completion({"q": 0.8})]
        ) as second:
            client = wrapper(
                monkeypatch,
                [
                    openai_profile("first", first, insufficient_balance=[402]),
                    openai_profile("second", second),
                ],
            )

            async def run():
                try:
                    initial = await ask(client)
                    later = await ask(client, {"claim": "second judgment"})
                    return initial, later
                finally:
                    await client.aclose()

            initial, later = asyncio.run(run())

    assert len(first.requests) == 1
    assert len(second.requests) == 2
    assert initial.provider == later.provider == "second"


def test_switch_target_without_credit_is_skipped(monkeypatch):
    with FakeProvider([Reply({"error": "synthetic"}, status=402)]) as first:
        with FakeProvider([]) as empty:
            with FakeProvider([completion({"q": 0.75})]) as last:
                checks = []

                def credit(provider, _credential, _key):
                    del _credential, _key
                    checks.append(provider)
                    return False if provider == "vercel" else True

                client = wrapper(
                    monkeypatch,
                    [
                        openai_profile(
                            "first", first, insufficient_balance=[402]
                        ),
                        openai_profile("empty", empty, codexbar="vercel"),
                        openai_profile("last", last),
                    ],
                    credit=credit,
                )

                async def run():
                    try:
                        return await ask(client)
                    finally:
                        await client.aclose()

                result = asyncio.run(run())

    assert checks == ["vercel"]
    assert len(first.requests) == 1
    assert empty.requests == []
    assert len(last.requests) == 1
    assert result.provider == "last"


@pytest.mark.parametrize("status", [400, 401])
def test_other_client_errors_do_not_switch(monkeypatch, status):
    with FakeProvider([Reply({"error": "synthetic"}, status=status)]) as first:
        with FakeProvider([]) as second:
            client = wrapper(
                monkeypatch,
                [
                    openai_profile("first", first, insufficient_balance=[405]),
                    openai_profile("second", second),
                ],
            )

            async def run():
                try:
                    await ask(client)
                finally:
                    await client.aclose()

            with pytest.raises(ProviderError, match=f"{status}:"):
                asyncio.run(run())

    assert len(first.requests) == 1
    assert second.requests == []


def test_exhausted_transient_retries_do_not_switch(monkeypatch):
    retry = {
        "max_attempts": 2,
        "per_attempt_timeout": 2,
        "backoff_initial": 0.001,
        "backoff_max": 0.001,
        "backoff_jitter": 0,
        "budget": 4,
    }
    with FakeProvider([Reply({"error": "synthetic"}, status=503)] * 2) as first:
        with FakeProvider([]) as second:
            client = wrapper(
                monkeypatch,
                [
                    openai_profile("first", first, retry=retry),
                    openai_profile("second", second),
                ],
            )

            async def run():
                try:
                    await ask(client)
                finally:
                    await client.aclose()

            with pytest.raises(ProviderError, match="after 2 attempts"):
                asyncio.run(run())

    assert len(first.requests) == 2
    assert second.requests == []


def test_no_credit_after_the_last_profile_runs_out(monkeypatch):
    with FakeProvider([Reply({"error": "synthetic"}, status=405)]) as last:
        client = wrapper(
            monkeypatch,
            [openai_profile("last", last, insufficient_balance=[405])],
        )

        async def run():
            try:
                await ask(client)
            finally:
                await client.aclose()

        with pytest.raises(
            ProviderError,
            match="^no_credit: No profile in the order has credit",
        ):
            asyncio.run(run())

    assert len(last.requests) == 1


def test_configuration_error_does_not_advance_to_another_profile(
    monkeypatch,
):
    with FakeProvider([]) as first:
        with FakeProvider([]) as second:
            client = wrapper(
                monkeypatch,
                [
                    openai_profile("first", first),
                    openai_profile("second", second),
                ],
            )
            attempts = []

            def missing_key(profile):
                attempts.append(profile["name"])
                raise JudgmentError(
                    "backend_not_configured", "synthetic-profile"
                )

            monkeypatch.setattr(
                "backfire.providers.load_credential", missing_key
            )

            async def run():
                try:
                    for _ in range(2):
                        with pytest.raises(ProviderConfigError):
                            await ask(client)
                finally:
                    await client.aclose()

            asyncio.run(run())

    assert attempts == ["first", "first"]
    assert second.requests == []


def test_concurrent_failures_advance_once(monkeypatch):
    with FakeProvider([Reply({"error": "synthetic"}, status=405)] * 2) as first:
        with FakeProvider(
            [completion({"q": 0.75}), completion({"q": 0.8})]
        ) as second:
            with FakeProvider([]) as third:
                client = wrapper(
                    monkeypatch,
                    [
                        openai_profile(
                            "first", first, insufficient_balance=[405]
                        ),
                        openai_profile("second", second),
                        openai_profile("third", third),
                    ],
                )

                async def run():
                    try:
                        return await asyncio.gather(ask(client), ask(client))
                    finally:
                        await client.aclose()

                results = asyncio.run(run())

    assert len(first.requests) == 2
    assert len(second.requests) == 2
    assert third.requests == []
    assert {result.provider for result in results} == {"second"}


class EducationProvider(JevProvider):
    name = "compatible"
    label = "synthetic"

    def __init__(self, *, exhausted=False):
        super().__init__(Redactor(()))
        self.exhausted = exhausted
        self.calls = []

    async def _send(self, state, questions, model, timeout):
        del timeout
        self.calls.append({"state": state, "questions": questions})
        if self.exhausted:
            raise self._status_error(405, "synthetic exhausted")
        return Evaluation(
            {key: {"noul": 0.8} for key in questions},
            Usage(1, 2),
            self.name,
            model,
        )

    async def aclose(self):
        return None


def test_education_switch_masks_once_and_restores_answers(
    tmp_path, monkeypatch
):
    config_root, data_root = tmp_path / "config", tmp_path / "data"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_root))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_root))
    roster = tmp_path / "roster.csv"
    with roster.open("w", encoding="utf-8", newline="") as file:
        csv.writer(file).writerows([("name",), ("가라온",)])
    config = xdg_path("config") / "backfire" / "education.toml"
    config.parent.mkdir(parents=True)
    config.write_text(f"roster = {json.dumps(str(roster))}\n", encoding="utf-8")

    first, second = EducationProvider(exhausted=True), EducationProvider()
    monkeypatch.setattr("backfire.providers.load_credential", lambda _: "key")

    def build(profile, key, retry):
        del key, retry
        return first if profile["name"] == "hive" else second

    monkeypatch.setattr("backfire.providers._build_provider", build)
    checks = []

    def check(provider, credential, key):
        del credential, key
        checks.append(provider)
        return True

    monkeypatch.setattr("backfire.providers.check_credit", check)
    calls = []

    def pseudonymize(state, questions):
        calls.append(None)
        return education_pseudonymize(state, questions)

    monkeypatch.setattr("backfire.providers.pseudonymize", pseudonymize)
    client = _OrderProvider(
        [
            {
                "name": "hive",
                "credential": "SYNTHETIC_API_KEY",
                "api": "openai",
                "insufficient_balance": [405],
            },
            {
                "name": "openrouter",
                "credential": "SYNTHETIC_API_KEY",
                "api": "jev",
                "codexbar": "openrouter",
            },
        ],
        education=True,
    )
    original_questions = {
        "가라온의 판단": NoulQuestion(
            "synthetic", NoulCriteria("true", "false")
        )
    }

    async def run():
        try:
            return await ask(
                client,
                {"claim": "가라온은 synthetic claim을 읽는다."},
                original_questions,
            )
        finally:
            await client.aclose()

    result = asyncio.run(run())

    assert len(calls) == 1
    assert checks == ["openrouter"]
    assert "가라온" not in json.dumps(second.calls[0], ensure_ascii=False)
    assert "학생" in json.dumps(second.calls[0], ensure_ascii=False)
    assert set(result.answers) == set(original_questions)
    assert result.provider == "openrouter"


def test_openai_profile_switches_on_405(monkeypatch):
    with FakeProvider([Reply({"error": "synthetic"}, status=405)]) as first:
        with FakeProvider([completion({"q": 0.75})]) as second:
            client = wrapper(
                monkeypatch,
                [
                    openai_profile("first", first, insufficient_balance=[405]),
                    openai_profile("second", second),
                ],
            )

            async def run():
                try:
                    return await ask(client)
                finally:
                    await client.aclose()

            result = asyncio.run(run())

    assert len(first.requests) == 1
    assert len(second.requests) == 1
    assert result.provider == "second"
