"""Build a plugin with its selected Backfire packages and profile."""

import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
MAX_BYTES = 16 * 1024 * 1024
PLUGINS = {
    "code": (("backfire", "jev_judge_mcp"), "backfire/config.toml", ()),
    "work": (
        ("backfire", "backfire_education", "jev_judge_mcp"),
        "backfire_education/config.toml",
        ("doc-regions", "wiki-consistency"),
    ),
}


def refuse_existing(output: Path) -> None:
    """Raise when the requested output path already exists."""
    try:
        output.lstat()
    except FileNotFoundError:
        return
    raise FileExistsError(f"Output already exists: {output}")


def lock_copy(
    project: str, directory: Path, *, extra: tuple[str, ...] = ()
) -> None:
    """Create an offline lock for a copied project."""
    exported = subprocess.run(
        [
            "uv",
            "export",
            "--package",
            project,
            "--frozen",
            "--no-hashes",
            "--no-emit-workspace",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if exported.returncode:
        raise ValueError(
            exported.stderr.strip() or f"uv export failed for {project}"
        )
    pins = [
        line.strip()
        for line in exported.stdout.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    pyproject = directory / "pyproject.toml"
    original = pyproject.read_bytes()
    setting = f"constraint-dependencies = {json.dumps(pins)}\n".encode()
    lines = original.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith(b"constraint-dependencies ="):
            lines[index] = setting
            break
    else:
        section = b"[tool.uv]\n"
        try:
            index = lines.index(section) + 1
        except ValueError as error:
            raise ValueError(f"Missing [tool.uv] in {pyproject}") from error
        lines.insert(index, setting)
    pyproject.write_bytes(b"".join(lines))
    try:
        result = subprocess.run(
            ["uv", "lock", "--offline"],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise ValueError(
                result.stderr.strip() or f"uv lock failed for {project}"
            )
    finally:
        pyproject.write_bytes(original)


def build(output: str | Path, *, plugin: str = "code") -> Path:
    """Build the selected plugin and runtime packages in the output path."""
    if plugin not in PLUGINS:
        raise ValueError(
            f"Unknown plugin: {plugin}; known plugins: {', '.join(PLUGINS)}"
        )
    packages, profile, projects = PLUGINS[plugin]
    output = Path(os.path.abspath(output))
    refuse_existing(output)
    destination = output.parent.resolve(strict=True) / output.name
    for path in (output, destination):
        if any(
            path.is_relative_to(ROOT / name) for name in ("plugins", "packages")
        ):
            raise ValueError(
                f"Output must be outside plugins/ and packages/: {output}"
            )
    output = destination
    try:
        budget = int(os.environ.get("BACKFIRE_TEST_BUILD_MAX_BYTES", MAX_BYTES))
    except ValueError:
        budget = -1
    if not 0 <= budget <= MAX_BYTES:
        raise ValueError(
            f"BACKFIRE_TEST_BUILD_MAX_BYTES must be between 0 and {MAX_BYTES}"
        )

    interrupted = False
    total = 0
    partial = None

    def interrupt(signum, frame):
        del signum, frame  # Unused.
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
            raise ValueError(
                f"Source is not a regular file or directory: {source}"
            )
        total += info.st_size
        if total > budget:
            raise ValueError(f"Build exceeds {budget}-byte budget: {source}")
        return shutil.copy2(source, target)

    def copy_tree(
        source: Path, target: Path, *, runtime_package=False, exclude=()
    ):
        check_source(source)
        excluded = set(exclude)
        if runtime_package:
            excluded.add("__pycache__")

        def walk_failed(error):
            raise error

        for directory, directories, files in os.walk(
            source, onerror=walk_failed
        ):
            directory = Path(directory)
            directories[:] = [
                name for name in directories if name not in excluded
            ]
            files = [name for name in files if name not in excluded]
            if runtime_package and directory == source:
                files = [name for name in files if name != "config.toml"]
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
        partial = Path(
            tempfile.mkdtemp(
                dir=output.parent, prefix=f"{output.name}.partial-"
            )
        )
        copy_tree(ROOT / "plugins" / plugin, partial)
        package = ROOT / "packages/backfire"
        runtime = partial / "backfire"
        runtime.mkdir()
        for path in ("pyproject.toml", ".python-version"):
            copy_file(package / path, runtime / path)
        pyproject = runtime / "pyproject.toml"
        content = pyproject.read_bytes()
        modules = (
            b'module-name = ["backfire", "backfire_tools", '
            b'"backfire_education", "jev_judge_mcp"]'
        )
        module_list = ", ".join('"' + name + '"' for name in packages)
        replacement = f"module-name = [{module_list}]".encode()
        updated = content.replace(modules, replacement, 1)
        if updated == content:
            raise ValueError(
                "Could not select copied backfire modules in pyproject.toml"
            )
        pyproject.write_bytes(updated)
        for name in packages:
            copy_tree(
                package / "src" / name,
                runtime / "src" / name,
                runtime_package=True,
            )
        copy_file(
            package / "src" / profile, runtime / "src/backfire/config.toml"
        )
        for name in projects:
            copy_tree(
                ROOT / "packages" / name,
                partial / name,
                exclude=(
                    ".venv",
                    "node_modules",
                    "__pycache__",
                    ".pytest_cache",
                    "tests",
                ),
            )
        lock_copy(
            "backfire",
            runtime,
            extra=("--extra", "education") if plugin == "work" else (),
        )
        for name in projects:
            copied = partial / name
            if name == "wiki-consistency":
                pyproject = copied / "pyproject.toml"
                content = pyproject.read_text(encoding="utf-8")
                for dependency in ("doc-regions", "backfire"):
                    source = f"{dependency} = {{ workspace = true }}"
                    if source not in content:
                        raise ValueError(
                            "Could not replace workspace source in copied "
                            "wiki-consistency pyproject.toml"
                        )
                    content = content.replace(
                        source,
                        (
                            f'{dependency} = {{ path = "../{dependency}", '
                            "editable = true }"
                        ),
                        1,
                    )
                pyproject.write_text(content, encoding="utf-8")
            lock_copy(name, copied)
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
    """Parse build arguments and return the command's exit status."""
    args = sys.argv[1:]
    if args[:1] == ["--"]:
        args = args[1:]
    try:
        if len(args) != 2 or not all(args):
            raise ValueError(
                "Usage: npm run backfire:build -- <plugin> <output>"
            )
        print(build(args[1], plugin=args[0]))
        return 0
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
