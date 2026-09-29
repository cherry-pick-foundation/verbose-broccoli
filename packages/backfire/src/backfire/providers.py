"""Build profile providers on PyModel and system-one-adapter."""

import asyncio
from dataclasses import replace
from typing import Callable

from jev_judge_mcp.domain import Usage
from jev_judge_mcp.errors import Redactor
import jev_judge_mcp.providers as pymodel
from jev_judge_mcp.providers.base import ProviderConnectionError
from jev_judge_mcp.providers.retry import RetryPolicy
from jev_judge_mcp.providers.retry import TransientFailure
from jev_judge_mcp.settings import Settings
from pydantic import SecretStr
from system_one_adapter import AsyncSystemOneAdapterClient
import system_one_adapter.providers.base as adapter_base
import system_one_adapter.providers.openai as adapter_openai
import typesafe_sdk as typesafe

from backfire.config import load_credential
from backfire.config import load_profile
from backfire.failures import JudgmentError
from backfire.vercel import VercelProvider
from backfire_education.pseudonymize import pseudonymize


class _AnswerlessError(Exception):
    pass


def _retry_policy(profile: dict) -> RetryPolicy | None:
    """Build PyModel's RetryPolicy from the profile's optional retry table."""
    table = profile.get("retry")
    if table is None:
        return None
    try:
        if "statuses" in table:
            table = {**table, "statuses": frozenset(table["statuses"])}
        return RetryPolicy(**table)
    except (OverflowError, TypeError, ValueError):
        raise JudgmentError("backend_not_configured", profile["name"]) from None


class _OpenAIModel(adapter_openai.AsyncOpenAIProvider):
    def __init__(self, profile: dict, key: str) -> None:
        super().__init__(
            profile["model"], base_url=profile["base_url"], api_key=key
        )
        self._request = profile.get("request", {})

    async def request(self, messages, *, schema, structured):
        kwargs = {
            "model": self.model_name,
            "messages": adapter_base.render_messages(messages),
            "response_format": adapter_openai._response_format(  # noqa: SLF001
                schema, structured=structured
            ),
        }
        if self._request:
            kwargs["extra_body"] = self._request
        adapter_base.record_request(kwargs, api=self.api)
        with adapter_base.translating(self.translate_error):
            return adapter_openai._result(  # noqa: SLF001
                await self._client.chat.completions.create(**kwargs)
            )


class _OpenAIProvider(pymodel.JevProvider):
    name, label = "compatible", "backfire profile"

    def __init__(
        self, profile: dict, key: str, *, retry: RetryPolicy | None = None
    ) -> None:
        super().__init__(Redactor([key]), retry=retry)
        self._model = profile["model"]
        self._provider = _OpenAIModel(profile, key)
        self._client = AsyncSystemOneAdapterClient(
            model=self._provider,
            structured_outputs=False,
            llm_answer_mode="probabilities",
            normalize_probabilities=False,
            n_retry_malformed_structure=0,
            retry=typesafe.RetryPolicy(max_retries=0),
        )

    def _transient(self, error: Exception) -> TransientFailure | None:
        if isinstance(error, _AnswerlessError):
            return TransientFailure("connect", detail="reply omitted an answer")
        return super()._transient(error)

    async def _send(self, state, questions, model, timeout):
        try:
            response = await self._client.system_one(
                state,
                questions,
                retry=typesafe.RetryPolicy(max_retries=0, timeout=timeout),
            )
        except typesafe.TypeSafeAPIResponseValidationError as error:
            if error.field_path and (
                error.field_path == "choices"
                or error.field_path.startswith("answers")
            ):
                raise _AnswerlessError from None
            raise pymodel.ProviderError(
                "backfire profile returned an invalid response"
            ) from None
        except typesafe.TypeSafeAPIConnectionError:
            raise ProviderConnectionError(
                "backfire profile connection failed"
            ) from None
        except typesafe.TypeSafeAPIError as error:
            failure = pymodel.ProviderError("backfire profile request failed")
            failure.status = error.status
            raise failure from None
        if questions.keys() - response.answers.keys():
            raise _AnswerlessError
        return pymodel.Evaluation(
            {
                key: answer.model_dump(mode="json")
                for key, answer in response.answers.items()
            },
            Usage(response.usage.input_tokens, response.usage.output_tokens),
            self.name,
            self._model or model,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
        await self._provider.aclose()


class _ProfileProvider(pymodel.JevProvider):
    name, label = "compatible", "backfire profile"

    def __init__(
        self, provider: pymodel.JevProvider, model: str | None, education: bool
    ) -> None:
        super().__init__(Redactor(()))
        self._provider, self._model, self._education = (
            provider,
            model,
            education,
        )
        self.name, self.label = provider.name, provider.label

    async def evaluate(self, state, questions, model, timeout):
        restore = None
        if self._education:
            try:
                state, questions, restore = await asyncio.to_thread(
                    pseudonymize, state, questions
                )
            except JudgmentError as error:
                failure = (
                    pymodel.ProviderConfigError(str(error))
                    if error.error_type == "backend_not_configured"
                    else pymodel.ProviderError(str(error))
                )
                raise failure from None
        result = await self._provider.evaluate(
            state, questions, self._model or model, timeout
        )
        return (
            replace(result, answers=restore(result.answers))
            if restore
            else result
        )

    async def _send(self, state, questions, model, timeout):
        raise NotImplementedError

    async def aclose(self) -> None:
        await self._provider.aclose()


def _jev_provider(
    profile: dict, key: str, *, retry: RetryPolicy | None = None
) -> pymodel.JevProvider:
    name = profile["jev_provider"]
    if name == "vercel":
        return VercelProvider(profile, key, retry=retry)
    secret, values = SecretStr(key), {"jev_provider": name}
    field = {
        "typesafe": "typesafe_api_key",
        "openrouter": "openrouter_api_key",
        "cloudflare": "cloudflare_api_token",
    }.get(name, "jev_api_key")
    values[field] = secret
    if name == "cloudflare":
        values["cloudflare_account_id"] = profile["account_id"]
    elif name == "compatible":
        values["jev_api_base_url"] = SecretStr(profile["base_url"])
    elif name == "typesafe" and "base_url" in profile:
        values["typesafe_base_url"] = SecretStr(profile["base_url"])
    try:
        return pymodel.resolve_provider(
            Settings.model_construct(**values), retry=retry
        )
    except pymodel.ProviderConfigError:
        raise pymodel.ProviderConfigError(
            str(JudgmentError("backend_not_configured", profile["name"]))
        ) from None


def provider_factory(
    *, education: bool = False
) -> Callable[[Settings], pymodel.JevProvider]:
    """Build the provider factory used by PyModel's Runtime."""

    def create(_settings: Settings) -> pymodel.JevProvider:
        del _settings
        try:
            profile = load_profile(education=education)
            retry = _retry_policy(profile)
            key = load_credential(profile)
            provider = (
                _OpenAIProvider(profile, key, retry=retry)
                if profile["api"] == "openai"
                else _jev_provider(profile, key, retry=retry)
            )
        except JudgmentError as error:
            raise pymodel.ProviderConfigError(str(error)) from None
        return _ProfileProvider(provider, profile.get("model"), education)

    return create
