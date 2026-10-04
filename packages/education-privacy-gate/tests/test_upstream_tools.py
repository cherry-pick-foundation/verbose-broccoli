"""All twelve real pinned tools; only a local mocked fetch answers judgments."""

import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path

from fastmcp import Client
import pytest
from test_proxy import DATA
from test_proxy import ORIGINALS
from test_proxy import assert_generic

from education_privacy_gate import __main__ as proxy_module
from education_privacy_gate.masking import Masker
from education_privacy_gate.roster import Registry

ENTRY = Path(
    os.environ.get(
        "JEV_TEST_ENTRY",
        "/tmp/che86-gate-check/npm/node_modules/@jkudish/jev-mcp/dist/index.js",
    )
).resolve()
BASELINE = Path(
    os.environ.get(
        "JEV_TEST_TOOL_LIST",
        "/home/choi-eunchang/.local/state/verbose-broccoli/workspaces/feature-jev-mcp-privacy/jev-mcp-privacy/results/w1-upstream-jev-mcp/attempt-1/tools-list.json",
    )
)
WRAPPER = Path(__file__).with_name("fixture-upstream.mjs").resolve()
TEXT = " ; ".join(ORIGINALS) + " ; 3학년 2반 2026학년도 85점"


def cases():
    evidence = [
        {"id": ORIGINALS[0], "text": TEXT},
        {"id": "evidence-b", "text": TEXT + " second"},
    ]
    files = [{"path": "fixtures/" + TEXT + ".py", "diff": TEXT}]
    return [
        ("jev_verify", {"claims": [TEXT], "evidence": evidence}),
        ("jev_screen", {"text": TEXT, "purpose": TEXT}),
        (
            "jev_noul",
            {
                "propositions": [TEXT],
                "context": evidence[0],
                "auto_accept": 0.9,
            },
        ),
        (
            "jev_find",
            {"query": TEXT, "candidates": [{"id": ORIGINALS[0], "text": TEXT}]},
        ),
        (
            "jev_classify",
            {
                "items": [{"id": ORIGINALS[0], "text": TEXT}],
                "classes": [
                    {"id": ORIGINALS[0], "description": TEXT},
                    {"id": ORIGINALS[1], "description": TEXT + " second"},
                ],
                "purpose": TEXT,
                "context": {
                    TEXT: [{"nested": TEXT, "numeric": 1234567890, "score": 85}]
                },
            },
        ),
        (
            "jev_decide",
            {
                "decision": TEXT,
                "evidence": TEXT,
                "priorities": TEXT,
                "candidates": [
                    {"id": "first", "description": TEXT},
                    {"id": "second", "description": TEXT + " second"},
                ],
                "requirements": [TEXT],
            },
        ),
        (
            "jev_rerank",
            {"query": TEXT, "candidates": [{"id": ORIGINALS[0], "text": TEXT}]},
        ),
        (
            "jev_compare",
            {
                "passage_a": TEXT,
                "passage_b": TEXT + " second",
                "aspects": [TEXT],
                "purpose": TEXT,
            },
        ),
        (
            "jev_extract",
            {
                "document": TEXT,
                "fields": [
                    {
                        "id": "value",
                        "description": TEXT,
                        "pattern": "(" + TEXT + ")",
                        "flags": "i",
                    }
                ],
                "purpose": TEXT,
            },
        ),
        (
            "jev_audit",
            {
                "source": TEXT,
                "records": [{"id": "first", "request": TEXT, "value": TEXT}],
            },
        ),
        ("jev_review", {"request": TEXT, "files": files, "tests": TEXT}),
        (
            "jev_gate",
            {
                "request": TEXT,
                "files": files,
                "tests": TEXT,
                "claims": [TEXT],
                "evidence": evidence,
            },
        ),
        ("jev_review", {"request": TEXT, "diff": TEXT, "tests": TEXT}),
        (
            "jev_gate",
            {
                "request": TEXT,
                "diff": TEXT,
                "tests": TEXT,
                "claims": [TEXT],
                "evidence": TEXT,
            },
        ),
        ("jev_verify", {"claims": [TEXT], "evidence": TEXT}),
        ("jev_verify", {"claims": [TEXT], "evidence": evidence[0]}),
        ("jev_noul", {"propositions": [TEXT], "context": TEXT}),
        ("jev_noul", {"propositions": [TEXT], "context": evidence}),
    ]


@pytest.fixture
def capture(monkeypatch):
    monkeypatch.setattr(
        proxy_module.roster, "load_registry", lambda: Registry.from_data(DATA)
    )
    captured = []
    restore = Masker.restore

    def record(self, result):
        captured.append(result)
        return restore(self, result)

    monkeypatch.setattr(Masker, "restore", record)
    return captured


