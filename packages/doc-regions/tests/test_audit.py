import hashlib
import json
import os
import selectors
import signal
import subprocess
import sys
import zipfile

import pytest

from doc_regions import audit as audit_module
from doc_regions.__main__ import main
from doc_regions.audit import audit

FINDINGS = [
    dict(
        id="ML-022",
        drift_type="reality",
        source="AGENTS.md:3",
        evidence="missing: scripts/missing.py",
        suggested_action="rewrite",
    ),
    dict(
        id="ML-023",
        drift_type="boundary",
        source=".specify/memory/constitution.md:2",
        evidence="layout",
        suggested_action="review",
    ),
    dict(
        id="ML-024",
        drift_type="reality",
        source="docs/other.md:1",
        evidence="other",
    ),
]


def archive(tmp_path, script=None, extra=None):
    if script is None:
        script = (
            "import json, pathlib, sys\n"
            'assert sys.argv[2:] == ["--format", "json"]\n'
            'assert "scripts/missing.py" in '
            '(pathlib.Path(sys.argv[1]) / "AGENTS.md").read_text()\n'
            f"print({json.dumps(dict(findings=FINDINGS))!r})\n"
        )
    path = tmp_path / "memorylint.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr("scripts/audit_workspace.py", script)
        if extra:
            output.writestr(*extra)
    return path.as_uri(), hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def root(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "AGENTS.md").write_text("# Rules\n\nRead scripts/missing.py.\n")
    (root / ".specify/memory").mkdir(parents=True)
    (root / ".specify/memory/constitution.md").write_text("# Rules\nLayout\n")
    return root


@pytest.fixture
def cache(tmp_path, monkeypatch):
    location = tmp_path / "cache"
    monkeypatch.setenv("XDG_CACHE_HOME", str(location))
    return location / "verbose-broccoli/memorylint/1.5.1"


def test_hash_extract_run_filter_and_cache(root, cache, tmp_path, unchanged):
    url, digest = archive(tmp_path)
    report_only = ["AGENTS.md", ".specify/memory/constitution.md"]
    with unchanged(root):
        result = audit(root, report_only, url=url, sha256=digest)
    assert result == {
        "memorylint": {
            "version": "1.5.1",
            "sha256": digest,
            "findings": FINDINGS[:2],
        }
    }
    assert (cache / "scripts/audit_workspace.py").exists()
    assert (
        sum(p.stat().st_size for p in cache.rglob("*") if p.is_file())
        <= 1024 * 1024
    )
    (tmp_path / "memorylint.zip").unlink()
    with unchanged(root), unchanged(cache):
        assert audit(root, report_only, url=url, sha256=digest) == result
    assert not list(cache.parent.glob(".1.5.1-*"))


def test_combined_sources_keep_finding_if_any_source_is_report_only(
    root, cache, tmp_path, unchanged
):
    del cache  # Unused.
    findings = [
        dict(
            id="ML-025",
            drift_type="boundary",
            source="AGENTS.md:10-12 + .specify/memory/constitution.md:40-41",
            evidence="conflict",
            suggested_action="review",
        ),
        dict(
            id="ML-026",
            drift_type="redundancy",
            source="docs/other.md:1-2 + docs/third.md:3-4",
            evidence="duplicate",
            suggested_action="merge",
        ),
    ]
    script = (
        "import json\n" + f"print({json.dumps({'findings': findings})!r})\n"
    )
    url, digest = archive(tmp_path, script=script)
    with unchanged(root):
        result = audit(
            root,
            ["AGENTS.md", ".specify/memory/constitution.md"],
            url=url,
            sha256=digest,
        )
    assert result["memorylint"]["findings"] == findings[:1]


def test_wrong_hash_never_executes_and_cleans(
    root, cache, tmp_path, monkeypatch, unchanged
):
    url, _ = archive(tmp_path)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *unused_a, **unused_k: pytest.fail("must not execute"),
    )
    with unchanged(root), pytest.raises(ValueError, match="SHA-256"):
        audit(root, ["AGENTS.md"], url=url, sha256="0" * 64)
    assert not cache.exists()
    assert not list(cache.parent.glob(".1.5.1-*"))


