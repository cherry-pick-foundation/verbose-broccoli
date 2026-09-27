"""Gate 7: exercise real stdio processes, local HTTP and pattern-child death."""

from contextlib import contextmanager
import ctypes
import errno
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

import pytest

from backfire.records import read_records
from fake_provider import FakeProvider, Reply, completion

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Process-death checks use Linux pidfds.")

CLIENT = """
import sys
for line in sys.stdin.buffer:
    sys.stdout.buffer.write(line)
    sys.stdout.buffer.flush()
"""
PATTERN_OBSERVER = """
import json, os, re, signal, socket
original = re.finditer
def observed(pattern, *args, **kwargs):
    if pattern == "(a+)+$":
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as ready:
            message = [os.getpid(), signal.getitimer(signal.ITIMER_REAL), signal.getsignal(signal.SIGALRM)]
            ready.sendto(json.dumps(message).encode(), os.environ["LIFECYCLE_PATTERN_READY"])
    return original(pattern, *args, **kwargs)
re.finditer = observed
"""
NOUL = {"name": "backfire_noul", "arguments": {"propositions": ["synthetic claim"]}}
EXTRACT = {"name": "backfire_extract", "arguments": {
    "document": "a" * 49_999 + "!",
    "fields": [{"id": "match", "pattern": "(a+)+$", "description": "synthetic match"}],
}}


def send(client, message):
    client.stdin.write(json.dumps({"jsonrpc": "2.0", **message}).encode() + b"\n")
    client.stdin.flush()


def receive(server, identifier):
    assert select.select([server.stdout], [], [], 5)[0], "Server did not answer within 5 s."
    message = json.loads(server.stdout.readline())
    assert message["id"] == identifier
    assert "error" not in message, message
    return message["result"]


@contextmanager
def session(tmp_path, *, provider=None, extra_env=None, initialize=True):
    env = {key: value for key, value in os.environ.items() if not key.startswith("BACKFIRE_TEST_")}
    env.update(XDG_CONFIG_HOME=str(tmp_path / "config"), XDG_STATE_HOME=str(tmp_path / "state"),
               PYTHONDONTWRITEBYTECODE="1")
    if provider is None:
        script = tmp_path / "script.json"
        script.write_text(json.dumps({"script": [], "requests_file": "requests.jsonl"}))
        env["BACKFIRE_TEST_JUDGE_SCRIPT"] = str(script)
    else:
        directory = tmp_path / "config/verbose-broccoli/backfire"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "config.toml").write_text('''
provider = "lifecycle-test"
[providers.lifecycle-test]
api = "openai"
base_url = "http://127.0.0.1:1/v1"
model = "synthetic-model"
credential = "SYNTHETIC_KEY"
thinking = {requested = "off"}
''')
        credential = directory / "lifecycle-test.env"
        credential.write_text("SYNTHETIC_KEY=synthetic-key\n")
        credential.chmod(0o600)
        env["BACKFIRE_TEST_PROVIDER_BASE_URL"] = provider.base_url
    env.update(extra_env or {})
    read_fd, write_fd = os.pipe()
    server = client = None
    try:
        with os.fdopen(read_fd, "rb", buffering=0) as source, os.fdopen(write_fd, "wb", buffering=0) as sink:
            server = subprocess.Popen(
                [sys.executable, "-m", "backfire", "serve-mcp"], stdin=source,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, bufsize=0,
            )
            # The client owns the only writer after this block. The test can
            # reap the server without keeping its input alive after client death.
            client = subprocess.Popen(
                [sys.executable, "-c", CLIENT], stdin=subprocess.PIPE,
                stdout=sink, stderr=subprocess.DEVNULL,
            )
        if initialize:
            send(client, {"id": 0, "method": "initialize", "params": {
                "protocolVersion": "2025-11-25", "capabilities": {},
                "clientInfo": {"name": "lifecycle-test", "version": "1"},
            }})
            assert receive(server, 0)["serverInfo"]["name"] == "backfire"
            send(client, {"method": "notifications/initialized"})
        yield server, client
    finally:
        for process in (client, server):
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()


