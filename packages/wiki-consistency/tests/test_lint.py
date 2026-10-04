from pathlib import Path

from conftest import REVISIONS
from conftest import SOURCE_ID
from conftest import add_revision
from conftest import commit_instance
from conftest import make_instance
from conftest import tree_hash
from conftest import update_regions
import pytest

from wiki_consistency.lint import _log_prefix
from wiki_consistency.lint import check


@pytest.fixture(autouse=True)
def private_cache(monkeypatch, tmp_path):
    cache = tmp_path / "xdg-cache"
    (cache / "verbose-broccoli").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache))


def checked(instance, env):
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    before = tree_hash(instance), tree_hash(cache)
    result = check(instance)
    assert (tree_hash(instance), tree_hash(cache)) == before
    return result


def test_check_lists_orphans_and_stale_citations_without_writing(tmp_path):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    orphan = instance / "wiki" / "concepts" / "orphan.qmd"
    orphan.write_text(
        "---\ntitle: Orphan\nsummary: An unlinked synthetic page.\n"
        "topics:\n  - Algebra\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[0]}\n---\n\n# Orphan\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []
    result = checked(instance, env)

    assert result["problems"] == []
    assert result["orphans"] == ["wiki/concepts/orphan.qmd"]
    assert result["stale_citations"] == [
        {
            "page": "wiki/concepts/orphan.qmd",
            "source_id": SOURCE_ID,
            "cited_revision": REVISIONS[0],
            "latest_revision": REVISIONS[-1],
        }
    ]


def test_log_prefix_is_checked_only_after_a_commit(tmp_path):
    instance, env = make_instance(tmp_path, commit=True)
    assert update_regions(instance) == []
    (instance / "wiki" / "log.qmd").write_text(
        "## [2026-09-28] raw-import | synthetic\n\n1 admitted.\n"
        "## [2026-09-28] lint | synthetic\n\n0 changed pages.\n",
        encoding="utf-8",
    )
    add_revision(instance, "20260929T000000000000Z", "new synthetic revision\n")
    assert update_regions(instance) == []

    result = checked(instance, env)

    assert result["problems"] == []


def test_index_must_have_one_page_catalog_region_and_no_text_outside_it(
    tmp_path,
):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    index = instance / "wiki" / "index.qmd"
    index.write_text(
        "Manual text.\n" + index.read_text(encoding="utf-8"), encoding="utf-8"
    )

    result = checked(instance, env)

    assert any(
        problem["document"] == "wiki/index.qmd"
        and "one page_catalog region" in problem["message"]
        for problem in result["problems"]
    )


@pytest.mark.parametrize("legacy", (False, True))
@pytest.mark.parametrize("change", ("append", "edit", "remove"))
def test_log_prefix_preserves_committed_bytes_across_rename(
    tmp_path, legacy, change
):
    instance, _ = make_instance(tmp_path)
    current = instance / "wiki/log.qmd"
    original = b"## Earlier log\r\n\r\nExact history.\r\n"
    current.write_bytes(original)
    if legacy:
        current.rename(instance / "wiki/log.md")
    commit_instance(instance)
    if legacy:
        (instance / "wiki/log.md").rename(current)
    if change == "append":
        current.write_bytes(original + b"\nNew entry.\n")
    elif change == "edit":
        current.write_bytes(original.replace(b"Exact", b"Changed"))
    else:
        current.unlink()
    before = tree_hash(instance)
    assert bool(_log_prefix(instance)) == (change != "append")
    assert tree_hash(instance) == before


def test_inert_examples_and_original_language_text_stay_readable(tmp_path):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    page = instance / "wiki/concepts/alpha.qmd"
    page.write_text(
        page.read_text()
        + (
            "\n```python\nprint('inert')\n```\n"
            "\n````markdown\n```{python}\nprint('example')\n```\n"
            "{{{< include example.qmd >}}}\n````\n"
            "\n`{{{< video example >}}}`\n"
            "\n{{</* video example */>}}\n"
            "\n{{{< include escaped >}}}\n"
        )
    )
    source = instance / "text/source/r1.qmd"
    source.parent.mkdir(parents=True)
    source.write_text(
        "한국어 원문\n```{python}\n원문\n```\n{{< include 원문 >}}\n"
    )
    assert checked(instance, env)["problems"] == []
