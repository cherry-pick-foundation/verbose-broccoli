"""Offline tests for offer discovery, judgment, and notification."""

import asyncio
from datetime import datetime
import importlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import Mock

import httpx
from mcp import StdioServerParameters
from mcp.types import CallToolResult
from mcp.types import ImageContent
from mcp.types import TextContent
import pytest

import credit_offers

END = "2026-09-27T12:00:00+09:00"
GATE_DIR = Path(__file__).resolve().parents[2] / "education-privacy-gate"
REFUSAL = "Privacy gate rejected the call."
# Synthetic stdio MCP server: records its launch and each call, then answers
# as the canned file says. No provider, key or network is involved.
SERVER = """
import json, os, sys, time
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, ImageContent, TextContent

log, canned = sys.argv[1:3]


def record(**entry):
    with open(log, "a") as handle:
        handle.write(json.dumps(entry) + "\\n")


record(event="launch", pid=os.getpid(), env=sorted(os.environ))
server = MCPServer("synthetic")


@server.tool(name="jev_classify")
def jev_classify(items: list, classes: list, purpose: str = ""):
    record(event="call", items=items, classes=classes, purpose=purpose)
    plan = json.load(open(canned))
    if plan["mode"] == "crash":
        os._exit(9)
    if plan["mode"] == "hang":
        time.sleep(60)
    content = [TextContent(type="text", text=t) for t in plan["texts"]]
    if plan["mode"] == "image":
        image = ImageContent(type="image", data="AA==", mime_type="image/png")
        content = [image]
    return CallToolResult(content=content, is_error=plan["is_error"])


server.run(transport="stdio")
"""
# The reviewed gate proxy over the mocked upstream, with a synthetic list.
LAUNCHER = """
import sys
from education_privacy_gate import __main__ as proxy, roster

person = {"kind": "person", "full": "\\uac00\\ub77c\\uc628"}
data = {"version": 1, "entries": [person]}
roster.load_registry = lambda: roster.Registry.from_data(data)
proxy.build_proxy(
    key="sk-or-synthetic-dummy-not-a-real-key", args=sys.argv[1:4]
).run(transport="stdio", show_banner=False)
"""


def offer(slug, status="active", expiry_date=None):
    return {
        "slug": slug,
        "title": f"Title {slug}",
        "provider": "Example Provider",
        "category": "api_provider",
        "amount": "Free credits",
        "expiry_date": expiry_date,
        "source_url": f"https://example.test/{slug}",
        "status": status,
    }


def install_tracker(
    monkeypatch, old=(), new=(), same_commit=False, forbidden=False
):
    start, _ = credit_offers._block(6, END)
    start_sha, end_sha = "old-commit", "new-commit"
    if same_commit:
        end_sha = start_sha
    requests = []
    config = credit_offers.TRACKER

    def respond(request):
        requests.append(request)
        if request.url.path.endswith("/commits"):
            if forbidden:
                return httpx.Response(403, request=request)
            sha = (
                start_sha
                if request.url.params["until"] == start.isoformat()
                else end_sha
            )
            return httpx.Response(200, json=[{"sha": sha}])
        if request.url.path.endswith(f"/{start_sha}/{config['index_path']}"):
            return httpx.Response(200, json={"offers": list(old)})
        if request.url.path.endswith(f"/{end_sha}/{config['index_path']}"):
            return httpx.Response(200, json={"offers": list(new)})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(credit_offers.httpx, "Client", lambda **_: client)
    return requests


def tool_result(payload=None, text=None, is_error=False):
    body = json.dumps(payload) if text is None else text
    return CallToolResult(
        content=[TextContent(type="text", text=body)], is_error=is_error
    )


def row(slug, choice):
    qualifies = choice == "qualifies"
    return {
        "id": slug,
        "classification": choice,
        "probabilities": {
            "qualifies": 0.9 if qualifies else 0.1,
            "excluded": 0.1 if qualifies else 0.9,
        },
        "confidence": 0.9,
        "margin": 0.8,
        "top_probability": 0.9,
        "decision": "auto",
    }


def payload(rows):
    return {
        "tool": "jev_classify",
        "model": "typesafe/jev-1.13",
        "provider": "openrouter",
        "results": rows,
        "usage": {"input_tokens": 12, "output_tokens": 3},
    }


