"""The in-process judge shared by tools and direct callers."""

import asyncio
from contextlib import aclosing
from typing import Literal, NotRequired, Protocol, TypedDict

from system_one_adapter import AsyncSystemOneAdapterClient
from typesafe_sdk import JSONContent
from typesafe_sdk import Questions

from backfire import config
from backfire.config import load_credential
from backfire.config import load_profile
from backfire.failures import JudgmentError
from backfire.failures import map_error
from backfire.failures import retry_policy
from backfire.provider import ProfileProvider
from backfire.provider import ProviderCall
from backfire.provider import provider_call
from backfire.records import RecordFile
from backfire.validate import validate_answers
from backfire.validate import validate_request


class NoulAnswer(TypedDict):
    """Probability returned for a Noul question."""

    type: Literal["noul"]
    noul: float


class ChoiceAnswer(TypedDict):
    """Selected choice, confidence, and choice probabilities."""

    type: Literal["choice"]
    choice: str
    confidence: float
    probabilities: dict[str, float]


class ScoreAnswer(TypedDict):
    """Score, confidence, probabilities, and score legend."""

    type: Literal["score"]
    score: float
    confidence: float
    probabilities: dict[str, float]
    legend: dict[str, str]


class JudgmentUsage(TypedDict):
    """Input and output token counts for a judgment."""

    input_tokens: int
    output_tokens: int


class JudgmentMetadata(TypedDict):
    """Local timing and thinking measurements for a judgment."""

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
    """Inputs and deadline for one judgment call."""

    state: JSONContent
    questions: Questions
    deadline: float
    record_file: RecordFile | None


class Judge(Protocol):
    """Protocol for asynchronous judgment providers."""

    async def __call__(
        self,
        state: JSONContent,
        questions: Questions,
        *,
        deadline: float,
        record_file: RecordFile | None = None,
    ) -> JudgmentResult:
        """Use an absolute loop deadline; callers may omit record_file.

        Tools provide their deadline and optional session writer. Cancellation
        propagates; the real judge owns validation and record writes.
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
    """Run one judgment with retries inside the caller's deadline."""
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
                # Education is optional in some builds.
                from backfire_education.pseudonymize import (  # noqa: PLC0415
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
    # Map provider failures to fixed errors.
    except Exception as error:  # noqa: BLE001
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