def end_client(client, ending):
    if ending == "eof":
        client.stdin.close()
    else:
        client.kill()
    assert client.wait(timeout=5) == (0 if ending == "eof" else -signal.SIGKILL)


def assert_stopped(server, started):
    assert server.wait(timeout=max(0, started + 5 - time.monotonic())) == 0
    assert time.monotonic() - started < 5
    assert server.stdout.read() == b"", "A response escaped after session shutdown."
    assert b"Traceback" not in server.stderr.read()


def records(tmp_path):
    return [row for path in (tmp_path / "state/verbose-broccoli/backfire/records").glob("*.jsonl")
            for row in read_records(path)]


@contextmanager
def observed_pattern():
    # A datagram from finditer proves the real child armed its timer and reached
    # matching. No sleep is used to guess whether the subprocess has started.
    with TemporaryDirectory(prefix="backfire-lifecycle-") as temporary:
        directory = Path(temporary)
        (directory / "sitecustomize.py").write_text(PATTERN_OBSERVER)
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as ready:
            address = str(directory / "ready")
            ready.bind(address)
            ready.settimeout(5)
            yield ready, {"PYTHONPATH": str(directory), "LIFECYCLE_PATTERN_READY": address}


@contextmanager
def pattern_process(ready):
    pid, (remaining, interval), handler = json.loads(ready.recv(256))
    assert 0 < remaining <= 1 and interval == 0 and handler == signal.SIG_DFL
    descriptor = os.pidfd_open(pid)
    try:
        yield pid, descriptor
    finally:
        if not select.select([descriptor], [], [], 0)[0]:
            signal.pidfd_send_signal(descriptor, signal.SIGKILL)
        os.close(descriptor)


@pytest.mark.parametrize("ending", ["eof", "kill"])
def test_idle_client_end_stops_server(tmp_path, ending):
    with session(tmp_path) as (server, client):
        started = time.monotonic()
        end_client(client, ending)
        assert_stopped(server, started)
        assert records(tmp_path) == []


def test_client_dies_before_mcp_initialization(tmp_path):
    script = tmp_path / "startup.json"
    os.mkfifo(script)
    with session(tmp_path, initialize=False, extra_env={"BACKFIRE_TEST_JUDGE_SCRIPT": str(script)}) as (server, client):
        deadline = time.monotonic() + 5
        while True:
            try:
                descriptor = os.open(script, os.O_WRONLY | os.O_NONBLOCK)
                break
            except OSError as error:
                if error.errno != errno.ENXIO or time.monotonic() >= deadline:
                    raise
                time.sleep(0.01)
        with os.fdopen(descriptor, "w") as writer:
            # Opening the FIFO writer proves the server is reading its script
            # during startup. Hold it there until the client's death is certain.
            started = time.monotonic()
            end_client(client, "kill")
            assert server.poll() is None
            json.dump({"script": [], "requests_file": "requests.jsonl"}, writer)
        assert_stopped(server, started)
        assert records(tmp_path) == []


@pytest.mark.parametrize("ending", ["eof", "kill"])
def test_client_end_cancels_provider_request(tmp_path, monkeypatch, ending):
    with FakeProvider([Reply(completion(), stall=True)]) as fake:
        connections = []
        setup = fake.server.RequestHandlerClass.setup

        def observe_connection(handler):
            setup(handler)
            connections.append(handler.connection)

        monkeypatch.setattr(fake.server.RequestHandlerClass, "setup", observe_connection)
        with session(tmp_path, provider=fake) as (server, client):
            send(client, {"id": 1, "method": "tools/call", "params": NOUL})
            assert fake.received.wait(5), "The provider request never started."
            connection, = connections
            started = time.monotonic()
            end_client(client, ending)
            assert_stopped(server, started)
            assert select.select([connection], [], [], max(0, started + 5 - time.monotonic()))[0]
            assert connection.recv(1, socket.MSG_PEEK) == b"", "The provider socket stayed open."
            assert not fake.release.is_set() and len(fake.requests) == 1
            tool, judgment = records(tmp_path)
            assert (tool["kind"], tool["outcome"], tool["result_digest"]) == ("tool_call", "session_ended", None)
            assert (judgment["kind"], judgment["outcome"], judgment["results"]) == ("judgment", "cancelled", None)