def classified(offers, choices):
    rows = [
        row(candidate["slug"], choice)
        for candidate, choice in zip(offers, choices, strict=True)
    ]
    return tool_result(payload(rows))


class FakeJudge:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    async def __call__(self, offers):
        self.calls.append(offers)
        if self.error:
            raise self.error
        return self.result


def install_judgment(monkeypatch, result=None, error=None):
    judge = FakeJudge(result, error)
    monkeypatch.setattr(credit_offers, "judge", judge)
    return judge


def test_default_end_is_latest_local_boundary():
    now = datetime.fromisoformat("2026-09-30T13:59:00+09:00")
    local = now.astimezone()
    start, end = credit_offers._block(6, now=now)
    expected = local.replace(hour=12, minute=0, second=0, microsecond=0)
    assert end == expected
    assert start == expected.replace(hour=6)


def test_explicit_end_and_non_dividing_hours():
    start, end = credit_offers._block(6, END)
    expected = datetime.fromisoformat(END).astimezone()
    assert end == expected
    assert start == expected.replace(hour=expected.hour - 6)
    with pytest.raises(ValueError, match="divide 24"):
        credit_offers._block(5, END)


def test_same_commit_exits_without_fetching_index_or_calling_jev(
    monkeypatch, capsys
):
    requests = install_tracker(monkeypatch, same_commit=True)
    judge = install_judgment(monkeypatch)

    status = credit_offers.main(["--end", END])

    assert status == 1
    assert len(requests) == 2
    assert all(
        not request.url.path.endswith("/index.json") for request in requests
    )
    assert judge.calls == []
    assert "jev_calls=0" in capsys.readouterr().out


def test_github_token_is_sent_only_to_api_requests_and_not_logged(
    monkeypatch, capsys
):
    token = "synthetic-github-token"
    monkeypatch.setenv("GITHUB_TOKEN", f"{token}\n")
    requests = install_tracker(
        monkeypatch, old=[offer("old")], new=[offer("new")]
    )
    judge = install_judgment(
        monkeypatch, classified([offer("new")], ["qualifies"])
    )

    assert credit_offers.main(["--end", END]) == 0

    captured = capsys.readouterr()
    api_requests = [r for r in requests if r.url.path.endswith("/commits")]
    raw_requests = [r for r in requests if r.url.path.endswith("/index.json")]
    assert len(api_requests) == 2
    assert all(
        r.headers["Authorization"] == f"Bearer {token}" for r in api_requests
    )
    assert len(raw_requests) == 2
    assert all("Authorization" not in r.headers for r in raw_requests)
    assert token not in captured.out + captured.err
    assert len(judge.calls) == 1


def test_github_token_is_redacted_from_error(monkeypatch, capsys):
    token = "synthetic-github-token"
    monkeypatch.setenv("GITHUB_TOKEN", token)
    monkeypatch.setattr(
        credit_offers,
        "_get_json",
        Mock(side_effect=httpx.LocalProtocolError(f"bad header {token}")),
    )

    assert credit_offers.main(["--end", END]) == 3

    captured = capsys.readouterr()
    assert "[redacted]" in captured.err
    assert token not in captured.out + captured.err


def test_github_token_is_not_logged_on_http_error(monkeypatch, capsys):
    token = "synthetic-github-token"
    monkeypatch.setenv("GITHUB_TOKEN", token)
    requests = install_tracker(monkeypatch, forbidden=True)

    assert credit_offers.main(["--end", END]) == 3

    captured = capsys.readouterr()
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == f"Bearer {token}"
    assert "403" in captured.err
    assert token not in captured.out + captured.err


@pytest.mark.parametrize("token", [None, ""])
def test_github_token_is_omitted_when_unset_or_empty(monkeypatch, token):
    if token is None:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    else:
        monkeypatch.setenv("GITHUB_TOKEN", token)
    requests = install_tracker(monkeypatch, same_commit=True)

    assert credit_offers.main(["--end", END]) == 1

    assert len(requests) == 2
    assert all("Authorization" not in request.headers for request in requests)


def test_filters_new_offers_and_judges_each_candidate_once(monkeypatch, capsys):
    existing = offer("existing")
    strong = offer("strong")
    excluded = offer("excluded")
    expired = offer("expired", expiry_date="2026-09-30")
    inactive = offer("inactive", status="expired")
    install_tracker(
        monkeypatch,
        old=[existing],
        new=[existing, strong, excluded, expired, inactive],
    )
    judge = install_judgment(
        monkeypatch, classified([strong, excluded], ["qualifies", "excluded"])
    )

    status = credit_offers.main(["--end", END])

    output = capsys.readouterr().out
    assert status == 0
    assert judge.calls == [[strong, excluded]]
    assert "strong\tqualifies\t0.9" in output
    assert "excluded\texcluded\t0.9" in output
    assert "jev_calls=1" in output


