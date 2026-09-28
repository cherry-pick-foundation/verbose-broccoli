"""Gate 8: deadlines, provider cancellation, and pattern cleanup."""

import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import signal
import sys
import time

import anyio
from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest
from test_boundary_core import session as memory_session

from backfire import patterns
from backfire.boundary import ERRORS
from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge
from backfire.records import read_records

pytestmark = pytest.mark.slow

NOUL = {"propositions": ["A synthetic deadline check."]}


@pytest.fixture(autouse=True)
def configuration(isolated_xdg, monkeypatch):
    del isolated_xdg  # Unused.
    for name in (
        "BACKFIRE_TEST_PROVIDER_BASE_URL",
        "BACKFIRE_TEST_REQUEST_LIMITS",
        "BACKFIRE_TEST_JUDGE_SCRIPT",
    ):
        monkeypatch.delenv(name, raising=False)
    directory = xdg_path("config") / "backfire"
    directory.mkdir(parents=True)
    (directory / "config.toml").write_text(
        """
provider = "deadline-test"
[providers.deadline-test]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "requested-model"
credential = "SYNTHETIC_KEY"
request = {max_tokens = 64, response_format = {type = "json_object"}}
thinking = {requested = "on", token_path = "reasoning_tokens"}
""",
        encoding="utf-8",
    )
    credential = directory / "deadline-test.env"
    credential.write_text("SYNTHETIC_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)


@asynccontextmanager
async def stdio_session(tmp_path, fake, *, overrun_provider=False):
    args = ["-m", "backfire", "serve-mcp"]
    if overrun_provider:
        # Let the fake request outlive the unchanged 118 s boundary timer so its
        # cancellation cannot race the HTTP client's own read timeout.
        args = [
            "-c",
            """
from backfire.provider import ProfileProvider, provider_call
from backfire.__main__ import main
request = ProfileProvider.request
async def overrun(self, *args, **kwargs):
    provider_call.get().deadline += 60
    return await request(self, *args, **kwargs)
ProfileProvider.request = overrun
main()
""",
            "serve-mcp",
        ]
    parameters = StdioServerParameters(
        command=sys.executable,
        args=args,
        cwd=Path(__file__).resolve().parents[1],
        env={
            "BACKFIRE_TEST_PROVIDER_BASE_URL": fake.base_url,
            "PYTHONDONTWRITEBYTECODE": "1",
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
        },
    )
    with anyio.fail_after(140):
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as client:
                await client.initialize()
                yield client


def session_records():
    return [
        row
        for path in (xdg_path("state") / "backfire/records").glob("*.jsonl")
        for row in read_records(path)
    ]


def extract_arguments(timed_out):
    return {
        "document": "a" * 49_990 + "! marker",
        "fields": [
            {
                "id": f"slow{index}",
                "pattern": "(a+)+$",
                "description": "No match before the timeout.",
            }
            for index in range(timed_out)
        ]
        + [
            {
                "id": "match",
                "pattern": "marker",
                "description": "The literal marker.",
            }
        ],
    }


def test_extract_pattern_timeouts_and_stalled_provider_share_the_call_deadline(
    tmp_path,
):
    with FakeProvider([Reply(completion(), stall=True)]) as fake:

        async def run():
            async with stdio_session(tmp_path, fake) as client:
                started = time.monotonic()
                async with asyncio.TaskGroup() as tasks:
                    call = tasks.create_task(
                        asyncio.wait_for(
                            client.call_tool(
                                "backfire_extract", extract_arguments(31)
                            ),
                            120,
                        )
                    )
                    assert await asyncio.to_thread(fake.received.wait, 115)
                    # All 31 valid catastrophic patterns exhaust their real
                    # 1,000 ms budget.
                    assert time.monotonic() - started >= 31
                    (request,) = fake.requests
                    prompt = request["body"]["messages"][0]["content"]
                    schema, _ = json.JSONDecoder().raw_decode(
                        prompt[prompt.index("{") :]
                    )
                    answers = schema["properties"]["answers"]
                    if "$ref" in answers:
                        answers = schema["$defs"][
                            answers["$ref"].rsplit("/", 1)[1]
                        ]
                    assert set(answers["properties"]) == {"f31"}
                    result = await call
                assert time.monotonic() - started < 120
                assert result.is_error
                assert result.content[0].text in (
                    ERRORS["deadline_exceeded"],
                    str(JudgmentError("provider_unavailable")),
                )

        asyncio.run(run())
        assert len(fake.requests) == 1
        rows = session_records()
        (tool,) = (row for row in rows if row["kind"] == "tool_call")
        (judgment,) = (row for row in rows if row["kind"] == "judgment")
        assert tool["tool"] == "backfire_extract" and tool["outcome"] in (
            "tool_error",
            "deadline_exceeded",
        )
        assert 31_000 <= tool["duration_ms"] < 120_000
        assert judgment["questions"] == [{"type": "choice", "cells": 2}]
        assert judgment["attempts"] == 1 and judgment["outcome"] in (
            "cancelled",
            "provider_unavailable",
        )


def test_real_deadline_cancels_provider_socket_and_keeps_other_calls_alive(
    tmp_path, monkeypatch
):
    fake = FakeProvider(
        [
            Reply(completion(), stall=True),
            completion({"p_proposition0": 0.97}),
            completion({"p_proposition0": 0.97}),
        ]
    )
    connections = []
    accept = fake.server.get_request

    def observe_connection():
        connection, address = accept()
        connections.append(connection)
        return connection, address

    monkeypatch.setattr(fake.server, "get_request", observe_connection)
    with fake:

        async def run():
            async with stdio_session(
                tmp_path, fake, overrun_provider=True
            ) as client:
                started = time.monotonic()
                async with asyncio.TaskGroup() as tasks:
                    stalled = tasks.create_task(
                        asyncio.wait_for(
                            client.call_tool("backfire_noul", NOUL), 120
                        )
                    )
                    assert await asyncio.to_thread(fake.received.wait, 10)
                    first_connection = connections[0]
                    other = await asyncio.wait_for(
                        client.call_tool("backfire_noul", NOUL), 5
                    )
                    assert not other.is_error and not stalled.done()
                    assert (
                        json.loads(other.content[0].text)["results"][0][
                            "probability"
                        ]
                        == 0.97
                    )
                    result = await stalled
                assert 118 <= time.monotonic() - started < 120
                assert (
                    result.is_error
                    and result.content[0].text == ERRORS["deadline_exceeded"]
                )
                # The fake is still stalled: EOF proves the real HTTP request
                # was closed.
                assert not fake.release.is_set()
                first_connection.settimeout(5)
                assert await asyncio.to_thread(first_connection.recv, 1) == b""
                after = await asyncio.wait_for(
                    client.call_tool("backfire_noul", NOUL), 5
                )
                assert not after.is_error
                assert (
                    json.loads(after.content[0].text)["results"][0][
                        "probability"
                    ]
                    == 0.97
                )

        asyncio.run(run())
        assert len(fake.requests) == 3
        rows = session_records()
        calls = {row["call"]: row for row in rows if row["kind"] == "tool_call"}
        assert {number: row["outcome"] for number, row in calls.items()} == {
            1: "deadline_exceeded",
            2: "ok",
            3: "ok",
        }
        assert 118_000 <= calls[1]["duration_ms"] < 120_000
        cancelled = [
            row
            for row in rows
            if row["kind"] == "judgment" and row["outcome"] == "cancelled"
        ]
        assert len(cancelled) == 1, rows
        assert (
            cancelled[0]["calls_in_flight"] == [1]
            and cancelled[0]["attempts"] == 1
        )


def test_client_cancellation_kills_pattern_child_before_any_provider_call(
    tmp_path, monkeypatch
):
    with FakeProvider([]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            input_sent = asyncio.Event()
            children = []
            spawn = asyncio.create_subprocess_exec

            async def observe_spawn(*args, **kwargs):
                child = await spawn(*args, **kwargs)
                children.append(child)
                close = child.stdin.close

                def observe_input_end():
                    close()
                    input_sent.set()

                monkeypatch.setattr(child.stdin, "close", observe_input_end)
                return child

            monkeypatch.setattr(
                patterns.asyncio, "create_subprocess_exec", observe_spawn
            )
            async with memory_session(tmp_path, judge) as (
                client,
                edge,
                records,
            ):
                call = asyncio.create_task(
                    client.call_tool("backfire_extract", extract_arguments(1))
                )
                try:
                    await asyncio.wait_for(input_sent.wait(), 3)
                    (child,) = children
                    assert child.returncode is None
                    call.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await call
                    assert len((await client.list_tools()).tools) == 11
                    await edge.join()
                    assert child.returncode == -signal.SIGKILL
                    assert len(children) == 1 and fake.requests == []
                    (row,) = read_records(records.path)
                    assert (
                        row["kind"] == "tool_call"
                        and row["outcome"] == "cancelled"
                    )
                    assert not edge.calls and not edge.work
                finally:
                    call.cancel()
                    await asyncio.gather(call, return_exceptions=True)

        asyncio.run(run())
