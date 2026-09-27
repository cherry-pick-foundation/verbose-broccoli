"""Offline checks using the pinned adapter's real question and answer models."""

import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from system_one_adapter import AsyncSystemOneAdapterClient
from system_one_adapter.providers.base import ProviderResult
from typesafe_sdk import Choice, Noul, Score

from backfire.failures import JudgmentError
from backfire.tools.answers import validate_score_answer
from backfire.validate import validate_answers, validate_request


def question(kind, count=3):
    criteria = [f"Level {index}" for index in range(count)]
    if kind == "choice":
        criteria = {str(index): value for index, value in enumerate(criteria)}
    return {"type": kind, "criteria": criteria}


def provider_for(raw_answers):
    return SimpleNamespace(
        model_name="synthetic-model",
        request=AsyncMock(return_value=ProviderResult(json.dumps({"answers": raw_answers}), 1, 1)),
        translate_error=lambda error: error,
    )


async def adapter_response(questions, provider):
    async with AsyncSystemOneAdapterClient(
        model=provider, structured_outputs=False, llm_answer_mode="probabilities",
        normalize_probabilities=False, n_retry_malformed_structure=0,
    ) as client:
        return await client.system_one("Synthetic evidence", questions)


def distribution_answer(kind, probabilities):
    return asyncio.run(adapter_response(
        {"q": question(kind, len(probabilities))},
        provider_for({"q": {str(index): value for index, value in enumerate(probabilities)}}),
    )).answers["q"]


@pytest.mark.parametrize("kind", ["choice", "score"])
@pytest.mark.parametrize("probabilities", [
    [0, 0, 1], [0.5, 0.5, 0], [1 / 3, 1 / 3, 1 / 3],
    [0, 0, 0.99], [1, 0.01, 0],
    [0, 0, 0.99 - 0.5e-12], [1, 0.01 + 0.5e-12, 0],
])
def test_allowed_distributions_preserve_every_adapter_field(kind, probabilities):
    answer = distribution_answer(kind, probabilities)
    before = deepcopy(answer.model_dump(mode="json"))
    validate_answers({"q": answer})
    assert answer.model_dump(mode="json") == before
    assert list(answer.probabilities.values()) == probabilities


@pytest.mark.parametrize("kind", ["choice", "score"])
@pytest.mark.parametrize("probabilities", [
    [0.3, 0.3, 0.3], [0, 0, 0.98], [1, 0.011, 0],
    [0, 0, 0.99 - 2e-12], [1, 0.01 + 2e-12, 0],
])
def test_sums_outside_tolerance_are_rejected(kind, probabilities):
    answer = distribution_answer(kind, probabilities)
    with pytest.raises(JudgmentError, match="^invalid_distribution: "):
        validate_answers({"q": answer})


@pytest.mark.parametrize("kind", ["choice", "score"])
def test_both_all_zero_adapter_fallbacks_are_rejected(kind):
    answer = distribution_answer(kind, [0, 0, 0])
    if kind == "choice":
        assert answer.choice == "0"
    else:
        assert answer.score == 1
    assert list(answer.probabilities.values()) == [0, 0, 0]
    with pytest.raises(JudgmentError, match="^invalid_distribution: "):
        validate_answers({"q": answer})


@pytest.mark.parametrize("probability", [0, 0.5, 1])
def test_returned_noul_values_include_genuine_uncertainty(probability):
    answers = asyncio.run(adapter_response(
        {"q": {"type": "noul"}}, provider_for({"q": probability}),
    )).answers
    validate_answers(answers)
    assert answers["q"].noul == probability


@pytest.mark.parametrize("probabilities, expected", [
    ([0, 0.005, 1], 2.005 / 1.005),
    ([0, 0.01, 1], 2.01 / 1.01),
    ([0.01, 0, 1], 2 / 1.01),
    ([0, 0, 0.99], 2),
])
def test_research_score_values_keep_adapter_mean_and_pass_tool_check(probabilities, expected):
    answer = distribution_answer("score", probabilities)
    before = answer.model_dump(mode="json")
    validate_answers({"q": answer})
    assert answer.score == pytest.approx(expected)
    assert answer.model_dump(mode="json") == before
    assert validate_score_answer(before) is not None


