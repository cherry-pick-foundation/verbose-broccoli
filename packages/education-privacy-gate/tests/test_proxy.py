"""Protocol checks use invented identifiers and an isolated stdio child."""

import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import resource
import subprocess
import sys
from types import SimpleNamespace

from fastmcp import Client
from fastmcp.server.middleware import MiddlewareContext
from fastmcp.tools.base import ToolResult
from mcp_types import LOG_LEVEL_META_KEY
from mcp_types import CallToolRequestParams
import pytest

from education_privacy_gate import __main__ as proxy_module
from education_privacy_gate.masking import Masker
from education_privacy_gate.roster import GateError
from education_privacy_gate.roster import Registry

FIXTURE = Path(__file__).with_name("fixture_server.py").resolve()
ORIGINALS = (
    "가라온",
    "synthetic-school",
    "010-2345-6789",
    "fictional@example.invalid",
    "1234567890",
    "991399-1234567",
)
DATA = {
    "version": 1,
    "entries": [
        {"kind": "person", "full": ORIGINALS[0], "romanized": ["Ga Raon"]},
        {"kind": "school", "spellings": [ORIGINALS[1]]},
    ],
}
GENERIC = str(GateError())


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    for name in ("home", "cwd", "tmp"):
        (tmp_path / name).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    monkeypatch.setenv("NODE_OPTIONS", "--invalid-planted-option")
    monkeypatch.setenv("HTTPS_PROXY", "https://invalid.invalid")
    monkeypatch.setenv("JEV_OPENROUTER_BASE_URL", "https://invalid.invalid")
    monkeypatch.chdir(tmp_path / "cwd")
    monkeypatch.setattr(
        proxy_module.roster, "load_registry", lambda: Registry.from_data(DATA)
    )
    created = []

    def tracked(registry):
        call = Masker(registry)
        created.append(call)
        return call

    monkeypatch.setattr(proxy_module, "Masker", tracked)
    return tmp_path, created


@asynccontextmanager
async def connected(tmp_path, timeout=3, mode="legacy", warm=True):
    child_log = tmp_path / "child.log"
    with child_log.open("w") as log:
        proxy = proxy_module.build_proxy(
            command=sys.executable,
            args=["-B", str(FIXTURE)],
            key="synthetic-dummy",
            log_file=log,
            timeout=timeout,
        )
        transport = proxy.client_factory().transport
        async with Client(proxy, timeout=10, mode=mode) as client:
            if warm:
                await client.list_tools()
            yield client, proxy, transport
        await transport.close()


def assert_generic(result):
    assert result.is_error
    assert [block.text for block in result.content] == [GENERIC]
    assert result.structured_content is None


@pytest.mark.parametrize(
    "level",
    [
        "debug",
        "info",
        "notice",
        "warning",
        "error",
        "critical",
        "alert",
        "emergency",
        "unsupported",
    ],
)
@pytest.mark.usefixtures("isolated")
def test_sdk_logging_levels(level):
    async def run():
        meta = {LOG_LEVEL_META_KEY: level}
        context = MiddlewareContext(
            message=CallToolRequestParams(name="echo", arguments={}),
            fastmcp_context=SimpleNamespace(
                request_context=SimpleNamespace(meta=meta),
                input_responses=None,
                request_state=None,
            ),
        )
        gate = proxy_module.PrivacyGate()
        gate.schemas = {"echo": {"type": "object"}}
        forwarded = []

        async def next_call(masked):
            forwarded.append(masked)
            return ToolResult(content="safe synthetic")

        result = await gate.on_call_tool(context, next_call)
        if level == "unsupported":
            assert_generic(result)
            assert not forwarded
        else:
            assert not result.is_error
            assert len(forwarded) == 1
            assert meta == {}

    asyncio.run(run())


def assert_cleared(created):
    assert created
    assert all(
        not m.reverse and not m.anchors and not m.assigned for m in created
    )


