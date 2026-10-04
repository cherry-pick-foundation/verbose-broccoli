# /// script
# requires-python = ">=3.14"
# dependencies = ["bagit==1.9.0"]
# ///
"""Admit approved originals into immutable Wiki BagIt revisions."""

import argparse
from datetime import datetime
from datetime import timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from uuid import uuid7
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("bagit").disabled = True

# warning filters must run first.
import bagit  # noqa: E402

KINDS = ("web", "files", "notes", "assets")
OUTCOMES = ("admitted", "already_admitted", "refused", "failed")


def roots():
    """Return configured XDG storage roots for the work vault."""
    home = Path.home()
    storage = {}
    configured = {}
    for name, default in (
        ("data", ".local/share"),
        ("state", ".local/state"),
        ("cache", ".cache"),
        ("config", ".config"),
    ):
        path = Path(
            os.environ.get(f"XDG_{name.upper()}_HOME") or home / default
        )
        if not path.is_absolute():
            path = home / default
        configured[name] = Path(os.path.normpath(path / "verbose-broccoli"))
        storage[name] = configured[name].resolve()
    storage["configured"] = configured
    return storage


def wiki_name(value):
    """Validate a Wiki folder name."""
    if value in ("", ".", "..") or "/" in value or "\0" in value:
        raise argparse.ArgumentTypeError("wiki must be a single folder name")
    return value


def initialize(instance):
    """Create the Wiki folder layout and report created paths."""
    for name in ("index", "overview", "log"):
        legacy = instance / "wiki" / f"{name}.md"
        if legacy.exists() or legacy.is_symlink():
            raise ValueError(
                f"Wiki migration required: {legacy} must be migrated "
                "before initialization"
            )
    created = []
    for path in (
        instance,
        instance / "raw",
        *(instance / "raw" / kind for kind in KINDS),
        instance / "text",
        instance / "wiki",
    ):
        if not path.exists():
            path.mkdir(parents=True)
            created.append(str(path))
    files = {"AGENTS.md": None, ".gitignore": b"/raw/\n"}
    files.update(
        {f"wiki/{name}.qmd": b"" for name in ("index", "overview", "log")}
    )
    for name, content in files.items():
        path = instance / name
        if path.exists():
            continue
        if content is None:
            content = (
                Path(__file__).parent.parent / "assets" / "AGENTS.md"
            ).read_bytes()
        with path.open("xb") as target:
            target.write(content)
        created.append(str(path))
    if not (instance / ".git").exists():
        subprocess.run(
            ["git", "init", "--quiet", str(instance)],
            check=True,
            capture_output=True,
        )
        created.append(str(instance / ".git"))
    print(json.dumps({"created": created}))
    return 0


def sha256(path):
    """Return the SHA-256 digest of a file."""
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def remove_staging(path):
    """Remove a temporary staging tree and its contents."""
    if path.is_symlink() or not path.is_dir():
        if path.exists() or path.is_symlink():
            path.unlink()
        return
    for root, dirs, files in os.walk(path):
        folder = Path(root)
        folder.chmod(0o700)
        for name in dirs:
            child = folder / name
            if not child.is_symlink():
                child.chmod(0o700)
        for name in files:
            child = folder / name
            if not child.is_symlink():
                child.chmod(0o600)
    shutil.rmtree(path)


def latest_revision(raw, original):
    """Find the latest bag for an original file."""
    # ponytail: scan bags per item; build an in-memory run lookup if imports
    # grow slow.
    matches = {}
    for info in raw.glob("*/*/*/bag-info.txt"):
        bag = bagit.Bag(str(info.parent))
        if bag.info.get("Internal-Sender-Identifier") == str(original):
            matches.setdefault(info.parent.parent, []).append(bag)
    if len(matches) > 1:
        raise ValueError("multiple sources have this original path")
    if not matches:
        return None
    return max(
        next(iter(matches.values())), key=lambda bag: Path(bag.path).name
    )


def selection_items(selection):
    """Read and validate selected paths from a JSONL file."""
    items = [
        json.loads(line)
        for line in selection.read_text(encoding="utf-8").splitlines()
    ]
    seen = set()
    for item in items:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "kind"}
            or not isinstance(item["path"], str)
            or not Path(item["path"]).is_absolute()
            or item["kind"] not in KINDS
        ):
            raise ValueError(
                "invalid selection: expected an absolute path and a known kind"
            )
        if item["path"] in seen:
            raise ValueError("invalid selection: duplicate path")
        seen.add(item["path"])
    return items


def exclusions(storage):
    """Return normalized storage and configured exclusion roots."""
    config = storage["config"] / "config.toml"
    excluded = []
    if config.exists():
        with config.open("rb") as source:
            table = tomllib.load(source)
        for key in ("wiki", "raw_import"):
            table = table.get(key, {})
            if not isinstance(table, dict):
                raise ValueError(
                    "invalid configuration: wiki.raw_import must be a table"
                )
        excluded = table.get("exclude", [])
        if not isinstance(excluded, list) or any(
            not isinstance(path, str) or not Path(path).is_absolute()
            for path in excluded
        ):
            raise ValueError(
                "invalid configuration: exclude must be a list of "
                "absolute paths"
            )
    roots = [
        root
        for key in ("data", "state", "cache")
        for root in (storage["configured"][key], storage[key])
    ]
    for path in excluded:
        configured = Path(os.path.normpath(path))
        roots.extend((configured, configured.resolve()))
    return roots


