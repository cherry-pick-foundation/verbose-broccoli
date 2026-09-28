"""Offline checks for the capture harness and its committed upstream oracle."""

import asyncio
from contextlib import asynccontextmanager
import hashlib
import json
from urllib.error import HTTPError
from urllib.request import Request
from urllib.request import urlopen

import anyio
from mcp import types
from mcp.server.lowlevel import Server
from mcp.shared.memory import create_client_server_memory_streams
import pytest

from backfire_tools.acceptance import capture_upstream as capture
from backfire_tools.acceptance.scripted_endpoint import scripted_endpoint
from backfire_tools.acceptance.scripted_endpoint import scripted_response


def post(url, body):
    request = Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.load(response)
    except HTTPError as response:
        return response.code, json.load(response)


def test_endpoint_records_state_and_question_order_and_scripted_answers():
    body = {
        "model": "ignored",
        "state": {"text": "한글", "nested": [1, None]},
        "questions": {
            "pick": {
                "type": "choice",
                "instructions": "Pick.",
                "criteria": {"second": None, "first": "A"},
            },
            "probability": {"type": "noul", "instructions": "Likely?"},
            "score": {"type": "score", "criteria": ["Low", "Medium", "High"]},
        },
    }
    with scripted_endpoint() as (url, exchanges):
        first = post(url, body)
        second = post(url, {**body, "state": "next"})
        assert (
            first
            == second
            == (
                200,
                {
                    "model": "scripted-upstream",
                    "usage": {"input_tokens": 11, "output_tokens": 7},
                    "answers": {
                        "pick": {
                            "type": "choice",
                            "choice": "second",
                            "confidence": 1,
                            "probabilities": {"second": 1, "first": 0},
                        },
                        "probability": {"type": "noul", "noul": 0.875},
                        "score": {
                            "type": "score",
                            "score": 1,
                            "confidence": 1,
                            "probabilities": {"0": 0, "1": 1, "2": 0},
                            "legend": {"0": "Low", "1": "Medium", "2": "High"},
                        },
                    },
                },
            )
        )
        assert [item["request"]["state"] for item in exchanges] == [
            body["state"],
            "next",
        ]
        assert exchanges[0]["request"] == {
            "state": body["state"],
            "questions": body["questions"],
        }
        assert list(exchanges[0]["request"]["questions"]) == [
            "pick",
            "probability",
            "score",
        ]
        assert exchanges[0]["response"] == {
            "status": first[0],
            "body": first[1],
        }


def test_single_choice_is_a_captured_judgment_failure():
    body = {
        "state": {},
        "questions": {"best": {"type": "choice", "criteria": {"only": None}}},
    }
    with scripted_endpoint() as (url, exchanges):
        status, answer = post(url, body)
        assert status == 400
        assert answer["error"].startswith("invalid_request:")
        assert exchanges == [
            {"request": body, "response": {"status": status, "body": answer}}
        ]


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"state": None, "questions": []},
        {"state": None, "questions": {"bad": {"type": "unknown"}}},
    ],
)
def test_handler_failures_fail_the_capture_instead_of_becoming_fixtures(body):
    with pytest.raises(RuntimeError, match="Scripted endpoint failed"):
        with scripted_endpoint() as (url, exchanges):
            assert post(url, body) == (
                500,
                {"error": "Scripted endpoint failed."},
            )
            assert exchanges == []


def test_capture_keeps_every_judgment_in_call_order_and_none_for_local_calls(
    tmp_path, monkeypatch
):
    async def list_tools(context, params):
        del context, params  # Unused.
        return types.ListToolsResult(
            tools=[types.Tool(name="jev_noul", input_schema={"type": "object"})]
        )

    async def call_tool(context, params):
        del context  # Unused.
        for index in range(params.arguments["count"]):
            assert (
                post(
                    endpoint,
                    {
                        "state": [params.arguments["case"], index],
                        "questions": {"p": {"type": "noul"}},
                    },
                )[0]
                == 200
            )
        return types.CallToolResult(
            content=[types.TextContent(type="text", text="unchanged 한글")]
        )

    server = Server(
        "jev-mcp",
        version="0.9.0",
        on_list_tools=list_tools,
        on_call_tool=call_tool,
    )
    endpoint = None

    @asynccontextmanager
    async def transport(parameters):
        nonlocal endpoint
        assert parameters.command == "synthetic-node" and parameters.args == [
            "dist/index.js"
        ]
        assert parameters.cwd == tmp_path
        assert parameters.env["JEV_PROVIDER"] == "compatible"
        assert parameters.env["JEV_MCP_MAX_ATTEMPTS"] == "1"
        endpoint = parameters.env["JEV_API_BASE_URL"]
        async with create_client_server_memory_streams() as (client, streams):
            async with anyio.create_task_group() as tasks:
                tasks.start_soon(
                    server.run, *streams, server.create_initialization_options()
                )
                try:
                    yield client
                finally:
                    tasks.cancel_scope.cancel()

    monkeypatch.setattr(capture, "stdio_client", transport)
    rows = [
        {
            "id": str(index),
            "tool": "backfire_noul",
            "arguments": {"case": index, "count": count},
        }
        for index, count in enumerate((2, 0, 1))
    ]
    _, tools, captured = asyncio.run(
        capture.capture_cases(tmp_path, "synthetic-node", rows)
    )
    assert tools["tools"][0]["name"] == "jev_noul"
    assert [
        [exchange["request"]["state"] for exchange in row["judgments"]]
        for row in captured
    ] == [
        [[0, 0], [0, 1]],
        [],
        [[2, 0]],
    ]
    for row in captured:
        assert row["result"] == {
            "content": [{"type": "text", "text": "unchanged 한글"}],
            "isError": False,
        }