def test_filtered_offers_make_no_jev_call(monkeypatch, capsys):
    install_tracker(
        monkeypatch,
        new=[
            offer("expired", expiry_date="2026-09-30"),
            offer("inactive", status="removed"),
        ],
    )
    judge = install_judgment(monkeypatch)

    status = credit_offers.main(["--end", END])

    assert status == 1
    assert judge.calls == []
    assert "jev_calls=0" in capsys.readouterr().out


def test_excluded_only_answer_returns_one(monkeypatch, capsys):
    candidate = offer("excluded")
    install_tracker(monkeypatch, new=[candidate])
    install_judgment(monkeypatch, classified([candidate], ["excluded"]))

    status = credit_offers.main(["--end", END])

    output = capsys.readouterr().out
    assert status == 1
    assert "excluded\texcluded\t0.9" in output
    assert "jev_calls=1" in output


def test_review_decision_does_not_change_the_choice(monkeypatch, capsys):
    candidate = offer("unsure")
    install_tracker(monkeypatch, new=[candidate])
    unsure = row("unsure", "qualifies")
    unsure["probabilities"] = {"qualifies": 0.55, "excluded": 0.45}
    unsure["decision"] = "review"
    install_judgment(monkeypatch, tool_result(payload([unsure])))

    assert credit_offers.main(["--end", END]) == 0
    assert "unsure\tqualifies\t0.55" in capsys.readouterr().out


def test_notification_only_contains_strong_offers(monkeypatch):
    strong, excluded = offer("strong"), offer("excluded")
    strong["title"] = "--version"
    install_tracker(monkeypatch, new=[strong, excluded])
    install_judgment(
        monkeypatch, classified([strong, excluded], ["qualifies", "excluded"])
    )
    sent = []

    def record(command, check):
        sent.append(command)
        assert check is True

    monkeypatch.setattr(credit_offers.subprocess, "run", record)

    status = credit_offers.main(["--end", END, "--notify"])

    assert status == 0
    assert len(sent) == 1
    assert sent[0][0] == "notify-send"
    assert sent[0][1:3] == ["--", "New API credit offers"]
    assert sent[0][3].startswith("--version — Example Provider")
    assert "Title excluded" not in sent[0][3]
    assert "Example Provider" in sent[0][3]
    assert "Free credits" in sent[0][3]
    assert "https://example.test/strong" in sent[0][3]


def test_no_notification_without_the_flag_or_a_strong_offer(monkeypatch):
    candidate = offer("excluded")
    install_tracker(monkeypatch, new=[candidate])
    install_judgment(monkeypatch, classified([candidate], ["excluded"]))
    run = Mock()
    monkeypatch.setattr(credit_offers.subprocess, "run", run)

    assert credit_offers.main(["--end", END, "--notify"]) == 1
    run.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        credit_offers.subprocess.CalledProcessError(1, ["notify-send"]),
        OSError("notify-send unavailable"),
    ],
)
def test_notification_failure_exits_three_after_printing_judgment(
    monkeypatch, capsys, error
):
    candidate = offer("candidate")
    install_tracker(monkeypatch, new=[candidate])
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "synthetic-test-key")
    install_judgment(monkeypatch, classified([candidate], ["qualifies"]))

    monkeypatch.setattr(
        credit_offers.subprocess, "run", Mock(side_effect=error)
    )

    status = credit_offers.main(["--end", END, "--notify"])

    captured = capsys.readouterr()
    assert status == 3
    assert "candidate\tqualifies\t0.9" in captured.out
    assert "jev_calls=1" in captured.out
    assert str(error) in captured.err
    assert "synthetic-test-key" not in captured.out + captured.err


def test_tracker_http_error_exits_three_without_key(monkeypatch, capsys):
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "synthetic-test-key")

    def forbidden(request):
        return httpx.Response(403, request=request)

    client = httpx.Client(transport=httpx.MockTransport(forbidden))
    monkeypatch.setattr(credit_offers.httpx, "Client", lambda **_: client)
    judge = install_judgment(monkeypatch)

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    assert judge.calls == []
    assert "403" in captured.err
    assert "jev_calls=0" in captured.out
    assert "synthetic-test-key" not in captured.out + captured.err


