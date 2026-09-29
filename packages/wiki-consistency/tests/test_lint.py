from pathlib import Path

from conftest import REVISIONS
from conftest import SOURCE_ID
from conftest import add_revision
from conftest import make_instance
from conftest import tree_hash
from conftest import update_regions

from wiki_consistency.lint import check


def checked(instance, env):
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    before = tree_hash(instance), tree_hash(cache)
    result = check(instance)
    assert (tree_hash(instance), tree_hash(cache)) == before
    return result


def test_check_lists_orphans_and_stale_citations_without_writing(tmp_path):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    orphan = instance / "wiki" / "concepts" / "orphan.md"
    orphan.write_text(
        "---\ntitle: Orphan\nsummary: An unlinked synthetic page.\n"
        "topics:\n  - Algebra\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[0]}\n---\n\n# Orphan\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []
    result = checked(instance, env)

    assert result["problems"] == []
    assert result["orphans"] == ["wiki/concepts/orphan.md"]
    assert result["stale_citations"] == [
        {
            "page": "wiki/concepts/orphan.md",
            "source_id": SOURCE_ID,
            "cited_revision": REVISIONS[0],
            "latest_revision": REVISIONS[-1],
        }
    ]


def test_log_prefix_is_checked_only_after_a_commit(tmp_path):
    instance, env = make_instance(tmp_path, commit=True)
    assert update_regions(instance) == []
    (instance / "wiki" / "log.md").write_text(
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
    index = instance / "wiki" / "index.md"
    index.write_text(
        "Manual text.\n" + index.read_text(encoding="utf-8"), encoding="utf-8"
    )

    result = checked(instance, env)

    assert any(
        problem["document"] == "wiki/index.md"
        and "one page_catalog region" in problem["message"]
        for problem in result["problems"]
    )
