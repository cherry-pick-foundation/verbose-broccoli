"""Retained original-language text and exact local source evidence."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import tempfile
from typing import Any, BinaryIO, Iterator, Mapping
import uuid
import warnings

# Prevent ONNX Runtime from writing telemetry files during import.
os.environ.setdefault("ORT_DISABLE_TELEMETRY", "1")

from hwpx import Hwp5ConversionWarning
from hwpx import HwpxDocument
from markdown_it import MarkdownIt
from markitdown import DocumentConverter
from markitdown import DocumentConverterResult
from markitdown import MarkItDown
from markitdown import StreamInfo
from markitdown import UnsupportedFormatException
from markitdown.converters import PlainTextConverter
import yaml

from doc_regions.regions import _split_lf_lines
from wiki_consistency import instance as storage
from wiki_consistency import sources

CONVERTER_VERSION = (
    f"{version('markitdown')}-hwpx-{version('python-hwpx')}-json-2"
)
EVIDENCE_BUDGET_BYTES = 1024**3
TEMP_SUFFIX = ".wiki-consistency-tmp"


class JsonConverter(PlainTextConverter):
    """Convert JSON and JSONL streams through MarkItDown."""

    def accepts(
        self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any
    ) -> bool:
        """Return whether the stream contains JSON or JSONL."""
        del file_stream, kwargs  # Unused.
        extension = (stream_info.extension or "").lower()
        mimetype = (stream_info.mimetype or "").split(";", 1)[0].strip().lower()
        return (
            extension in {".json", ".jsonl"} or mimetype == "application/json"
        )

    def convert(
        self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any
    ):
        """Normalize JSON content in the converted Markdown."""
        result = super().convert(file_stream, stream_info, **kwargs)
        try:
            if (stream_info.extension or "").lower() == ".jsonl":
                lines = []
                for line in result.markdown.splitlines(keepends=True):
                    content = line.rstrip("\r\n")
                    if content.strip():
                        lines.append(
                            json.dumps(json.loads(content), ensure_ascii=False)
                            + line[len(content) :]
                        )
                    else:
                        lines.append(line)
                result.markdown = "".join(lines)
            else:
                result.markdown = json.dumps(
                    json.loads(result.markdown), ensure_ascii=False
                )
        except json.JSONDecodeError:
            pass
        return result


class HwpxConverter(DocumentConverter):
    """Convert HWP and HWPX documents through python-hwpx."""

    def accepts(
        self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any
    ) -> bool:
        """Return whether the stream has an HWP or HWPX extension."""
        del file_stream, kwargs  # Unused.
        return (stream_info.extension or "").lower() in {".hwp", ".hwpx"}

    def convert(
        self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any
    ) -> DocumentConverterResult:
        """Export the document with python-hwpx and release its resources."""
        del stream_info, kwargs  # Unused.
        document = HwpxDocument.open(file_stream.read())
        try:
            return DocumentConverterResult(document.text.markdown())
        finally:
            document.close()


def _component(value: str) -> str:
    if (
        not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or "\0" in value
    ):
        raise ValueError(f"invalid path component: {value!r}")
    return value


def _safe_path(root: Path, path: Path) -> Path:
    root = Path(root).absolute()
    path = Path(path).absolute()
    if ".." in path.parts or not path.is_relative_to(root):
        raise ValueError("evidence path escapes its root")
    if any(candidate.is_symlink() for candidate in (path, *path.parents)):
        raise ValueError("evidence paths cannot be symlinks")
    return path


def _text_path(instance: Path, source_id: str, revision: str) -> Path:
    return _safe_path(
        instance,
        Path(instance)
        / "text"
        / _component(source_id)
        / f"{_component(revision)}.qmd",
    )


def _tree_size(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(
        path.stat().st_size for path in root.rglob("*") if path.is_file()
    )


def _check_budget(root: Path, incoming: int, budget_bytes: int) -> None:
    if not isinstance(budget_bytes, int) or budget_bytes < 1:
        raise ValueError("evidence budget must be a positive integer")
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
        del frame  # Unused.
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


def _raw_record(instance: Path, item: Mapping[str, object]):
    root = Path(instance).absolute()
    source_id, revision = str(item["id"]), str(item["revision"])
    kind = _component(str(item["kind"]))
    expected = (
        root / "raw" / kind / _component(source_id) / _component(revision)
    )
    given = Path(str(item["path"]))
    bag = _safe_path(root, given if given.is_absolute() else root / given)
    if bag != expected:
        raise ValueError("raw directory identity mismatch")
    matches = [
        row
        for row in storage.revisions(root).get(source_id, [])
        if row["revision"] == revision
    ]
    if len(matches) != 1:
        raise ValueError("missing or ambiguous raw revision")
    info_path = _safe_path(root, bag / "bag-info.txt")
    manifest_path = _safe_path(root, bag / "manifest-sha256.txt")
    info = sources._bag_info(info_path)  # noqa: SLF001
    if info.get_all("External-Identifier") != [source_id]:
        raise ValueError("raw source identity mismatch")
    if info.get_all("Admission-Time") != [revision]:
        raise ValueError("raw revision identity mismatch")
    name, digest = sources._manifest(manifest_path)  # noqa: SLF001
    payload = _safe_path(bag / "data", bag / "data" / name)
    payloads = list((bag / "data").iterdir())
    if payloads != [payload] or not payload.is_file():
        raise ValueError(
            "source revision must contain exactly one payload file"
        )
    with payload.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != actual:
        raise ValueError("raw SHA-256 changed")
    return payload, digest, info


def _payload_path(instance: Path, item: Mapping[str, object]) -> Path:
    return _raw_record(instance, item)[0]


def _detail(error: Exception, payload: Path | None = None) -> str:
    detail = " ".join(str(error).split()) or type(error).__name__
    if payload is not None:
        detail = detail.replace(str(payload), "source payload")
    return detail


def _write_immutable(
    target: Path, content: bytes, root: Path, budget_bytes: int
) -> bool:
    _safe_path(root, target)
    if target.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    _check_budget(root, len(content), budget_bytes)
    temporary = target.with_name(
        f".{target.name}.{uuid.uuid4().hex}{TEMP_SUFFIX}"
    )
    try:
        with temporary.open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists():
            return False
        try:
            os.link(temporary, target)
        except FileExistsError:
            return False
        return True
    finally:
        temporary.unlink(missing_ok=True)


def convert(
    instance: Path,
    wiki_id: str,
    cache: Path,
    revisions: Mapping[str, list[Mapping[str, object]]],
    *,
    budget_bytes: int = EVIDENCE_BUDGET_BYTES,
) -> dict[str, object]:
    """Retain each selected raw revision once; never promote old cache text."""
    _component(wiki_id)
    if not isinstance(budget_bytes, int) or budget_bytes < 1:
        raise ValueError("evidence budget must be a positive integer")
    root = Path(instance).absolute()
    evidence_root = _safe_path(cache, Path(cache) / "wiki-evidence")
    _cleanup_temporary_files(_safe_path(root, root / "text"))
    converted, present = 0, 0
    unreadable, partial, problems = [], [], []
    converter = None
    with _clean_on_signals():
        for source_key in sorted(revisions):
            seen = set()
            for item in sorted(
                revisions[source_key], key=lambda v: v["revision"]
            ):
                source_id, revision = str(item["id"]), str(item["revision"])
                if source_key != source_id or revision in seen:
                    raise ValueError("ambiguous selected raw revision")
                seen.add(revision)
                payload, digest, _ = _raw_record(root, item)
                target = _text_path(root, source_id, revision)
                if target.exists():
                    present += 1
                else:
                    mark = _safe_path(
                        cache,
                        evidence_root
                        / wiki_id
                        / "retained-text"
                        / source_id
                        / f"{revision}.{digest}.unreadable.json",
                    )
                    if mark.is_file():
                        stored = json.loads(mark.read_text(encoding="utf-8"))
                        if stored.get("sha256") != digest:
                            raise ValueError(
                                "unreadable receipt raw hash mismatch"
                            )
                        unreadable.append(
                            {
                                "id": source_id,
                                "revision": revision,
                                "reason": stored["reason"],
                                "detail": stored["detail"],
                            }
                        )
                        continue
                    detail = ""
                    try:
                        if payload.suffix.lower() in {".txt", ".md"}:
                            text = payload.read_bytes().decode("utf-8")
                            converter_info = {
                                "name": "python-utf-8",
                                "version": platform.python_version(),
                            }
                        elif payload.suffix.lower() == ".pdf":
                            backend = subprocess.run(
                                ["pdftotext", "-v"],
                                check=True,
                                capture_output=True,
                                text=True,
                            )
                            found = re.search(
                                r"^pdftotext version (\S+)",
                                backend.stderr + backend.stdout,
                                re.MULTILINE,
                            )
                            if found is None:
                                raise ValueError(
                                    "pdftotext version unavailable"
                                )
                            extracted = subprocess.run(
                                ["pdftotext", "-raw", payload, "-"],
                                check=True,
                                capture_output=True,
                            )
                            text = extracted.stdout.decode("utf-8")
                            detail = " ".join(
                                extracted.stderr.decode(
                                    "utf-8", errors="replace"
                                )
                                .replace(str(payload), "source payload")
                                .split()
                            )
                            converter_info = {
                                "name": "pdftotext -raw",
                                "version": found[1],
                            }
                        else:
                            if converter is None:
                                converter = MarkItDown()
                                converter.register_converter(JsonConverter())
                                converter.register_converter(HwpxConverter())
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter(
                                    "always", Hwp5ConversionWarning
                                )
                                text = (
                                    converter.convert(payload).text_content
                                    or ""
                                )
                            detail = "; ".join(
                                _detail(w.message, payload)
                                for w in caught
                                if issubclass(w.category, Hwp5ConversionWarning)
                            )
                            converter_info = {
                                "name": "markitdown",
                                "version": CONVERTER_VERSION,
                            }
                        reason = (
                            ""
                            if any(c.isalpha() for c in text)
                            else "empty_text"
                        )
                        if reason:
                            detail = "converted text contains no letters"
                    except UnsupportedFormatException as error:
                        reason, detail = (
                            "unsupported_format",
                            _detail(error, payload),
                        )
                    except Exception as error:  # noqa: BLE001
                        reason, detail = (
                            "conversion_failed",
                            _detail(error, payload),
                        )
                    if reason:
                        result = {
                            "reason": reason,
                            "detail": detail,
                            "sha256": digest,
                        }
                        _write_immutable(
                            mark,
                            json.dumps(result).encode(),
                            evidence_root,
                            budget_bytes,
                        )
                        unreadable.append(
                            {
                                "id": source_id,
                                "revision": revision,
                                "reason": reason,
                                "detail": detail,
                            }
                        )
                        continue
                    metadata = {
                        "source-id": source_id,
                        "revision": revision,
                        "sha256": digest,
                        "converter": converter_info,
                        "checked-against-original": False,
                        "conversion-status": "partial"
                        if detail
                        else "extracted",
                        "conversion-warning": detail or None,
                    }
                    front = yaml.safe_dump(
                        metadata, allow_unicode=True, sort_keys=False
                    )
                    content = f"---\n{front}---\n{text}".encode("utf-8")
                    if _write_immutable(
                        target, content, root / "text", budget_bytes
                    ):
                        converted += 1
                    else:
                        present += 1
                retained = read(root, source_id, revision)
                problems.extend(
                    {
                        "document": f"text/{source_id}/{revision}.qmd",
                        "line": 1,
                        "message": message,
                    }
                    for message in retained["problems"]
                )
                if retained["conversion-status"] == "partial":
                    partial.append(
                        {
                            "id": source_id,
                            "revision": revision,
                            "detail": retained["conversion-warning"],
                        }
                    )
    return {
        "converted": converted,
        "present": present,
        "unreadable": unreadable,
        "partial": partial,
        "problems": problems,
    }


def read(
    instance: Path,
    source_id: str,
    revision: str,
    *,
    review: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Read the full retained body with current raw and extraction provenance.

    Missing or invalid identities raise; unknown legacy quality facts are
    preserved as null and listed in problems. No conversion is performed.
    A true review flag needs a caller-supplied original-review receipt bound
    to sha256 and extraction-sha256, with a nonempty evidence reference.
    """
    target = _text_path(instance, source_id, revision)
    if not target.is_file():
        raise LookupError(f"retained text is absent: {source_id}/{revision}")
    candidates = [
        item
        for item in storage.revisions(instance).get(source_id, [])
        if item["revision"] == revision
    ]
    if len(candidates) != 1:
        raise ValueError("missing or ambiguous raw revision")
    _, digest, _ = _raw_record(instance, candidates[0])
    content = target.read_bytes()
    document = content.decode("utf-8")
    metadata, errors = storage._front_matter_mapping(document)  # noqa: SLF001
    if errors:
        raise ValueError(errors[0]["message"])
    _, end, _ = storage._front_matter(document)  # noqa: SLF001
    body = "".join(_split_lf_lines(document)[end + 1 :])
    extraction_digest = hashlib.sha256(content).hexdigest()
    if (
        metadata.get("source-id"),
        metadata.get("revision"),
        metadata.get("sha256"),
    ) != (source_id, revision, digest):
        raise ValueError("retained header/raw identity mismatch")
    problems = []
    converter = metadata.get("converter")
    if not isinstance(converter, dict):
        converter = {"name": None, "version": None}
    for field in ("name", "version"):
        if (
            not isinstance(converter.get(field), str)
            or not converter[field].strip()
        ):
            converter[field] = None
            problems.append(f"unknown converter {field}")
    checked = metadata.get("checked-against-original")
    if checked is not False and checked is not True:
        checked = None
        problems.append("unknown original review status")
    if checked is True:
        if (
            not isinstance(review, dict)
            or review.get("sha256") != digest
            or review.get("extraction-sha256") != extraction_digest
            or not isinstance(review.get("evidence"), str)
            or not review["evidence"].strip()
        ):
            checked = None
            problems.append("missing or stale original review evidence")
    status = metadata.get("conversion-status")
    if status not in {"extracted", "partial"}:
        status = None
        problems.append("unknown conversion status")
    if not body.strip():
        problems.append("absent text body")
    if not any(marker[0] for marker in _markers(body)):
        problems.append("missing locator evidence")
    return {
        "id": f"{source_id}/{revision}",
        "source-id": source_id,
        "revision": revision,
        "sha256": digest,
        "extraction-sha256": extraction_digest,
        "converter": converter,
        "checked-against-original": checked,
        "conversion-status": status,
        "conversion-warning": metadata.get("conversion-warning"),
        "problems": problems,
        "first_line": end + 2,
        "text": body,
    }