def bad_rows():
    wrong = row("a", "qualifies")
    return {
        "invalid-response": {
            **row("a", "qualifies"),
            "status": "invalid_response",
            "classification": None,
            "probabilities": None,
            "confidence": None,
        },
        "unknown-class": {**wrong, "classification": "maybe"},
        "missing-probability": {
            **wrong,
            "probabilities": {"qualifies": 0.9},
        },
        "extra-class": {
            **wrong,
            "probabilities": {**wrong["probabilities"], "maybe": 0.0},
        },
        "out-of-range": {
            **wrong,
            "probabilities": {"qualifies": 1.5, "excluded": -0.5},
        },
        "boolean": {
            **wrong,
            "probabilities": {"qualifies": True, "excluded": False},
        },
        "text-number": {
            **wrong,
            "probabilities": {"qualifies": "0.9", "excluded": "0.1"},
        },
        "no-classification": {
            k: v for k, v in wrong.items() if k != "classification"
        },
        "not-an-object": "qualifies",
        "other-id": {**wrong, "id": "b"},
    }


@pytest.mark.parametrize("case", sorted(bad_rows()))
def test_invalid_answer_fails_with_status_three(monkeypatch, capsys, case):
    candidate = offer("a")
    install_tracker(monkeypatch, new=[candidate])
    install_judgment(monkeypatch, tool_result(payload([bad_rows()[case]])))

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    assert "Invalid choice answer" in captured.err
    assert "jev_calls=1" in captured.out


@pytest.mark.parametrize(
    "result",
    [
        tool_result(text="not json"),
        tool_result(text="[]"),
        tool_result({"tool": "jev_classify"}),
        tool_result({"results": "x"}),
        tool_result(payload([])),
        CallToolResult(content=[]),
        CallToolResult(
            content=[
                TextContent(type="text", text=json.dumps(payload([]))),
                TextContent(type="text", text="second block"),
            ]
        ),
        CallToolResult(
            content=[
                ImageContent(type="image", data="AA==", mime_type="image/png")
            ]
        ),
    ],
    ids=(
        "text",
        "list",
        "no-results",
        "string-results",
        "no-rows",
        "no-blocks",
        "two-blocks",
        "image-block",
    ),
)
def test_malformed_result_fails_with_status_three(monkeypatch, capsys, result):
    install_tracker(monkeypatch, new=[offer("a")])
    install_judgment(monkeypatch, result)

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    assert "Invalid choice answer" in captured.err
    assert "jev_calls=1" in captured.out


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError(f"jev-mcp: {REFUSAL}"),
        RuntimeError("jev-mcp: Connection closed"),
        FileNotFoundError("uv"),
        ValueError("65 offers exceed the 64 one call can judge"),
    ],
    ids=("refusal", "closed", "no-uv", "too-many"),
)
def test_judgment_failures_exit_three_without_a_call(
    monkeypatch, capsys, error
):
    install_tracker(monkeypatch, new=[offer("candidate")])
    judge = install_judgment(monkeypatch, error=error)
    monkeypatch.setattr(credit_offers.subprocess, "run", Mock())

    assert credit_offers.main(["--end", END, "--notify"]) == 3

    captured = capsys.readouterr()
    assert str(error) in captured.err
    assert "jev_calls=0" in captured.out
    assert len(judge.calls) == 1
    credit_offers.subprocess.run.assert_not_called()


def test_invalid_arguments_exit_two(capsys):
    with pytest.raises(SystemExit) as error:
        credit_offers.main(["--hours", "5"])
    assert error.value.code == 2
    assert "divide 24" in capsys.readouterr().err


def test_search_writes_no_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_tracker(monkeypatch, same_commit=True)
    before = set(Path(tmp_path).iterdir())
    install_judgment(monkeypatch)

    assert credit_offers.main(["--end", END]) == 1
    assert set(Path(tmp_path).iterdir()) == before


# The real MCP client call, against a synthetic stdio server.


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    log, canned = tmp_path / "server.log", tmp_path / "canned.json"

    def install(mode="answer", texts=(), is_error=False):
        canned.write_text(
            json.dumps({"mode": mode, "texts": texts, "is_error": is_error})
        )
        monkeypatch.setattr(
            credit_offers,
            "GATE",
            StdioServerParameters(
                command=sys.executable,
                args=["-c", SERVER, str(log), str(canned)],
            ),
        )

    def entries():
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text().splitlines()]

    return install, entries


