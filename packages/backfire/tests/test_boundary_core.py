import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import anyio
from mcp import types
from mcp.client.session import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from mcp.shared.message import SessionMessage
import pytest

from backfire import boundary, patterns
from backfire.records import RecordFile, RecordWriteError, digest, read_records
from backfire.server import TOOLS, create_server
from backfire.tools import extract
from scripted_judge import ScriptedJudge


@asynccontextmanager
async def session(tmp_path, judge):
    with RecordFile(tmp_path / "records") as records:
        edge = boundary.Boundary(records, TOOLS)
        server = create_server(judge, edge)
        with anyio.fail_after(5):
            async with create_client_server_memory_streams() as (client_streams, server_streams):
                async with anyio.create_task_group() as tasks:
                    tasks.start_soon(edge.run, server, *server_streams)
                    try:
                        async with ClientSession(*client_streams) as client:
                            await client.initialize()
                            yield client, edge, records
                    finally:
                        edge.stop()


def request(identifier=1):
    return SessionMessage(types.JSONRPCRequest(
        jsonrpc="2.0", id=identifier, method="tools/call",
        params={"name": "backfire_noul", "arguments": {"propositions": ["test"]}},
    ))


def test_record_and_judge_receive_the_original_call_context(tmp_path):
    judge = ScriptedJudge([{
        "model": "scripted-model", "answers": {"p_proposition0": {"type": "noul", "noul": 0.99}},
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }])

    async def run():
        async with session(tmp_path, judge) as (client, edge, records):
            result = await client.call_tool("backfire_noul", {"propositions": ["test"]})
            assert not result.is_error
            row, = read_records(records.path)
            assert row["input_digest"] == digest({"tool": "backfire_noul", "arguments": {"propositions": ["test"]}})
            assert row["result_digest"] == digest(result.model_dump(by_alias=True, exclude_unset=True))
            assert row["decisions"] == [{"label": "likely", "auto": True, "status": "ok"}]
            assert row["model"] == "scripted-model"
            assert row["outcome"] == "ok" and row["call"] == 1
            observed = judge.requests[0]
            assert observed["record_file"].session == records.session
            assert observed["record_file"].calls_in_flight == {1}
            assert 117 < observed["deadline"] - asyncio.get_running_loop().time() <= 118
            assert records.calls_in_flight == set() and not edge.calls

    asyncio.run(run())


def test_deadline_cancels_work_and_session_still_serves(tmp_path, monkeypatch):
    monkeypatch.setattr(boundary, "CALL_SECONDS", 0.05)
    judge = ScriptedJudge([{"stall": True}])

    async def run():
        async with session(tmp_path, judge) as (client, edge, records):
            result = await client.call_tool("backfire_noul", {"propositions": ["test"]})
            assert result.is_error
            assert result.content[0].text == boundary.ERRORS["deadline_exceeded"]
            assert len((await client.list_tools()).tools) == 11
            assert not edge.work
            row, = read_records(records.path)
            assert row["outcome"] == "deadline_exceeded" and row["decisions"] is None
            assert row["result_digest"] == digest(result.model_dump(by_alias=True, exclude_unset=True))

    asyncio.run(run())


def test_cancellation_closes_once_and_drops_late_response(tmp_path):
    async def run():
        with RecordFile(tmp_path / "records") as records:
            edge = boundary.Boundary(records, TOOLS)
            incoming = request()
            edge.receive(incoming)
            edge.receive(SessionMessage(types.JSONRPCNotification(
                jsonrpc="2.0", method="notifications/cancelled", params={"requestId": 1},
            )))
            late = SessionMessage(types.JSONRPCResponse(jsonrpc="2.0", id=1, result={"content": []}))
            assert edge.response(late) is None
            assert records.calls_in_flight == set()
            row, = read_records(records.path)
            assert row["outcome"] == "cancelled" and row["result_digest"] is None
            edge.stop()
            await edge.join()

    asyncio.run(run())


def test_client_cancellation_keeps_the_sdk_session_serving(tmp_path):
    judge = ScriptedJudge([{"stall": True}])

    async def run():
        async with session(tmp_path, judge) as (client, edge, records):
            call = asyncio.create_task(client.call_tool("backfire_noul", {"propositions": ["test"]}))
            while not judge.requests:
                await asyncio.sleep(0)
            call.cancel()
            with pytest.raises(asyncio.CancelledError):
                await call
            assert len((await client.list_tools()).tools) == 11
            row, = read_records(records.path)
            assert row["outcome"] == "cancelled"
            assert not edge.calls and not edge.work

    asyncio.run(run())


def test_shutdown_cancels_a_deadline_reply_waiting_for_output(tmp_path, monkeypatch):
    monkeypatch.setattr(boundary, "CALL_SECONDS", 0)

    async def run():
        with RecordFile(tmp_path / "records") as records:
            edge = boundary.Boundary(records, TOOLS)
            edge.output, receive = anyio.create_memory_object_stream(0)
            async with edge.output, receive:
                edge.receive(request())
                while edge.calls:
                    await asyncio.sleep(0)
                assert edge.timers
                edge.stop()
                await asyncio.wait_for(edge.join(), 1)
                assert not edge.timers

    asyncio.run(run())


def test_record_failure_replaces_result(tmp_path, monkeypatch):
    def fail(**kwargs):
        raise RecordWriteError("private diagnostic")

    async def run():
        async with session(tmp_path, ScriptedJudge([])) as (client, edge, records):
            monkeypatch.setattr(records, "write_tool_call", fail)
            result = await client.call_tool("backfire_noul", {})
            assert result.is_error and result.content[0].text == boundary.ERRORS["record_write_failed"]
            assert not edge.calls and not records.calls_in_flight

    asyncio.run(run())


