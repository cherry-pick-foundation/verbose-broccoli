"""Gate 9: the real adapter's Score boundaries pass both ported review tools."""

import asyncio
import json
from pathlib import Path
import sys

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import pytest

from fake_provider import FakeProvider, completion


@pytest.mark.parametrize("tool", ["backfire_review", "backfire_gate"])
@pytest.mark.parametrize("probabilities,score,confidence", [
    ({"0": 0, "1": 0.005, "2": 1}, 2.005 / 1.005, 0.9925373134328358),
    ({"0": 0, "1": 0, "2": 0.99}, 2, 1),
], ids=["total-above-one", "total-at-lower-tolerance"])
def test_adapter_score_boundaries_pass_review_and_gate(tmp_path, tool, probabilities, score, confidence):
    directory = tmp_path / "config/verbose-broccoli/backfire"
    directory.mkdir(parents=True)
    (directory / "config.toml").write_text('''
provider = "score-test"
[providers.score-test]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "requested-model"
credential = "SYNTHETIC_KEY"
request = {max_tokens = 64, response_format = {type = "json_object"}}
thinking = {requested = "on", token_path = "reasoning_tokens"}
''', encoding="utf-8")
    credential = directory / "score-test.env"
    credential.write_text("SYNTHETIC_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)

    low_risk = {"0": 1, "1": 0, "2": 0}
    answers = {
        "correctness": probabilities, "spec_match": probabilities,
        "test_gap": low_risk, "blast_radius": low_risk, "safe_to_apply": 1,
    }
    arguments = {"request": "Add a synthetic check", "diff": "+ assert 1 + 1 == 2"}
    if tool == "backfire_gate":
        arguments.update(claims=["The synthetic check passed"], evidence="1 check passed")
        answers["claim_0"] = {"verified": 1, "contradicted": 0, "unsupported": 0}

    with FakeProvider([completion(answers)]) as fake:
        parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "backfire", "serve-mcp"],
            cwd=Path(__file__).resolve().parents[1],
            env={"BACKFIRE_TEST_PROVIDER_BASE_URL": fake.base_url, "PYTHONDONTWRITEBYTECODE": "1",
                 "XDG_CONFIG_HOME": str(tmp_path / "config"), "XDG_STATE_HOME": str(tmp_path / "state")},
        )

        async def run():
            with anyio.fail_after(20):
                async with stdio_client(parameters) as streams:
                    async with ClientSession(*streams) as client:
                        await client.initialize()
                        result = await client.call_tool(tool, arguments)
                        assert not result.is_error, result.content
                        assert len(result.content) == 1
                        return json.loads(result.content[0].text)

        payload = asyncio.run(run())
        assert len(fake.requests) == 1

    assert payload["tool"] == tool
    assert payload["model"] == "reported-model"
    assert payload["action"] == "auto"
    assert payload["reason_codes"] == ["accepted"]
    review = payload["review"] if tool == "backfire_gate" else payload
    assert review["action"] == "auto"
    assert review["reason_codes"] == ["accepted"]
    assert set(review["scores"]) == {"correctness", "spec_match", "test_gap", "blast_radius"}
    for rubric, expected_score, expected_confidence in (
        ("correctness", score, confidence), ("spec_match", score, confidence),
        ("test_gap", 0, 1), ("blast_radius", 0, 1),
    ):
        assert review["scores"][rubric] == {
            "score": pytest.approx(expected_score, abs=1e-12),
            "confidence": pytest.approx(expected_confidence, abs=1e-12),
            "probabilities": answers[rubric],
        }
    if tool == "backfire_gate":
        assert payload["verification"]["summary"] == {
            "verified": 1, "contradicted": 0, "unsupported": 0,
            "needs_review": 0, "invalid_response": 0,
        }