def assert_stopped(entries):
    for launch in (e for e in entries() if e["event"] == "launch"):
        with pytest.raises(ProcessLookupError):
            os.kill(launch["pid"], 0)


def test_gate_is_the_one_frozen_offline_proxy_without_keys():
    gate = credit_offers.GATE
    assert gate.command == "uv"
    assert gate.args == [
        "--directory",
        str(GATE_DIR),
        "run",
        "--frozen",
        "--offline",
        "--no-sync",
        "jev-mcp",
    ]
    assert gate.env is None and gate.cwd is None


def test_judge_sends_one_bounded_classify_call(monkeypatch, synthetic):
    install, entries = synthetic
    first, second = offer("first"), offer("second")
    answer = classified([first, second], ["qualifies", "excluded"])
    install(texts=[answer.content[0].text])
    for name in ("OPENROUTER_API_KEY", "GITHUB_TOKEN", "NODE_OPTIONS"):
        monkeypatch.setenv(name, "synthetic-marker")
    monkeypatch.setenv("JEV_PROVIDER", "synthetic-marker")

    result = asyncio.run(credit_offers.judge([first, second]))

    assert result.content[0].text == answer.content[0].text
    launches = [e for e in entries() if e["event"] == "launch"]
    calls = [e for e in entries() if e["event"] == "call"]
    assert len(launches) == len(calls) == 1
    assert not {
        "OPENROUTER_API_KEY",
        "GITHUB_TOKEN",
        "JEV_PROVIDER",
        "NODE_OPTIONS",
    } & set(launches[0]["env"])
    assert [item["id"] for item in calls[0]["items"]] == ["first", "second"]
    assert [json.loads(item["text"]) for item in calls[0]["items"]] == [
        {field: candidate[field] for field in credit_offers.FIELDS}
        for candidate in (first, second)
    ]
    assert calls[0]["classes"] == [
        {"id": choice, "description": description}
        for choice, description in credit_offers.CRITERIA.items()
    ]
    assert calls[0]["purpose"] == "Judge each API credit offer."
    assert_stopped(entries)


def test_judge_accepts_the_most_offers_and_refuses_one_more(synthetic):
    install, entries = synthetic
    offers = [offer(f"offer-{n}") for n in range(credit_offers.MAX_OFFERS)]
    install(texts=["{}"])

    asyncio.run(credit_offers.judge(offers))
    assert len([e for e in entries() if e["event"] == "call"]) == 1
    seen = len(entries())

    with pytest.raises(ValueError, match="65 offers exceed the 64"):
        asyncio.run(credit_offers.judge([*offers, offer("one-more")]))
    assert len(entries()) == seen


@pytest.mark.parametrize(
    "texts",
    [[REFUSAL], ["note: restored text"], []],
    ids=("gate-refusal", "upstream-error", "empty-error"),
)
def test_error_result_is_an_error_and_ends_the_session(synthetic, texts):
    install, entries = synthetic
    install(texts=texts, is_error=True)

    with pytest.raises(RuntimeError, match="jev-mcp: ") as error:
        asyncio.run(credit_offers.judge([offer("a")]))

    assert str(error.value) == "jev-mcp: " + " ".join(texts)
    assert [e["event"] for e in entries()] == ["launch", "call"]
    assert_stopped(entries)


def test_image_error_block_is_still_an_error(synthetic):
    install, entries = synthetic
    install(mode="image", is_error=True)

    with pytest.raises(RuntimeError, match="jev-mcp:"):
        asyncio.run(credit_offers.judge([offer("a")]))
    assert_stopped(entries)


def test_closed_connection_is_a_runtime_error(synthetic):
    install, entries = synthetic
    install(mode="crash")

    with pytest.raises(RuntimeError, match="Connection closed"):
        asyncio.run(credit_offers.judge([offer("a")]))
    assert [e["event"] for e in entries()] == ["launch", "call"]
    assert_stopped(entries)


def test_silent_proxy_times_out_and_is_stopped(monkeypatch, synthetic):
    install, entries = synthetic
    install(mode="hang")
    monkeypatch.setattr(credit_offers, "TIMEOUT", 1)

    with pytest.raises(RuntimeError, match="timed out"):
        asyncio.run(credit_offers.judge([offer("a")]))
    assert_stopped(entries)


