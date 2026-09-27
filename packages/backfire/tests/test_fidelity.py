"""Replay the pinned Node capture through the real stdio server (T030).

Only the name mapping and UPSTREAM.md differences apply. Difference 1 changes
the pattern description and one syntax error; difference 2 changes one failed
judgment; difference 4 changes the explicitly listed validation errors below.
Difference 3 is the scripted in-process judge. No captured case exercises
difference 5 (JavaScript prototype keys), so it permits no result changes here.
"""

import asyncio
import json
from pathlib import Path
import sys

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.shared.exceptions import MCPError

FIXTURES = Path(__file__).resolve().parents[3] / "scripts/backfire/fixtures"
CAPTURE = FIXTURES / "upstream-0.9.0"
CASES = [json.loads(line) for line in (CAPTURE / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
TOOL_LIST = json.loads((CAPTURE / "tools-list.json").read_text(encoding="utf-8"))

# UPSTREAM.md difference 4: exact jsonschema diagnostics, retaining the prefix.
VALIDATION_DIFFERENCES = {
    "verify-failure-en": "[] should be non-empty",
    "verify-failure-ko": "-0.1 is less than the minimum of 0",
    "screen-failure-en": "'' should be non-empty",
    "screen-failure-ko": "-0.1 is less than the minimum of 0",
    "noul-failure-en": "'' should be non-empty",
    "noul-failure-ko": "0.5 is less than or equal to the minimum of 0.5",
    "find-failure-ko": "0 is less than the minimum of 1",
    "classify-failure-ko": "[{'id': 'test_success', 'description': '테스트가 성공한 결과.'}] is too short",
    "decide-failure-ko": "[{'id': 'reuse-helper', 'description': '기존 헬퍼를 사용한다.'}] is too short",
    "rerank-failure-ko": "0 is less than the minimum of 1",
    "compare-failure-en": "'' should be non-empty",
    "compare-failure-ko": "1.1 is greater than the maximum of 1",
}
JUDGMENT_DIFFERENCES = {
    # UPSTREAM.md difference 2: the singleton Choice fails the request schema.
    "find-failure-en-single-candidate": (
        "invalid_request: The questions do not match the request schema; correct the questions."
    ),
}
PATTERN_DIFFERENCES = {
    # UPSTREAM.md difference 1: Python re's diagnostic for the captured "(".
    "extract-boundary-ko-invalid-pattern": (
        "Invalid regular expression: /(/g: Unterminated group",
        "missing ), unterminated subpattern at position 0",
    ),
}


def mapped(value):
    return json.loads(json.dumps(value).replace("jev_", "backfire_").replace("jev-mcp", "backfire"))


def wire(value):
    return value.model_dump(by_alias=True, exclude_unset=True)


def expected_outcome(case):
    outcome = mapped({key: case[key] for key in ("result", "error") if key in case})
    identifier = case["id"]
    if identifier in VALIDATION_DIFFERENCES:
        prefix = (
            "MCP error -32602: Input validation error: "
            f"Invalid arguments for tool {mapped(case['tool'])}: "
        )
        assert outcome["result"]["content"][0]["text"].startswith(prefix)
        outcome["result"]["content"][0]["text"] = prefix + VALIDATION_DIFFERENCES[identifier]
    elif identifier in JUDGMENT_DIFFERENCES:
        outcome["result"]["content"][0]["text"] = JUDGMENT_DIFFERENCES[identifier]
    elif identifier in PATTERN_DIFFERENCES:
        before, after = PATTERN_DIFFERENCES[identifier]
        text = outcome["result"]["content"][0]["text"]
        assert text.count(before) == 1
        outcome["result"]["content"][0]["text"] = text.replace(before, after)
    return outcome


@pytest.fixture(scope="module")
def replay(tmp_path_factory):
    directory = tmp_path_factory.mktemp("fidelity")
    requests_file = directory / "requests.jsonl"
    steps = []
    for case in CASES:
        for judgment in case["judgments"]:
            response = judgment["response"]
            if response["status"] == 200:
                # The capture is the oracle; never synthesize answers from port requests.
                steps.append({"result": response["body"]})
            else:
                assert response == {"status": 400, "body": {
                    "error": "invalid_request: Choice requires at least two options.",
                }}
                steps.append({"error": JUDGMENT_DIFFERENCES[case["id"]]})
    script = directory / "script.json"
    script.write_text(json.dumps({"requests_file": str(requests_file), "script": steps}), encoding="utf-8")
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "backfire", "serve-mcp"],
        env={"BACKFIRE_TEST_JUDGE_SCRIPT": str(script), "PYTHONDONTWRITEBYTECODE": "1",
             "XDG_CONFIG_HOME": str(directory / "config"), "XDG_STATE_HOME": str(directory / "state")},
    )

    async def run():
        results = {}
        with anyio.fail_after(60):
            async with stdio_client(parameters) as streams:
                async with ClientSession(*streams) as client:
                    assert (await client.initialize()).server_info.name == "backfire"
                    tools = wire(await client.list_tools())
                    offset = 0
                    for case in CASES:
                        try:
                            outcome = {"result": wire(await client.call_tool(mapped(case["tool"]), case["arguments"]))}
                        except MCPError as error:
                            outcome = {"error": wire(error.error)}
                        # The judge closes its log append before returning the answer.
                        # Awaiting the response gives a barrier; no sleeps or polling.
                        logged = [json.loads(line) for line in requests_file.read_text(encoding="utf-8").splitlines()]
                        results[case["id"]] = (outcome, logged[offset:])
                        offset = len(logged)
        return tools, results

    return asyncio.run(run())


