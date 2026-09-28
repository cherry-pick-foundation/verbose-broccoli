"""Immutable, local Markdown conversions of Wiki source revisions."""

from __future__ import annotations

import json
import os
import signal
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping

# Prevent ONNX Runtime from writing telemetry files during import.
os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")

from markitdown import MarkItDown, UnsupportedFormatException


CONVERTER_VERSION = "0.1.8"
EVIDENCE_BUDGET_BYTES = 1024**3
TEMP_SUFFIX = ".wiki-consistency-tmp"


def _component(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value or "\0" in value:
        raise ValueError(f"invalid evidence path component: {value!r}")
    return value


def _paths(cache: Path, wiki_id: str, source_id: str, revision: str) -> tuple[Path, Path, Path]:
    root = Path(cache) / "wiki-evidence"
    base = root / _component(wiki_id) / f"markitdown-{CONVERTER_VERSION}" / _component(source_id)
    stem = _component(revision)
    resolved_root = root.resolve()
    if not base.resolve().is_relative_to(resolved_root):
        raise ValueError("evidence path escapes the cache")
    return root, base / f"{stem}.md", base / f"{stem}.unreadable.json"


def _tree_size(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _check_budget(root: Path, incoming: int, budget_bytes: int) -> None:
    used = _tree_size(root)
    if used + incoming > budget_bytes:
        raise ValueError(
            f"wiki-evidence cache budget exceeded before write: "
            f"{used} + {incoming} bytes exceeds {budget_bytes} bytes"
        )


def _cleanup_temporary_files(root: Path) -> None:
    if root.exists():
        for path in root.rglob(f"*{TEMP_SUFFIX}"):
            if path.is_file():
                path.unlink()


@contextmanager
def _clean_on_signals() -> Iterator[None]:
    previous: dict[signal.Signals, object] = {}

    def exit_on_signal(signum: int, frame: object) -> None:
        raise SystemExit(128 + signum)

    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            previous[signum] = signal.signal(signum, exit_on_signal)
        except ValueError:
            pass
    try:
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def _payload_path(instance: Path, item: Mapping[str, object]) -> Path:
    bag = Path(str(item["path"]))
    if not bag.is_absolute():
        bag = Path(instance) / bag
    payloads = [path for path in (bag / "data").iterdir() if path.is_file()]
    if len(payloads) != 1:
        raise ValueError("source revision must contain exactly one payload file")
    return payloads[0]


def _detail(error: Exception, payload: Path | None = None) -> str:
    detail = " ".join(str(error).split()) or type(error).__name__
    if payload is not None:
        detail = detail.replace(str(payload), "source payload")
    return detail


def _write_immutable(target: Path, content: bytes, root: Path, budget_bytes: int) -> bool:
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    _check_budget(root, len(content), budget_bytes)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}{TEMP_SUFFIX}")
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists():
            return False
        os.rename(temporary, target)
        return True
    finally:
        temporary.unlink(missing_ok=True)


def _existing_unreadable(mark: Path, source_id: str, revision: str) -> dict[str, str]:
    stored = json.loads(mark.read_text(encoding="utf-8"))
    return {
        "id": source_id,
        "revision": revision,
        "reason": stored["reason"],
        "detail": stored["detail"],
    }


def convert(
    instance: Path,
    wiki_id: str,
    cache: Path,
    revisions: Mapping[str, list[Mapping[str, object]]],
    *,
    budget_bytes: int = EVIDENCE_BUDGET_BYTES,
) -> dict[str, object]:
    """Convert each given raw revision once into the Wiki evidence cache."""
    evidence_root = Path(cache) / "wiki-evidence"
    evidence_root.mkdir(parents=True, exist_ok=True)
    _cleanup_temporary_files(evidence_root)
    converted = 0
    present = 0
    unreadable: list[dict[str, str]] = []
    converter = MarkItDown()

    with _clean_on_signals():
        try:
            for source_key in sorted(revisions):
                for item in sorted(revisions[source_key], key=lambda value: str(value["revision"])):
                    source_id = str(item["id"])
                    revision = str(item["revision"])
                    root, target, mark = _paths(Path(cache), wiki_id, source_id, revision)
                    if target.is_file():
                        present += 1
                        continue
                    if mark.is_file():
                        unreadable.append(_existing_unreadable(mark, source_id, revision))
                        continue

                    payload: Path | None = None
                    try:
                        payload = _payload_path(Path(instance), item)
                        if payload.suffix.lower() in {".txt", ".md"}:
                            text = payload.read_bytes().decode("utf-8")
                        else:
                            text = converter.convert(payload).text_content or ""
                        if not any(character.isalpha() for character in text):
                            reason = "empty_text"
                            detail = "converted text contains no letters"
                        else:
                            reason = ""
                            detail = ""
                    except UnsupportedFormatException as error:
                        reason = "unsupported_format"
                        detail = _detail(error, payload)
                    except Exception as error:
                        reason = "conversion_failed"
                        detail = _detail(error, payload)

                    if reason:
                        mark_data = json.dumps(
                            {"reason": reason, "detail": detail},
                            ensure_ascii=False,
                            sort_keys=True,
                        ).encode("utf-8")
                        if not _write_immutable(mark, mark_data, root, budget_bytes):
                            if target.is_file():
                                present += 1
                            else:
                                unreadable.append(_existing_unreadable(mark, source_id, revision))
                        else:
                            unreadable.append(
                                {"id": source_id, "revision": revision, "reason": reason, "detail": detail}
                            )
                    else:
                        if _write_immutable(target, text.encode("utf-8"), root, budget_bytes):
                            converted += 1
                        else:
                            present += 1
        finally:
            _cleanup_temporary_files(evidence_root)

    unreadable.sort(key=lambda entry: (entry["id"], entry["revision"]))
    return {"converted": converted, "present": present, "unreadable": unreadable}


def read(cache: Path, wiki_id: str, source_id: str, revision: str) -> dict[str, str]:
    """Read converted text or the unreadable reason for a revision."""
    _, target, mark = _paths(Path(cache), wiki_id, source_id, revision)
    if target.is_file():
        return {"text": target.read_text(encoding="utf-8")}
    if mark.is_file():
        return {"unreadable": json.loads(mark.read_text(encoding="utf-8"))["reason"]}
    raise LookupError(f"evidence is not converted: {source_id}/{revision}")