@pytest.mark.parametrize("questions", [
    {"q": question("choice", 250)},
    {f"item{index}": question("choice", 5) for index in range(60)},
    {f"item{index}": question("choice", 21) for index in range(32)},
    {f"noul{index}": {"type": "noul"} for index in range(672)},
    {f"score{index}": question("score") for index in range(224)},
    {"choice": question("choice", 250), "score": question("score", 421), "noul": {"type": "noul"}},
    {"score": question("score", 672)},
])
def test_requests_at_limits_are_accepted_without_changing_inputs(questions, monkeypatch):
    monkeypatch.delenv("BACKFIRE_TEST_REQUEST_LIMITS", raising=False)
    before = deepcopy(questions)
    prepared = validate_request(questions)
    assert list(prepared) == list(questions)
    assert all(isinstance(item, (Noul, Choice, Score)) for item in prepared.values())
    assert questions == before


@pytest.mark.parametrize("questions", [
    {"q": question("choice", 251)},
    {**{f"item{index}": question("choice", 21) for index in range(32)}, "extra": {"type": "noul"}},
    {f"noul{index}": {"type": "noul"} for index in range(673)},
    {"score": question("score", 673)},
    {"choice": question("choice", 250), "score": question("score", 422), "noul": {"type": "noul"}},
])
def test_requests_over_limits_fail_before_provider_call(questions, monkeypatch):
    monkeypatch.delenv("BACKFIRE_TEST_REQUEST_LIMITS", raising=False)
    provider = provider_for({})

    async def evaluate():
        prepared = validate_request(questions)
        return await adapter_response(prepared, provider)

    with pytest.raises(JudgmentError, match="^request_limit_exceeded: "):
        asyncio.run(evaluate())
    provider.request.assert_not_called()


@pytest.mark.parametrize("questions", [
    {}, [], ["private-question"], {"q": {"type": "unknown"}},
    {"q": {"type": "choice"}}, {"q": question("choice", 1)},
    {"q": question("score", 1)}, {"q": {"type": "noul", "private-question": True}},
])
def test_invalid_questions_use_adapter_schema_and_fixed_error(questions):
    with pytest.raises(JudgmentError, match="^invalid_request: ") as caught:
        validate_request(questions)
    assert "private-question" not in str(caught.value)


def test_question_models_are_revalidated():
    questions = {"noul": Noul(), "choice": Choice(criteria={"a": None, "b": None}),
                 "score": Score(criteria=["Low", "High"])}
    assert validate_request(questions) == questions
    questions["score"].criteria = ["Only one level"]
    with pytest.raises(JudgmentError, match="^invalid_request: "):
        validate_request(questions)


def test_probe_override_replaces_both_limits_and_is_read_per_request(monkeypatch):
    monkeypatch.setenv("BACKFIRE_TEST_REQUEST_LIMITS", "400,800")
    validate_request({"a": question("choice", 400), "b": question("choice", 400)})
    for questions in ({"a": question("choice", 401)},
                      {"a": question("choice", 400), "b": question("choice", 400), "c": Noul()}):
        with pytest.raises(JudgmentError, match="^request_limit_exceeded: "):
            validate_request(questions)
    monkeypatch.setenv("BACKFIRE_TEST_REQUEST_LIMITS", "2,3")
    validate_request({"a": question("choice", 2), "b": Noul()})
    with pytest.raises(JudgmentError, match="^request_limit_exceeded: "):
        validate_request({"a": question("choice", 3)})
    monkeypatch.delenv("BACKFIRE_TEST_REQUEST_LIMITS")
    with pytest.raises(JudgmentError, match="^request_limit_exceeded: "):
        validate_request({"a": question("choice", 251)})


@pytest.mark.parametrize("override", ["", "150", "150,300,400", "-1,300", "150,0", "private-value,300", "1.5,300"])
def test_invalid_probe_overrides_fail_with_safe_configuration_error(monkeypatch, override):
    monkeypatch.setenv("BACKFIRE_TEST_REQUEST_LIMITS", override)
    with pytest.raises(JudgmentError, match="^backend_not_configured: ") as caught:
        validate_request({"q": Noul()})
    assert "BACKFIRE_TEST_REQUEST_LIMITS" in str(caught.value)
    assert "private-value" not in str(caught.value)
