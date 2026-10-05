"""Offline contracts for the gated jev-mcp route. No browser, key or network."""

import importlib
import json
import os
from pathlib import Path
import socket
import sys
from unittest.mock import Mock

from mcp import StdioServerParameters
import pytest

from jev_ultrafast import model

GATE_DIR = Path(__file__).resolve().parents[2] / "education-privacy-gate"
REFUSAL = "Privacy gate rejected the call."
# Synthetic stdio MCP server: records its launch and each call, then answers
# as the plan file says. No provider, key or network is involved.
SERVER = """
import json, os, sys, time
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, TextContent

log, canned = sys.argv[1:3]


def record(**entry):
    with open(log, "a") as handle:
        handle.write(json.dumps(entry) + "\\n")


record(event="launch", pid=os.getpid(), env=sorted(os.environ))
server = MCPServer("synthetic")


@server.tool(name="jev_classify")
def jev_classify(
    items: list, classes: list, purpose: str = "", context: dict | None = None
):
    record(
        event="call",
        items=items,
        classes=classes,
        purpose=purpose,
        context=context,
    )
    plan = json.load(open(canned))
    head = items[0]["id"]
    mode = plan["modes"].get(head, "answer")
    if mode == "crash":
        os._exit(9)
    if mode == "hang":
        time.sleep(60)
    if mode == "error":
        text = TextContent(type="text", text=plan["error"])
        return CallToolResult(content=[text], is_error=True)
    ids = [c["id"] for c in classes]
    row = {
        "id": head,
        "classification": plan["picks"][head],
        "probabilities": {i: float(i == plan["picks"][head]) for i in ids},
        "confidence": 0.9,
        "margin": 1,
        "top_probability": 1,
        "decision": "auto",
    }
    payload = {
        "tool": "jev_classify",
        "model": "synthetic-model",
        "provider": "openrouter",
        "results": [row],
        "usage": {"input_tokens": 5, "output_tokens": 2},
    }
    text = TextContent(type="text", text=json.dumps(payload))
    return CallToolResult(content=[text])


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


def page():
    return {
        "url": "https://example.test/",
        "title": "Search",
        "text": "Search",
        "actions": [
            {
                "id": "e1",
                "kind": "fill",
                "label": "Search",
                "role": "textbox",
                "value": "",
                "node": 10,
            },
            {
                "id": "e2",
                "kind": "click",
                "label": "Open Search",
                "role": "textbox",
                "value": "",
                "node": 10,
            },
            {
                "id": "e3",
                "kind": "click",
                "label": "Go",
                "role": "button",
                "value": "",
                "node": 20,
            },
            {"id": "wait", "kind": "wait", "label": "Wait"},
        ],
    }


def wide_page(count):
    return {
        "url": "https://example.test/",
        "title": "Wide",
        "text": "Wide",
        "actions": [
            {
                "id": f"e{n}",
                "kind": "click",
                "label": f"Item {n}",
                "node": n,
                "role": "button",
                "value": "",
            }
            for n in range(1, count + 1)
        ],
    }


@pytest.fixture(autouse=True)
def no_direct_network(monkeypatch):
    """Any direct connection from this process would be a provider bypass."""
    refuse = Mock(side_effect=AssertionError("direct network use"))
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.setattr(socket.socket, "connect", refuse)


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    log, canned = tmp_path / "server.log", tmp_path / "canned.json"

    def install(picks, modes=None, error=REFUSAL):
        canned.write_text(
            json.dumps({"picks": picks, "modes": modes or {}, "error": error})
        )
        monkeypatch.setattr(
            model,
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


def heads(entries):
    return [e["items"][0]["id"] for e in entries() if e["event"] == "call"]


def test_gate_is_the_one_frozen_offline_proxy_without_keys():
    gate = model.GATE
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


def test_no_direct_provider_route_remains():
    package = Path(model.__file__).parent
    assert not (package / "providers.toml").exists()
    source = (package / "model.py").read_text()
    for provider_fact in (
        "openrouter.ai",
        "api.typesafe.ai",
        "ai-gateway.vercel.sh",
        "api.cloudflare.com",
        "OPENROUTER_API_KEY",
        "TYPESAFE_API_KEY",
        "AI_GATEWAY_API_KEY",
        "CLOUDFLARE_API_TOKEN",
        "JEV_PROVIDER",
        "TEXT_MODEL",
        "httpx",
    ):
        assert provider_fact not in source


def test_choose_asks_both_heads_in_one_gated_session(monkeypatch, synthetic):
    install, entries = synthetic
    install({"operation": "CLICK", "click_target": "2"})
    for name in (
        "OPENROUTER_API_KEY",
        "JEV_PROVIDER",
        "TYPESAFE_API_KEY",
        "NODE_OPTIONS",
    ):
        monkeypatch.setenv(name, "synthetic-marker")

    decision = model.choose(page(), "Find a book", [])

    log = entries()
    assert [e["event"] for e in log] == ["launch", "call", "call"]
    assert heads(entries) == ["operation", "click_target"]
    assert not {
        "OPENROUTER_API_KEY",
        "JEV_PROVIDER",
        "TYPESAFE_API_KEY",
        "NODE_OPTIONS",
    } & set(log[0]["env"])
    operation, target = log[1], log[2]
    assert [c["id"] for c in operation["classes"]] == [
        "TYPE_TEXT",
        "CLICK",
        "WAIT",
        "DONE",
        "BLOCKED",
    ]
    assert [c["id"] for c in target["classes"]] == ["1", "2"]
    assert target["context"]["operation"] == "CLICK"
    assert decision["choice"] == "e3"
    assert decision["operation"] == "CLICK" and decision["target"] == "2"
    assert decision["probabilities"] == {"e2": 0.0, "e3": 1.0}
    assert decision["confidence"] == decision["target_confidence"] == 0.9
    assert decision["model"] == "synthetic-model"
    assert decision["usage"] == {"input_tokens": 10, "output_tokens": 4}
    assert decision["latency_ms"] >= 0
    assert [r["items"][0]["id"] for r in decision["request"]] == heads(entries)
    assert_stopped(entries)


def test_control_operation_makes_one_call(synthetic):
    install, entries = synthetic
    install({"operation": "WAIT"})

    decision = model.choose(page(), "Find a book", [])

    assert [e["event"] for e in entries()] == ["launch", "call"]
    assert decision["choice"] == "wait" and decision["target"] is None
    assert decision["usage"] == {"input_tokens": 5, "output_tokens": 2}
    assert_stopped(entries)


@pytest.mark.parametrize(
    ("failing", "calls"), [("operation", 1), ("click_target", 2)]
)
def test_refusal_is_an_error_and_nothing_more_is_requested(
    synthetic, failing, calls
):
    install, entries = synthetic
    install(
        {"operation": "CLICK", "click_target": "1"}, modes={failing: "error"}
    )

    with pytest.raises(RuntimeError, match="refused or failed") as error:
        model.choose(page(), "Find a book", [])

    assert REFUSAL in str(error.value) and "no action executed" in str(
        error.value
    )
    assert [e["event"] for e in entries()] == ["launch"] + ["call"] * calls
    assert_stopped(entries)


def test_upstream_error_text_is_reported_not_accepted(synthetic):
    install, entries = synthetic
    install(
        {"operation": "DONE"}, modes={"operation": "error"}, error="API 429"
    )

    with pytest.raises(RuntimeError, match="API 429"):
        model.choose(page(), "Find a book", [])
    assert len(heads(entries)) == 1


def test_closed_connection_is_a_runtime_error(synthetic):
    install, entries = synthetic
    install({"operation": "DONE"}, modes={"operation": "crash"})

    with pytest.raises(RuntimeError, match="Connection closed.*no action"):
        model.choose(page(), "Find a book", [])
    assert [e["event"] for e in entries()] == ["launch", "call"]
    assert_stopped(entries)


def test_silent_proxy_times_out_and_is_stopped(monkeypatch, synthetic):
    install, entries = synthetic
    install({"operation": "DONE"}, modes={"operation": "hang"})
    monkeypatch.setattr(model, "TIMEOUT", 1)

    with pytest.raises(RuntimeError, match="timed out"):
        model.choose(page(), "Find a book", [])
    assert_stopped(entries)


def test_production_command_fails_closed_without_a_key_file(
    monkeypatch, tmp_path
):
    # An empty home means the proxy finds no key file; nothing real is read.
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(
        model,
        "GATE",
        model.GATE.model_copy(
            update={"env": {"HOME": str(home), "PATH": os.environ["PATH"]}}
        ),
    )

    with pytest.raises(RuntimeError, match="Connection closed"):
        model.choose(page(), "Find a book", [])


# The real gate proxy over the mocked upstream, with a synthetic list.


@pytest.fixture
def real_gate(monkeypatch):
    entry = GATE_DIR / "node_modules/@jkudish/jev-mcp/dist/index.js"
    wrapper = GATE_DIR / "tests/fixture-upstream.mjs"
    assert entry.is_file(), (
        "Run npm run education-privacy-gate:install before running"
    )
    monkeypatch.setattr(
        model,
        "GATE",
        StdioServerParameters(
            command=sys.executable,
            args=["-c", LAUNCHER, str(wrapper), str(entry), "normal"],
        ),
    )


@pytest.mark.usefixtures("real_gate")
def test_real_gate_chooses_end_to_end():
    start = wide_page(3)
    start["title"] = "Search for 가라온"

    decision = model.choose(start, "Open the first item", [])

    # The mocked upstream always selects each question's first option.
    assert decision["operation"] == "CLICK"
    assert decision["target"] == "1" and decision["choice"] == "e1"
    assert decision["confidence"] == decision["target_confidence"] == 0.99
    assert decision["probabilities"] == {"e1": 1, "e2": 0, "e3": 0}
    assert decision["model"] == "typesafe/jev-1.13"
    # Upstream returns non-numeric usage here; it is ignored, not summed.
    assert decision["usage"] == {}
    assert len(decision["request"]) == 2


@pytest.mark.usefixtures("real_gate")
def test_real_gate_lone_option_needs_no_second_request():
    decision = model.choose(page(), "Find a book", [])

    assert decision["operation"] == "TYPE_TEXT" and decision["choice"] == "e1"
    assert decision["confidence"] == 0.99
    assert decision["target_confidence"] == 1.0
    assert len(decision["request"]) == 1


@pytest.mark.usefixtures("real_gate")
def test_real_gate_accepts_250_targets_and_refuses_251():
    decision = model.choose(wide_page(250), "Open the first item", [])
    assert decision["operation"] == "CLICK" and decision["choice"] == "e1"
    assert len(decision["request"][1]["classes"]) == 250

    with pytest.raises(RuntimeError, match=REFUSAL):
        model.choose(wide_page(251), "Open the first item", [])


@pytest.mark.usefixtures("real_gate")
def test_real_gate_still_answers_after_a_refusal():
    with pytest.raises(RuntimeError, match=REFUSAL):
        model.choose(wide_page(251), "Open the first item", [])
    assert model.choose(wide_page(2), "Open one", [])["choice"] == "e1"


@pytest.mark.parametrize(
    "config", ["/synthetic/config", None, "relative/config", ""]
)
def test_gate_storage_environment(monkeypatch, config):
    monkeypatch.setattr(model, "GATE", model.GATE)
    if config is None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", config)
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-marker")
    monkeypatch.setenv("JEV_PROVIDER", "synthetic-marker")
    monkeypatch.setenv("NODE_OPTIONS", "synthetic-marker")
    importlib.reload(model)
    expected = (
        {"XDG_CONFIG_HOME": config}
        if config and config.startswith("/")
        else None
    )
    assert model.GATE.env == expected
