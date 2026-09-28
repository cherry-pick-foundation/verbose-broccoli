"""T027: exercise the MCP boundary through the real stdio entry point."""

import asyncio
from contextlib import asynccontextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys

from mcp_types.methods import serialize_server_result
import pytest
import rfc8785

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MESSAGE_LIMIT = 10 * 1024 * 1024
ANSWER = {
    "model": "scripted-model",
    "answers": {"p_proposition0": {"type": "noul", "noul": 0.97}},
    "usage": {"input_tokens": 1, "output_tokens": 2},
}
NOUL = {
    "name": "backfire_noul",
    "arguments": {"propositions": ["한글\nunchanged"]},
}
PROTOCOL_2026_META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {
        "name": "boundary-test",
        "version": "1",
    },
    "io.modelcontextprotocol/clientCapabilities": {},
}
LOCAL_EXTRACT = {
    "name": "backfire_extract",
    "arguments": {
        "document": "no digits",
        "fields": [
            {"id": "number", "pattern": r"\d+", "description": "number"},
        ],
    },
}


def install_stream_probe(path, hold_id):
    """Hold completed SDK replies until cancellation arrives."""
    # Loaded only by subprocess hook, not pytest.
    import anyio  # noqa: PLC0415

    # Loaded only by subprocess hook, not pytest.
    from mcp.server.lowlevel import Server  # noqa: PLC0415

    # Loaded only by subprocess hook, not pytest.
    from backfire.boundary import Boundary  # noqa: PLC0415

    def capture(direction, item):
        message = item.message.model_dump(by_alias=True, exclude_unset=True)
        with open(path, "a", encoding="utf-8") as output:
            output.write(
                json.dumps({"direction": direction, "message": message}) + "\n"
            )
        return message

    original_run, original_response = Server.run, Boundary.response

    async def run(self, read_stream, write_stream, *args, **kwargs):
        cancelled = asyncio.Event()
        receive, send = read_stream.receive, write_stream.send

        async def observed_receive():
            item = await receive()
            message = capture("received", item)
            if (
                message.get("method") == "notifications/cancelled"
                and message.get("params", {}).get("requestId") == hold_id
            ):
                cancelled.set()
            return item

        async def observed_send(item):
            message = capture("sent", item)
            if hold_id is not None and message.get("id") == hold_id:
                # Shield the delivery so the SDK cannot swallow the late reply.
                with anyio.CancelScope(shield=True):
                    print("response_held", file=sys.stderr, flush=True)
                    await cancelled.wait()
                    await send(item)
            else:
                await send(item)

        read_stream.receive, write_stream.send = observed_receive, observed_send
        await original_run(self, read_stream, write_stream, *args, **kwargs)

    def response(self, item):
        result = original_response(self, item)
        if hold_id is not None and getattr(item.message, "id", None) == hold_id:
            print(
                "response_dropped" if result is None else "response_forwarded",
                file=sys.stderr,
                flush=True,
            )
        return result

    Server.run, Boundary.response = run, response


@asynccontextmanager
async def server(
    tmp_path, script=(), *, probe=False, hold_id=None, call_seconds=None
):
    script_path = tmp_path / "script.json"
    script_path.write_text(
        json.dumps({"script": list(script), "requests_file": "requests.jsonl"})
    )
    environment = {
        **os.environ,
        "BACKFIRE_TEST_JUDGE_SCRIPT": str(script_path),
        "PYTHONDONTWRITEBYTECODE": "1",
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
    }
    if probe or call_seconds is not None:
        lines = [
            "import sys",
            "if sys.orig_argv[-2:] == ['backfire', 'serve-mcp']:",
        ]
        if probe:
            trace_path = str(tmp_path / "trace.jsonl")
            lines.extend(
                (
                    "    from test_boundary import install_stream_probe",
                    f"    install_stream_probe({trace_path!r}, {hold_id!r})",
                )
            )
        if call_seconds is not None:
            lines.extend(
                (
                    "    from backfire import boundary",
                    f"    boundary.CALL_SECONDS = {call_seconds!r}",
                )
            )
        (tmp_path / "sitecustomize.py").write_text("\n".join(lines) + "\n")
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(tmp_path), str(Path(__file__).parent))
        )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "backfire",
        "serve-mcp",
        cwd=PACKAGE_ROOT,
        env=environment,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        yield process
    finally:
        process.stdin.close()
        try:
            await asyncio.wait_for(process.wait(), 10)
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()