@pytest.mark.usefixtures("isolated")
def test_original_and_masked_schema_both_hold():
    async def run():
        gate = proxy_module.PrivacyGate()
        gate.schemas = {
            "echo": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "maxLength": 16},
                    "number": {"type": "integer"},
                },
            }
        }
        forwarded = []

        async def next_call(context):
            forwarded.append(context.message.arguments)
            return ToolResult(content="safe synthetic")

        for args in (
            {"text": ORIGINALS[1] + "!"},
            {"number": 1234567890},
        ):
            result = await gate.on_call_tool(
                MiddlewareContext(
                    message=CallToolRequestParams(name="echo", arguments=args)
                ),
                next_call,
            )
            assert_generic(result)
            assert not forwarded
        result = await gate.on_call_tool(
            MiddlewareContext(
                message=CallToolRequestParams(
                    name="echo", arguments={"text": ORIGINALS[1], "number": 85}
                )
            ),
            next_call,
        )
        assert not result.is_error
        assert forwarded == [{"text": "School 01", "number": 85}]

    asyncio.run(run())


@pytest.mark.usefixtures("isolated")
def test_numbered_label_collision_forwards_and_restores():
    async def run():
        gate = proxy_module.PrivacyGate()
        gate.schemas = {
            "echo": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
            }
        }
        original = "010-2345-6789 Phone 01"
        forwarded = []

        async def next_call(context):
            forwarded.append(context.message.arguments)
            return ToolResult(content=context.message.arguments["text"])

        result = await gate.on_call_tool(
            MiddlewareContext(
                message=CallToolRequestParams(
                    name="echo", arguments={"text": original}
                )
            ),
            next_call,
        )
        assert not result.is_error
        assert forwarded == [{"text": "Phone 02 Phone 01"}]
        assert result.content[0].text == original

    asyncio.run(run())


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and path.name != "child.log"
    }


def test_versions_launch_and_main_injection(isolated, monkeypatch):
    from importlib.metadata import version  # noqa: PLC0415

    root, _ = isolated
    assert {
        name: version(name)
        for name in ("mcp", "mcp-types", "fastmcp", "faker", "phonenumbers")
    } == {
        "mcp": "2.2.0",
        "mcp-types": "2.2.0",
        "fastmcp": "4.0.10",
        "faker": "40.40.0",
        "phonenumbers": "9.0.40",
    }
    proxy = proxy_module.build_proxy(key="synthetic-dummy")
    child = proxy.client_factory()
    assert type(child) is Client and not child.is_connected()
    assert Path(child.transport.command).is_absolute()
    assert Path(child.transport.command).name == "node"
    assert len(child.transport.args) == 1
    entry = Path(child.transport.args[0])
    assert entry.is_absolute() and str(entry).endswith(
        "node_modules/@jkudish/jev-mcp/dist/index.js"
    )
    assert child.transport.cwd == "/"
    assert child.transport.env == {
        "JEV_PROVIDER": "openrouter",
        "OPENROUTER_API_KEY": "synthetic-dummy",
        "JEV_MCP_MODEL": "typesafe/jev-1.13",
    }
    assert child._session_kwargs["read_timeout_seconds"] == 60
    assert child._session_kwargs["sampling_callback"] is None
    assert child._session_kwargs.get("elicitation_callback") is None
    assert child._session_kwargs["list_roots_callback"] is None
    assert child._response_cache is None
    assert proxy.provider_error_strategy == "raise"
    assert proxy.name == "jev-mcp"
    calls = []
    monkeypatch.setattr(
        proxy_module,
        "build_proxy",
        lambda **kw: type(
            "Runner",
            (),
            {"run": lambda _, **options: calls.append((kw, options))},
        )(),
    )
    proxy_module.main(key_source=lambda: "synthetic-dummy")
    assert calls == [
        (
            {"key": "synthetic-dummy"},
            {"transport": "stdio", "show_banner": False},
        )
    ]
    assert root.is_dir()


