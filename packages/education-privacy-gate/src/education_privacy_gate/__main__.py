"""One tools-only proxy with mandatory per-call privacy middleware.

Accept SDK integer progress counters and fixed logging levels, discard all
frontend metadata, and reject string counters/application metadata. The backend
SDK stamps its own counters/connection fields; no caller metadata is relayed.
"""

from contextlib import redirect_stderr
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import get_args

# Set before importing FastMCP: its settings load at import time.
os.environ.update(
    FASTMCP_CHECK_FOR_UPDATES="off",
    FASTMCP_TELEMETRY_MODE="off",
    FASTMCP_ENV_FILE="",
    FASTMCP_LOG_ENABLED="false",
)

from fastmcp import Client  # noqa: E402
from fastmcp.client.transports import StdioTransport  # noqa: E402
from fastmcp.exceptions import ToolError  # noqa: E402
from fastmcp.server import create_proxy  # noqa: E402
from fastmcp.server.middleware import Middleware  # noqa: E402
from fastmcp.tools.base import ToolResult  # noqa: E402
from jsonschema import validate  # noqa: E402
from mcp_types import CLIENT_CAPABILITIES_META_KEY  # noqa: E402
from mcp_types import CLIENT_INFO_META_KEY  # noqa: E402
from mcp_types import LOG_LEVEL_META_KEY  # noqa: E402
from mcp_types import PROTOCOL_VERSION_META_KEY  # noqa: E402
from mcp_types import LoggingLevel  # noqa: E402
from mcp_types import TextContent  # noqa: E402

from education_privacy_gate import roster  # noqa: E402
from education_privacy_gate.masking import Masker  # noqa: E402
from education_privacy_gate.roster import GateError  # noqa: E402

_CONNECTION_META = {
    CLIENT_CAPABILITIES_META_KEY,
    CLIENT_INFO_META_KEY,
    PROTOCOL_VERSION_META_KEY,
}


async def _discard(*unused_args):
    """Discard untrusted log/progress notifications without formatting them."""


def _pattern(schema, path):
    if not path:
        return "pattern" in schema
    alternatives = schema.get("anyOf", schema.get("oneOf", []))
    if alternatives:
        return any(_pattern(branch, path) for branch in alternatives)
    part, *rest = path
    child = (
        schema.get("items", {})
        if isinstance(part, int)
        else schema.get("properties", {}).get(
            part, schema.get("additionalProperties", {})
        )
    )
    return isinstance(child, dict) and _pattern(child, rest)


