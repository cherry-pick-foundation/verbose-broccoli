"""Synthetic stdio server; no provider, registry or persistent captures."""

import asyncio
import json
import os
from pathlib import Path
import sys

os.environ.update(
    FASTMCP_CHECK_FOR_UPDATES="off",
    FASTMCP_TELEMETRY_MODE="off",
    FASTMCP_ENV_FILE="",
)
sys.dont_write_bytecode = True

from fastmcp import FastMCP  # noqa: E402
from fastmcp.server.context import Context  # noqa: E402
from fastmcp.server.middleware import Middleware  # noqa: E402
from fastmcp.tools.base import InputRequiredToolResult  # noqa: E402
from fastmcp.tools.base import ToolResult  # noqa: E402
from mcp_types import ImageContent  # noqa: E402
from mcp_types import InputRequiredResult  # noqa: E402

server = FastMCP("synthetic-upstream", mask_error_details=False)


class WireFailure(Middleware):
    """Raise at the protocol boundary rather than return a tool error result."""

    async def on_call_tool(self, context, call_next):
        """Raise outside the tool runner to exercise thrown MCP errors."""
        arguments = context.message.arguments or {}
        if arguments.get("action") == "raise":
            raise ValueError(json.dumps(arguments))
        return await call_next(context)


server.add_middleware(WireFailure())


@server.tool(output_schema=None)
async def echo(
    payload: dict, ctx: Context, action: str = "ok", delay: float = 0
) -> ToolResult:
    """Echo only what arrived after masking, in every supported result field."""
    await asyncio.sleep(delay)
    if action == "exit":
        os._exit(7)
    if action == "raise":
        raise ValueError(json.dumps(payload))
    if action == "continuation":
        return InputRequiredToolResult(
            InputRequiredResult(request_state="synthetic-state")
        )
    if action == "plain-error":
        return ToolResult(content="note: " + payload["text"], is_error=True)
    if action == "reverse-collision":
        return ToolResult(content=json.dumps({payload["text"]: 1, "가라온": 2}))
    if action == "opaque":
        return ToolResult(
            content=[
                ImageContent(type="image", data="AA==", mime_type="image/png")
            ]
        )
    if action == "notify":
        await ctx.info(json.dumps(payload))
        await ctx.report_progress(1, 1, json.dumps(payload))
    encoded = json.dumps(payload, ensure_ascii=False)
    return ToolResult(
        content=encoded,
        structured_content={
            "echo": payload,
            "nested": json.dumps({"encoded": encoded}),
        },
        meta={
            "seen": payload,
            "encoded": encoded,
            "request_meta": ctx.request_context.meta,
        },
        is_error=action == "error",
    )


@server.tool(output_schema=None)
def launch() -> dict:
    """Return public process mechanics, never environment values or keys."""
    return {
        "env_keys": sorted(os.environ),
        "cwd": str(Path.cwd()),
        "entry": str(Path(sys.argv[0]).resolve()),
    }


@server.resource("synthetic://known")
def resource() -> str:
    """Expose a synthetic direct-read trap."""
    return "must not reach client"


@server.resource("synthetic://template/{value}")
def template(value: str) -> str:
    """Expose a synthetic template trap."""
    return value


@server.prompt()
def summarize(text: str) -> str:
    """Expose a synthetic prompt trap."""
    return text


if __name__ == "__main__":
    server.run(transport="stdio", show_banner=False)