@asynccontextmanager
async def upstream(tmp_path, mode="normal"):
    assert ENTRY.is_file(), (
        "Prepare the scratch locked npm closure before running"
    )
    assert WRAPPER.is_file(), "The test wrapper must exist"
    with (tmp_path / ("node-" + mode + ".log")).open("w") as log:
        proxy = proxy_module.build_proxy(
            key="sk-or-synthetic-dummy-not-a-real-key",
            args=[str(WRAPPER), str(ENTRY), mode],
            log_file=log,
        )
        transport = proxy.client_factory().transport
        async with Client(proxy, timeout=20, mode="legacy") as client:
            yield client
        await transport.close()
    assert all(
        original not in (tmp_path / ("node-" + mode + ".log")).read_text()
        for original in ORIGINALS
    )


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


@pytest.mark.parametrize(
    "name,args",
    cases(),
    ids=[name + str(i) for i, (name, _) in enumerate(cases())],
)
def test_every_tool(name, args, tmp_path, capture):
    async def run():
        async with upstream(tmp_path) as client:
            result = await client.call_tool_mcp(name, args)
            assert not result.is_error, result
            parsed = json.loads(result.content[0].text)
            assert parsed["tool"] == name
            assert parsed["provider"] == "openrouter"
            assert parsed["model"] == "typesafe/jev-1.13"
            raw = json.loads(capture[-1]["content"][0]["text"])
            recorded = raw["usage"]["input_tokens"]
            body = json.dumps(recorded, ensure_ascii=False)
            assert all(original not in body for original in ORIGINALS)
            assert recorded["external_network_requests"] == 0
            assert recorded["deadlines"] and set(recorded["deadlines"]) == {
                60000
            }
            assert (
                recorded["url"] == "https://openrouter.ai/api/alpha/decisions"
            )
            assert recorded["request"]["model"] == "typesafe/jev-1.13"
            assert set(recorded["env_keys"]) <= {
                "HOME",
                "LOGNAME",
                "PATH",
                "SHELL",
                "TERM",
                "USER",
                "JEV_PROVIDER",
                "OPENROUTER_API_KEY",
                "JEV_MCP_MODEL",
            }
            assert recorded["cwd"] == "/" and recorded["entry"] == str(ENTRY)
            # Entire arbitrary usage trees and encoded JSON restore too.
            restored_request = parsed["usage"]["input_tokens"]["request"]
            assert TEXT in json.dumps(restored_request, ensure_ascii=False)
            assert (
                json.loads(parsed["usage"]["output_tokens"])["echo"]
                == restored_request["state"]
            )
            assert "3학년 2반 2026학년도 85점" in json.dumps(
                restored_request, ensure_ascii=False
            )
            if name == "jev_verify":
                assert parsed["results"][0]["claim"] == TEXT
                if isinstance(args["evidence"], list):
                    assert (
                        parsed["results"][0]["supporting_evidence"]
                        == ORIGINALS[0]
                    )
            elif name == "jev_noul":
                assert parsed["results"][0]["proposition"] == TEXT
                assert parsed["results"][0]["label"] == "likely"
            elif name in ("jev_find", "jev_rerank"):
                rows = parsed["top" if name == "jev_find" else "ranked"]
                assert parsed["query"] == TEXT
                assert rows[0]["id"] == ORIGINALS[0] and rows[0]["text"] == TEXT
            elif name == "jev_classify":
                assert parsed["results"][0]["id"] == ORIGINALS[0]
                assert set(parsed["results"][0]["probabilities"]) == {
                    ORIGINALS[0],
                    ORIGINALS[1],
                }
                assert parsed["summary"]["by_class"] == {ORIGINALS[0]: 1}
                assert (
                    restored_request["state"]["context"][TEXT][0]["numeric"]
                    == "1234567890"
                )
                assert (
                    restored_request["state"]["context"][TEXT][0]["score"] == 85
                )
            elif name == "jev_compare":
                assert parsed["aspects"][0]["aspect"] == TEXT
            elif name == "jev_extract":
                assert parsed["results"][0]["value"] == TEXT
                assert parsed["results"][0]["status"] == "auto"
                assert (
                    restored_request["state"]["fields"][0]["pattern"]
                    == "(" + TEXT + ")"
                )
            elif name == "jev_audit":
                assert parsed["records"][0]["value"] == TEXT
            elif name in ("jev_review", "jev_gate") and "files" in args:
                review = parsed if name == "jev_review" else parsed["review"]
                assert review["files"][0]["path"] == args["files"][0]["path"]
                assert all(
                    row["file"] == args["files"][0]["path"]
                    for row in review["limiting"]
                )
            if name == "jev_gate":
                assert parsed["verification"]["results"][0]["claim"] == TEXT

    asyncio.run(run())


@pytest.mark.usefixtures("capture")
def test_pinned_list(tmp_path):
    async def run():
        async with upstream(tmp_path) as client:
            actual = await client.list_tools()
            baseline = json.loads(BASELINE.read_text())["tools"]
            assert len(actual) == 12
            assert {tool.name: tool.input_schema for tool in actual} == {
                tool["name"]: tool["inputSchema"] for tool in baseline
            }
            assert all(tool.output_schema is None for tool in actual)

    asyncio.run(run())


