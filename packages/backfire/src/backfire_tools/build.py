"""Build a code plugin containing the Backfire runtime package."""

import os
import shutil
import signal
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MAX_BYTES = 16 * 1024 * 1024


def refuse_existing(output: Path) -> None:
    try:
        output.lstat()
    except FileNotFoundError:
        return
    raise FileExistsError(f"Output already exists: {output}")


def build(output: str | Path) -> Path:
    output = Path(os.path.abspath(output))
    refuse_existing(output)
    destination = output.parent.resolve(strict=True) / output.name
    for path in (output, destination):
        if any(path.is_relative_to(ROOT / name) for name in ("plugins", "packages")):
            raise ValueError(f"Output must be outside plugins/ and packages/: {output}")
    output = destination
    try:
        budget = int(os.environ.get("BACKFIRE_TEST_BUILD_MAX_BYTES", MAX_BYTES))
    except ValueError:
        budget = -1
    if not 0 <= budget <= MAX_BYTES:
        raise ValueError(f"BACKFIRE_TEST_BUILD_MAX_BYTES must be between 0 and {MAX_BYTES}")

    interrupted = False
    total = 0
    partial = None

    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True

    def check_source(source: Path):
        if interrupted:
            raise InterruptedError("Build interrupted")
        info = source.lstat()
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"Source symbolic link is not allowed: {source}")
        return info

    def copy_file(source, target):
        nonlocal total
        info = check_source(Path(source))
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Source is not a regular file or directory: {source}")
        total += info.st_size
        if total > budget:
            raise ValueError(f"Build exceeds {budget}-byte budget: {source}")
        return shutil.copy2(source, target)

    def copy_tree(source: Path, target: Path, *, exclude_cache=False):
        check_source(source)

        def walk_failed(error):
            raise error

        for directory, directories, files in os.walk(source, onerror=walk_failed):
            directory = Path(directory)
            if exclude_cache:
                directories[:] = [name for name in directories if name != "__pycache__"]
                files = [name for name in files if name != "__pycache__"]
            destination = target / directory.relative_to(source)
            destination.mkdir(parents=True, exist_ok=True)
            for name in directories:
                check_source(directory / name)
            for name in files:
                copy_file(directory / name, destination / name)

    previous = {
        signum: signal.signal(signum, interrupt)
        for signum in (signal.SIGINT, signal.SIGTERM)
    }
    try:
        partial = Path(tempfile.mkdtemp(dir=output.parent, prefix=f"{output.name}.partial-"))
        copy_tree(ROOT / "plugins/code", partial)
        package = ROOT / "packages/backfire"
        runtime = partial / "backfire"
        runtime.mkdir()
        for path in ("pyproject.toml", ".python-version", "uv.lock"):
            copy_file(package / path, runtime / path)
        copy_tree(package / "src/backfire", runtime / "src/backfire", exclude_cache=True)
        if interrupted:
            raise InterruptedError("Build interrupted")
        refuse_existing(output)
        partial.rename(output)
        partial = None
        return output
    finally:
        try:
            if partial is not None:
                shutil.rmtree(partial)
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--"]:
        args = args[1:]
    try:
        if len(args) != 1 or not args[0]:
            raise ValueError("Usage: deno task backfire:build -- <output>")
        print(build(args[0]))
        return 0
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