@pytest.mark.parametrize(
    "extra",
    [
        ("big.bin", "x" * (1024 * 1024)),
        ("big.bin", os.urandom(1024 * 1024 + 1)),
    ],
)
def test_budget_before_download_or_extraction_write(
    root, cache, tmp_path, extra, unchanged
):
    url, digest = archive(tmp_path, extra=extra)
    with unchanged(root), pytest.raises(ValueError, match="1 MiB"):
        audit(root, ["AGENTS.md"], url=url, sha256=digest)
    assert not cache.exists()
    assert not list(cache.parent.glob(".1.5.1-*"))


@pytest.mark.parametrize("entry", ["../escape.py", "/escape.py"])
def test_zip_paths_cannot_escape_cache(root, cache, tmp_path, entry, unchanged):
    url, digest = archive(tmp_path, extra=(entry, "bad"))
    with unchanged(root), pytest.raises(ValueError, match="archive path"):
        audit(root, ["AGENTS.md"], url=url, sha256=digest)
    assert not cache.exists()
    assert not list(cache.parent.glob(".1.5.1-*"))


def test_failed_download_cleans_temporary_directory(
    root, cache, tmp_path, unchanged
):
    with unchanged(root), pytest.raises(OSError):
        audit(
            root,
            ["AGENTS.md"],
            url=(tmp_path / "absent.zip").as_uri(),
            sha256="0" * 64,
        )
    assert not cache.exists()
    assert not list(cache.parent.glob(".1.5.1-*"))


def test_script_failure_leaves_no_temporary_directory(
    root, cache, tmp_path, unchanged
):
    url, digest = archive(
        tmp_path, script='raise RuntimeError("failed audit")\n'
    )
    with unchanged(root), pytest.raises(subprocess.CalledProcessError):
        audit(root, ["AGENTS.md"], url=url, sha256=digest)
    assert not list(cache.parent.glob(".1.5.1-*"))


def test_next_run_removes_killed_run_leftovers(
    root, cache, tmp_path, unchanged
):
    leftover = cache.parent / ".1.5.1-killed"
    leftover.mkdir(parents=True)
    (leftover / "partial.zip").write_bytes(b"incomplete")
    url, digest = archive(tmp_path)
    with unchanged(root):
        audit(root, ["AGENTS.md"], url=url, sha256=digest)
    assert not leftover.exists()


def test_cli_audit_uses_config_and_prints_json(tmp_path, monkeypatch, capsys):
    (tmp_path / "target.md").write_text("target")
    (tmp_path / "AGENTS.md").write_text("report only")
    (tmp_path / "config.toml").write_text(
        'targets = ["target.md"]\nreport_only = ["AGENTS.md"]\n'
        'generators = "sources"\ngenerator_path = "scripts"\n'
    )
    expected = {
        "memorylint": {"version": "1.5.1", "sha256": "digest", "findings": []}
    }
    seen = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        audit_module,
        "audit",
        lambda root, report_only: seen.append((root, report_only)) or expected,
    )
    assert main(["audit", "config.toml"]) == 0
    assert seen == [(tmp_path, ["AGENTS.md"])]
    assert json.loads(capsys.readouterr().out) == expected


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_interrupt_cleans_download(root, cache, tmp_path, signum, unchanged):
    url, digest = archive(tmp_path)
    # Wait at a deterministic point after the staging directory has been
    # created.
    script = """
import contextlib, signal, sys
import doc_regions.audit as module
@contextlib.contextmanager
def wait_for_signal(*args, **kwargs):
    print("ready", flush=True)
    signal.pause()
    yield
module.urlopen = wait_for_signal
module.audit(sys.argv[1], ["AGENTS.md"], url=sys.argv[2], sha256=sys.argv[3])
"""
    with unchanged(root):
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", script, str(root), url, digest],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                assert selector.select(timeout=10), (
                    "child did not reach download"
                )
            assert child.stdout.readline().strip() == "ready"
            child.send_signal(signum)
            child.communicate(timeout=10)
            assert child.returncode != 0
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate()
    assert not cache.exists()
    assert not list(cache.parent.glob(".1.5.1-*"))
