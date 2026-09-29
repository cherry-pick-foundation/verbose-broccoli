"""The console and module entry serve PyModel's tools over stdio."""

import json
import os
from pathlib import Path
import select
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = (
    ["uv", "run", "--frozen", "--offline", "--no-sync", "backfire"],
    [sys.executable, "-m", "backfire"],
)
NAMES = (
    "jev_verify",
    "jev_screen",
    "jev_find",
    "jev_classify",
    "jev_decide",
    "jev_rerank",
    "jev_compare",
    "jev_extract",
    "jev_review",
    "jev_gate",
    "jev_score",
    "jev_noul",
)


@pytest.mark.parametrize("entry", ENTRY_POINTS, ids=("console", "module"))
def test_help_lists_serve_mcp(entry):
    result = subprocess.run(
        [*entry, "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "serve-mcp" in result.stdout


@pytest.mark.parametrize("entry", ENTRY_POINTS, ids=("console", "module"))
@pytest.mark.parametrize("education", [False, True], ids=["code", "education"])
def test_stdio_lists_pymodel_tools_then_noul(tmp_path, entry, education):
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_STATE_HOME": str(tmp_path / "state"),
    }
    process = subprocess.Popen(
        [*entry, "serve-mcp", *(["--education"] if education else [])],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:

        def send(value):
            process.stdin.write(json.dumps(value) + "\n")
            process.stdin.flush()

        def receive(identifier):
            assert select.select([process.stdout], [], [], 15)[0], (
                process.stderr.read()
            )
            message = json.loads(process.stdout.readline())
            assert message["id"] == identifier, message
            return message["result"]

        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "entry-test", "version": "1"},
                },
            }
        )
        assert receive(1)["serverInfo"]["name"] == "jev-mcp"
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        assert [tool["name"] for tool in receive(2)["tools"]] == list(NAMES)
    finally:
        process.stdin.close()
        try:
            assert process.wait(timeout=15) == 0
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()