async def send(process, message):
    message = {"jsonrpc": "2.0", **message}
    process.stdin.write(
        json.dumps(message, ensure_ascii=False).encode() + b"\n"
    )
    await asyncio.wait_for(process.stdin.drain(), 10)
    return message


async def receive(process):
    line = await asyncio.wait_for(process.stdout.readline(), 10)
    assert line, "Server ended before replying"
    return json.loads(line)


async def initialize(process):
    request = await send(
        process,
        {
            "id": "initialize",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "boundary-test", "version": "1"},
            },
        },
    )
    reply = await receive(process)
    assert (
        reply["id"] == request["id"]
        and reply["result"]["serverInfo"]["name"] == "backfire"
    )
    notification = await send(process, {"method": "notifications/initialized"})
    return [request, notification], [reply]


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def records_directory(tmp_path):
    return tmp_path / "state/verbose-broccoli/backfire/records"


def records(tmp_path):
    return [
        row
        for path in sorted(records_directory(tmp_path).glob("*.jsonl"))
        for row in lines(path)
    ]


def digest(value):
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def assert_record(row, number, params, reply, outcome):
    assert row["kind"] == "tool_call" and row["call"] == number
    assert row["tool"] == params.get("name", "unknown")
    assert row["outcome"] == outcome
    assert row["input_digest"] == digest(
        {
            "tool": params.get("name"),
            "arguments": params.get("arguments", {}),
        }
    )
    assert row["result_digest"] == (
        digest(reply["result"]) if "result" in reply else None
    )
    assert row["duration_ms"] >= 0


def test_protocol_2026_tool_result_is_complete(tmp_path):
    async def run():
        async with server(tmp_path, [ANSWER]) as process:
            await send(
                process,
                {
                    "id": "modern",
                    "method": "tools/call",
                    "params": {
                        **NOUL,
                        "_meta": PROTOCOL_2026_META,
                    },
                },
            )
            reply = await receive(process)
            assert "result" in reply and "error" not in reply, reply
            assert reply["result"]["resultType"] == "complete"

    asyncio.run(run())


def test_protocol_2026_deadline_reply_validates(tmp_path):
    async def run():
        async with server(
            tmp_path, [{"stall": True}], call_seconds=0.05
        ) as process:
            await send(
                process,
                {
                    "id": "deadline",
                    "method": "tools/call",
                    "params": {
                        **NOUL,
                        "_meta": PROTOCOL_2026_META,
                    },
                },
            )
            reply = await receive(process)
            assert (
                reply["id"] == "deadline"
                and "result" in reply
                and "error" not in reply
            )
            assert reply["result"]["content"][0]["text"].startswith(
                "deadline_exceeded:"
            )
            assert (
                serialize_server_result(
                    "tools/call", "2026-07-28", reply["result"]
                )
                == reply["result"]
            )

    asyncio.run(run())


