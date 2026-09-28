"""Run the pinned MemoryLint audit from its bounded cache."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
from urllib.request import urlopen
import zipfile


VERSION = "1.5.1"
URL = (
    "https://github.com/RbBtSn0w/spec-kit-extensions/releases/download/"
    "memorylint-v1.5.1/memorylint.zip"
)
SHA256 = "df4b31049dcd7f794e7bbed1460b5f5f5008b12a966939366e354926bb5f6648"
BUDGET = 1024 * 1024


def verify_hash(archive, sha256):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != sha256:
        raise ValueError("MemoryLint archive SHA-256 mismatch")


def install(cache, url, sha256):
    cache.parent.mkdir(parents=True, exist_ok=True)
    for leftover in cache.parent.glob(f".{VERSION}-*"):
        if leftover.is_dir() and not leftover.is_symlink():
            shutil.rmtree(leftover)
        else:
            leftover.unlink()
    if cache.exists():
        size = sum(
            path.stat().st_size for path in cache.rglob("*") if path.is_file()
        )
        if size > BUDGET:
            raise ValueError("MemoryLint cache exceeds the 1 MiB limit")
        verify_hash(cache / "archive.zip", sha256)
        return

    def interrupted(signum, frame):
        raise SystemExit(128 + signum)

    handlers = {
        number: signal.getsignal(number)
        for number in (signal.SIGINT, signal.SIGTERM)
    }
    temporary = None
    try:
        for number in handlers:
            signal.signal(number, interrupted)
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{VERSION}-", dir=cache.parent)
        )
        archive = temporary / "archive.zip"
        size = 0
        with urlopen(url) as response, archive.open("wb") as output:
            while chunk := response.read(65536):
                if size + len(chunk) > BUDGET:
                    raise ValueError(
                        "MemoryLint download exceeds the 1 MiB limit"
                    )
                output.write(chunk)
                size += len(chunk)
        verify_hash(archive, sha256)
        with zipfile.ZipFile(archive) as source:
            for entry in source.infolist():
                path = Path(entry.filename)
                file_type = (entry.external_attr >> 16) & 0o170000
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or path == Path("archive.zip")
                    or file_type == 0o120000
                ):
                    raise ValueError(f"Unsafe archive path: {entry.filename}")
                if size + entry.file_size > BUDGET:
                    raise ValueError(
                        "MemoryLint extraction exceeds the 1 MiB limit"
                    )
                source.extract(entry, temporary)
                size += entry.file_size
        temporary.rename(cache)
    finally:
        if temporary is not None and temporary.exists():
            shutil.rmtree(temporary)
        for number, handler in handlers.items():
            signal.signal(number, handler)


def audit(root, report_only, *, url=URL, sha256=SHA256):
    root = Path(root).resolve()
    cache_home = Path(
        os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    )
    cache = cache_home / "verbose-broccoli" / "memorylint" / VERSION
    install(cache, url, sha256)
    scripts = list(cache.glob("**/scripts/audit_workspace.py"))
    if len(scripts) != 1:
        raise ValueError(
            "MemoryLint archive must contain one scripts/audit_workspace.py"
        )
    result = subprocess.run(
        [sys.executable, "-B", str(scripts[0]), str(root), "--format", "json"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    findings = json.loads(result.stdout)["findings"]
    selected = [
        finding
        for finding in findings
        if any(
            source.rsplit(":", 1)[0] in report_only
            for source in finding["source"].split(" + ")
        )
    ]
    return {
        "memorylint": {
            "version": VERSION,
            "sha256": sha256,
            "findings": selected,
        }
    }
