import asyncio
from importlib.metadata import version
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from backfire.config import load_profile
from backfire.failures import JudgmentError
from backfire_tools.build import ROOT, build

TOOL_NAMES = {
    "backfire_gate",
    "backfire_review",
    "backfire_verify",
    "backfire_noul",
    "backfire_classify",
    "backfire_find",
    "backfire_rerank",
    "backfire_compare",
    "backfire_screen",
    "backfire_extract",
    "backfire_decide",
}


def snapshot(plugin: Path):
    entries = {}
    for directory, directories, files in os.walk(plugin):
        relative = Path(directory).relative_to(plugin)
        if relative == Path("backfire"):
            directories[:] = [name for name in directories if name != ".venv"]
        if relative.is_relative_to("backfire/src/backfire"):
            directories[:] = [
                name for name in directories if name != "__pycache__"
            ]
        for name in directories + files:
            path = Path(directory) / name
            assert not path.is_symlink(), path
            entries[str(relative / name)] = (
                None if path.is_dir() else path.read_bytes()
            )
    return entries


def assert_own_import(plugin: Path):
    package = plugin / "backfire"
    result = subprocess.run(
        [
            str(package / ".venv/bin/python"),
            "-I",
            "-c",
            "import backfire; print(backfire.__file__)",
        ],
        cwd=plugin.parent,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert (
        Path(result.stdout.strip()).resolve()
        == package / "src/backfire/__init__.py"
    )


async def served_session(plugin: Path, uv: str):
    # Start without inherited settings, using only this test's config and state.
    config, state = plugin.parent / "config", plugin.parent / "state"
    parameters = StdioServerParameters(
        command=shutil.which("env"),
        args=[
            "-i",
            f"XDG_CONFIG_HOME={config}",
            f"XDG_STATE_HOME={state}",
            uv,
            "--directory",
            str(plugin / "backfire"),
            "run",
            "--frozen",
            "--offline",
            "--no-sync",
            "backfire",
            "serve-mcp",
        ],
        cwd=plugin.parent,
    )
    with anyio.fail_after(20):
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as client:
                initialized = await client.initialize()
                assert initialized.server_info.name == "backfire"
                assert initialized.server_info.version == version("backfire")
                tools = (await client.list_tools()).tools
                assert len(tools) == 11
                assert {tool.name for tool in tools} == TOOL_NAMES
                result = await client.call_tool(
                    "backfire_verify",
                    {"claims": ["synthetic claim"], "evidence": "document"},
                )
                assert result.is_error
                assert len(result.content) == 1
                credential = (
                    config
                    / "verbose-broccoli/backfire"
                    / f"{load_profile()['name']}.env"
                )
                assert result.content[0].text == str(
                    JudgmentError("backend_not_configured", str(credential))
                )


def test_built_copies_install_offline_serve_and_remain_independent():
    uv = shutil.which("uv")
    assert uv is not None, (
        "Run deno task backfire:install to prepare uv and its caches."
    )
    uv = str(Path(uv).resolve())
    with TemporaryDirectory(prefix="backfire-load-") as temporary:
        parent = Path(temporary).resolve()
        assert not parent.is_relative_to(ROOT)
        copies = [build(parent / name) for name in ("first", "second")]
        original = [snapshot(plugin) for plugin in copies]
        for plugin in copies:
            result = subprocess.run(
                [uv, "sync", "--frozen", "--no-dev"],
                cwd=plugin / "backfire",
                env={**os.environ, "UV_OFFLINE": "1"},
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, (
                result.stderr
                + "\nRun deno task backfire:install to prepare the offline caches."
            )
            assert_own_import(plugin)
        asyncio.run(served_session(copies[0], uv))
        for plugin, before in zip(copies, original):
            assert snapshot(plugin) == before
        shutil.rmtree(copies[0])
        assert_own_import(copies[1])
        asyncio.run(served_session(copies[1], uv))
        assert snapshot(copies[1]) == original[1]
    assert not parent.exists()
