"""Build profile providers on PyModel and system-one-adapter."""

import asyncio
from dataclasses import replace
import logging
import re
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
from backfire.config import load_profiles
from backfire.credit import check_credit
from backfire.failures import JudgmentError
from backfire_education.pseudonymize import pseudonymize
from backfire_education.pseudonymize import strings

logger = logging.getLogger(__name__)
# Hangul syllables and Jamo, composed or decomposed.
_HANGUL = re.compile(
    "[\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\uac00-\ud7af\ud7b0-\ud7ff"
    "\uffa0-\uffdc]"
)


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
            raise self._status_error(error.status, str(error)) from None
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


def _build_provider(
    profile: dict, key: str, retry: RetryPolicy | None
) -> pymodel.JevProvider:
    return (
        _OpenAIProvider(profile, key, retry=retry)
        if profile["api"] == "openai"
        else _jev_provider(profile, key, retry=retry)
    )


class _OrderProvider(pymodel.JevProvider):
    name, label = "compatible", "backfire profile"

    def __init__(self, profiles: list[dict], education: bool) -> None:
        super().__init__(Redactor(()))
        self.name = profiles[0]["name"] if profiles else "compatible"
        self._profiles = profiles
        self._education = education
        self._profile_index = 0
        self._current: tuple[dict, pymodel.JevProvider] | None = None
        self._providers: list[pymodel.JevProvider] = []
        self._lock = asyncio.Lock()

    async def _next_profile(
        self,
    ) -> tuple[dict, pymodel.JevProvider] | None:
        while self._profile_index < len(self._profiles):
            profile = self._profiles[self._profile_index]
            try:
                retry = _retry_policy(profile)
                key = load_credential(profile)
                provider = _build_provider(profile, key, retry)
                if "codexbar" in profile:
                    credit = await asyncio.to_thread(
                        check_credit,
                        profile["codexbar"],
                        profile["credential"],
                        key,
                    )
                    if credit is False:
                        logger.warning(
                            "skipping profile %s: no credit", profile["name"]
                        )
                        await provider.aclose()
                        self._profile_index += 1
                        continue
                    if credit is None:
                        logger.warning(
                            "credit unknown for profile %s; using it",
                            profile["name"],
                        )
            except JudgmentError as error:
                raise pymodel.ProviderConfigError(str(error)) from None
            self._profile_index += 1
            self._providers.append(provider)
            self._current = (profile, provider)
            self.name = profile["name"]
            return self._current
        return None

    async def _active_profile(
        self,
    ) -> tuple[dict, pymodel.JevProvider] | None:
        async with self._lock:
            return self._current or await self._next_profile()

    async def _after_insufficient_balance(
        self, failed: tuple[dict, pymodel.JevProvider]
    ) -> None:
        async with self._lock:
            if self._current is failed:
                self._current = None
                current = await self._next_profile()
                if current is not None:
                    logger.warning(
                        "switching profile from %s to %s after insufficient "
                        "balance",
                        failed[0]["name"],
                        current[0]["name"],
                    )

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
        if any(_HANGUL.search(text) for text in strings((state, questions))):
            raise pymodel.ProviderError(str(JudgmentError("hangul_remaining")))
        while True:
            current = await self._active_profile()
            if current is None:
                raise pymodel.ProviderError(str(JudgmentError("no_credit")))
            profile, provider = current
            try:
                result = await provider.evaluate(
                    state, questions, profile.get("model") or model, timeout
                )
            except pymodel.ProviderError as error:
                match = re.match(
                    rf"^{re.escape(provider.label)} (\d+):", str(error)
                )
                if match is None or int(match.group(1)) not in profile.get(
                    "insufficient_balance", [402]
                ):
                    raise
                await self._after_insufficient_balance(current)
                continue
            return replace(
                result,
                answers=restore(result.answers) if restore else result.answers,
                provider=profile["name"],
            )

    async def _send(self, state, questions, model, timeout):
        raise NotImplementedError

    async def aclose(self) -> None:
        for provider in self._providers:
            await provider.aclose()


def _jev_provider(
    profile: dict, key: str, *, retry: RetryPolicy | None = None
) -> pymodel.JevProvider:
    name = profile["jev_provider"]
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
            profiles = load_profiles()
        except JudgmentError as error:
            raise pymodel.ProviderConfigError(str(error)) from None
        return _OrderProvider(profiles, education)

    return create