def test_messages_pass_unchanged_and_every_call_is_recorded_before_reply(
    tmp_path,
):
    async def run():
        async with server(
            tmp_path,
            [ANSWER, {"error": "refused: synthetic failure"}],
            probe=True,
        ) as process:
            sent, received = await initialize(process)
            calls = [
                ("unicode-id-한글", NOUL, "ok"),
                (7, LOCAL_EXTRACT, "ok"),
                ("tool-error", NOUL, "tool_error"),
                (
                    "invalid-arguments",
                    {"name": "backfire_noul", "arguments": {}},
                    "tool_error",
                ),
                ("missing-arguments", {"name": "backfire_noul"}, "tool_error"),
                ("protocol-error", {"arguments": {}}, "protocol_error"),
            ]
            for number, (identifier, params, outcome) in enumerate(calls, 1):
                sent.append(
                    await send(
                        process,
                        {
                            "id": identifier,
                            "method": "tools/call",
                            "params": {
                                **params,
                                "_meta": {
                                    "progressToken": f"progress-{number}"
                                },
                            },
                        },
                    )
                )
                reply = await receive(process)
                received.append(reply)
                assert reply["id"] == identifier
                if "result" in reply:
                    assert "resultType" not in reply["result"]
                    assert reply["result"].get("isError") is not False
                rows = records(tmp_path)
                assert len(rows) == number
                assert_record(rows[-1], number, params, reply, outcome)
                if identifier == "unicode-id-한글":
                    result = json.loads(reply["result"]["content"][0]["text"])
                    assert (
                        result["results"][0]["proposition"] == "한글\nunchanged"
                    )
                    assert result["results"][0]["probability"] == 0.97
                    assert rows[-1]["model"] == "scripted-model"
                    assert rows[-1]["decisions"] == [
                        {"label": "likely", "auto": True, "status": "ok"}
                    ]
                elif identifier == 7:
                    result = json.loads(reply["result"]["content"][0]["text"])
                    assert (
                        result["provider"] == "none"
                        and result["results"][0]["status"] == "not_found"
                    )
                    assert rows[-1]["model"] == "jev-latest"
                    assert rows[-1]["decisions"] == [{"status": "not_found"}]
                elif identifier == "tool-error":
                    assert reply["result"] == {
                        "content": [
                            {
                                "type": "text",
                                "text": "refused: synthetic failure",
                            }
                        ],
                        "isError": True,
                    }
                elif identifier in ("invalid-arguments", "missing-arguments"):
                    assert reply["result"]["isError"] is True
                    assert reply["result"]["content"][0]["text"].startswith(
                        "MCP error -32602: Input validation error: "
                        "Invalid arguments for tool backfire_noul: "
                    )
                else:
                    assert (
                        reply["error"]["code"] == -32602
                        and "result" not in reply
                    )
                    assert (
                        rows[-1]["decisions"] is None
                        and rows[-1]["model"] is None
                    )
            for identifier, method in ((11, "tools/list"), ("ping", "ping")):
                sent.append(
                    await send(process, {"id": identifier, "method": method})
                )
                received.append(await receive(process))
                assert received[-1]["id"] == identifier
            assert len(received[-2]["result"]["tools"]) == 11
            assert received[-1] == {
                "jsonrpc": "2.0",
                "id": "ping",
                "result": {},
            }
            assert len(records(tmp_path)) == len(calls)
        assert process.returncode == 0
        assert await process.stdout.read() == b""
        trace = lines(tmp_path / "trace.jsonl")
        assert [
            row["message"] for row in trace if row["direction"] == "received"
        ] == sent
        assert [
            row["message"] for row in trace if row["direction"] == "sent"
        ] == received
        assert len(lines(tmp_path / "requests.jsonl")) == 2
        assert len({row["session"] for row in records(tmp_path)}) == 1

    asyncio.run(run())


def test_completed_response_is_dropped_after_cancellation(tmp_path):
    async def run():
        async with server(
            tmp_path, [ANSWER, ANSWER], probe=True, hold_id="cancel-me"
        ) as process:
            await initialize(process)
            await send(
                process,
                {"id": "cancel-me", "method": "tools/call", "params": NOUL},
            )
            assert (
                await asyncio.wait_for(process.stderr.readline(), 10)
                == b"response_held\n"
            )
            assert records(tmp_path) == []
            await send(
                process,
                {
                    "method": "notifications/cancelled",
                    "params": {"requestId": "cancel-me"},
                },
            )
            assert (
                await asyncio.wait_for(process.stderr.readline(), 10)
                == b"response_dropped\n"
            )
            (row,) = records(tmp_path)
            assert_record(row, 1, NOUL, {}, "cancelled")
            assert row["decisions"] is None and row["model"] is None
            (held,) = [
                row["message"]
                for row in lines(tmp_path / "trace.jsonl")
                if row["direction"] == "sent"
                and row["message"].get("id") == "cancel-me"
            ]
            assert not held["result"].get("isError")
            assert (
                json.loads(held["result"]["content"][0]["text"])["results"][0][
                    "probability"
                ]
                == 0.97
            )
            # A second cancellation must neither reopen nor duplicate the call.
            await send(
                process,
                {
                    "method": "notifications/cancelled",
                    "params": {"requestId": "cancel-me"},
                },
            )
            await send(
                process,
                {"id": "after-cancel", "method": "tools/call", "params": NOUL},
            )
            reply = await receive(process)
            assert reply["id"] == "after-cancel" and not reply["result"].get(
                "isError"
            )
            rows = records(tmp_path)
            assert len(rows) == 2 and rows[0] == row
            assert_record(rows[1], 2, NOUL, reply, "ok")
        assert process.returncode == 0
        assert await process.stdout.read() == b""

    asyncio.run(run())


