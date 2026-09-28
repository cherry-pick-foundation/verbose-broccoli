"""Session records, cancellation and deadlines around the SDK's parsed streams."""

import asyncio
from dataclasses import dataclass
import json
import os
import select
import sys

import anyio
from mcp import types
from mcp.shared.message import SessionMessage

from backfire.decisions import decision_units
from backfire.records import RecordFile, RecordWriteError, digest

MAX_LINE_BYTES = 10 * 1024 * 1024
CALL_SECONDS = 118
ERRORS = {
    "deadline_exceeded": "deadline_exceeded: The tool call exceeded its deadline; split the request or try again.",
    "record_write_failed": "record_write_failed: Cannot write the tool-call record; check record directory permissions and available space.",
}


class MessageTooLarge(Exception):
    """The transport must end the session without parsing this line."""


class BoundedLineReader:
    """Read bytes without a blocking reader thread; the SDK still parses JSON."""

    def __init__(self, fd: int):
        self.fd = fd
        self.buffer = bytearray()

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            end = self.buffer.find(b"\n")
            if end > MAX_LINE_BYTES or (
                end < 0 and len(self.buffer) > MAX_LINE_BYTES
            ):
                raise MessageTooLarge("message_limit_exceeded")
            if end >= 0:
                line = self.buffer[: end + 1]
                del self.buffer[: end + 1]
                return line.decode("utf-8", errors="replace")
            # Regular files and /dev/null are readable but cannot register with epoll.
            if not select.select([self.fd], [], [], 0)[0]:
                await anyio.wait_readable(self.fd)
            chunk = os.read(
                self.fd, min(65536, MAX_LINE_BYTES + 1 - len(self.buffer))
            )
            if not chunk:
                if not self.buffer:
                    raise StopAsyncIteration
                line, self.buffer = self.buffer, bytearray()
                return line.decode("utf-8", errors="replace")
            self.buffer.extend(chunk)


@dataclass
class Call:
    request_id: str | int
    number: int
    tool: str
    input_digest: str
    started: float
    deadline: float
    task: asyncio.Task | None = None
    timer: asyncio.Task | None = None


def error_response(request_id, error_type):
    return SessionMessage(
        types.JSONRPCResponse(
            jsonrpc="2.0",
            id=request_id,
            result={
                "content": [{"type": "text", "text": ERRORS[error_type]}],
                "isError": True,
                "resultType": "complete",
            },
        )
    )


