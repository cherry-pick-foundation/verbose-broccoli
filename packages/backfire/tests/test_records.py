"""Record content, on-disk budgets, and real process-lock lifecycle checks."""

from contextlib import contextmanager
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

from backfire import records
from backfire.records import RecordFile, RecordWriteError, digest, read_records


def total_bytes(directory):
    return sum(path.stat().st_size for path in directory.glob("*.jsonl"))


@contextmanager
def child(script, directory):
    process = subprocess.Popen(
        [sys.executable, "-c", textwrap.dedent(script), str(directory)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    try:
        yield process
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)
        for pipe in (process.stdin, process.stdout, process.stderr):
            pipe.close()


def ready(process):
    assert select.select([process.stdout], [], [], 10)[0], "writer did not become ready"
    return Path(process.stdout.readline().strip())


def test_digest_matches_canonical_bytes_and_changes_with_input():
    value = {"b": -0.0, "a": [1.0, 1e-7, 1e20, "한글"]}
    canonical = '{"a":[1,1e-7,100000000000000000000,"한글"],"b":0}'.encode()
    assert digest(value) == hashlib.sha256(canonical).hexdigest()
    assert digest({"\ue000": 1, "\U00010000": 2}) == hashlib.sha256(
        '{"\U00010000":2,"\ue000":1}'.encode()
    ).hexdigest()
    base = {"tool": "backfire_gate", "arguments": {"claim": "a", "diff": "b", "threshold": 0.8}}
    for key, value in (("claim", "changed"), ("diff", "uncommitted"), ("threshold", 0.9)):
        assert digest({**base, "arguments": {**base["arguments"], key: value}}) != digest(base)
    assert digest({"arguments": base["arguments"], "tool": base["tool"]}) == digest(base)
    assert digest({"tool": "backfire_gate", "arguments": {}}) != digest(
        {"tool": "backfire_gate", "arguments": None}
    )


def test_record_writers_keep_only_contract_fields_and_numeric_positions(tmp_path):
    secret = "synthetic-private-content"
    questions = {
        secret + "-choice": {"type": "choice", "instructions": secret,
                             "criteria": {secret + "-z": secret, secret + "-a": secret}},
        secret + "-noul": {"type": "noul", "instructions": secret},
        secret + "-score": {"type": "score", "instructions": secret, "criteria": [secret] * 3},
    }
    result = {
        "model": "reported-model", "usage": {"input_tokens": 20, "output_tokens": 30, "debug": secret},
        "answers": {
            secret + "-choice": {"choice": secret + "-a", "confidence": 0.9, "debug": secret},
            secret + "-noul": {"noul": 0.5},
            secret + "-score": {"score": 1.3, "confidence": 0.8, "legend": [secret] * 3},
        },
        "debug": secret,
    }
    wire_result = {"content": [{"type": "text", "text": json.dumps({"id": secret})}]}
    with RecordFile(tmp_path / "records") as record:
        assert record.path.name.endswith(f"-{record.session}.jsonl")
        assert record.path.stat().st_mode & 0o777 == 0o600
        record.write_judgment(
            state={"text": secret}, questions=questions, requested_model="selected-model",
            calls_in_flight=[2, 3], outcome="ok", result=result,
            metadata={"thinking_evidence": True, "reasoning_tokens": 10,
                      "attempts": 2, "latency_ms": 12.5, "debug": secret},
        )
        record.write_tool_call(
            call=2, tool="backfire_gate", input_digest=digest({"tool": "backfire_gate", "arguments": {"text": secret}}),
            outcome="ok", decisions=[{"action": "review", "truncated": False}],
            result=wire_result, model="reported-model", duration_ms=30.25,
        )
        judgment, call = list(read_records(record.path))
        assert secret not in record.path.read_text()
        assert judgment == {
            "kind": "judgment", "time": judgment["time"], "session": record.session,
            "judgment": 1, "calls_in_flight": [2, 3],
            "payload_digest": digest({"model": "selected-model", "state": {"text": secret}, "questions": questions}),
            "questions": [{"type": "choice", "cells": 2}, {"type": "noul", "cells": 1}, {"type": "score", "cells": 3}],
            "outcome": "ok", "results": [{"index": 1, "confidence": 0.9}, {"p": 0.5}, {"score": 1.3, "confidence": 0.8}],
            "model": "reported-model", "thinking_evidence": True,
            "usage": {"input_tokens": 20, "output_tokens": 30, "reasoning_tokens": 10},
            "attempts": 2, "latency_ms": 12.5,
        }
        assert call == {
            "kind": "tool_call", "time": call["time"], "session": record.session,
            "call": 2, "tool": "backfire_gate",
            "input_digest": digest({"tool": "backfire_gate", "arguments": {"text": secret}}),
            "outcome": "ok", "decisions": [{"action": "review", "truncated": False}],
            "result_digest": digest(wire_result), "model": "reported-model", "duration_ms": 30.25,
        }
        assert judgment["time"].endswith("Z") and call["time"].endswith("Z")


@pytest.mark.parametrize("outcome", ["backend_not_configured", "invalid_request", "cancelled"])
def test_failed_judgments_have_no_results_and_keep_sequence_across_rotation(tmp_path, monkeypatch, outcome):
    monkeypatch.setattr(records, "ROTATE_BYTES", 600)
    with RecordFile(tmp_path) as record:
        paths = []
        for expected in (1, 2):
            record.write_judgment(
                state="private", questions={"private-id": {"type": "private-type"}},
                requested_model=None, calls_in_flight=[1], outcome=outcome,
                metadata={"attempts": 0, "latency_ms": 1, "thinking_evidence": "private"},
            )
            paths.append(record.path)
            entry = list(read_records(record.path))[-1]
            assert entry["judgment"] == expected
            assert entry["outcome"] == outcome
            assert entry["questions"] == [{"type": None, "cells": 0}]
            assert entry["results"] is None and entry["model"] is None
            assert entry["thinking_evidence"] is None
            assert entry["usage"] == {"input_tokens": None, "output_tokens": None, "reasoning_tokens": None}
            assert entry["payload_digest"] == digest({"model": None, "state": "private", "questions": {"private-id": {"type": "private-type"}}})
            assert "private" not in record.path.read_text()
        assert paths[0] != paths[1]


@pytest.mark.parametrize("outcome", ["tool_error", "protocol_error", "cancelled", "deadline_exceeded", "session_ended"])
def test_tool_call_without_a_result(tmp_path, outcome):
    with RecordFile(tmp_path) as record:
        record.write_tool_call(call=1, tool="unknown", input_digest=digest({}), outcome=outcome,
                               decisions=None, result=None, model=None, duration_ms=0)
        entry, = read_records(record.path)
        assert entry["outcome"] == outcome
        assert entry["result_digest"] is None and entry["decisions"] is None and entry["model"] is None


def test_budget_is_never_exceeded_across_real_size_rotations(tmp_path):
    assert records.ROTATE_BYTES == 10 * 1024 * 1024
    assert records.BUDGET_BYTES == 50 * 1024 * 1024
    paths = []
    with RecordFile(tmp_path) as record:
        for index in range(8):
            record._append({"index": index, "padding": "x" * (9 * 1024 * 1024)})
            paths.append(record.path)
            assert total_bytes(tmp_path) <= 50 * 1024 * 1024
            assert record.path.stat().st_size < 10 * 1024 * 1024
        assert sorted(tmp_path.glob("*.jsonl")) == paths[-5:]
    assert total_bytes(tmp_path) <= 50 * 1024 * 1024


def test_rotation_boundary_and_oversized_line(tmp_path, monkeypatch):
    monkeypatch.setattr(records, "ROTATE_BYTES", 16)
    with RecordFile(tmp_path) as record:
        original = record.path
        record._append({"n": 1})
        record._append({"n": 2})
        assert record.path == original and original.stat().st_size == 16
        record._append({"n": 3})
        assert record.path != original
        with pytest.raises(RecordWriteError):
            record._append({"large": "x" * 16})
        assert list(read_records(original)) == [{"n": 1}, {"n": 2}]
        assert list(read_records(record.path)) == [{"n": 3}]


def test_live_files_are_never_deleted_and_close_allows_oldest_cleanup(tmp_path, monkeypatch):
    monkeypatch.setattr(records, "BUDGET_BYTES", 100)
    with RecordFile(tmp_path) as first, RecordFile(tmp_path) as second:
        first._append({"x": "a" * 32})
        second._append({"x": "b" * 32})
        before = {path: path.read_bytes() for path in tmp_path.glob("*.jsonl")}
        with pytest.raises(RecordWriteError, match="record_write_failed"):
            second._append({"x": "c" * 32})
        assert {path: path.read_bytes() for path in before} == before
        first.close()
        second._append({"x": "c" * 32})
        assert not first.path.exists() and second.path.exists()
        assert total_bytes(tmp_path) <= 100


def test_two_processes_write_and_rotate_with_one_directory_budget(tmp_path):
    script = """
        import sys
        from pathlib import Path
        from backfire import records
        records.ROTATE_BYTES = 1024
        records.BUDGET_BYTES = 4096
        with records.RecordFile(Path(sys.argv[1])) as writer:
            print(writer.path, flush=True)
            sys.stdin.readline()
            for index in range(100):
                writer._append({"session": writer.session, "index": index, "padding": "x" * 100})
                with writer._locked():
                    assert sum(p.stat().st_size for p in writer.directory.glob("*.jsonl")) <= 4096
            print(writer.path, flush=True)
            sys.stdin.readline()
    """
    with child(script, tmp_path) as first, child(script, tmp_path) as second:
        first_path, second_path = ready(first), ready(second)
        assert first_path != second_path
        for process in (first, second):
            process.stdin.write("start\n")
            process.stdin.flush()
        first_final, second_final = ready(first), ready(second)
        assert first_final != first_path and second_final != second_path
        assert first_final.exists() and second_final.exists()
        assert total_bytes(tmp_path) <= 4096
        assert list(read_records(first_final))[-1]["index"] == 99
        assert list(read_records(second_final))[-1]["index"] == 99
        for process in (first, second):
            output, error = process.communicate("stop\n", timeout=10)
            assert process.returncode == 0, error
    assert total_bytes(tmp_path) <= 4096
    for path in tmp_path.glob("*.jsonl"):
        assert all(entry["session"] in path.name for entry in read_records(path))


def test_killed_writer_releases_both_locks_and_partial_line_is_ignored(tmp_path, monkeypatch):
    script = """
        import os, sys
        from pathlib import Path
        from backfire.records import RecordFile
        with RecordFile(Path(sys.argv[1])) as writer:
            writer._append({"complete": 1})
            with writer._locked():
                os.write(writer._file, b'{"partial":"\\xe2')
                print(writer.path, flush=True)
                sys.stdin.readline()
    """
    with child(script, tmp_path) as process:
        old = ready(process)
        assert list(read_records(old)) == [{"complete": 1}]
        process.kill()
        process.wait(timeout=10)
    with old.open("rb") as source:
        fcntl.flock(source, fcntl.LOCK_EX | fcntl.LOCK_NB)
    monkeypatch.setattr(records, "BUDGET_BYTES", 64)
    with RecordFile(tmp_path) as next_session:
        next_session._append({"new": "x" * 40})
        assert not old.exists()
        assert list(read_records(next_session.path)) == [{"new": "x" * 40}]
        assert total_bytes(tmp_path) <= 64


def test_partial_write_failure_prevents_future_appends(tmp_path, monkeypatch):
    with RecordFile(tmp_path) as record:
        record._append({"complete": 1})
        write = os.write
        calls = 0

        def partial_then_fail(fd, data):
            nonlocal calls
            calls += 1
            if calls == 1:
                return write(fd, data[:5])
            raise OSError(errno.ENOSPC, "synthetic-private-error")

        monkeypatch.setattr(os, "write", partial_then_fail)
        with pytest.raises(RecordWriteError) as caught:
            record._append({"complete": 2})
        assert str(tmp_path) in str(caught.value)
        assert "synthetic-private-error" not in str(caught.value)
        assert list(read_records(record.path)) == [{"complete": 1}]
        before = record.path.read_bytes()
        monkeypatch.setattr(os, "write", write)
        with pytest.raises(RecordWriteError):
            record._append({"complete": 3})
        assert record.path.read_bytes() == before


def test_short_writes_are_completed_and_closed_writer_fails(tmp_path, monkeypatch):
    write = os.write
    monkeypatch.setattr(os, "write", lambda fd, data: write(fd, data[:3]))
    with RecordFile(tmp_path) as record:
        record._append({"complete": 1})
        assert list(read_records(record.path)) == [{"complete": 1}]
    record.close()
    with pytest.raises(RecordWriteError):
        record._append({"closed": True})


def test_start_failures_name_directory_and_exclusive_creation_preserves_file(tmp_path, monkeypatch):
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("existing")
    with pytest.raises(RecordWriteError, match=str(blocked)):
        RecordFile(blocked)
    monkeypatch.setattr(records, "_time", lambda: "2026-09-27T00:00:00.000000Z")
    monkeypatch.setattr(records, "uuid4", lambda: SimpleNamespace(hex="same-session"))
    with RecordFile(tmp_path) as record:
        record._append({"existing": True})
    with pytest.raises(RecordWriteError, match=str(tmp_path)):
        RecordFile(tmp_path)
    assert list(read_records(record.path)) == [{"existing": True}]
    monkeypatch.setattr(fcntl, "flock", lambda *args: (_ for _ in ()).throw(PermissionError("private")))
    with pytest.raises(RecordWriteError, match=str(tmp_path)) as caught:
        RecordFile(tmp_path)
    assert "private" not in str(caught.value)
