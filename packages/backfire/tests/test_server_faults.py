"""Check judgment failures at the MCP tool boundary."""

import asyncio

import pytest

from backfire.config import load_profile, xdg_path
from backfire.failures import JudgmentError, MESSAGES
from backfire.judge import judge
from backfire.tools import verify
from fake_provider import FakeProvider, Reply
from scripted_judge import ScriptedJudge
from test_server import session, wire

PINNED_MODEL = "deepseek-ai/deepseek-v4.1-flash"
ARGUMENTS = {"claims": ["synthetic claim"], "evidence": "synthetic evidence"}


@pytest.mark.parametrize("error_type", sorted(MESSAGES))
def test_each_judgment_error_is_returned_as_a_tool_error(monkeypatch, error_type):
    async def fail(*args, **kwargs):
        raise JudgmentError(error_type)

    monkeypatch.setattr(verify, "call", fail)

    async def run():
        async with session(ScriptedJudge([])) as (client, _):
            result = await client.call_tool(verify.NAME, ARGUMENTS)
            assert wire(result) == {
                "content": [{"type": "text", "text": str(JudgmentError(error_type))}],
                "isError": True,
            }

    asyncio.run(run())


def test_missing_credential_names_the_file_at_the_tool_boundary(monkeypatch):
    credential = xdg_path("config") / "backfire" / "hive.env"
    assert not credential.exists()

    with FakeProvider([]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            async with session(judge) as (client, _):
                result = await client.call_tool(
                    "backfire_noul", {"propositions": ["synthetic proposition"]},
                )
                return wire(result)

        result = asyncio.run(run())

    error = JudgmentError("backend_not_configured", str(credential))
    assert result == {
        "content": [{"type": "text", "text": str(error)}], "isError": True,
    }
    assert fake.requests == []


def test_every_retry_request_keeps_the_pinned_model_and_returns_no_judgment(monkeypatch):
    profile = load_profile()
    assert profile["model"] == PINNED_MODEL
    directory = xdg_path("config") / "backfire"
    directory.mkdir(parents=True, exist_ok=True)
    credential = directory / "hive.env"
    credential.write_text("HIVE_API_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)

    with FakeProvider([Reply({"error": "synthetic"}, 429, {"Retry-After": "0"})] * 4) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            async with session(judge) as (client, _):
                return wire(await client.call_tool(
                    "backfire_noul", {"propositions": ["synthetic proposition"]},
                ))

        result = asyncio.run(run())

    assert result == {
        "content": [{"type": "text", "text": str(JudgmentError("rate_limited"))}],
        "isError": True,
    }
    assert len(fake.requests) == 4
    assert all(request["body"]["model"] == PINNED_MODEL for request in fake.requests)
