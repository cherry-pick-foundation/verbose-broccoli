import hashlib
from pathlib import Path
import re
import shutil

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src" / "jev_judge_mcp"
UPSTREAM_ROOT = Path(__file__).resolve().parent / "upstream"
RECORD = SOURCE_ROOT / "UPSTREAM.md"


def _section(record: str, name: str) -> str:
    lines = record.splitlines()
    start = lines.index(f"## {name}") + 1
    end = next(
        (
            index
            for index in range(start, len(lines))
            if lines[index].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _file_rows(record: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for line in _section(record, "Files").splitlines():
        if not line.startswith("|"):
            continue
        columns = [column.strip() for column in line.strip("|").split("|")]
        if columns[0] == "Upstream path" or set(columns[0]) <= {"-", ":"}:
            continue
        if len(columns) != 3:
            raise ValueError(f"invalid Files table row: {line}")
        path, digest, status = columns
        if path in rows:
            raise ValueError(f"duplicate Files table row: {path}")
        rows[path] = digest, status
    return rows


def _record_errors(
    record_path: Path, source_root: Path, upstream_root: Path
) -> list[str]:
    record = record_path.read_text(encoding="utf-8")
    rows = _file_rows(record)
    paths: dict[str, Path] = {}
    for path in source_root.rglob("*"):
        if not path.is_file() or path.name == "UPSTREAM.md":
            continue
        relative = path.relative_to(source_root).as_posix()
        upstream_path = (
            relative
            if relative in {"LICENSE", "THIRD_PARTY_NOTICES.md"}
            else f"src/jev_judge_mcp/{relative}"
        )
        paths[upstream_path] = path
    for path in upstream_root.rglob("*"):
        if path.is_file():
            paths[path.relative_to(upstream_root).as_posix()] = path

    changes = _section(record, "Changes")
    errors: list[str] = []
    for path in sorted(paths.keys() - rows.keys()):
        errors.append(f"{path}: vendored file has no table row")
    for upstream_path, (digest, status) in rows.items():
        if upstream_path not in paths:
            errors.append(f"{upstream_path}: table row has no vendored file")
            continue
        if status not in {"unchanged", "changed", "added"}:
            errors.append(f"{upstream_path}: invalid status {status!r}")
        elif status == "unchanged":
            actual = hashlib.sha256(
                paths[upstream_path].read_bytes()
            ).hexdigest()
            if actual != digest:
                errors.append(
                    f"{upstream_path}: unchanged file differs "
                    "from its recorded SHA-256"
                )
        elif f"`{upstream_path}`" not in changes:
            errors.append(
                f"{upstream_path}: changed or added file has no Changes entry"
            )
        if status == "added" and digest != "-":
            errors.append(
                f"{upstream_path}: added file must use `-` for its upstream "
                "SHA-256"
            )
        elif status != "added" and not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"{upstream_path}: invalid upstream SHA-256")
    return errors


def test_upstream_record_matches_every_vendored_file() -> None:
    errors = _record_errors(RECORD, SOURCE_ROOT, UPSTREAM_ROOT)
    assert not errors, "\n".join(errors)


def test_temporary_copy_reports_changed_missing_and_unlisted_files(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "src" / "jev_judge_mcp"
    upstream_root = tmp_path / "upstream"
    source_root.mkdir(parents=True)
    original = (SOURCE_ROOT / "cache.py").read_bytes()
    cache_copy = source_root / "cache.py"
    shutil.copyfile(SOURCE_ROOT / "cache.py", cache_copy)
    digest = hashlib.sha256(original).hexdigest()
    record_path = tmp_path / "UPSTREAM.md"

    def write_record(rows: str) -> None:
        record_path.write_text(
            "## Files\n\n| Upstream path | SHA-256 | Status |\n"
            "| --- | --- | --- |\n"
            f"{rows}\n## Changes\n\nNone yet.\n",
            encoding="utf-8",
        )

    write_record(f"| src/jev_judge_mcp/cache.py | {digest} | unchanged |")
    cache_copy.write_bytes(original + b"changed")
    errors = _record_errors(record_path, source_root, upstream_root)
    assert any("src/jev_judge_mcp/cache.py" in error for error in errors)

    cache_copy.write_bytes(original)
    extra = upstream_root / "tests" / "unit" / "unlisted.py"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"upstream test")
    errors = _record_errors(record_path, source_root, upstream_root)
    assert any("tests/unit/unlisted.py" in error for error in errors)

    write_record(
        f"| src/jev_judge_mcp/cache.py | {digest} | unchanged |\n"
        "| tests/unit/missing.py | " + "0" * 64 + " | unchanged |"
    )
    errors = _record_errors(record_path, source_root, upstream_root)
    assert any("tests/unit/missing.py" in error for error in errors)
