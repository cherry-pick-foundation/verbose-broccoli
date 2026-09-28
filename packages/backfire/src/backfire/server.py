"""The eleven ported tools on the MCP SDK's low-level stdio server."""

import asyncio
from importlib.metadata import version
import signal
import sys

import anyio
import jsonschema
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from backfire.boundary import Boundary
from backfire.boundary import BoundedLineReader
from backfire.boundary import MessageTooLarge
from backfire.config import xdg_path
from backfire.judge import Judge
from backfire.records import RecordFile
from backfire.records import RecordWriteError
from backfire.tools import classify
from backfire.tools import compare
from backfire.tools import decide
from backfire.tools import extract
from backfire.tools import find
from backfire.tools import gate
from backfire.tools import noul
from backfire.tools import rerank
from backfire.tools import review
from backfire.tools import screen
from backfire.tools import verify

# The order of jev-mcp 0.9.0's tools/list.
TOOLS = {
    tool.NAME: tool
    for tool in (
        verify,
        screen,
        noul,
        find,
        classify,
        decide,
        rerank,
        compare,
        extract,
        review,
        gate,
    )
}


def create_server(judge: Judge, boundary: Boundary | None = None) -> Server:
    """Build the MCP server and optionally attach call-boundary records."""

    async def list_tools(context, params):
        del context, params  # Unused.

        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name=tool.NAME,
                    title=tool.TITLE,
                    description=tool.DESCRIPTION,
                    input_schema=tool.INPUT_SCHEMA,
                    execution=types.ToolExecution(**tool.EXECUTION),
                )
                for tool in TOOLS.values()
            ]
        )

    async def invoke(params, deadline, record_file):
        try:
            tool = TOOLS.get(params.name)
            if tool is None:
                raise ValueError(
                    f"MCP error -32602: Tool {params.name} not found"
                )
            arguments = params.arguments if params.arguments is not None else {}
            try:
                await asyncio.to_thread(
                    jsonschema.validate, arguments, tool.INPUT_SCHEMA
                )
            except jsonschema.ValidationError as error:
                raise ValueError(
                    "MCP error -32602: Input validation error: "
                    f"Invalid arguments for tool {params.name}: {error.message}"
                ) from error
            text, is_error = await tool.call(
                arguments,
                judge,
                deadline=deadline,
                record_file=record_file,
            )
        except Exception as error:  # noqa: BLE001  # Keep tool failures in MCP responses.
            text, is_error = str(error), True
        # The SDK drops resultType for legacy versions; a dict avoids adding
        # isError: false to successful results.
        result = {
            "content": [{"type": "text", "text": text}],
            "resultType": "complete",
        }
        return {**result, "isError": True} if is_error else result

    async def call_tool(context, params):
        if boundary is None:
            return await invoke(
                params, asyncio.get_running_loop().time() + 118, None
            )
        return await boundary.call(
            context.request_id,
            lambda deadline, records: invoke(params, deadline, records),
        )

    return Server(
        "backfire",
        version=version("backfire"),
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )


async def serve(judge: Judge) -> None:
    """Serve MCP over stdio with session records and signal handling."""
    try:
        records = RecordFile(xdg_path("state") / "backfire" / "records")
    except RecordWriteError as error:
        raise SystemExit(str(error)) from None
    with records:
        boundary = Boundary(records, TOOLS)
        server = create_server(judge, boundary)

        async def signals():
            with anyio.open_signal_receiver(
                signal.SIGTERM, signal.SIGINT
            ) as receiver:
                async for _ in receiver:
                    boundary.stop()
                    return

        async def transport():
            async with stdio_server(
                stdin=BoundedLineReader(sys.stdin.fileno())
            ) as streams:
                await boundary.run(server, *streams)

        try:
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(signals)
                tasks.start_soon(transport)
                await boundary.stopped.wait()
                tasks.cancel_scope.cancel()
        except* (
            MessageTooLarge,
            OSError,
            anyio.BrokenResourceError,
            anyio.ClosedResourceError,
        ):
            print("session_ended", file=sys.stderr)