def test_tools_list_matches_capture(replay):
    expected = mapped(TOOL_LIST)
    extract = next(tool for tool in expected["tools"] if tool["name"] == "backfire_extract")
    pattern = extract["inputSchema"]["properties"]["fields"]["items"]["properties"]["pattern"]
    assert pattern["description"] == (
        "JavaScript regex source (without delimiters) that matches candidate values. "
        "Runs in a sandboxed worker with a hard timeout."
    )
    # UPSTREAM.md difference 1 changes this field only, not the rest of the schema.
    pattern["description"] = (
        "Python regular expression source (without delimiters) that matches candidate values, "
        "in Python re syntax: for example (?P<name>...) for a named group, not JavaScript's "
        "(?<name>...). Runs in a child process with a hard timeout."
    )
    assert replay[0] == expected


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_judgment_requests_match_capture_in_order(replay, case):
    expected = mapped([judgment["request"] for judgment in case["judgments"]])
    # Also retain object order, including question and Choice-criteria order.
    assert json.dumps(replay[1][case["id"]][1], ensure_ascii=False) == json.dumps(expected, ensure_ascii=False)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_result_and_error_text_match_capture(replay, case):
    # Keep text opaque: parsing result JSON could hide ordering/formatting drift.
    assert replay[1][case["id"]][0] == expected_outcome(case)


def test_capture_coverage_and_recorded_difference_cases():
    known = [json.loads(line) for line in (FIXTURES / "known-answers-v1.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(case["id"], mapped(case["tool"]), case["arguments"]) for case in CASES] == [
        (case["id"], case["tool"], case["arguments"]) for case in known
    ]
    indexed = {case["id"]: case for case in CASES}
    assert len(indexed) == len(CASES)
    assert {case["tool"] for case in CASES} == {tool["name"] for tool in TOOL_LIST["tools"]}
    assert {
        "extract-boundary-en-no-match", "extract-boundary-ko-invalid-pattern",
        "extract-boundary-ko-timeout", "extract-normal-ko-korean-value",
    } <= indexed.keys()
    for identifier in VALIDATION_DIFFERENCES | JUDGMENT_DIFFERENCES | PATTERN_DIFFERENCES:
        case = indexed[identifier]
        assert expected_outcome(case) != mapped({"result": case["result"]})