def refusal(path, original, excluded):
    """Return why an original path must not be admitted, if any."""
    try:
        str(original).encode("utf-8")
    except UnicodeError:
        return "original path is not valid UTF-8"
    if path.is_symlink() or not path.is_file():
        return (
            "original is not a regular file (symbolic links are not admitted)"
        )
    listed = Path(os.path.normpath(path))
    if any(
        candidate.is_relative_to(root)
        for candidate in (listed, original)
        for root in excluded
    ):
        return "original is under an excluded location"
    return None


def admit_item(item, raw, run, excluded):
    """Admit one source file and return its outcome."""
    result = dict(
        path=item["path"],
        outcome="failed",
        source_id=None,
        revision=None,
        reason=None,
    )
    staged = run / str(uuid7())
    try:
        path = Path(item["path"])
        original = path.resolve()
        reason = refusal(path, original, excluded)
        if reason:
            result.update(outcome="refused", reason=reason)
            return result
        digest = sha256(original)
        modified = datetime.fromtimestamp(
            original.stat().st_mtime, timezone.utc
        )
        latest = latest_revision(raw, original)
        source_id = Path(latest.path).parent.name if latest else str(uuid7())
        if latest and Path(latest.path).parent.parent.name != item["kind"]:
            result.update(
                outcome="refused",
                reason=(
                    "source already belongs to kind "
                    f"{Path(latest.path).parent.parent.name}"
                ),
            )
            return result
        if (
            latest
            and latest.entries[f"data/{original.name}"]["sha256"] == digest
        ):
            result.update(
                outcome="already_admitted",
                source_id=source_id,
                revision=Path(latest.path).name,
            )
            return result
        revision = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        if latest and revision <= Path(latest.path).name:
            raise ValueError("new revision would not sort after the latest one")
        staged.mkdir()
        payload = staged / original.name
        shutil.copy2(original, payload)
        payload.chmod(payload.stat().st_mode | 0o600)
        provenance = {
            "External-Identifier": source_id,
            "Internal-Sender-Identifier": str(original),
            "Source-Modified": modified.isoformat(),
            "Admission-Time": revision,
        }
        bag = bagit.make_bag(
            str(staged), bag_info=provenance.copy(), checksums=["sha256"]
        )
        if any(bag.info.get(key) != value for key, value in provenance.items()):
            raise ValueError("provenance not preserved by bag-info.txt")
        bag.validate()
        if bag.entries[f"data/{original.name}"]["sha256"] != digest:
            raise ValueError("copied payload digest mismatch")
        destination = raw / item["kind"] / source_id / revision
        destination.parent.mkdir(parents=True, exist_ok=True)
        for path in staged.rglob("*"):
            path.chmod(0o555 if path.is_dir() else 0o444)
        staged.rename(destination)
        destination.chmod(0o555)
        result.update(
            outcome="admitted", source_id=source_id, revision=revision
        )
    # record failures per selected item.
    except Exception as error:  # noqa: BLE001
        result["reason"] = str(error)
    finally:
        if staged.exists():
            remove_staging(staged)
    return result


def admit(selection, instance, storage):
    """Admit selected files into immutable raw revisions."""
    items = selection_items(selection)
    excluded = exclusions(storage)
    counts = dict.fromkeys(OUTCOMES, 0)
    staging = storage["cache"] / "raw-import" / instance.name
    staging.mkdir(parents=True, exist_ok=True)
    run = staging / str(uuid7())
    run.mkdir()
    try:
        for item in items:
            result = admit_item(item, instance / "raw", run, excluded)
            counts[result["outcome"]] += 1
            print(json.dumps(result), flush=True)
    finally:
        shutil.rmtree(run)
    print(json.dumps({"summary": counts}))
    if counts["refused"] or counts["failed"]:
        print(
            f"{counts['refused']} refused, {counts['failed']} failed",
            file=sys.stderr,
        )
        return 1
    return 0


def verify(instance):
    """Validate every raw BagIt revision."""
    invalid = []
    revisions = sorted((instance / "raw").glob("*/*/*"))
    for revision in revisions:
        try:
            bagit.Bag(str(revision)).validate()
        # collect failures per revision.
        except Exception as error:  # noqa: BLE001
            invalid.append(
                {
                    "revision": str(revision.relative_to(instance)),
                    "reason": str(error),
                }
            )
    print(json.dumps({"count": len(revisions), "invalid": invalid}))
    if invalid:
        print(f"{len(invalid)} invalid revisions", file=sys.stderr)
        return 1
    return 0


def main():
    """Run the raw-import command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki", type=wiki_name, default="work")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "admit", "verify"):
        command = commands.add_parser(name)
        command.add_argument(
            "--wiki", type=wiki_name, default=argparse.SUPPRESS
        )
        if name == "admit":
            command.add_argument("--selection", type=Path, required=True)
    args = parser.parse_args()
    try:
        storage = roots()
        instance = storage["data"] / "vaults" / args.wiki
        if args.command == "init":
            return initialize(instance)
        if not (instance / "raw").is_dir():
            raise ValueError("Wiki instance is missing; run init first")
        if args.command == "verify":
            return verify(instance)
        return admit(args.selection, instance, storage)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
