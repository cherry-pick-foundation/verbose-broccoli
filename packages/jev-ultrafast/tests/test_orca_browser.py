"""Offline contracts for Orca and Chrome browser modes."""

import importlib
import json
import os
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from jev_ultrafast import browser


@pytest.fixture
def cdp_calls(monkeypatch):
    calls = []

    def cdp(method, **params):
        calls.append((method, params))
        if method == "Target.getTargets":
            return {
                "targetInfos": [{"type": "page", "targetId": "owned-target"}]
            }
        if method == "Target.createTarget":
            return {"targetId": "owned-target"}
        if method == "Target.attachToTarget":
            return {"sessionId": "owned-session"}
        if method == "Runtime.evaluate":
            return {"result": {"value": "complete"}}
        return {}

    monkeypatch.setattr(browser, "cdp", cdp)
    return calls


def test_orca_mode_uses_and_closes_only_its_tab(monkeypatch, cdp_calls):
    orca_calls = []

    def orca(*args):
        orca_calls.append(args)
        return {"browserPageId": "owned-page", "cdpUrl": "ws://127.0.0.1:1234/"}

    restart = Mock()
    monkeypatch.setattr(browser, "BROWSER_MODE", "orca")
    monkeypatch.setattr(browser, "_orca", orca)
    monkeypatch.setattr(browser, "restart_daemon", restart)
    monkeypatch.setattr(browser, "ensure_daemon", Mock())
    monkeypatch.setenv("BU_CDP_WS", "ws://old-tab/")

    agent = browser.Browser("https://example.test/")

    assert os.environ["BU_CDP_WS"] == "ws://127.0.0.1:1234/"
    assert orca_calls == [
        ("tab", "create", "--url", "about:blank", "--worktree", "current"),
        ("exec", "--command", "get cdp-url", "--page", "owned-page"),
    ]
    assert (
        "Target.attachToTarget",
        {"targetId": "owned-target", "flatten": True},
    ) in cdp_calls
    assert any(
        method == "Page.navigate" and params["url"] == "https://example.test/"
        for method, params in cdp_calls
    )

    agent.close()

    assert orca_calls[-1] == ("tab", "close", "--page", "owned-page")
    assert restart.call_count == 2


def test_failed_orca_start_closes_tab_and_stops_daemon(monkeypatch, cdp_calls):
    orca_calls = []

    def orca(*args):
        orca_calls.append(args)
        return {"browserPageId": "owned-page", "cdpUrl": "ws://127.0.0.1:1234/"}

    def cdp(method, **params):
        cdp_calls.append((method, params))
        if method == "Target.getTargets":
            return {
                "targetInfos": [{"type": "page", "targetId": "owned-target"}]
            }
        if method == "Target.attachToTarget":
            raise RuntimeError("CDP attach failed")
        return {}

    restart = Mock()
    monkeypatch.setattr(browser, "BROWSER_MODE", "orca")
    monkeypatch.setattr(browser, "_orca", orca)
    monkeypatch.setattr(browser, "cdp", cdp)
    monkeypatch.setattr(browser, "restart_daemon", restart)
    monkeypatch.setattr(browser, "ensure_daemon", Mock())

    with pytest.raises(RuntimeError, match="CDP attach failed"):
        browser.Browser("https://example.test/")

    assert orca_calls[-1] == ("tab", "close", "--page", "owned-page")
    assert restart.call_count == 2


def test_chrome_mode_keeps_upstream_target_calls(monkeypatch, cdp_calls):
    restart = Mock()
    monkeypatch.setattr(browser, "BROWSER_MODE", "chrome")
    monkeypatch.setattr(browser, "restart_daemon", restart)
    monkeypatch.setattr(browser, "ensure_daemon", Mock())

    agent = browser.Browser("https://example.test/")
    agent.close()

    assert (
        "Target.createTarget",
        {"url": "about:blank", "background": True},
    ) in cdp_calls
    assert ("Target.closeTarget", {"targetId": "owned-target"}) in cdp_calls
    restart.assert_not_called()


def test_unknown_browser_mode_fails(monkeypatch):
    original = os.environ.get("JEV_BROWSER")
    monkeypatch.setenv("JEV_BROWSER", "safari")
    with pytest.raises(ValueError, match="safari"):
        importlib.reload(browser)
    if original is None:
        monkeypatch.delenv("JEV_BROWSER", raising=False)
    else:
        monkeypatch.setenv("JEV_BROWSER", original)
    importlib.reload(browser)


def test_orca_helper_adds_json_and_reports_chrome_hint(monkeypatch):
    commands = []

    def run(command, **_):
        commands.append(command)
        return SimpleNamespace(stdout=json.dumps({"result": {"page": 1}}))

    monkeypatch.setattr(browser.subprocess, "run", run)
    assert browser._orca("tab", "create")["page"] == 1
    assert commands == [["orca", "tab", "create", "--json"]]

    monkeypatch.setattr(
        browser.subprocess,
        "run",
        Mock(
            side_effect=subprocess.CalledProcessError(
                1, "orca", stderr="Orca unavailable"
            )
        ),
    )
    with pytest.raises(
        RuntimeError, match="Orca unavailable.*JEV_BROWSER=chrome"
    ):
        browser._orca("tab", "create")