@pytest.mark.parametrize("ending", ["eof", "kill"])
def test_client_end_kills_active_pattern_child(tmp_path, ending):
    with observed_pattern() as (ready, env), session(tmp_path, extra_env=env) as (server, client):
        send(client, {"id": 1, "method": "tools/call", "params": EXTRACT})
        with pattern_process(ready) as (pid, descriptor):
            started = time.monotonic()
            end_client(client, ending)
            assert_stopped(server, started)
            assert select.select([descriptor], [], [], 0)[0], f"Pattern child {pid} outlived its server."
            row, = records(tmp_path)
            assert row["outcome"] == "session_ended" and row["result_digest"] is None
            assert (tmp_path / "requests.jsonl").read_text() == ""


def test_killed_server_leaves_pattern_child_to_its_own_timer(tmp_path):
    # Adopt only this test's orphan so waitpid can prove SIGALRM and reap it.
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    assert libc.prctl(37, ctypes.byref(previous), 0, 0, 0) == 0  # PR_GET_CHILD_SUBREAPER
    assert libc.prctl(36, 1, 0, 0, 0) == 0  # PR_SET_CHILD_SUBREAPER
    orphan = None
    try:
        with observed_pattern() as (ready, env), session(tmp_path, extra_env=env) as (server, client):
            send(client, {"id": 1, "method": "tools/call", "params": EXTRACT})
            with pattern_process(ready) as (orphan, descriptor):
                started = time.monotonic()
                server.kill()
                assert server.wait(timeout=5) == -signal.SIGKILL
                # pattern_process checks the one-shot 1000 ms OS timer. Allow
                # scheduling/reaping time here; SIGALRM must still end the child.
                assert select.select([descriptor], [], [], max(0, started + 2 - time.monotonic()))[0], (
                    "The orphan pattern child's 1000 ms timer did not end it."
                )
                pid, status = os.waitpid(orphan, 0)
                assert pid == orphan and os.waitstatus_to_exitcode(status) == -signal.SIGALRM
                orphan = None
                assert (tmp_path / "requests.jsonl").read_text() == ""
    finally:
        if orphan is not None:
            os.waitpid(orphan, 0)
        assert libc.prctl(36, previous.value, 0, 0, 0) == 0


def test_concurrent_sessions_share_records_without_interfering(tmp_path):
    answer = completion({"p_proposition0": 0.99})
    with FakeProvider([Reply(answer, stall=True)]) as first, FakeProvider([answer, answer]) as second:
        with session(tmp_path, provider=first) as (first_server, first_client), session(tmp_path, provider=second) as (server, client):
            send(first_client, {"id": 1, "method": "tools/call", "params": NOUL})
            assert first.received.wait(5)
            send(client, {"id": 1, "method": "tools/call", "params": NOUL})
            result = receive(server, 1)
            assert not result.get("isError")
            assert json.loads(result["content"][0]["text"])["results"][0]["probability"] == 0.99
            started = time.monotonic()
            end_client(first_client, "kill")
            assert_stopped(first_server, started)
            assert server.poll() is None
            send(client, {"id": 2, "method": "tools/call", "params": NOUL})
            assert receive(server, 2) == result
            files = list((tmp_path / "state/verbose-broccoli/backfire/records").glob("*.jsonl"))
            assert len(files) == 2
            sessions = [list(read_records(path)) for path in files]
            assert len({row["session"] for rows in sessions for row in rows}) == 2
            assert sorted([row["outcome"] for row in rows if row["kind"] == "tool_call"] for rows in sessions) == [
                ["ok", "ok"], ["session_ended"],
            ]
            assert len(first.requests) == 1 and len(second.requests) == 2
            started = time.monotonic()
            end_client(client, "eof")
            assert_stopped(server, started)