def _markers(body):
    markers = []
    if re.search(r"\r(?!\n)", body):
        return markers
    lines = _split_lf_lines(body)
    for token in MarkdownIt("commonmark").parse(body):
        if token.level != 0 or token.map is None:
            continue
        if token.type == "heading_open":
            first, end = token.map
            match = re.search(
                r"\{#((?:p-[0-9]+|sec-[\w-]+))\}\s*$", lines[first].rstrip()
            )
            markers.append(
                (match[1] if match else None, first, end, int(token.tag[1:]))
            )
        elif token.type == "paragraph_open":
            for line in range(*token.map):
                match = re.fullmatch(
                    r":::+\s*\{#(p-[0-9]+)\}\s*", lines[line].rstrip()
                )
                if match:
                    markers.append((match[1], line, line + 1, 0))
    return markers


def read_located(
    instance: Path,
    source_id: str,
    revision: str,
    locator: str,
    *,
    max_chars: int,
    review: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Read one exact page, contiguous page range, or heading section span.

    Line bounds are inclusive, one-based retained-file lines. Marker lines are
    excluded from the selected body. Unknown provenance and partial output fail.
    """
    if not isinstance(max_chars, int) or max_chars < 1:
        raise ValueError("max_chars must be a positive integer")
    retained = read(instance, source_id, revision, review=review)
    if retained["problems"] or retained["conversion-status"] != "extracted":
        raise ValueError(
            "unverifiable retained text: "
            + "; ".join(retained["problems"])
            + (
                "; partial output"
                if retained["conversion-status"] == "partial"
                else ""
            )
        )
    page = re.fullmatch(r"p\.\s*([0-9]+)", locator.strip())
    pages = re.fullmatch(r"pp\.\s*([0-9]+)\s*-\s*([0-9]+)", locator.strip())
    section = re.fullmatch(r"sec\.\s*([\w-]+)", locator.strip())
    if page or pages:
        first = int((page or pages)[1])
        last = first if page else int(pages[2])
        if first < 1 or last < first or last - first > max_chars:
            raise ValueError("out-of-range page locator")
        wanted = [f"p-{n}" for n in range(first, last + 1)]
    elif section:
        wanted = [f"sec-{section[1]}"]
    else:
        raise ValueError("unsupported locator")
    markers = _markers(retained["text"])
    identified = [m[0] for m in markers if m[0]]
    if len(identified) != len(set(identified)):
        raise ValueError("duplicate locator marker")
    selected = []
    for key in wanted:
        found = next((m for m in markers if m[0] == key), None)
        if found is None:
            raise ValueError(f"missing locator marker: {key}")
        selected.append(found)
    if page or pages:
        page_markers = [m for m in markers if m[0] and m[0].startswith("p-")]
        positions = [page_markers.index(m) for m in selected]
        if positions != list(
            range(positions[0], positions[0] + len(positions))
        ):
            raise ValueError("noncontiguous page range")
        boundary = next(
            (m[1] for m in page_markers if m[1] > selected[-1][1]),
            len(_split_lf_lines(retained["text"])),
        )
    else:
        boundary = next(
            (
                m[1]
                for m in markers
                if m[1] > selected[0][1] and m[3] and m[3] <= selected[0][3]
            ),
            len(_split_lf_lines(retained["text"])),
        )
    start = selected[0][2]
    lines = _split_lf_lines(retained["text"])
    if page or pages:
        div_lines = (
            [
                line
                for token in MarkdownIt("commonmark").parse(retained["text"])
                if token.type == "paragraph_open" and token.level == 0
                for line in range(*token.map)
                if re.match(r"^:::+", lines[line])
            ]
            if any(marker[3] == 0 for marker in selected)
            else []
        )
        for marker in selected:
            if marker[3] != 0:
                continue
            stop = next(
                (m[1] for m in page_markers if m[1] > marker[1]), len(lines)
            )
            delimiters = [
                line for line in div_lines if marker[2] <= line < stop
            ]
            if len(delimiters) != 1 or not re.fullmatch(
                r":::+\s*", lines[delimiters[0]]
            ):
                raise ValueError("ambiguous page div bounds")
            if marker == selected[-1]:
                boundary = delimiters[0]
    text = "".join(lines[start:boundary])
    if not text.strip():
        raise ValueError("absent located text")
    if len(text) > max_chars:
        raise ValueError("oversized located span")
    return {
        key: retained[key]
        for key in (
            "id",
            "source-id",
            "revision",
            "sha256",
            "extraction-sha256",
            "converter",
            "checked-against-original",
            "conversion-status",
        )
    } | {
        "locator": locator,
        "locator_ids": wanted,
        "first_line": retained["first_line"] + start,
        "last_line": retained["first_line"] + boundary - 1,
        "text": text,
    }


@contextmanager
def bibliography(
    instance: Path,
    revisions: Mapping[str, list[Mapping[str, object]]],
    *,
    budget_bytes: int,
    env=None,
) -> Iterator[Path]:
    """Yield fresh private cache CSL JSON; remove this run on every exit.

    Entries contain id, type, title and custom source-id, revision, sha256,
    raw-provenance (kind and relative payload name). No admission dates,
    private sender identifiers or absolute source paths are exported.
    """
    if not isinstance(budget_bytes, int) or budget_bytes < 1:
        raise ValueError("bibliography budget must be a positive integer")
    cache = storage.roots(env)["cache"]
    root = _safe_path(cache, cache / "wiki-bibliography")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    with (
        _clean_on_signals(),
        tempfile.TemporaryDirectory(prefix="run-", dir=root) as run,
    ):
        entries, seen = [], set()
        for source_id in sorted(revisions):
            for item in sorted(
                revisions[source_id], key=lambda v: v["revision"]
            ):
                key = f"{source_id}/{item['revision']}"
                if source_id != item["id"] or key in seen:
                    raise ValueError("ambiguous bibliography revision")
                seen.add(key)
                payload, digest, _ = _raw_record(instance, item)
                entries.append(
                    {
                        "id": key,
                        "type": "document",
                        "title": payload.name,
                        "custom": {
                            "source-id": source_id,
                            "revision": item["revision"],
                            "sha256": digest,
                            "raw-provenance": {
                                "kind": item["kind"],
                                "payload": f"data/{payload.name}",
                            },
                        },
                    }
                )
        target = Path(run) / "sources.json"
        content = json.dumps(
            entries, ensure_ascii=False, sort_keys=True, indent=2
        ).encode()
        _write_immutable(target, content, root, budget_bytes)
        target.chmod(0o600)
        yield target
