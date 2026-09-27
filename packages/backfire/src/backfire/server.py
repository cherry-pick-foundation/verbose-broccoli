"""The eleven ported tools on the MCP SDK's low-level stdio server."""

import asyncio
from importlib.metadata import version

import jsonschema
from mcp import types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from backfire.judge import Judge
from backfire.tools import (
    classify, compare, decide, extract, find, gate, noul, rerank, review, screen, verify,
)

TOOLS = {tool.NAME: tool for tool in (
    verify, screen, noul, find, classify, rerank, compare, extract, review, gate, decide,
)}


def create_server(judge: Judge) -> Server:
    async def list_tools(context, params):
        return types.ListToolsResult(tools=[
            types.Tool(
                name=tool.NAME,
                title=tool.TITLE,
                description=tool.DESCRIPTION,
                input_schema=tool.INPUT_SCHEMA,
                execution=types.ToolExecution(**tool.EXECUTION),
            )
            for tool in TOOLS.values()
        ])

    async def call_tool(context, params):
        deadline = asyncio.get_running_loop().time() + 118
        try:
            tool = TOOLS.get(params.name)
            if tool is None:
                raise ValueError(f"MCP error -32602: Tool {params.name} not found")
            arguments = params.arguments if params.arguments is not None else {}
            try:
                jsonschema.validate(arguments, tool.INPUT_SCHEMA)
            except jsonschema.ValidationError as error:
                raise ValueError(
                    "MCP error -32602: Input validation error: "
                    f"Invalid arguments for tool {params.name}: {error.message}"
                ) from error
            # T026 replaces this fixed deadline and the missing record file with the MCP boundary's.
            text, is_error = await tool.call(
                arguments, judge, deadline=deadline, record_file=None,
            )
        except Exception as error:
            text, is_error = str(error), True
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)], is_error=is_error,
        )

    return Server(
        "backfire", version=version("backfire"),
        on_list_tools=list_tools, on_call_tool=call_tool,
    )


async def serve(judge: Judge) -> None:
    server = create_server(judge)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
