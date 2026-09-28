"""Content-free session records with process locks and a bounded JSONL store."""

from contextlib import AbstractContextManager, contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
from uuid import uuid4

import rfc8785

ROTATE_BYTES = 10 * 1024 * 1024
BUDGET_BYTES = 50 * 1024 * 1024


def digest(value) -> str:
    """Return lowercase SHA-256 of the value's RFC 8785 canonical JSON."""
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def read_records(path: Path):
    """Read complete records; an interrupted final line is not a record."""
    with path.open("rb") as source:
        for line in source:
            if not line.endswith(b"\n"):
                break
            yield json.loads(line)


def _time() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _number(value):
    return (
        value if type(value) in (int, float) and math.isfinite(value) else None
    )


class RecordWriteError(OSError):
    """The caller must withhold its verdict when this error is raised."""


class RecordFile(AbstractContextManager):
    """One server's synchronous writer; pass in its resolved records directory.

    The active file stays locked until rotation or close. Rotated files are
    closed and may be removed by the next budget check. Callers must write on
    the server's event-loop thread, where an append cannot interleave with
    another append in this session.
    """

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.session = uuid4().hex
        self.calls_in_flight: set[int] = set()
        self.path: Path | None = None
        self._file = None
        self._directory_lock = None
        self._failed = False
        self._judgment = 0
        try:
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._directory_lock = os.open(
                self.directory / ".lock", os.O_CREAT | os.O_RDWR, 0o600
            )
            with self._locked():
                self._make_room(0)
                self._rotate()
        except OSError:
            self.close()
            raise self._error() from None

    def _error(self):
        return RecordWriteError(
            f"record_write_failed: Cannot write records in {self.directory}; "
            "check permissions and available space."
        )

    @contextmanager
    def _locked(self):
        fcntl.flock(self._directory_lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(self._directory_lock, fcntl.LOCK_UN)

    def _rotate(self):
        path = self.directory / f"{_time()}-{self.session}.jsonl"
        new_file = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            fcntl.flock(new_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(new_file)
            path.unlink()
            raise
        if self._file is not None:
            os.close(self._file)
        self._file, self.path = new_file, path

    def _make_room(self, size):
        files = sorted(self.directory.glob("*.jsonl"))
        total = sum(path.stat().st_size for path in files)
        for path in files:
            if total + size <= BUDGET_BYTES:
                return
            with path.open("rb") as candidate:
                try:
                    fcntl.flock(candidate, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    continue
                length = os.fstat(candidate.fileno()).st_size
                path.unlink()
                total -= length
        if total + size > BUDGET_BYTES:
            raise self._error()

    def _append(self, record):
        line = (
            json.dumps(record, separators=(",", ":"), allow_nan=False).encode()
            + b"\n"
        )
        if self._file is None or self._failed or len(line) > ROTATE_BYTES:
            raise self._error()
        try:
            with self._locked():
                size = os.fstat(self._file).st_size
                if size and size + len(line) > ROTATE_BYTES:
                    self._rotate()
                self._make_room(len(line))
                try:
                    remaining = memoryview(line)
                    while remaining:
                        written = os.write(self._file, remaining)
                        if not written:
                            raise self._error()
                        remaining = remaining[written:]
                    os.fsync(self._file)
                except OSError:
                    # Never append after a partial line, even if space returns.
                    self._failed = True
                    raise
        except OSError:
            raise self._error() from None

    def write_tool_call(
        self,
        *,
        call: int,
        tool: str,
        input_digest: str,
        outcome: str,
        decisions: list[dict] | None,
        result: dict | None,
        model: str | None,
        duration_ms: float,
    ) -> None:
        """Write the boundary's projection, never raw arguments or result text.

        The boundary supplies its normalized tool name, decision_units output,
        and parsed model. input_digest is computed on receipt from the exact
        {tool, arguments} pair, using {} only when arguments were omitted.
        result is the MCP response's result object, used only for its digest.
        """
        self._append(
            {
                "kind": "tool_call",
                "time": _time(),
                "session": self.session,
                "call": call,
                "tool": tool,
                "input_digest": input_digest,
                "outcome": outcome,
                "decisions": decisions,
                "result_digest": digest(result) if result is not None else None,
                "model": model,
                "duration_ms": duration_ms,
            }
        )

    def write_judgment(
        self,
        *,
        state,
        questions: dict,
        requested_model: str | None,
        calls_in_flight: list[int],
        outcome: str,
        result: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Project question/answer data by position; the judge validates answers.

        calls_in_flight is the snapshot from when the judgment began, and
        outcome is ok, cancelled, or a fixed judgment error type. Invalid
        questions keep only their recognized type and count; failed judgments
        have no results. Metadata is copied field by field, never wholesale.
        """
        summaries, results = [], []
        for identifier, question in questions.items():
            question = question if isinstance(question, dict) else {}
            kind = question.get("type")
            kind = kind if kind in ("noul", "choice", "score") else None
            criteria = question.get("criteria")
            cells = (
                1
                if kind == "noul"
                else (
                    len(criteria)
                    if (kind == "choice" and isinstance(criteria, dict))
                    or (kind == "score" and isinstance(criteria, list))
                    else 0
                )
            )
            summaries.append({"type": kind, "cells": cells})
            if outcome == "ok" and result is not None:
                answer = result["answers"][identifier]
                if kind == "noul":
                    results.append({"p": _number(answer["noul"])})
                elif kind == "choice":
                    results.append(
                        {
                            "index": list(criteria).index(answer["choice"]),
                            "confidence": _number(answer["confidence"]),
                        }
                    )
                elif kind == "score":
                    results.append(
                        {
                            "score": _number(answer["score"]),
                            "confidence": _number(answer["confidence"]),
                        }
                    )
        metadata = metadata or {}
        usage = result["usage"] if result is not None else {}
        self._judgment += 1
        self._append(
            {
                "kind": "judgment",
                "time": _time(),
                "session": self.session,
                "judgment": self._judgment,
                "calls_in_flight": list(calls_in_flight),
                "payload_digest": digest(
                    {
                        "model": requested_model,
                        "state": state,
                        "questions": questions,
                    }
                ),
                "questions": summaries,
                "outcome": outcome,
                "results": results
                if outcome == "ok" and result is not None
                else None,
                "model": result.get("model") if result is not None else None,
                "thinking_evidence": metadata.get("thinking_evidence")
                if type(metadata.get("thinking_evidence")) is bool
                else None,
                "usage": {
                    "input_tokens": _number(usage.get("input_tokens")),
                    "output_tokens": _number(usage.get("output_tokens")),
                    "reasoning_tokens": _number(
                        metadata.get("reasoning_tokens")
                    ),
                },
                "attempts": _number(metadata.get("attempts")),
                "latency_ms": _number(metadata.get("latency_ms")),
            }
        )

    def close(self) -> None:
        """Release both descriptors; the kernel releases their file locks."""
        if self._file is not None:
            os.close(self._file)
            self._file = None
        if self._directory_lock is not None:
            os.close(self._directory_lock)
            self._directory_lock = None

    def __exit__(self, *exc):
        self.close()
