"""Validate request limits and answer distributions for the pinned adapter."""

from collections.abc import Mapping
import os

from system_one_adapter._schema import (
    convert_question_collection_to_validated_api_question_models,
)
from typesafe_sdk import Answer
from typesafe_sdk import Choice
from typesafe_sdk import ChoiceAnswer
from typesafe_sdk import Noul
from typesafe_sdk import Questions
from typesafe_sdk import Score
from typesafe_sdk import ScoreAnswer

from backfire.failures import JudgmentError
from backfire.lib import PROBABILITY_SUM_TOLERANCE

# Gate 3 synthetic known-answer limits; hard-tier batches are quality guidance.
OPTION_LIMIT = 250
CELL_LIMIT = 672


def validate_request(questions: Questions) -> dict[str, Noul | Choice | Score]:
    """Reuse the adapter's schema and check size before any provider call."""
    if not isinstance(questions, Mapping):
        raise JudgmentError("invalid_request")
    try:
        prepared = convert_question_collection_to_validated_api_question_models(
            questions
        )
    except ValueError:
        raise JudgmentError("invalid_request") from None

    option_limit, cell_limit = OPTION_LIMIT, CELL_LIMIT
    override = os.environ.get("BACKFIRE_TEST_REQUEST_LIMITS")
    if override is not None:
        try:
            option_limit, cell_limit = map(int, override.split(","))
            if min(option_limit, cell_limit) <= 0:
                raise ValueError
        except ValueError:
            raise JudgmentError(
                "backend_not_configured", "BACKFIRE_TEST_REQUEST_LIMITS"
            ) from None

    cells = 0
    for question in prepared.values():
        if (
            isinstance(question, Choice)
            and len(question.criteria) > option_limit
        ):
            raise JudgmentError("request_limit_exceeded")
        cells += 1 if isinstance(question, Noul) else len(question.criteria)
        if cells > cell_limit:
            raise JudgmentError("request_limit_exceeded")
    return prepared


def validate_answers(answers: Mapping[str, Answer]) -> None:
    """Check schema-validated adapter answers without changing any fields.

    The sum check also rejects both all-zero placeholder fallbacks. Noul values,
    including 0.5, and the adapter's score and confidence remain untouched.
    """
    for answer in answers.values():
        if isinstance(answer, (ChoiceAnswer, ScoreAnswer)):
            if (
                not abs(sum(answer.probabilities.values()) - 1)
                <= PROBABILITY_SUM_TOLERANCE
            ):
                raise JudgmentError("invalid_distribution")
