"""The in-process judge shared by tools and direct callers."""

import asyncio
from contextlib import aclosing
from typing import Literal, NotRequired, Protocol, TypedDict

from system_one_adapter import AsyncSystemOneAdapterClient
from typesafe_sdk import JSONContent, Questions

from backfire import config
from backfire.config import load_credential, load_profile
from backfire.failures import JudgmentError, map_error, retry_policy
from backfire.provider import ProfileProvider, ProviderCall, provider_call
from backfire.records import RecordFile
from backfire.validate import validate_answers, validate_request


class NoulAnswer(TypedDict):
    type: Literal["noul"]
    noul: float


class ChoiceAnswer(TypedDict):
    type: Literal["choice"]
    choice: str
    confidence: float
    probabilities: dict[str, float]


class ScoreAnswer(TypedDict):
    type: Literal["score"]
    score: float
    confidence: float
    probabilities: dict[str, float]
    legend: dict[str, str]


class JudgmentUsage(TypedDict):
    input_tokens: int
    output_tokens: int


class JudgmentMetadata(TypedDict):
    attempts: int
    latency_ms: float
    thinking_evidence: bool | None
    reasoning_tokens: int | None


class JudgmentResult(TypedDict):
    """Wire fields and optional local metadata, without adapter diagnostics."""

    model: str
    answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer]
    usage: JudgmentUsage
    metadata: NotRequired[JudgmentMetadata]


class JudgmentRequest(TypedDict):
    state: JSONContent
    questions: Questions
    deadline: float
    record_file: RecordFile | None


class Judge(Protocol):
    async def __call__(
        self,
        state: JSONContent,
        questions: Questions,
        *,
        deadline: float,
        record_file: RecordFile | None = None,
    ) -> JudgmentResult:
        """Use an absolute asyncio-loop deadline; direct callers omit record_file.

        Tools pass their call's deadline and session record writer. Cancellation
        propagates to in-flight work; no result may follow it. Request/answer
        validation and record writes belong to the real judge, not this interface.
        """
        ...


async def judge(
    state: JSONContent,
    questions: Questions,
    *,
    deadline: float,
    record_file: RecordFile | None = None,
    pseudonymize: bool | None = None,
) -> JudgmentResult:
    """Evaluate once with the adapter's retry layer and the caller's deadline."""
    loop = asyncio.get_running_loop()
    started = loop.time()
    call = ProviderCall(deadline)
    token = provider_call.set(call)
    calls_in_flight = (
        sorted(record_file.calls_in_flight) if record_file is not None else []
    )
    profile, result = {}, None
    outcome = "cancelled"
    try:
        prepared = validate_request(questions)
        provider_state, provider_questions, restore = state, questions, None
        enabled = (
            config.load_pseudonymize() if pseudonymize is None else pseudonymize
        )
        if enabled:
            try:
                from backfire_education.pseudonymize import (
                    pseudonymize as replace,
                )
            except ImportError:
                raise JudgmentError(
                    "backend_not_configured", str(config.SHIPPED_CONFIG)
                ) from None
            async with asyncio.timeout_at(deadline):
                (
                    provider_state,
                    provider_questions,
                    restore,
                ) = await asyncio.to_thread(
                    replace,
                    state,
                    prepared,
                )
        profile = load_profile()
        credential = load_credential(profile)
        async with aclosing(ProfileProvider(profile, credential)) as provider:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise JudgmentError("provider_unavailable")
            async with AsyncSystemOneAdapterClient(
                model=provider,
                structured_outputs=False,
                llm_answer_mode="probabilities",
                normalize_probabilities=False,
                n_retry_malformed_structure=0,
                retry=retry_policy(profile, remaining_seconds=remaining),
            ) as client:
                response = await client.system_one(
                    provider_state, provider_questions
                )
                validate_answers(response.answers)
                answers = {
                    key: answer.model_dump(mode="json")
                    for key, answer in response.answers.items()
                }
                result = {
                    "model": call.model,
                    "answers": restore(answers)
                    if restore is not None
                    else answers,
                    "usage": call.usage,
                    "metadata": call.metadata,
                }
        outcome = "ok"
        return result
    except asyncio.CancelledError:
        raise
    except Exception as error:
        failure = (
            JudgmentError("provider_unavailable")
            if isinstance(error, TimeoutError)
            else map_error(error, profile)
        )
        outcome = failure.error_type
        raise failure from None
    finally:
        call.metadata["latency_ms"] = (loop.time() - started) * 1000
        provider_call.reset(token)
        if record_file is not None:
            record_file.write_judgment(
                state=state,
                questions=questions,
                requested_model=profile.get("model"),
                calls_in_flight=calls_in_flight,
                outcome=outcome,
                result=result
                or {"model": call.model, "usage": call.usage or {}},
                metadata=call.metadata,
            )