class Boundary:
    def __init__(self, records: RecordFile, tool_names):
        self.records = records
        self.tool_names = tool_names
        self.calls: dict[str | int, Call] = {}
        self.closed: set[str | int] = set()
        self.work: set[asyncio.Task] = set()
        self.timers: set[asyncio.Task] = set()
        self.stopped = anyio.Event()
        self.sequence = 0

    def receive(self, item):
        if not isinstance(item, SessionMessage):
            return
        message = item.message
        params = (
            (message.params or {})
            if isinstance(
                message, (types.JSONRPCRequest, types.JSONRPCNotification)
            )
            else {}
        )
        if (
            isinstance(message, types.JSONRPCRequest)
            and message.method == "tools/call"
        ):
            started = asyncio.get_running_loop().time()
            self.sequence += 1
            name = params.get("name")
            call = Call(
                message.id,
                self.sequence,
                name
                if isinstance(name, str) and name in self.tool_names
                else "unknown",
                digest(
                    {"tool": name, "arguments": params.get("arguments", {})}
                ),
                started,
                started + CALL_SECONDS,
            )
            self.calls[message.id] = call
            self.closed.discard(message.id)
            self.records.calls_in_flight.add(call.number)
            call.timer = asyncio.create_task(self._expire(call))
            self.timers.add(call.timer)
            call.timer.add_done_callback(self.timers.discard)
        elif (
            isinstance(message, types.JSONRPCNotification)
            and message.method == "notifications/cancelled"
        ):
            identifier = params.get("requestId")
            if (
                type(identifier) in (str, int)
                and (call := self.calls.get(identifier)) is not None
            ):
                self._close(call, "cancelled")

    def _close(self, call, outcome, result=None):
        del self.calls[call.request_id]
        self.records.calls_in_flight.remove(call.number)
        self.closed.add(call.request_id)
        if call.timer is not asyncio.current_task():
            call.timer.cancel()
        if (
            outcome in ("cancelled", "deadline_exceeded", "session_ended")
            and call.task is not None
        ):
            call.task.cancel()
        parsed = None
        if result is not None:
            try:
                parsed = json.loads(result["content"][0]["text"])
            except (KeyError, IndexError, TypeError, ValueError):
                pass
        model = parsed.get("model") if isinstance(parsed, dict) else None
        try:
            self.records.write_tool_call(
                call=call.number,
                tool=call.tool,
                input_digest=call.input_digest,
                outcome=outcome,
                decisions=decision_units(call.tool, parsed),
                result=result,
                model=model if isinstance(model, str) else None,
                duration_ms=(asyncio.get_running_loop().time() - call.started)
                * 1000,
            )
        except RecordWriteError:
            print("record_write_failed", file=sys.stderr)
            return False
        return True

    def response(self, item):
        message = item.message
        if isinstance(message, (types.JSONRPCResponse, types.JSONRPCError)):
            if (call := self.calls.get(message.id)) is not None:
                result = (
                    message.result
                    if isinstance(message, types.JSONRPCResponse)
                    else None
                )
                outcome = (
                    "protocol_error"
                    if result is None
                    else "tool_error"
                    if result.get("isError")
                    else "ok"
                )
                if not self._close(call, outcome, result):
                    return error_response(message.id, "record_write_failed")
            elif message.id in self.closed:
                return None
        return item

    async def _expire(self, call):
        await asyncio.sleep(
            max(0, call.deadline - asyncio.get_running_loop().time())
        )
        if self.calls.get(call.request_id) is call:
            reply = error_response(call.request_id, "deadline_exceeded")
            if not self._close(call, "deadline_exceeded", reply.message.result):
                reply = error_response(call.request_id, "record_write_failed")
            try:
                await self.output.send(reply)
            except (anyio.BrokenResourceError, anyio.ClosedResourceError):
                self.stop()

    async def call(self, request_id, invoke):
        call = self.calls.get(request_id)
        if call is None or self.stopped.is_set():
            return types.CallToolResult(content=[], is_error=True)
        call.task = asyncio.create_task(invoke(call.deadline, self.records))
        self.work.add(call.task)

        def finished(task):
            self.work.discard(task)
            if not task.cancelled():
                task.exception()

        call.task.add_done_callback(finished)
        # SDK cancellation must not repeatedly interrupt a pattern child's cleanup.
        try:
            return await asyncio.shield(call.task)
        except asyncio.CancelledError:
            if self.calls.get(request_id) is call:
                raise
            # The boundary already settled it. Do not abort the SDK's task group;
            # response() drops the handler's now-late return value.
            return types.CallToolResult(content=[], is_error=True)

    def stop(self):
        self.stopped.set()
        for call in list(self.calls.values()):
            self._close(call, "session_ended")
        for timer in self.timers:
            if timer is not asyncio.current_task():
                timer.cancel()

    async def join(self):
        with anyio.CancelScope(shield=True):
            await asyncio.gather(
                *self.work, *self.timers, return_exceptions=True
            )

    async def run(self, server, read_stream, write_stream):
        self.output = write_stream
        incoming, server_read = anyio.create_memory_object_stream(0)
        server_write, outgoing = anyio.create_memory_object_stream(0)

        async def receive():
            try:
                async with incoming:
                    async for item in read_stream:
                        self.receive(item)
                        await incoming.send(item)
            finally:
                self.stop()

        async def send():
            try:
                async with outgoing:
                    async for item in outgoing:
                        if (reply := self.response(item)) is not None:
                            await write_stream.send(reply)
            finally:
                self.stop()

        try:
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(receive)
                tasks.start_soon(send)
                tasks.start_soon(
                    server.run,
                    server_read,
                    server_write,
                    server.create_initialization_options(),
                )
                await self.stopped.wait()
                tasks.cancel_scope.cancel()
        finally:
            self.stop()
            await self.join()