@pytest.mark.parametrize(
    "shape", ["no-newline", "padded-json", "large-argument"]
)
def test_oversized_line_ends_session_before_dispatch(tmp_path, shape):
    if shape == "no-newline":
        payload = b" " * (MESSAGE_LIMIT + 1)
    elif shape == "padded-json":
        message = json.dumps(
            {"jsonrpc": "2.0", "id": "oversized", "method": "ping"}
        ).encode()
        payload = message + b" " * (MESSAGE_LIMIT + 1 - len(message)) + b"\n"
    else:
        payload = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "oversized",
                    "method": "tools/call",
                    "params": {
                        "name": "backfire_noul",
                        "arguments": {
                            "propositions": ["test"],
                            "context": "가" * (MESSAGE_LIMIT // 3 + 1),
                        },
                    },
                },
                ensure_ascii=False,
            ).encode()
            + b"\n"
        )

    async def run():
        async with server(tmp_path) as process:
            await initialize(process)
            process.stdin.write(payload)
            try:
                await asyncio.wait_for(process.stdin.drain(), 10)
            except (BrokenPipeError, ConnectionResetError):
                pass
            # Keep stdin open: EOF must not be what makes this test pass.
            assert await asyncio.wait_for(process.wait(), 10) == 0
            assert await process.stdout.read() == b""
            assert await process.stderr.read() == b"session_ended\n"
            assert records(tmp_path) == []
            assert lines(tmp_path / "requests.jsonl") == []

    asyncio.run(run())


def test_line_at_limit_and_following_line_are_accepted(tmp_path):
    async def run():
        async with server(tmp_path) as process:
            await initialize(process)
            message = {"jsonrpc": "2.0", "id": "at-limit", "method": "ping"}
            encoded = json.dumps(message).encode()
            process.stdin.write(
                encoded + b" " * (MESSAGE_LIMIT - len(encoded)) + b"\n"
            )
            await asyncio.wait_for(process.stdin.drain(), 10)
            assert await receive(process) == {
                "jsonrpc": "2.0",
                "id": "at-limit",
                "result": {},
            }
            await send(process, {"id": "next", "method": "ping"})
            assert await receive(process) == {
                "jsonrpc": "2.0",
                "id": "next",
                "result": {},
            }
            assert records(tmp_path) == []
        assert process.returncode == 0

    asyncio.run(run())


def test_record_write_failure_withholds_result_and_session_recovers(tmp_path):
    async def run():
        async with server(tmp_path) as process:
            await initialize(process)
            blocker = records_directory(tmp_path) / "locked-budget.jsonl"
            with blocker.open("wb") as locked:
                locked.truncate(50 * 1024 * 1024)
                fcntl.flock(locked, fcntl.LOCK_EX | fcntl.LOCK_NB)
                await send(
                    process,
                    {
                        "id": "unrecordable",
                        "method": "tools/call",
                        "params": LOCAL_EXTRACT,
                    },
                )
                reply = await receive(process)
                assert reply == {
                    "jsonrpc": "2.0",
                    "id": "unrecordable",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "record_write_failed: Cannot write the "
                                    "tool-call record; check record directory "
                                    "permissions and available space."
                                ),
                            }
                        ],
                        "isError": True,
                        "resultType": "complete",
                    },
                }
                assert (
                    await asyncio.wait_for(process.stderr.readline(), 10)
                    == b"record_write_failed\n"
                )
            blocker.unlink()
            assert records(tmp_path) == []
            await send(
                process,
                {
                    "id": "recovered",
                    "method": "tools/call",
                    "params": LOCAL_EXTRACT,
                },
            )
            reply = await receive(process)
            assert reply["id"] == "recovered" and not reply["result"].get(
                "isError"
            )
            (row,) = records(tmp_path)
            assert_record(row, 2, LOCAL_EXTRACT, reply, "ok")
            assert lines(tmp_path / "requests.jsonl") == []
        assert process.returncode == 0
        assert await process.stdout.read() == b""

    asyncio.run(run())