def test_production_command_fails_closed_without_a_key_file(
    monkeypatch, tmp_path
):
    # An empty home means the proxy finds no key file; nothing real is read.
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(
        credit_offers,
        "GATE",
        credit_offers.GATE.model_copy(
            update={"env": {"HOME": str(home), "PATH": os.environ["PATH"]}}
        ),
    )

    with pytest.raises(RuntimeError, match="Connection closed"):
        asyncio.run(credit_offers.judge([offer("a")]))


# The real gate proxy over the mocked upstream, with a synthetic list.


@pytest.fixture
def real_gate(monkeypatch):
    entry = GATE_DIR / "node_modules/@jkudish/jev-mcp/dist/index.js"
    wrapper = GATE_DIR / "tests/fixture-upstream.mjs"
    assert entry.is_file(), (
        "Run npm run education-privacy-gate:install before running"
    )
    monkeypatch.setattr(
        credit_offers,
        "GATE",
        StdioServerParameters(
            command=sys.executable,
            args=["-c", LAUNCHER, str(wrapper), str(entry), "normal"],
        ),
    )


@pytest.mark.usefixtures("real_gate")
def test_real_gate_judges_offers_end_to_end(monkeypatch, capsys):
    candidate = offer("strong")
    candidate["title"] = "Credits for 가라온"
    install_tracker(monkeypatch, new=[candidate])

    status = credit_offers.main(["--end", END])

    output = capsys.readouterr().out
    assert status == 0
    assert "strong\tqualifies\t1.0" in output
    assert "jev_calls=1" in output


@pytest.mark.usefixtures("real_gate")
def test_real_upstream_error_passes_through_the_gate(monkeypatch, capsys):
    install_tracker(monkeypatch, new=[offer("same"), offer("same")])

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    assert "Duplicate item id: same" in captured.err
    assert "jev_calls=0" in captured.out


@pytest.mark.parametrize(
    "case",
    [
        "sum-off",
        "non-max",
        "near-non-max",
        "duplicate-id",
        "extra-id",
        "missing-id",
        "invalid-response",
    ],
)
def test_choice_trust_boundary(case):
    first, second = row("a", "qualifies"), row("b", "excluded")
    rows = [first, second]
    if case == "sum-off":
        first["probabilities"] = {"qualifies": 0.9, "excluded": 0.085}
    elif case == "non-max":
        first["classification"] = "excluded"
    elif case == "near-non-max":
        first["probabilities"] = {
            "qualifies": 0.5 - 2e-8,
            "excluded": 0.5 + 2e-8,
        }
    elif case == "duplicate-id":
        rows = [first, first, second]
    elif case == "extra-id":
        rows.append(row("extra", "qualifies"))
    elif case == "missing-id":
        rows = [first]
    else:
        first["status"] = "invalid_response"
    with pytest.raises(ValueError, match="^Invalid choice answer$"):
        credit_offers._answers(
            tool_result(payload(rows)), [offer("a"), offer("b")]
        )


@pytest.mark.parametrize(
    "probabilities",
    [
        {"qualifies": 0.9, "excluded": 0.09},
        {"qualifies": 0.5 - 2e-10, "excluded": 0.5 + 2e-10},
    ],
)
def test_choice_old_tolerance_accepts(probabilities):
    first = {
        **row("a", "qualifies"),
        "probabilities": probabilities,
        "confidence": "bad",
        "margin": -5,
    }
    assert credit_offers._answers(tool_result(payload([first])), [offer("a")])[
        "a"
    ] == ("qualifies", probabilities["qualifies"])


@pytest.mark.parametrize(
    "config", ["/synthetic/config", None, "relative/config", ""]
)
def test_gate_storage_environment(monkeypatch, config):
    monkeypatch.setattr(credit_offers, "GATE", credit_offers.GATE)
    if config is None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", config)
    monkeypatch.setenv("JEV_PROVIDER", "synthetic-marker")
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-marker")
    monkeypatch.setenv("NODE_OPTIONS", "synthetic-marker")
    importlib.reload(credit_offers)
    expected = (
        {"XDG_CONFIG_HOME": config}
        if config and config.startswith("/")
        else None
    )
    assert credit_offers.GATE.env == expected
