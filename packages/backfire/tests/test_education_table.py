import hashlib
import hmac
import json
import multiprocessing
import os
from pathlib import Path
import stat
import traceback

import pytest

from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire_education import table


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    return xdg_path("data") / "backfire" / "pseudonyms.json"


def test_reload_stability_hmac_privacy_counters_and_no_unneeded_writes(data):
    identifiers = [
        ("student", "가라온"),
        ("given", "라온"),
        ("school", "가상별학교"),
        ("guardian", "다루미"),
        ("phone", "+12025550123"),
        ("email", "learner@example.test"),
    ]
    first = table.assign(identifiers)
    assert list(first.values()) == [
        "학생01",
        "학생02",
        "학교01",
        "보호자01",
        "연락처01",
        "이메일01",
    ]
    raw, before = data.read_bytes(), data.stat()
    assert table.assign(identifiers) == first
    assert (
        data.read_bytes() == raw
        and data.stat().st_mtime_ns == before.st_mtime_ns
    )
    document = json.loads(raw)
    assert len(bytes.fromhex(document["key"])) == 32
    for (kind, value), pseudonym in first.items():
        assert value.encode() not in raw
        digest = hmac.new(
            bytes.fromhex(document["key"]),
            f"{kind}:{value}".encode(),
            hashlib.sha256,
        ).hexdigest()
        assert document["entries"][digest] == pseudonym
    assert table.assign([("student", "다새봄")]) == {
        ("student", "다새봄"): "학생03"
    }
    assert table.assign(identifiers) == first
    assert stat.S_IMODE(data.parent.stat().st_mode) == 0o700
    for path in (data, data.with_suffix(".lock")):
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.stat().st_uid == os.getuid()
    assert data.with_suffix(".lock").read_bytes() == b""


def test_numbers_can_exceed_two_digits_and_table_deletion_resets(data):
    result = table.assign(("student", f"synthetic-{i}") for i in range(104))
    assert list(result.values())[-1] == "학생104"
    previous_key = json.loads(data.read_bytes())["key"]
    data.unlink()
    assert (
        table.assign([("student", "new-synthetic")])[
            ("student", "new-synthetic")
        ]
        == "학생01"
    )
    assert json.loads(data.read_bytes())["key"] != previous_key


def _assign_in_process(root, start, prefix):
    os.environ["XDG_DATA_HOME"] = root
    assert start.wait(10)
    table.assign(
        [("student", f"{prefix}-{i}") for i in range(40)]
        + [("student", "shared-synthetic")]
    )


def test_two_processes_do_not_lose_or_duplicate_assignments(data):
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    processes = [
        context.Process(
            target=_assign_in_process,
            args=(os.environ["XDG_DATA_HOME"], start, prefix),
        )
        for prefix in ("a", "b")
    ]
    try:
        for process in processes:
            process.start()
        start.set()
        for process in processes:
            process.join(15)
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)
    document = json.loads(data.read_bytes())
    assert (
        len(document["entries"]) == len(set(document["entries"].values())) == 81
    )
    assert document["counters"] == {"학생": 81}


@pytest.mark.parametrize("failure", [PermissionError, KeyboardInterrupt])
def test_failed_or_interrupted_rename_keeps_old_table_and_removes_temporary(
    data, monkeypatch, failure
):
    table.assign([("student", "가라온")])
    old = data.read_bytes()

    def interrupt(source, destination):
        assert Path(source).parent == data.parent and destination == data
        assert stat.S_IMODE(Path(source).stat().st_mode) == 0o600
        raise failure("synthetic-private-diagnostic")

    monkeypatch.setattr(table.os, "replace", interrupt)
    with pytest.raises(
        JudgmentError if failure is PermissionError else KeyboardInterrupt
    ) as caught:
        table.assign([("student", "다새봄")])
    if failure is PermissionError:
        assert caught.value.detail == str(data)
        assert "synthetic-private-diagnostic" not in "".join(
            traceback.format_exception(caught.value)
        )
    assert data.read_bytes() == old
    assert set(data.parent.iterdir()) == {data, data.with_suffix(".lock")}


def test_budget_leaves_previous_table_unchanged(data, monkeypatch):
    table.assign([("student", "가라온")])
    old = data.read_bytes()
    assert table.BUDGET_BYTES == 1024 * 1024
    monkeypatch.setattr(table, "BUDGET_BYTES", len(old))
    assert (
        table.assign([("student", "가라온")])[("student", "가라온")] == "학생01"
    )
    with pytest.raises(JudgmentError) as caught:
        table.assign([("student", "다새봄")])
    assert caught.value.detail == str(data)
    assert data.read_bytes() == old
    data.write_bytes(old + b" ")
    with pytest.raises(JudgmentError):
        table.assign([])


@pytest.mark.parametrize(
    "change",
    [
        lambda unused_d: [],
        lambda d: {**d, "version": True},
        lambda d: {**d, "key": "private-invalid"},
        lambda d: {**d, "entries": []},
        lambda d: {**d, "counters": {"학생": False}},
        lambda d: {**d, "counters": {}},
        lambda d: {**d, "extra": "private-invalid"},
        lambda d: {**d, "entries": {"0" * 64: "학생01", "1" * 64: "학생01"}},
        lambda d: {**d, "entries": {"bad": "학생01"}},
        lambda d: {**d, "entries": {"0" * 64: "학생00"}},
    ],
)
def test_malformed_tables_fail_privately(data, change):
    table.assign([("student", "가라온")])
    data.write_text(json.dumps(change(json.loads(data.read_bytes()))))
    with pytest.raises(JudgmentError) as caught:
        table.assign([])
    assert caught.value.detail == str(data)
    assert "private-invalid" not in str(caught.value)


@pytest.mark.parametrize("target", ["table", "lock"])
@pytest.mark.parametrize(
    "problem",
    ["mode", "owner", "directory", "fifo", "unreadable", "unwritable"],
)
def test_unusable_table_or_lock_fails(data, monkeypatch, target, problem):
    table.assign([("student", "가라온")])
    path = data if target == "table" else data.with_suffix(".lock")
    if problem == "mode":
        path.chmod(0o640)
    elif problem == "owner":
        original = os.fstat

        def wrong_owner(fd):
            info = original(fd)
            if info.st_ino == path.stat().st_ino:
                fields = list(info)
                fields[4] += 1
                return os.stat_result(fields)
            return info

        monkeypatch.setattr(os, "fstat", wrong_owner)
    elif problem in ("directory", "fifo"):
        path.unlink()
        path.mkdir(mode=0o600) if problem == "directory" else os.mkfifo(
            path, mode=0o600
        )
    else:
        path.chmod(0o200 if problem == "unreadable" else 0o400)
    with pytest.raises(JudgmentError) as caught:
        table.assign([])
    assert caught.value.detail == str(path)


def test_empty_assignment_does_not_write_table_and_relative_root_fails(
    data, monkeypatch
):
    assert table.assign([]) == {}
    assert not data.exists()
    monkeypatch.setenv("XDG_DATA_HOME", "relative")
    with pytest.raises(JudgmentError) as caught:
        table.assign([])
    assert caught.value.detail == "XDG_DATA_HOME"
