import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

import doc_regions.regions as regions
from doc_regions.regions import check
from doc_regions.regions import update

CODE = 'import sources; cog.out(sources.render("source.txt"))'


def region(code=CODE, output="fresh\n"):
    return f"<!-- [[[cog {code} ]]] -->\n{output}<!-- [[[end]]] -->\n"


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    generators = tmp_path / "generators"
    generators.mkdir()
    (generators / "sources.py").write_text(
        "from pathlib import Path\n"
        "def render(source):\n"
        "    return Path(source).read_text()\n"
    )
    (root / "source.txt").write_text("fresh\n")
    (root / "doc.md").write_text(
        "# Title\n\nBefore.\n\n" + region() + "\nAfter.\n"
    )
    return root, ["doc.md"], "sources", generators


def test_current_region_is_read_only_and_root_relative(workspace, unchanged):
    with unchanged(workspace[0].parent):
        assert check(*workspace) == []


@pytest.mark.parametrize(
    "separator", ["\u2028", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85"]
)
def test_cog_marker_line_counts_only_lf_breaks(workspace, separator, unchanged):
    root = workspace[0]
    (root / "doc.md").write_text(
        f"Paragraph{separator}continues.\n<!-- [[[end]]] -->\n"
    )
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems[0]["line"] == 2


def test_stale_has_cog_diff_line_and_update_command(workspace, unchanged):
    root = workspace[0]
    (root / "source.txt").write_text("new\n")
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems
    assert problems[0]["document"] == "doc.md"
    assert problems[0]["line"] == 5
    assert "-fresh" in problems[0]["message"]
    assert "+new" in problems[0]["message"]
    assert "npm run doc-regions:update" in problems[0]["message"]


def test_stale_names_caller_supplied_update_command(workspace, unchanged):
    root = workspace[0]
    (root / "source.txt").write_text("new\n")
    with unchanged(root.parent):
        problems = check(*workspace, fix_command="wiki-consistency update")
    assert problems
    assert "Run wiki-consistency update" in problems[0]["message"]


@pytest.mark.parametrize(
    "text, message",
    [
        (region().replace("<!-- [[[end]]] -->\n", ""), "unclosed"),
        ("<!-- [[[end]]] -->\n", "end"),
        (region(output=region()), "nested"),
        (region('print("bad")'), "shape"),
        (
            region('import sources; cog.out(sources.unknown("source.txt"))'),
            "unknown",
        ),
        (
            region(
                'import sources; cog.out(sources.render(source="source.txt"))'
            ),
            "shape",
        ),
        (
            region('import sources; cog.out(sources.render("missing.txt"))'),
            "missing.txt",
        ),
        (
            region('import sources; cog.out(sources.render("../outside.txt"))'),
            "root-relative",
        ),
        (
            region('import sources; cog.out(sources._private("source.txt"))'),
            "shape",
        ),
        (
            region(
                'import sources as other; cog.out(sources.render("source.txt"))'
            ),
            "shape",
        ),
        ("`" + region().splitlines()[0] + "`\n", "malformed"),
    ],
)
def test_bad_region_names_document_and_line(
    workspace, text, message, unchanged
):
    root = workspace[0]
    (root / "doc.md").write_text(text)
    with unchanged(root.parent):
        problems = check(*workspace)
    assert any(message in p["message"] for p in problems), problems
    assert all(p["document"] == "doc.md" and p["line"] >= 1 for p in problems)


@pytest.mark.parametrize(
    "text, broken",
    [
        ("[missing](missing.md)\n", True),
        ("# Title\n\n[missing](#no-heading)\n", True),
        ("# Title\n\n[valid](#title)\n", False),
        ("[external](https://does-not-exist.invalid/foo)\n", False),
    ],
)
def test_lychee_offline_links(workspace, text, broken, unchanged):
    root = workspace[0]
    (root / "doc.md").write_text(text)
    with unchanged(root.parent):
        problems = check(*workspace)
    assert bool(problems) == broken
    if broken:
        assert "missing" in str(problems) or "no-heading" in str(problems)


@pytest.mark.parametrize(
    "target, broken",
    [
        ("existing file.txt", False),
        ("existing doc.md#existing-heading", False),
        ("missing file.txt", True),
        ("existing doc.md#missing-heading", True),
        ("/missing-root-relative.md", True),
    ],
)
def test_lychee_absolute_local_links(workspace, target, broken, unchanged):
    root = workspace[0]
    outside = root.parent / "linked files"
    outside.mkdir()
    (outside / "existing file.txt").write_text("exists\n")
    (outside / "existing doc.md").write_text("# Existing heading\n")
    target = target if target.startswith("/") else outside / target
    (root / "doc.md").write_text(f"[text](<{target}>)\n")
    with unchanged(root.parent):
        problems = check(*workspace)
    assert bool(problems) == broken


def test_update_changes_only_output_and_is_idempotent(workspace):
    root = workspace[0]
    original = (root / "doc.md").read_bytes()
    (root / "source.txt").write_text("changed\n")
    assert update(*workspace) == []
    updated = (root / "doc.md").read_bytes()
    assert updated == original.replace(b"fresh\n", b"changed\n")
    assert update(*workspace) == []
    assert (root / "doc.md").read_bytes() == updated


@pytest.mark.parametrize(
    "target, broken",
    (
        ("../../text/source/target.qmd#natural-heading", False),
        ("../../text/source/target.qmd#sec-custom", False),
        ("#self-heading", False),
        ("../../text/source/space%20target.qmd#natural-heading", False),
        ("original-uri", False),
        ("../plain.md#plain-heading", False),
        ("../original.txt", False),
        ("https://does-not-exist.invalid/external.qmd", False),
        ("../../text/source/missing.qmd", True),
        ("../../text/source/target.qmd#absent-heading", True),
        ("#absent-self-heading", True),
    ),
)
def test_real_lychee_qmd_views_preserve_bytes_and_original_references(
    workspace, unchanged, monkeypatch, target, broken
):
    root, _, module, generators = workspace
    (root / "wiki/concepts").mkdir(parents=True)
    (root / "text/source").mkdir(parents=True)
    body = b"# Natural heading\r\n\r\n## Explicit {#sec-custom}\r\n"
    for name in ("target.qmd", "space target.qmd"):
        (root / "text/source" / name).write_bytes(body)
    original = root / "text/source/target.qmd"
    (root / "wiki/plain.md").write_text("# Plain heading\n")
    (root / "wiki/original.txt").write_text("Original bytes.\n")
    if target == "original-uri":
        target = original.as_uri() + "#natural-heading"
    document = "wiki/concepts/source.qmd"
    (root / document).write_bytes(
        f"# Self heading\r\n\r\n[Link]({target})\r\n".encode()
    )
    originals = {
        path: path.read_bytes() for path in root.rglob("*") if path.is_file()
    }
    hashes = {
        path: hashlib.sha256(data).hexdigest()
        for path, data in originals.items()
    }
    real_run = regions.run
    views = []

    def capture(directory, arguments):
        if arguments[0] == "lychee":
            view = Path(arguments[-1])
            views.append(view)
            assert view.read_bytes() == originals[root / document]
            assert (
                arguments[arguments.index("--base-url") + 1]
                == (root / document).as_uri()
            )
            remaps = [
                arguments[index + 1]
                for index, option in enumerate(arguments)
                if option == "--remap"
            ]
            assert len(remaps) == 2 and all(
                item.startswith("^file://") for item in remaps
            )
            view_root = view.parents[2]
            assert (view_root / "text/source/target.md").read_bytes() == body
            assert (
                view_root / "text/source/space target.md"
            ).read_bytes() == body
        return real_run(directory, arguments)

    monkeypatch.setattr(regions, "run", capture)
    with unchanged(root.parent):
        problems = check(
            root,
            [document],
            module,
            generators,
            link_view_roots=("wiki", "text"),
        )
    assert bool(problems) == broken, problems
    assert views and all(not view.exists() for view in views)
    assert {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in originals
    } == hashes
    if broken:
        assert problems[0]["document"] == document and problems[0]["line"] == 3
        assert "doc-regions-links-" not in problems[0]["message"]


def test_qmd_view_refuses_escaping_source(workspace, unchanged):
    root = workspace[0]
    (root / "wiki").mkdir()
    outside = root.parent / "outside.qmd"
    outside.write_text("Must not read.\n")
    (root / "wiki/linked.qmd").symlink_to(outside)
    with unchanged(root.parent), pytest.raises(ValueError, match="leaves root"):
        check(*workspace, link_view_roots=("wiki", "text"))


def test_qmd_requires_explicit_view_roots(workspace, unchanged):
    root, _, module, generators = workspace
    (root / "doc.qmd").write_text("[Bad](missing.qmd)\n")
    with (
        unchanged(root.parent),
        pytest.raises(ValueError, match="no named link view"),
    ):
        check(root, ["doc.qmd"], module, generators)


def test_update_validates_all_targets_before_writing(workspace, unchanged):
    root, targets, module, generators = workspace
    (root / "source.txt").write_text("changed\n")
    (root / "bad.md").write_text(region('print("bad")'))
    with unchanged(root.parent):
        assert update(root, targets + ["bad.md"], module, generators)


def test_missing_target(workspace, unchanged):
    root, _, module, generators = workspace
    with unchanged(root.parent):
        problems = check(root, ["missing.md"], module, generators)
    assert problems[0]["document"] == "missing.md"


def test_indented_region_in_list(workspace, unchanged):
    root = workspace[0]
    (root / "doc.md").write_text(
        "- Item\n\n"
        + "".join("  " + line for line in region().splitlines(True))
    )
    with unchanged(root.parent):
        assert check(*workspace) == []


def test_link_problem_reports_actual_line(workspace, unchanged):
    root = workspace[0]
    (root / "doc.md").write_text("# Title\n\nParagraph.\n\n[bad](missing.md)\n")
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems[0]["line"] == 5


def test_stale_second_region_reports_its_line(workspace, unchanged):
    root = workspace[0]
    (root / "doc.md").write_text(
        region() + "\nParagraph.\n\n" + region(output="stale\n")
    )
    with unchanged(root.parent):
        problems = check(*workspace)
    assert problems[0]["line"] == 7


def test_check_checks_target_links_without_regions_and_ignores_report_only(
    tmp_path, unchanged
):
    root = tmp_path / "root"
    root.mkdir()
    (root / "target.md").write_text("[local](local.md)\n")
    (root / "local.md").write_text("# Local\n")
    (root / "AGENTS.md").write_text("[missing](absent.md)\n")
    (root / "regions.toml").write_text(
        'targets = ["target.md"]\nreport_only = ["AGENTS.md"]\n'
        'generators = "sources"\ngenerator_path = "scripts"\n'
    )
    with unchanged(root):
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "doc_regions",
                "check",
                "regions.toml",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"problems": []}


def test_update_preserves_crlf_agent_bytes(workspace):
    root = workspace[0]
    original = (
        "Before.\r\n\r\n" + region().replace("\n", "\r\n") + "\r\nAfter."
    ).encode()
    (root / "doc.md").write_bytes(original)
    (root / "source.txt").write_text("changed\n")
    assert update(*workspace) == []
    updated = (root / "doc.md").read_bytes()
    assert updated.startswith(b"Before.\r\n\r\n")
    assert updated.endswith(b"\r\nAfter.")
    assert update(*workspace) == []
    assert (root / "doc.md").read_bytes() == updated
