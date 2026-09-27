"""The in-process judge contract for tools and direct callers."""

from pathlib import Path
from typing import Literal, Protocol, TypedDict

from typesafe_sdk import JSONContent, Questions


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


class JudgmentResult(TypedDict):
    """Only the wire fields, without the adapter's diagnostic objects."""

    model: str
    answers: dict[str, NoulAnswer | ChoiceAnswer | ScoreAnswer]
    usage: JudgmentUsage


class JudgmentRequest(TypedDict):
    state: JSONContent
    questions: Questions
    deadline: float
    record_file: Path | None


class Judge(Protocol):
    async def __call__(
        self,
        state: JSONContent,
        questions: Questions,
        *,
        deadline: float,
        record_file: Path | None = None,
    ) -> JudgmentResult:
        """Use an absolute asyncio-loop deadline; direct callers omit record_file.

        Tools pass their call's deadline and session record path. Cancellation
        propagates to in-flight work; no result may follow it. Request/answer
        validation and record writes belong to the real judge, not this interface.
        """
        ...