def test_restore_errors_refusals_and_no_files(isolated, caplog):
    root, created = isolated

    async def run():
        async with connected(root) as (client, _, _):
            original = {
                ORIGINALS[0]: {
                    "values": list(ORIGINALS),
                    "grade": 3,
                    "score": 85,
                    "id": 1234567890,
                }
            }
            expected = {
                ORIGINALS[0]: {
                    "values": list(ORIGINALS),
                    "grade": 3,
                    "score": 85,
                    "id": "1234567890",
                }
            }
            before = snapshot(root)
            for action in ("ok", "error", "notify"):
                result = await client.call_tool_mcp(
                    "echo", {"payload": original, "action": action}
                )
                assert result.is_error == (action == "error")
                assert json.loads(result.content[0].text) == expected
                assert result.structured_content["echo"] == expected
                assert (
                    json.loads(
                        json.loads(result.structured_content["nested"])[
                            "encoded"
                        ]
                    )
                    == expected
                )
                assert result.meta["seen"] == expected
                assert json.loads(result.meta["encoded"]) == expected
            for name, args in (
                ("echo", {"payload": original, "action": "raise"}),
                ("echo", {"payload": original, "action": "opaque"}),
                (ORIGINALS[0], {"payload": original}),
                ("echo", {"payload": original, "delay": 1234567890}),
            ):
                assert_generic(await client.call_tool_mcp(name, args))
            assert_generic(
                await client.call_tool_mcp(
                    "echo",
                    {"payload": original},
                    meta={"private": ORIGINALS[0]},
                )
            )
            result = await client.call_tool_mcp(
                "echo", {"payload": {"safe": "works"}}
            )
            assert not result.is_error
            assert snapshot(root) == before
        assert_cleared(created)

    asyncio.run(run())
    assert all(original not in caplog.text for original in ORIGINALS)
    assert all(
        original not in (root / "child.log").read_text()
        for original in ORIGINALS
    )


