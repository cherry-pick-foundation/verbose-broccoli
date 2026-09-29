"""The retained extension tool uses PyModel's published tool framework."""

import asyncio
import json

from jev_judge_mcp.domain import Usage
from jev_judge_mcp.errors import Redactor
from jev_judge_mcp.providers import Evaluation
from jev_judge_mcp.providers import JevProvider
from jev_judge_mcp.settings import Settings
from jev_judge_mcp.tools import Runtime
from jev_judge_mcp.tools import Toolset

from backfire.noul import MAX_NOUL_TOTAL_CHARS
from backfire.noul import NOUL


class StubProvider(JevProvider):
    name = "compatible"
    label = "synthetic"

    def __init__(self, values):
        super().__init__(Redactor(()))
        self.values = values
        self.questions = None
        self.state = None

    async def _send(self, state, questions, model, timeout):
        del timeout
        self.state, self.questions = state, questions
        answers = {
            f"p_proposition{index}": {"noul": value}
            for index, value in enumerate(self.values)
        }
        return Evaluation(answers, Usage(1, 2), self.name, model)

    async def aclose(self):
        return None


def invoke(provider, arguments):
    tools = Toolset(
        Runtime(Settings.model_construct(), lambda _: provider), (NOUL,)
    )

    async def run():
        try:
            return await tools.call("jev_noul", arguments)
        finally:
            await tools.aclose()

    return asyncio.run(run())


def test_definition_and_questions_keep_the_noul_contract():
    schema = NOUL.definition.input_schema
    assert NOUL.name == "jev_noul"
    assert "exclusiveMinimum" not in schema["properties"]["auto_accept"]
    provider = StubProvider([0.8, 0.2, 0.5])
    result = invoke(
        provider,
        {
            "propositions": [
                "synthetic true",
                "synthetic false",
                "synthetic unsure",
            ],
            "auto_accept": 0.51,
        },
    )
    payload = json.loads(result.content[0].text)
    assert [question["type"] for question in provider.questions.values()] == [
        "noul"
    ] * 3
    assert provider.questions["p_proposition0"]["criteria"] == {
        "true": (
            "The proposition is likely true, given the supplied context "
            "(when present) and general knowledge"
        ),
        "false": "The proposition is likely not true",
    }
    assert [row["label"] for row in payload["results"]] == [
        "likely",
        "unlikely",
        "uncertain",
    ]
    assert payload["thresholds"]["auto_accept"] == 0.51


def test_invalid_answer_is_reported_for_every_proposition():
    provider = StubProvider([2])
    result = invoke(provider, {"propositions": ["synthetic statement"]})
    payload = json.loads(result.content[0].text)
    assert payload["status"] == "invalid_response"
    assert payload["invalid"] == ["proposition0"]
    assert payload["results"][0]["label"] is None


def test_auto_accept_requires_more_than_one_half():
    result = invoke(
        StubProvider([0.8]),
        {"propositions": ["synthetic statement"], "auto_accept": 0.5},
    )
    assert result.is_error
    assert "auto_accept must exceed 0.5" in result.content[0].text
    accepted = invoke(
        StubProvider([0.8]),
        {"propositions": ["synthetic statement"], "auto_accept": 0.51},
    )
    assert not accepted.is_error


def test_batch_budget_fails_before_provider_creation():
    provider = StubProvider([])
    result = invoke(
        provider,
        {
            "propositions": ["p" * 2000] * 64,
            "context": "c" * (MAX_NOUL_TOTAL_CHARS - 128_000 + 1),
        },
    )
    assert result.is_error
    assert "Split the batch" in result.content[0].text
    assert provider.questions is None
