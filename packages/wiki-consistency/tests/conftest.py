"""Fixtures for synthetic Wiki consistency tests."""

import hashlib
from pathlib import Path
import socket
import subprocess
import sys
import warnings

import bagit
import pytest

from doc_regions.config import files
from doc_regions.regions import update

sys.dont_write_bytecode = True

SOURCE_ID = "0199a0e2-7c1b-7d3e-9f00-000000000000"
REVISIONS = ("20260927T000000000000Z", "20260928T000000000000Z")
INDEX = (
    "<!-- [[[cog import wiki_consistency.sources; "
    'cog.out(wiki_consistency.sources.page_catalog("wiki/**/*.qmd")) ]]] -->\n'
    "<!-- [[[end]]] -->\n"
)


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    """Block network access, bytecode writes and user config in each test."""
    real_socket = socket.socket

    def blocked(family=socket.AF_INET, *args, **kwargs):
        if family != socket.AF_UNIX:
            raise AssertionError("network access is forbidden")
        return real_socket(family, *args, **kwargs)

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=DeprecationWarning, module=r"bagit"
        )
        yield


def add_revision(instance, revision, content, *, source_id=SOURCE_ID):
    """Create a BagIt revision with synthetic document content."""
    path = instance / "raw" / "files" / source_id / revision
    path.mkdir(parents=True)
    (path / "document.txt").write_text(content, encoding="utf-8")
    bagit.make_bag(
        str(path),
        bag_info={
            "External-Identifier": source_id,
            "Internal-Sender-Identifier": "/synthetic/document.txt",
            "Source-Modified": "2026-09-26T12:34:56+00:00",
            "Admission-Time": revision,
            "Bagging-Date": "2026-09-28",
        },
        checksums=["sha256"],
    )
    return path


def _page(title, summary, revision, body="", topics=("Algebra",)):
    return (
        f"---\ntitle: {title}\nsummary: {summary}\ntopics:\n"
        + "".join(f"  - {topic}\n" for topic in topics)
        + "sources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {revision}\n---\n{body}"
    )


def replace_page_topics(page, field):
    """Replace a synthetic page's topics field with the given text."""
    text = page.read_text(encoding="utf-8")
    start = text.index("topics:\n")
    end = text.index("sources:\n", start)
    page.write_text(text[:start] + field + text[end:], encoding="utf-8")


def make_instance(tmp_path, *, wiki_id="work", commit=False):
    """Create a synthetic Wiki instance and its isolated environment."""
    home = tmp_path / "home"
    data_home = tmp_path / "xdg-data"
    cache_home = tmp_path / "xdg-cache"
    env = {
        "HOME": str(home),
        "XDG_DATA_HOME": str(data_home),
        "XDG_CACHE_HOME": str(cache_home),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg-config"),
    }
    instance = data_home / "verbose-broccoli" / "vaults" / wiki_id
    (instance / "wiki" / "concepts").mkdir(parents=True)
    (instance / "wiki" / "sources").mkdir(parents=True)
    (instance / "raw").mkdir()
    (instance / "AGENTS.md").write_text(
        "---\ntopics:\n  - Algebra\n  - Reference\n  - Unused\n---\n"
        "Synthetic Wiki schema.\n",
        encoding="utf-8",
    )
    (instance / ".gitignore").write_text("/raw/\n", encoding="utf-8")
    (instance / "wiki" / "index.qmd").write_text(INDEX, encoding="utf-8")
    (instance / "wiki" / "overview.qmd").write_text(
        "# Overview\n\nSee [alpha](concepts/alpha.qmd).\n", encoding="utf-8"
    )
    (instance / "wiki" / "log.qmd").write_text(
        "## [2026-09-28] raw-import | synthetic\n\n1 admitted.\n",
        encoding="utf-8",
    )
    add_revision(instance, REVISIONS[0], "first synthetic revision\n")
    add_revision(instance, REVISIONS[1], "latest synthetic revision\n")
    (instance / "wiki" / "concepts" / "alpha.qmd").write_text(
        _page(
            "Alpha",
            "A synthetic page.",
            REVISIONS[-1],
            "# Alpha\n\nSee [the source](../sources/source.qmd).\n",
        ),
        encoding="utf-8",
    )
    region = (
        "<!-- [[[cog import wiki_consistency.sources; "
        f"cog.out(wiki_consistency.sources.source_provenance("
        f'"raw/files/{SOURCE_ID}/*/bag-info.txt", '
        f'"raw/files/{SOURCE_ID}/*/manifest-sha256.txt")) ]]] -->\n'
        "<!-- [[[end]]] -->\n"
    )
    (instance / "wiki" / "sources" / "source.qmd").write_text(
        _page(
            "Source",
            "A synthetic source.",
            REVISIONS[-1],
            region,
            topics=("Reference",),
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "init", "--quiet", str(instance)],
        check=True,
        text=True,
        capture_output=True,
    )
    if commit:
        commit_instance(instance)
    return instance, env


def commit_instance(instance):
    """Commit the synthetic pages of a Wiki instance."""
    subprocess.run(
        ["git", "add", "AGENTS.md", ".gitignore", "wiki"],
        cwd=instance,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Synthetic",
            "-c",
            "user.email=synthetic@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "synthetic instance",
        ],
        cwd=instance,
        check=True,
        text=True,
        capture_output=True,
    )


def update_regions(instance):
    """Regenerate source regions for the synthetic Wiki."""
    targets = [
        path.relative_to(instance).as_posix()
        for path in files(instance, "wiki/**/*.qmd")
    ]
    generators = Path(__file__).parents[1] / "src"
    return update(instance, targets, "wiki_consistency.sources", generators)


def tree_hash(root):
    """Return a deterministic hash of a tree's paths and bytes."""
    root = Path(root)
    if not root.exists():
        return None
    digest = hashlib.sha256()
    for path in (root, *sorted(root.rglob("*"))):
        relative = "." if path == root else path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8") + b"\0")
        if path.is_symlink():
            digest.update(b"l" + path.readlink().as_posix().encode("utf-8"))
        elif path.is_dir():
            digest.update(b"d")
        else:
            digest.update(b"f" + path.read_bytes())
    return digest.hexdigest()
