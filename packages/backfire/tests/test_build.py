import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_FILES = ("pyproject.toml", ".python-version", "uv.lock")
MAX_BYTES = 16 * 1024 * 1024


def run_build(
    output: Path,
    source: Path = ROOT,
    *,
    plugin: str = "code",
    budget: str = str(MAX_BYTES),
):
    entry = (
        ["-m", "backfire_tools.build"]
        if source == ROOT
        else [str(source / "packages/backfire/src/backfire_tools/build.py")]
    )
    return subprocess.run(
        [sys.executable, *entry, "--", plugin, str(output)],
        env={**os.environ, "BACKFIRE_TEST_BUILD_MAX_BYTES": budget},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def tree(
    directory: Path, *, exclude: tuple[str, ...] = ()
) -> dict[str, bytes | None]:
    entries = {"": None}
    excluded = set(exclude)

    def walk_failed(error):
        raise error

    for current, directories, files in os.walk(directory, onerror=walk_failed):
        current = Path(current)
        directories[:] = [name for name in directories if name not in excluded]
        for name in directories:
            path = current / name
            assert not path.is_symlink(), f"Unexpected link: {path}"
            entries[path.relative_to(directory).as_posix()] = None
        for name in files:
            path = current / name
            assert not path.is_symlink(), f"Unexpected link: {path}"
            entries[path.relative_to(directory).as_posix()] = path.read_bytes()
    return entries


def no_output(output: Path) -> None:
    assert not os.path.lexists(output)
    assert not list(output.parent.glob(f"{output.name}.partial-*"))


@pytest.fixture
def source_repository(tmp_path: Path) -> Path:
    source = tmp_path / "repository"
    for path in ("plugins/code", "plugins/work", "packages/backfire/src"):
        shutil.copytree(
            ROOT / path,
            source / path,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    for path in PACKAGE_FILES:
        shutil.copy2(
            ROOT / "packages/backfire" / path,
            source / "packages/backfire" / path,
        )
    return source


@pytest.mark.parametrize("plugin", ["code", "work"])
def test_build_preserves_plugin_and_copies_only_runtime(
    tmp_path: Path, plugin: str
) -> None:
    output = tmp_path / plugin
    result = run_build(output, plugin=plugin)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{output}\n"
    assert result.stderr == ""
    projects = ("doc-regions", "wiki-consistency") if plugin == "work" else ()
    plugin_files = {
        path: contents
        for path, contents in tree(output).items()
        if path != "backfire"
        and not path.startswith("backfire/")
        and not any(
            path == name or path.startswith(f"{name}/") for name in projects
        )
    }
    assert plugin_files == tree(ROOT / "plugins" / plugin)

    package = ROOT / "packages/backfire"
    expected = {"": None, "src": None}
    for path in PACKAGE_FILES:
        expected[path] = (package / path).read_bytes()
    runtime_packages = (
        ("backfire",)
        if plugin == "code"
        else ("backfire", "backfire_education")
    )
    for name in runtime_packages:
        for path, contents in tree(package / "src" / name).items():
            if "__pycache__" not in Path(path).parts and path != "config.toml":
                expected[(Path("src") / name / path).as_posix()] = contents
    profile = package / "src" / runtime_packages[-1] / "config.toml"
    expected["src/backfire/config.toml"] = profile.read_bytes()
    assert tree(output / "backfire") == expected
    assert "src/backfire/__main__.py" in expected
    for path, contents in expected.items():
        if contents is not None:
            assert (output / "backfire" / path).stat().st_mode == (
                profile
                if path == "src/backfire/config.toml"
                else package / path
            ).stat().st_mode
    assert not os.path.lexists(ROOT / "plugins" / plugin / "backfire")
    for name in projects:
        source = ROOT / "packages" / name
        built = output / name
        assert tree(built) == tree(
            source,
            exclude=(
                ".venv",
                "node_modules",
                "__pycache__",
                ".pytest_cache",
                "tests",
            ),
        )
        for path in ("pyproject.toml", "uv.lock", "src"):
            assert (built / path).exists()
        assert not any(
            path.is_dir()
            and path.name
            in {".venv", "node_modules", "__pycache__", ".pytest_cache"}
            for path in built.rglob("*")
        )
        if name == "wiki-consistency":
            assert (built / "package.json").is_file()
            assert (built / "package-lock.json").is_file()
    if plugin == "code":
        assert not (output / "doc-regions").exists()
        assert not (output / "wiki-consistency").exists()
    assert list(tmp_path.iterdir()) == [output]


def test_built_work_plugin_runs_wiki_check_offline_without_checkout(
    tmp_path: Path,
) -> None:
    output = tmp_path / "work"
    assert not output.is_relative_to(ROOT)
    result = run_build(output, plugin="work")
    assert result.returncode == 0, result.stderr
    assert (output / "mcp.json").is_file()

    data_home = tmp_path / "data"
    cache_home = tmp_path / "cache"
    wiki_id = "build-test"
    instance = data_home / "verbose-broccoli" / "vaults" / wiki_id
    (instance / "wiki").mkdir(parents=True)
    (instance / "AGENTS.md").write_text(
        "---\ntopics: []\n---\n# Wiki rules\n", encoding="utf-8"
    )
    (instance / "wiki" / "index.md").write_text(
        "<!-- [[[cog import wiki_consistency.sources; "
        "cog.out(wiki_consistency.sources.page_catalog("
        '"wiki/**/*.md")) ]]] -->\n'
        "<!-- [[[end]]] -->\n",
        encoding="utf-8",
    )
    (instance / "wiki" / "overview.md").write_text("", encoding="utf-8")
    (instance / "wiki" / "log.md").write_text("", encoding="utf-8")
    subprocess.run(
        ["git", "init", "--quiet"],
        cwd=instance,
        check=True,
        capture_output=True,
    )

    uv_cache = subprocess.run(
        ["uv", "cache", "dir"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    env = {
        **os.environ,
        "UV_CACHE_DIR": uv_cache,
        "XDG_DATA_HOME": str(data_home),
        "XDG_CACHE_HOME": str(cache_home),
    }
    doc_regions = subprocess.run(
        [
            "uv",
            "sync",
            "--project",
            str(output / "doc-regions"),
            "--frozen",
            "--offline",
            "--no-dev",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert doc_regions.returncode == 0, doc_regions.stderr
    backfire = subprocess.run(
        [
            "uv",
            "sync",
            "--project",
            str(output / "backfire"),
            "--frozen",
            "--offline",
            "--no-dev",
            "--extra",
            "education",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert backfire.returncode == 0, backfire.stderr
    install = subprocess.run(
        [
            "uv",
            "sync",
            "--project",
            str(output / "wiki-consistency"),
            "--frozen",
            "--offline",
            "--no-dev",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert install.returncode == 0, install.stderr
    check = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(output / "wiki-consistency"),
            "--frozen",
            "--offline",
            "--no-sync",
            "wiki-consistency",
            "check",
            "--wiki",
            wiki_id,
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert check.returncode == 0, check.stderr


@pytest.mark.parametrize("plugin", ["chat", "unknown", "../code"])
def test_unknown_plugin_writes_nothing(tmp_path: Path, plugin: str) -> None:
    output = tmp_path / "output"
    result = run_build(output, plugin=plugin)
    assert result.returncode == 1
    assert (
        f"Unknown plugin: {plugin}; known plugins: code, work" in result.stderr
    )
    no_output(output)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "args",
    [[], ["code"], ["output"], ["code", "output", "extra"], ["", "output"]],
)
def test_build_requires_plugin_and_output(
    tmp_path: Path, args: list[str]
) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "backfire_tools.build", *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 1
    assert (
        result.stderr
        == "Usage: deno task backfire:build -- <plugin> <output>\n"
    )
    assert list(tmp_path.iterdir()) == []


def test_build_excludes_development_files_and_caches(
    tmp_path: Path, source_repository: Path
) -> None:
    excluded = (
        "src/backfire/__pycache__/compiled.pyc",
        "src/backfire/nested/__pycache__/compiled.pyc",
        "src/backfire_tools/acceptance/example.py",
        "src/backfire.egg-info/PKG-INFO",
        "tests/test_example.py",
        ".venv/example",
    )
    for path in excluded:
        target = source_repository / "packages/backfire" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("excluded")
    output = tmp_path / "code"
    result = run_build(output, source_repository)
    assert result.returncode == 0, result.stderr
    for path in (*excluded, "src/backfire_tools"):
        assert not os.path.lexists(output / "backfire" / path)
    assert not any(
        "__pycache__" in Path(path).parts for path in tree(output / "backfire")
    )


@pytest.mark.parametrize("kind", ["file", "directory", "symlink"])
def test_build_refuses_existing_output(tmp_path: Path, kind: str) -> None:
    output = tmp_path / "code"
    if kind == "file":
        output.write_text("keep")
    elif kind == "directory":
        output.mkdir()
        (output / "keep").write_text("keep")
    else:
        output.symlink_to(tmp_path / "missing")
    result = run_build(output)
    assert result.returncode == 1
    assert "Output already exists" in result.stderr
    assert list(tmp_path.iterdir()) == [output]
    if kind == "file":
        assert output.read_text() == "keep"
    elif kind == "directory":
        assert tree(output) == {"": None, "keep": b"keep"}
    else:
        assert output.readlink() == tmp_path / "missing"


@pytest.mark.parametrize("parent", ["plugins", "packages"])
def test_build_refuses_outputs_in_source_packages(
    tmp_path: Path, source_repository: Path, parent: str
) -> None:
    alias = tmp_path / parent
    alias.symlink_to(source_repository / parent, target_is_directory=True)
    for directory in (source_repository / parent, alias):
        output = directory / "new-output"
        result = run_build(output, source_repository)
        assert result.returncode == 1
        assert "Output must be outside" in result.stderr
        no_output(output)


@pytest.mark.parametrize(
    "directory", ["plugins/code", "packages/backfire/src/backfire"]
)
@pytest.mark.parametrize("kind", ["file", "directory", "dangling"])
def test_build_rejects_source_links_and_keeps_unrelated_partial(
    tmp_path: Path, source_repository: Path, directory: str, kind: str
) -> None:
    link = source_repository / directory / "link"
    targets = {
        "file": source_repository / "plugins/code/plugin.json",
        "directory": source_repository / "plugins/code",
        "dangling": tmp_path / "missing",
    }
    link.symlink_to(targets[kind], target_is_directory=kind == "directory")
    unrelated = tmp_path / "other.partial-keep"
    unrelated.mkdir()
    (unrelated / "keep").write_text("keep")
    output = tmp_path / "code"
    result = run_build(output, source_repository)
    assert result.returncode == 1
    assert f"Source symbolic link is not allowed: {link}" in result.stderr
    no_output(output)
    assert tree(unrelated) == {"": None, "keep": b"keep"}


def test_build_over_budget_cleans_partial(tmp_path: Path) -> None:
    output = tmp_path / "code"
    result = run_build(output, budget="1")
    assert result.returncode == 1
    assert "Build exceeds 1-byte budget" in result.stderr
    no_output(output)


@pytest.mark.parametrize("exceed_budget", [False, True])
def test_read_only_source_directory_does_not_prevent_build_or_cleanup(
    tmp_path: Path, source_repository: Path, exceed_budget: bool
) -> None:
    directory = source_repository / "plugins/code"
    budget = str(
        sum(
            path.stat().st_size
            for path in directory.rglob("*")
            if path.is_file()
        )
    )
    directory.chmod(0o555)
    output = tmp_path / "code"
    try:
        result = run_build(
            output,
            source_repository,
            budget=budget if exceed_budget else str(MAX_BYTES),
        )
        if exceed_budget:
            assert result.returncode == 1
            assert f"Build exceeds {budget}-byte budget" in result.stderr
            no_output(output)
        else:
            assert result.returncode == 0, result.stderr
    finally:
        directory.chmod(0o755)


@pytest.mark.parametrize("budget", ["-1", str(MAX_BYTES + 1), "1.5", "invalid"])
def test_build_refuses_invalid_budget(tmp_path: Path, budget: str) -> None:
    output = tmp_path / "code"
    result = run_build(output, budget=budget)
    assert result.returncode == 1
    assert (
        f"BACKFIRE_TEST_BUILD_MAX_BYTES must be between 0 and {MAX_BYTES}"
        in result.stderr
    )
    no_output(output)


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_interruption_during_copy_cleans_partial(
    tmp_path: Path, signum: int
) -> None:
    output = tmp_path / "code"
    script = f"""
import signal
import threading
from backfire_tools import build

copy = build.shutil.copy2
def pause_copy(source, destination):
    result = copy(source, destination)
    received = threading.Event()
    handler = signal.getsignal({int(signum)})
    def resume(signum, frame):
        handler(signum, frame)
        received.set()
    signal.signal({int(signum)}, resume)
    print("copy-paused", flush=True)
    if not received.wait(10):
        raise TimeoutError("Test did not send the signal")
    return result

build.shutil.copy2 = pause_copy
raise SystemExit(build.main())
"""
    with subprocess.Popen(
        [sys.executable, "-c", script, "code", str(output)],
        env={**os.environ, "BACKFIRE_TEST_BUILD_MAX_BYTES": str(MAX_BYTES)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as child:
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=10), (
                    "Build did not reach the copy"
                )
            assert child.stdout.readline() == "copy-paused\n"
            assert list(tmp_path.glob("code.partial-*"))
            child.send_signal(signum)
            _, stderr = child.communicate(timeout=10)
            assert child.returncode == 1, stderr
            assert "Build interrupted" in stderr
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=10)
    no_output(output)
