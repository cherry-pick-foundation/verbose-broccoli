"""The Vercel port is exercised against a local HTTP stub."""

import asyncio

from fake_provider import FakeProvider
from jev_judge_mcp.domain import ChoiceQuestion
from jev_judge_mcp.domain import NoulCriteria
from jev_judge_mcp.domain import NoulQuestion

from backfire.vercel import VercelProvider


def test_request_mapping_answers_and_usage():
    body = {
        "answers": {
            "probability": {"type": "boolean", "probability": 0.75},
            "choice": {
                "type": "choice",
                "choice": "yes",
                "probabilities": {"yes": 0.8, "no": 0.2},
            },
        },
        "providerMetadata": {"typesafe": {"confidence": {"choice": 0.9}}},
        "usage": {"inputTokens": 3, "outputTokens": 4},
    }
    with FakeProvider([body]) as fake:
        root = fake.base_url.removesuffix("/v1")
        client = VercelProvider(
            {"base_url": root + "/v4/ai/evaluation-model"}, "synthetic-key"
        )

        async def run():
            try:
                return await client.evaluate(
                    {"claim": "synthetic"},
                    {
                        "probability": NoulQuestion(
                            "Is it likely?", NoulCriteria("yes", "no")
                        ),
                        "choice": ChoiceQuestion(
                            "Choose", {"yes": "yes", "no": "no"}
                        ),
                    },
                    "typesafe-ai/custom",
                    3,
                )
            finally:
                await client.aclose()

        result = asyncio.run(run())

    request = fake.requests[0]
    assert request["path"] == "/v4/ai/evaluation-model"
    assert request["headers"]["authorization"] == "Bearer synthetic-key"
    assert request["headers"]["ai-gateway-protocol-version"] == "0.0.1"
    assert request["headers"]["ai-gateway-auth-method"] == "api-key"
    assert (
        request["headers"]["ai-evaluation-model-specification-version"] == "4"
    )
    assert request["headers"]["ai-model-id"] == "typesafe-ai/custom"
    assert request["body"]["state"] == {"claim": "synthetic"}
    assert request["body"]["questions"]["probability"]["type"] == "boolean"
    assert result.answers["probability"] == {"type": "noul", "noul": 0.75}
    assert result.answers["choice"]["confidence"] == 0.9
    assert (result.usage.input_tokens, result.usage.output_tokens) == (3, 4)