def test_capture_builds_temporary_pinned_source_and_writes_only_after_success(
    tmp_path, monkeypatch
):
    cases = tmp_path / "known.jsonl"
    cases.write_text(
        '{"id":"one","tool":"backfire_noul","arguments":{"propositions":["A"]}}\n'
    )
    output = tmp_path / "output"
    paths, commands = [], []

    def fetch(directory):
        paths.append(directory)
        (directory / "source.tar.gz").write_bytes(b"synthetic archive")
        source = directory / "source"
        (source / "src").mkdir(parents=True)
        for name in (
            "src/index.ts",
            "src/lib.ts",
            "src/provider.ts",
            "package.json",
            "package-lock.json",
        ):
            (source / name).write_text(name)
        return source

    def run(arguments, **kwargs):
        commands.append(arguments)
        assert kwargs["cwd"] == paths[0] / "source"
        assert kwargs["env"] == {
            "PATH": "/synthetic/bin",
            "HOME": str(paths[0]),
        }
        assert kwargs["check"] is True
        assert not output.exists()

    async def captured(source, node, rows):
        assert source == paths[0] / "source" and node == "/synthetic/node"
        assert rows[0]["id"] == "one"
        return {}, {"tools": []}, [{"id": "one", "judgments": [], "result": {}}]

    monkeypatch.setenv("PATH", "/synthetic/bin")
    monkeypatch.setattr(
        capture.shutil, "which", lambda name: f"/synthetic/{name}"
    )
    monkeypatch.setattr(
        capture.subprocess,
        "check_output",
        lambda args, **kw: (
            "v24.19.0\n" if args[0].endswith("node") else "11.11.1\n"
        ),
    )
    monkeypatch.setattr(capture.subprocess, "run", run)
    monkeypatch.setattr(capture, "fetch_source", fetch)
    monkeypatch.setattr(capture, "capture_cases", captured)
    metadata = capture.capture(cases, output)
    assert commands == [
        ["/synthetic/npm", "ci", "--ignore-scripts"],
        ["/synthetic/npm", "run", "build"],
    ]
    assert not paths[0].exists()
    assert metadata["node"] == "v24.19.0" and metadata["npm"] == "11.11.1"
    assert (
        metadata["known_answers_sha256"]
        == hashlib.sha256(cases.read_bytes()).hexdigest()
    )
    assert json.loads((output / "cases.jsonl").read_text())["judgments"] == []
    before = {path.name: path.read_bytes() for path in output.iterdir()}

    async def broken(*args):
        del args  # Unused.
        raise RuntimeError("Capture interrupted")

    monkeypatch.setattr(capture.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(capture, "capture_cases", broken)
    with pytest.raises(RuntimeError, match="Capture interrupted"):
        capture.capture(cases, output)
    assert not paths[-1].exists()
    assert {path.name: path.read_bytes() for path in output.iterdir()} == before


def test_committed_capture_covers_every_argument_set_and_local_extract_cases():
    root = capture.FIXTURES / "upstream-0.9.0"
    source = capture.FIXTURES / "known-answers-v1.jsonl"
    cases = [json.loads(line) for line in source.read_text().splitlines()]
    captured = [
        json.loads(line)
        for line in (root / "cases.jsonl").read_text().splitlines()
    ]
    metadata = json.loads((root / "metadata.json").read_text())
    tools = json.loads((root / "tools-list.json").read_text())["tools"]
    assert metadata["revision"] == capture.REVISION
    assert metadata["source_url"] == capture.SOURCE_URL
    assert metadata["known_answers_sha256"] == capture.sha256(source)
    assert (
        metadata["source_sha256"]["src/index.ts"]
        == "10ae5eee5fbe0de52a4e5e8240b550585a12bab953235d511d550b3decccaac7"
    )
    assert (
        metadata["source_sha256"]["src/lib.ts"]
        == "6b96ab62448b4154a7e4a25ff6ca064b43d5df3fa0e087f6b02fa25e767067d2"
    )
    assert int(metadata["node"].lstrip("v").split(".")[0]) >= 22
    assert metadata["npm"]
    assert len(tools) == 11 and {row["tool"] for row in captured} == {
        tool["name"] for tool in tools
    }
    assert len(captured) == metadata["case_count"] == len(cases)
    assert metadata["judgment_count"] == sum(
        len(row["judgments"]) for row in captured
    )
    for case, row in zip(cases, captured, strict=True):
        assert (row["id"], row["tool"], row["arguments"]) == (
            case["id"],
            case["tool"].replace("backfire_", "jev_", 1),
            case["arguments"],
        )
        assert ("result" in row) != ("error" in row)
        for judgment in row["judgments"]:
            assert set(judgment["request"]) == {"state", "questions"}
            status, body = scripted_response(judgment["request"])
            assert judgment["response"] == {"status": status, "body": body}
    indexed = {row["id"]: row for row in captured}
    for identifier in (
        "extract-boundary-en-no-match",
        "extract-boundary-ko-invalid-pattern",
        "extract-boundary-ko-timeout",
    ):
        assert indexed[identifier]["judgments"] == []
    korean = indexed["extract-normal-ko-korean-value"]
    assert len(korean["judgments"]) == 1
    assert (
        json.loads(korean["result"]["content"][0]["text"])["results"][0][
            "value"
        ]
        == "재시도하지 않습니다"
    )
    timeout = indexed["extract-boundary-ko-timeout"]
    assert json.loads(timeout["result"]["content"][0]["text"])["results"][0][
        "reason"
    ] == ("regex timed out after 1000ms; simplify the pattern")
