import asyncio
from contextlib import asynccontextmanager
from importlib.metadata import version

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_client_server_memory_streams

from backfire.server import create_server
from backfire.tools import (
    classify, compare, decide, extract, find, gate, noul, rerank, review, screen, verify,
)
from scripted_judge import ScriptedJudge

MODULES = (verify, screen, noul, find, classify, decide, rerank, compare, extract, review, gate)


@asynccontextmanager
async def session(judge):
    server = create_server(judge)
    with anyio.fail_after(10):
        async with create_client_server_memory_streams() as (client_streams, server_streams):
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(server.run, *server_streams, server.create_initialization_options())
                try:
                    async with ClientSession(*client_streams) as client:
                        initialized = await client.initialize()
                        yield client, initialized
                finally:
                    tasks.cancel_scope.cancel()


def wire(result):
    return result.model_dump(by_alias=True, exclude_unset=True)


def test_registration_preserves_exact_module_metadata():
    async def run():
        async with session(ScriptedJudge([])) as (client, initialized):
            assert initialized.server_info.name == "backfire"
            assert initialized.server_info.version == version("backfire")
            result = wire(await client.list_tools())
            assert result == {"tools": [
                {"name": tool.NAME, "title": tool.TITLE, "description": tool.DESCRIPTION,
                 "inputSchema": tool.INPUT_SCHEMA, "execution": tool.EXECUTION}
                for tool in MODULES
            ]}
    asyncio.run(run())


@pytest.mark.parametrize("tool", MODULES, ids=lambda tool: tool.NAME)
def test_each_tool_checks_required_arguments(tool):
    judge = ScriptedJudge([])

    async def run():
        async with session(judge) as (client, _):
            for arguments in (None, {}):
                result = await client.call_tool(tool.NAME, arguments)
                assert result.is_error
                assert len(result.content) == 1
                assert result.content[0].text.startswith(
                    "MCP error -32602: Input validation error: "
                    f"Invalid arguments for tool {tool.NAME}: "
                )
                assert "is a required property" in result.content[0].text
            assert len((await client.list_tools()).tools) == 11
    asyncio.run(run())
    assert judge.requests == []


@pytest.mark.parametrize("arguments, detail", [
    ({"claims": [], "evidence": "document"}, "[] should be non-empty"),
    ({"claims": [7], "evidence": "document"}, "7 is not of type 'string'"),
    ({"claims": ["claim"], "evidence": "document", "auto_accept": 1.1},
     "1.1 is greater than the maximum of 1"),
    ({"claims": ["claim"], "evidence": "document", "extra": True},
     "Additional properties are not allowed ('extra' was unexpected)"),
])
def test_schema_errors_use_the_upstream_prefix_and_jsonschema_detail(arguments, detail):
    judge = ScriptedJudge([])

    async def run():
        async with session(judge) as (client, _):
            assert wire(await client.call_tool(verify.NAME, arguments)) == {
                "content": [{"type": "text", "text":
                    "MCP error -32602: Input validation error: "
                    f"Invalid arguments for tool backfire_verify: {detail}"}],
                "isError": True,
            }
    asyncio.run(run())
    assert judge.requests == []


@pytest.mark.parametrize("tool, arguments, detail", [
    (noul, {"propositions": [" \t"]}, "propositions must not be blank at propositions"),
    (gate, {"request": "request", "diff": "diff", "claims": ["claim"], "evidence": " "},
     "backfire_gate requires at least one evidence item with non-empty text. at evidence"),
])
def test_tool_refinements_keep_upstream_errors(tool, arguments, detail):
    judge = ScriptedJudge([])

    async def run():
        async with session(judge) as (client, _):
            result = await client.call_tool(tool.NAME, arguments)
            assert result.is_error
            assert result.content[0].text == (
                "MCP error -32602: Input validation error: "
                f"Invalid arguments for tool {tool.NAME}: {detail}"
            )
    asyncio.run(run())
    assert judge.requests == []


@pytest.mark.parametrize("is_error", [False, True])
def test_call_passes_arguments_judge_deadline_and_returned_error_flag(monkeypatch, is_error):
    arguments = {"claims": ["claim"], "evidence": "document"}
    judge = ScriptedJudge([])
    calls = []

    async def call(received, received_judge, *, deadline, record_file):
        calls.append(received)
        assert received == arguments
        assert received_judge is judge
        assert 117 < deadline - asyncio.get_running_loop().time() <= 118
        assert record_file is None
        return "unchanged tool text", is_error

    monkeypatch.setattr(verify, "call", call)

    async def run():
        async with session(judge) as (client, _):
            # Upstream sends isError only for errors.
            assert wire(await client.call_tool(verify.NAME, arguments)) == {
                "content": [{"type": "text", "text": "unchanged tool text"}],
                **({"isError": True} if is_error else {}),
            }
    asyncio.run(run())
    assert len(calls) == 1


def test_tool_exception_is_only_its_message_and_the_session_keeps_serving(monkeypatch):
    async def call(*args, **kwargs):
        raise RuntimeError("synthetic failure: unchanged 한글")

    monkeypatch.setattr(verify, "call", call)

    async def run():
        async with session(ScriptedJudge([])) as (client, _):
            for name, arguments, message in (
                (verify.NAME, {"claims": ["claim"], "evidence": "document"},
                 "synthetic failure: unchanged 한글"),
                ("backfire_unknown", {}, "MCP error -32602: Tool backfire_unknown not found"),
            ):
                assert wire(await client.call_tool(name, arguments)) == {
                    "content": [{"type": "text", "text": message}], "isError": True,
                }
            assert len((await client.list_tools()).tools) == 11
    asyncio.run(run())