@pytest.mark.parametrize("outcome", ["cancelled", "session_ended"])
def test_boundary_cancellation_reaps_pattern_child(tmp_path, monkeypatch, outcome):
    async def run():
        spawned = asyncio.Event()
        children = []
        original_spawn = asyncio.create_subprocess_exec

        async def observe_spawn(*args, **kwargs):
            child = await original_spawn(*args, **kwargs)
            children.append(child)
            spawned.set()
            return child

        monkeypatch.setattr(patterns.asyncio, "create_subprocess_exec", observe_spawn)
        judge = ScriptedJudge([])
        arguments = {"document": "a" * 49999 + "!", "fields": [
            {"id": "match", "pattern": "(a+)+$", "description": "match"},
        ]}
        with RecordFile(tmp_path / "records") as records:
            edge = boundary.Boundary(records, TOOLS)
            edge.receive(request())
            call = asyncio.create_task(edge.call(1, lambda deadline, writer: extract.call(
                arguments, judge, deadline=deadline, record_file=writer,
            )))
            try:
                await asyncio.wait_for(spawned.wait(), 2)
                if outcome == "cancelled":
                    edge.receive(SessionMessage(types.JSONRPCNotification(
                        jsonrpc="2.0", method="notifications/cancelled", params={"requestId": 1},
                    )))
                else:
                    edge.stop()
                await asyncio.wait_for(call, 1)
                await edge.join()
                assert len(children) == 1 and children[0].returncode == -signal.SIGKILL
                assert not judge.requests
                row, = read_records(records.path)
                assert row["outcome"] == outcome
            finally:
                edge.stop()
                await edge.join()
                await asyncio.gather(call, return_exceptions=True)

    asyncio.run(run())


def test_stdio_oversized_line_ends_without_waiting_for_newline(tmp_path):
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"script": [], "requests_file": "requests.jsonl"}))

    async def run():
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "backfire", "serve-mcp",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "BACKFIRE_TEST_JUDGE_SCRIPT": str(script)},
        )
        try:
            process.stdin.write(b" " * (10 * 1024 * 1024 + 1))
            await asyncio.wait_for(process.stdin.drain(), 5)
            assert await asyncio.wait_for(process.wait(), 5) == 0
            assert await process.stdout.read() == b""
            assert await process.stderr.read() == b"session_ended\n"
        finally:
            if process.returncode is None:
                process.kill()
            await process.wait()
            process.stdin.close()

    asyncio.run(run())


@pytest.mark.parametrize("ending", ["eof", "output_failure", signal.SIGTERM, signal.SIGINT])
def test_stdio_shutdown_records_and_cancels_open_work(tmp_path, ending):
    script = tmp_path / "script.json"
    script.write_text(json.dumps({"script": [{"stall": True}], "requests_file": "requests.jsonl"}))
    process = subprocess.Popen(
        [sys.executable, "-m", "backfire", "serve-mcp"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={**os.environ, "BACKFIRE_TEST_JUDGE_SCRIPT": str(script)},
    )

    def send(message):
        process.stdin.write(json.dumps({"jsonrpc": "2.0", **message}).encode() + b"\n")
        process.stdin.flush()

    try:
        send({"id": 0, "method": "initialize", "params": {
            "protocolVersion": "2025-11-25", "capabilities": {},
            "clientInfo": {"name": "boundary-test", "version": "1"},
        }})
        assert select.select([process.stdout], [], [], 5)[0]
        assert json.loads(process.stdout.readline())["id"] == 0
        send({"method": "notifications/initialized"})
        send({"id": 1, "method": "tools/call", "params": request().message.params})
        captured = tmp_path / "requests.jsonl"
        deadline = time.monotonic() + 3
        while (not captured.exists() or not captured.stat().st_size) and time.monotonic() < deadline:
            time.sleep(0.01)
        assert captured.stat().st_size
        if ending == "eof":
            process.stdin.close()
        elif ending == "output_failure":
            process.stdout.close()
            send({"id": 2, "method": "tools/list"})
        else:
            process.send_signal(ending)
        assert process.wait(timeout=5) == 0
        assert b"Traceback" not in process.stderr.read()
        directory = Path(os.environ["XDG_STATE_HOME"]) / "verbose-broccoli/backfire/records"
        row, = (row for path in directory.glob("*.jsonl") for row in read_records(path))
        assert row["outcome"] == "session_ended" and row["call"] == 1
        assert row["result_digest"] is None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()


@pytest.mark.parametrize("newline", [b"", b"\n"])
def test_line_limit_counts_bytes_before_newline(tmp_path, monkeypatch, newline):
    monkeypatch.setattr(boundary, "MAX_LINE_BYTES", 16)

    async def run():
        read_fd, write_fd = os.pipe()
        try:
            os.write(write_fd, "한".encode() * 6 + newline)
            with pytest.raises(boundary.MessageTooLarge):
                await asyncio.wait_for(anext(boundary.BoundedLineReader(read_fd)), 1)
        finally:
            os.close(read_fd)
            os.close(write_fd)

    asyncio.run(run())


def test_bounded_reader_keeps_lines_and_final_unterminated_input(tmp_path, monkeypatch):
    monkeypatch.setattr(boundary, "MAX_LINE_BYTES", 16)
    path = tmp_path / "input"
    path.write_bytes(b"x" * 16 + b"\nsecond\nlast")

    async def run():
        with path.open("rb") as source:
            assert [line async for line in boundary.BoundedLineReader(source.fileno())] == [
                "x" * 16 + "\n", "second\n", "last",
            ]

    asyncio.run(run())