def test_upstream_receives_standins_and_inherited_env(isolated):
    root, _ = isolated

    async def run():
        # Read the fixture directly only to inspect what the gate actually sent.
        captured = []
        original_restore = Masker.restore

        def inspect_result(self, tree):
            captured.append(tree)
            return original_restore(self, tree)

        from unittest.mock import patch  # noqa: PLC0415

        with patch.object(Masker, "restore", inspect_result):
            async with connected(root) as (client, _, _):
                await client.call_tool_mcp(
                    "echo", {"payload": {"values": list(ORIGINALS)}}
                )
                seen = json.dumps(captured[-1], ensure_ascii=False)
                assert all(original not in seen for original in ORIGINALS)
                assert all(
                    label in seen
                    for label in (
                        "School 01",
                        "Phone 01",
                        "Email 01",
                        "EduOK 01",
                        "Resident number 01",
                    )
                )
                launch = json.loads(
                    (await client.call_tool_mcp("launch", {})).content[0].text
                )
                expected = {
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
                # The fixture sets these before importing FastMCP.
                assert set(launch["env_keys"]) <= expected | {
                    "FASTMCP_CHECK_FOR_UPDATES",
                    "FASTMCP_TELEMETRY_MODE",
                    "FASTMCP_ENV_FILE",
                    "LC_CTYPE",
                }
                assert launch["cwd"] == "/"
                assert launch["entry"] == str(FIXTURE)

    asyncio.run(run())


def test_tools_only(isolated):
    root, _ = isolated

    async def run():
        async with connected(root) as (client, _, _):
            assert await client.list_resources() == []
            assert await client.list_resource_templates() == []
            assert await client.list_prompts() == []
            for method in (
                lambda: client.read_resource("synthetic://known"),
                lambda: client.read_resource(
                    "synthetic://template/" + ORIGINALS[0]
                ),
                lambda: client.get_prompt("summarize", {"text": ORIGINALS[0]}),
            ):
                with pytest.raises(
                    Exception, match="Privacy gate rejected the call"
                ):
                    await method()
            assert not (
                await client.call_tool_mcp("echo", {"payload": {}})
            ).is_error

    asyncio.run(run())


def test_timeout_exit_cancel_concurrent_recovery(isolated):
    root, created = isolated

    async def run():
        async with connected(root, timeout=3) as (client, _, _):
            for args in ({"delay": 4}, {"action": "exit"}):
                assert_generic(
                    await client.call_tool_mcp(
                        "echo", {"payload": {"text": ORIGINALS[0]}, **args}
                    )
                )
                assert not (
                    await client.call_tool_mcp("echo", {"payload": {}})
                ).is_error
            pending = asyncio.create_task(
                client.call_tool_mcp(
                    "echo", {"payload": {"text": ORIGINALS[0]}, "delay": 4}
                )
            )
            await asyncio.sleep(0.05)
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
            await asyncio.sleep(0.3)
            values = [
                {"text": ORIGINALS[0] + suffix}
                for suffix in (" first", " second")
            ]
            results = await asyncio.gather(
                *(
                    client.call_tool_mcp(
                        "echo", {"payload": value, "delay": 0.05}
                    )
                    for value in values
                )
            )
            assert [json.loads(r.content[0].text) for r in results] == values
        assert_cleared(created)

    asyncio.run(run())


def test_large_call_measurement(isolated):
    root, _ = isolated

    async def run():
        async with connected(root) as (client, _, _):
            before = resource.getrusage(resource.RUSAGE_SELF)
            text = ("plain synthetic text " * 16000) + ORIGINALS[0]
            result = await client.call_tool_mcp(
                "echo", {"payload": {"text": text}}
            )
            assert json.loads(result.content[0].text)["text"] == text
            after = resource.getrusage(resource.RUSAGE_SELF)
            child = resource.getrusage(resource.RUSAGE_CHILDREN)
            print(
                json.dumps(
                    {
                        "measurement": "large-synthetic-call",
                        "input_chars": len(text),
                        "proxy_test_peak_rss_kib": after.ru_maxrss,
                        "proxy_test_cpu_seconds": after.ru_utime
                        + after.ru_stime
                        - before.ru_utime
                        - before.ru_stime,
                        "child_peak_rss_kib": child.ru_maxrss,
                        "child_cpu_seconds": child.ru_utime + child.ru_stime,
                    }
                )
            )

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_frontend_meta_never_reaches_backend(mode, isolated):
    root, _ = isolated

    async def run():
        async with connected(root, mode=mode) as (client, _, _):
            result = await client.call_tool_mcp(
                "echo",
                {"payload": {"text": ORIGINALS[0]}},
                meta={"progressToken": 876543210},
            )
            assert not result.is_error
            meta = result.meta["request_meta"]
            assert meta.get("progressToken") != 876543210
            assert type(meta["progressToken"]) is int
            assert set(meta) <= {
                "progressToken",
                "io.modelcontextprotocol/protocolVersion",
                "io.modelcontextprotocol/clientInfo",
                "io.modelcontextprotocol/clientCapabilities",
                "io.modelcontextprotocol/logLevel",
            }
            assert ORIGINALS[0] not in json.dumps(meta, ensure_ascii=False)
            print(
                json.dumps(
                    {
                        "observation": "backend-sdk-meta",
                        "frontend_mode": mode,
                        "keys": sorted(meta),
                    }
                )
            )
            for meta in (
                {"progressToken": ORIGINALS[0]},
                {"private": ORIGINALS[0]},
            ):
                assert_generic(
                    await client.session.call_tool(
                        "echo", {"payload": {}}, meta=meta
                    )
                )

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_client_vendor_meta_is_accepted_and_discarded(mode, isolated):
    root, _ = isolated
    vendor = {
        "claudecode/toolUseId": "toolu_synthetic",
        "claudecode/agentId": ORIGINALS[0],
        "claudecode/isObserver": True,
        "anthropic/requestId": "req_synthetic",
    }

    async def run():
        async with connected(root, mode=mode) as (client, _, _):
            result = await client.call_tool_mcp(
                "echo", {"payload": {"text": ORIGINALS[0]}}, meta=vendor
            )
            assert not result.is_error
            seen = json.dumps(result.meta["request_meta"], ensure_ascii=False)
            assert not any(key in seen for key in vendor)
            assert "toolu_synthetic" not in seen and ORIGINALS[0] not in seen
            for meta in (
                {"claudecode": "x"},
                {"xclaudecode/toolUseId": "x"},
                {"claudecode/toolUseId": "x", "private": ORIGINALS[0]},
            ):
                assert_generic(
                    await client.session.call_tool(
                        "echo", {"payload": {}}, meta=meta
                    )
                )

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_codex_meta_is_accepted_and_discarded(mode, isolated):
    root, _ = isolated
    codex = {
        "callId": "call_synthetic",
        "threadId": "thread_synthetic",
        "sessionId": "session_synthetic",
        "windowId": "window_synthetic",
        "itemId": "item_synthetic",
        "x-codex-turn-metadata": {"turn_id": ORIGINALS[0]},
        "codex_bridge_mcp_call_id": "bridge_synthetic",
        "progressToken": 7,
    }

    async def run():
        async with connected(root, mode=mode) as (client, _, _):
            result = await client.call_tool_mcp(
                "echo", {"payload": {"text": ORIGINALS[0]}}, meta=codex
            )
            assert not result.is_error
            seen = json.dumps(result.meta["request_meta"], ensure_ascii=False)
            assert not any(
                key in seen for key in codex if key != "progressToken"
            )
            assert "_synthetic" not in seen and ORIGINALS[0] not in seen
            for meta in (
                {"callid": "x"},
                {"call_id": "x"},
                {"codex/callId": "x"},
                {"codex_apps": {}},
                {"sandbox-state": {}},
                {"callId": "x", "private": ORIGINALS[0]},
                {"callId": "x", "progressToken": "7"},
            ):
                assert_generic(
                    await client.session.call_tool(
                        "echo", {"payload": {}}, meta=meta
                    )
                )
            if mode == "legacy":  # auto mode demands protocol envelope keys
                # Bypass SDK integer coercion to send the malformed wire value.
                raw = await client.session._dispatcher.send_raw_request(
                    "tools/call",
                    {
                        "name": "echo",
                        "arguments": {"payload": {}},
                        "_meta": {"callId": "x", "progressToken": True},
                    },
                )
                assert raw["isError"]
                assert raw["content"][0]["text"] == GENERIC
            assert not (
                await client.call_tool_mcp("echo", {"payload": {}})
            ).is_error

    asyncio.run(run())


def test_concurrent_first_calls_need_no_warm_up(isolated):
    root, created = isolated

    async def run():
        async with connected(root, warm=False) as (client, _, _):
            values = [{"text": ORIGINALS[0] + f" call {i}"} for i in range(4)]
            results = await asyncio.gather(
                *(
                    client.call_tool_mcp("echo", {"payload": value})
                    for value in values
                )
            )
            assert not any(result.is_error for result in results)
            assert [json.loads(r.content[0].text) for r in results] == values
        assert_cleared(created)

    asyncio.run(run())


@pytest.mark.parametrize("output_schema", [None, {"type": "object"}])
@pytest.mark.usefixtures("isolated")
def test_cold_schema_fetch_refuses_output_schemas(output_schema):
    async def run():
        gate = proxy_module.PrivacyGate()
        tools = [
            SimpleNamespace(
                name="echo",
                parameters={"type": "object"},
                output_schema=output_schema,
            )
        ]

        async def list_tools():
            async def tools_next(unused_context):
                return tools

            return await gate.on_list_tools(None, tools_next)

        ctx = SimpleNamespace(
            request_context=SimpleNamespace(meta=None),
            input_responses=None,
            request_state=None,
            fastmcp=SimpleNamespace(list_tools=list_tools),
        )
        forwarded = []

        async def next_call(masked):
            forwarded.append(masked)
            return ToolResult(content="safe synthetic")

        result = await gate.on_call_tool(
            MiddlewareContext(
                message=CallToolRequestParams(name="echo", arguments={}),
                fastmcp_context=ctx,
            ),
            next_call,
        )
        if output_schema is None:
            assert not result.is_error
            assert len(forwarded) == 1
        else:
            assert_generic(result)
            assert not forwarded and gate.schemas is None

    asyncio.run(run())


def test_plain_error_and_reverse_collision(isolated):
    root, created = isolated

    async def run():
        async with connected(root) as (client, _, _):
            result = await client.call_tool_mcp(
                "echo",
                {"payload": {"text": ORIGINALS[0]}, "action": "plain-error"},
            )
            assert result.is_error
            assert result.content[0].text == "note: Ga Raon"
            assert_generic(
                await client.call_tool_mcp(
                    "echo",
                    {
                        "payload": {"text": ORIGINALS[0]},
                        "action": "reverse-collision",
                    },
                )
            )
        assert_cleared(created)

    asyncio.run(run())


@pytest.mark.parametrize("failure", ["registry", "exhaustion", "depth"])
def test_preflight_cleanup_and_recovery(failure, isolated, monkeypatch):
    root, created = isolated

    async def run():
        async with connected(root) as (client, _, _):
            if failure == "registry":

                def unsafe():
                    raise GateError()

                monkeypatch.setattr(
                    proxy_module.roster, "load_registry", unsafe
                )
                payload = {"text": ORIGINALS[0]}
            elif failure == "exhaustion":

                def exhausted(registry):
                    call = Masker(registry)
                    call.faker = type(
                        "Names", (), {"first_name": lambda _: ORIGINALS[0]}
                    )()
                    created.append(call)
                    return call

                monkeypatch.setattr(proxy_module, "Masker", exhausted)
                payload = {"text": ORIGINALS[0]}
            else:
                payload = "deep"
                for _ in range(65):
                    payload = {"nested": payload}
            assert_generic(
                await client.call_tool_mcp("echo", {"payload": payload})
            )
            if created:
                assert_cleared(created)
            else:
                assert failure == "registry"
            monkeypatch.setattr(
                proxy_module.roster,
                "load_registry",
                lambda: Registry.from_data(DATA),
            )
            monkeypatch.setattr(proxy_module, "Masker", Masker)
            assert not (
                await client.call_tool_mcp(
                    "echo", {"payload": {"text": ORIGINALS[0]}}
                )
            ).is_error

    asyncio.run(run())


def test_startup_failure_has_fixed_text():
    def fail():
        raise RuntimeError(ORIGINALS[0])

    with pytest.raises(SystemExit, match="^Privacy gate rejected the call\\.$"):
        proxy_module.main(key_source=fail)


@pytest.mark.parametrize("config", [None, "", "relative", "absolute"])
def test_startup_provider_path_uses_config_root(config, tmp_path, monkeypatch):
    import dotenv  # noqa: PLC0415

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    if config is None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    else:
        monkeypatch.setenv(
            "XDG_CONFIG_HOME",
            str(tmp_path / "config") if config == "absolute" else config,
        )
    paths = []

    def synthetic_values(path, *, interpolate):
        paths.append(path)
        assert interpolate is False
        return {"OPENROUTER_API_KEY": "synthetic-dummy"}

    monkeypatch.setattr(dotenv, "dotenv_values", synthetic_values)
    monkeypatch.setattr(
        proxy_module,
        "build_proxy",
        lambda **unused_options: SimpleNamespace(
            run=lambda **unused_options: None
        ),
    )
    proxy_module.main()
    root = (
        tmp_path / "config"
        if config == "absolute"
        else tmp_path / "home/.config"
    )
    assert paths == [root / "verbose-broccoli/providers/openrouter.env"]
    assert (
        proxy_module.roster.registry_config_dir().parent
        == root / "verbose-broccoli"
    )


def test_continuations_and_raw_boolean_progress_are_blocked(isolated):
    root, created = isolated

    async def run():
        async with connected(root) as (client, _, _):
            assert_generic(
                await client.call_tool_mcp(
                    "echo",
                    {
                        "payload": {"text": ORIGINALS[0]},
                        "action": "continuation",
                    },
                )
            )
            # Bypass SDK integer coercion to send the malformed wire value.
            raw = await client.session._dispatcher.send_raw_request(
                "tools/call",
                {
                    "name": "echo",
                    "arguments": {"payload": {}},
                    "_meta": {"progressToken": True},
                },
            )
            assert raw["isError"]
            assert raw["content"][0]["text"] == GENERIC
        assert_cleared(created)
        async with connected(root, mode="auto") as (client, _, _):
            assert_generic(
                await client.session.call_tool(
                    "echo", {"payload": {}}, input_responses={}
                )
            )

    asyncio.run(run())


@pytest.mark.parametrize("managed", [True, False])
def test_node_resolution_with_mise_and_path(managed, tmp_path, monkeypatch):
    node = tmp_path / "node"
    node.write_text("")
    calls = []

    def lookup(name):
        return "/synthetic/mise" if name == "mise" else str(node)

    def resolve(command, *, text, cwd):
        calls.append((command, text, cwd))
        if not managed:
            raise subprocess.CalledProcessError(1, command)
        return str(node) + "\n"

    monkeypatch.setattr(proxy_module.shutil, "which", lookup)
    monkeypatch.setattr(proxy_module.subprocess, "check_output", resolve)
    assert proxy_module._node_command() == str(node)
    assert calls == [(["mise", "which", "node"], True, "/")]


@pytest.mark.parametrize("node", [None, "relative/node", "/missing/node"])
def test_node_resolution_rejects_missing_or_relative_path(node, monkeypatch):
    monkeypatch.setattr(
        proxy_module.shutil,
        "which",
        lambda name: "/synthetic/mise" if name == "mise" else node,
    )

    def unavailable(command, **unused_options):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(
        proxy_module.subprocess,
        "check_output",
        unavailable,
    )
    with pytest.raises(GateError):
        proxy_module._node_command()