@pytest.mark.parametrize(
    "name,args",
    [
        (
            "jev_decide",
            {
                "decision": TEXT,
                "candidates": [
                    {"id": ORIGINALS[1], "description": TEXT},
                    {"id": "safe", "description": TEXT},
                ],
            },
        ),
        (
            "jev_extract",
            {
                "document": TEXT,
                "fields": [
                    {"id": ORIGINALS[1], "pattern": ".+", "description": TEXT}
                ],
            },
        ),
        (
            "jev_audit",
            {
                "source": TEXT,
                "records": [
                    {"id": ORIGINALS[1], "request": TEXT, "value": TEXT}
                ],
            },
        ),
        (
            "jev_find",
            {
                "query": TEXT,
                "candidates": [{"text": TEXT}],
                "top_k": 1234567890,
            },
        ),
        ("jev_noul", {"propositions": [TEXT] * 65}),
        ("jev_noul", {"propositions": ["x" * 2001]}),
        ("jev_noul", {"propositions": [TEXT], "auto_accept": 0.5}),
        (
            "jev_find",
            {"query": TEXT, "candidates": [{"id": ORIGINALS[1], "text": TEXT}]},
        ),
        (
            "jev_verify",
            {
                "claims": [TEXT],
                "evidence": {"id": "x" * 64 + ORIGINALS[0], "text": TEXT},
            },
        ),
    ],
)
def test_preflight_refuses_before_backend(name, args, tmp_path, capture):
    async def run():
        async with upstream(tmp_path) as client:
            before = len(capture)
            assert_generic(await client.call_tool_mcp(name, args))
            # Restoration would run only for a forwarded result.
            assert len(capture) == before
            assert not (
                await client.call_tool_mcp(
                    "jev_screen", {"text": "safe synthetic"}
                )
            ).is_error

    asyncio.run(run())


@pytest.mark.usefixtures("capture")
def test_extract_local_no_match_and_invalid_regex(tmp_path):
    async def run():
        async with upstream(tmp_path) as client:
            for pattern, status in (
                ("not-in-document", "not_found"),
                ("[", "invalid_pattern"),
                (ORIGINALS[0] + "[", "invalid_pattern"),
            ):
                result = await client.call_tool_mcp(
                    "jev_extract",
                    {
                        "document": TEXT,
                        "fields": [
                            {
                                "id": "value",
                                "description": TEXT,
                                "pattern": pattern,
                            }
                        ],
                    },
                )
                parsed = json.loads(result.content[0].text)
                assert parsed["provider"] == "none" and parsed["usage"] is None
                assert parsed["results"][0]["status"] == status
                if pattern.startswith(ORIGINALS[0]):
                    assert "Ga Raon" in parsed["results"][0]["reason"]

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["oversize", "retry"])
@pytest.mark.usefixtures("capture")
def test_reused_response_ceiling_and_retries(mode, tmp_path):
    async def run():
        async with upstream(tmp_path, mode) as client:
            result = await client.call_tool_mcp("jev_screen", {"text": TEXT})
            if mode == "oversize":
                assert result.is_error
                assert (
                    "Response exceeded 1000000 bytes" in result.content[0].text
                )
                assert all(
                    original not in result.content[0].text
                    for original in ORIGINALS
                )
            else:
                assert not result.is_error
                parsed = json.loads(result.content[0].text)
                assert parsed["usage"]["input_tokens"]["attempt"] == 3

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["deadline", "retry-one", "retry-six"])
@pytest.mark.usefixtures("capture")
def test_supported_upstream_deadline_and_attempt_controls(mode, tmp_path):
    async def run():
        async with upstream(tmp_path, mode) as client:
            result = await client.call_tool_mcp("jev_screen", {"text": TEXT})
            if mode == "retry-six":
                assert not result.is_error
                parsed = json.loads(result.content[0].text)
                assert parsed["usage"]["input_tokens"]["attempt"] == 6
            else:
                assert result.is_error
                expected = "25ms deadline" if mode == "deadline" else "API 429"
                assert expected in result.content[0].text

    asyncio.run(run())


@pytest.mark.parametrize(
    "propositions", [["safe synthetic"] * 64, ["x" * 2000]]
)
@pytest.mark.usefixtures("capture")
def test_noul_schema_boundaries_are_accepted(propositions, tmp_path):
    async def run():
        async with upstream(tmp_path) as client:
            result = await client.call_tool_mcp(
                "jev_noul", {"propositions": propositions}
            )
            assert not result.is_error
            parsed = json.loads(result.content[0].text)
            assert [
                row["proposition"] for row in parsed["results"]
            ] == propositions

    asyncio.run(run())