class PrivacyGate(Middleware):
    """Mask, validate and restore each call, failing closed with fixed text."""

    def __init__(self, client):
        self.client = client
        self.schemas = None

    async def on_call_tool(self, context, call_next):
        """Gate every call and restore supported upstream error results too."""
        try:
            ctx = context.fastmcp_context
            meta = (
                ctx.request_context.meta
                if ctx and ctx.request_context
                else None
            )
            if (
                meta
                and (
                    set(meta)
                    - _CONNECTION_META
                    - {"progressToken", LOG_LEVEL_META_KEY}
                    or (
                        LOG_LEVEL_META_KEY in meta
                        and meta[LOG_LEVEL_META_KEY]
                        not in get_args(LoggingLevel)
                    )
                    or (
                        "progressToken" in meta
                        and type(meta["progressToken"]) is not int
                    )
                )
            ) or (
                ctx
                and (
                    ctx.input_responses is not None
                    or ctx.request_state is not None
                )
            ):
                raise GateError()
            if meta:
                meta.clear()
            with Masker(roster.load_registry()) as call:
                if self.schemas is None:
                    async with self.client:
                        tools = await self.client.list_tools()
                    if any(tool.output_schema is not None for tool in tools):
                        raise GateError()
                    self.schemas = {
                        tool.name: tool.input_schema for tool in tools
                    }
                schema = self.schemas[context.message.name]
                masked = call.mask(
                    context.message.arguments or {},
                    constrained=lambda path: _pattern(schema, path),
                )
                validate(masked, schema)
                # Only verify/find sanitize external IDs in the pinned upstream.
                field = {
                    "jev_verify": "evidence",
                    "jev_find": "candidates",
                }.get(context.message.name)
                if field:
                    original = (context.message.arguments or {})[field]
                    changed = masked[field]
                    pairs = (
                        zip(original, changed)
                        if isinstance(original, list)
                        else [(original, changed)]
                    )
                    for before, after in pairs:
                        if isinstance(before, dict) and before.get(
                            "id"
                        ) != after.get("id"):
                            identifier = after.get("id", "")
                            if len(identifier) > 64 or not re.fullmatch(
                                r"[A-Za-z0-9_.-]+", identifier
                            ):
                                raise GateError()
                message = context.message.model_copy(
                    update={"arguments": masked}
                )
                result = await call_next(context.copy(message=message))
                if type(result) is not ToolResult or any(
                    block.type != "text" for block in result.content
                ):
                    raise GateError()
                # Construct anew: never retain ToolResult's raw MCP shortcut.
                restored = call.restore(result.model_dump(mode="json"))
                restored["content"] = [
                    TextContent.model_validate(block)
                    for block in restored["content"]
                ]
                return ToolResult(**restored)
        except Exception:  # noqa: BLE001 - fixed errors at the trust boundary
            return ToolResult(content=str(GateError()), is_error=True)

    async def on_list_tools(self, context, call_next):
        """Cache trusted schemas and refuse unexpected output schemas."""
        try:
            tools = await call_next(context)
            if any(tool.output_schema is not None for tool in tools):
                raise GateError()
            if self.schemas is None:
                self.schemas = {tool.name: tool.parameters for tool in tools}
            return tools
        except Exception:  # noqa: BLE001 - fixed errors at the trust boundary
            raise ToolError(str(GateError())) from None

    async def on_list_resources(self, unused_context, call_next):  # noqa: ARG002
        """Hide resources, resource templates and prompts."""
        return []

    on_list_resource_templates = on_list_resources
    on_list_prompts = on_list_resources

    async def on_read_resource(self, unused_context, call_next):  # noqa: ARG002
        """Block direct resource/template reads and prompt retrieval."""
        raise ToolError(str(GateError()))

    on_get_prompt = on_read_resource


def _node_command():
    if shutil.which("mise"):
        command = subprocess.check_output(
            ["mise", "which", "node"],
            text=True,
            # Neutral cwd: the global Node, and no dependency on this checkout's
            # mise configuration being trusted.
            cwd="/",
        ).strip()
    else:
        command = shutil.which("node")
    if (
        not command
        or not Path(command).is_absolute()
        or not Path(command).is_file()
    ):
        raise GateError()
    return command


def build_proxy(*, key, command=None, args=None, log_file=None, timeout=60):
    """Build the mandatory proxy; parameters are a synthetic-test seam only."""
    entry = (
        Path(__file__).resolve().parents[2]
        / "node_modules/@jkudish/jev-mcp/dist/index.js"
    )
    transport = StdioTransport(
        command if command is not None else _node_command(),
        args if args is not None else [str(entry)],
        env={
            "JEV_PROVIDER": "openrouter",
            "OPENROUTER_API_KEY": key,
            "JEV_MCP_MODEL": "typesafe/jev-1.13",
        },
        cwd="/",
        log_file=log_file if log_file is not None else Path(os.devnull),
    )
    client = Client(
        transport,
        timeout=timeout,
        cache=False,
        log_handler=_discard,
        progress_handler=_discard,
    )
    proxy = create_proxy(
        client,
        name="jev-mcp",
        provider_error_strategy="raise",
        mask_error_details=True,
        tasks=False,
    )
    proxy.add_middleware(PrivacyGate(client))
    return proxy


def main(*, key_source=None):
    """Load the protected key at startup and serve the gated stdio route."""
    logging.disable(logging.CRITICAL)
    with open(os.devnull, "w") as sink, redirect_stderr(sink):
        try:
            if key_source is None:
                from dotenv import dotenv_values  # noqa: PLC0415

                key = dotenv_values(
                    Path.home()
                    / ".config/verbose-broccoli/providers/openrouter.env",
                    interpolate=False,
                ).get("OPENROUTER_API_KEY")
            else:
                key = key_source()
            if not key:
                raise GateError()
            build_proxy(key=key).run(transport="stdio", show_banner=False)
        except Exception:  # noqa: BLE001 - fixed errors at the trust boundary
            raise SystemExit(str(GateError())) from None


if __name__ == "__main__":
    main()
