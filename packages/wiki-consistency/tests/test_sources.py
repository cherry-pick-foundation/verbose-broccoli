import hashlib
import os
import time

from conftest import REVISIONS
from conftest import SOURCE_ID
from conftest import _page
from conftest import make_instance
from conftest import replace_page_topics
from conftest import update_regions
import pytest

from wiki_consistency.lint import check
from wiki_consistency.lint import update
from wiki_consistency.sources import page_catalog
from wiki_consistency.sources import source_provenance


def test_page_catalog_groups_sorted_pages_by_topic_without_reading_schema(
    tmp_path, monkeypatch
):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    alpha = instance / "wiki" / "concepts" / "alpha.qmd"
    replace_page_topics(alpha, "topics:\n  - Algebra\n  - Geometry\n")
    source = instance / "wiki" / "sources" / "source.qmd"
    replace_page_topics(source, "topics:\n  - Algebra\n")
    (instance / "wiki" / "concepts" / "beta.qmd").write_text(
        _page(
            "Beta",
            "A third synthetic page.",
            REVISIONS[-1],
            topics=("Reference",),
        ),
        encoding="utf-8",
    )
    (instance / "AGENTS.md").unlink()

    expected = (
        "## Algebra\n\n"
        "- [Alpha](concepts/alpha.qmd) — A synthetic page.\n"
        "- [Source](sources/source.qmd) — A synthetic source.\n\n"
        "## Geometry\n\n"
        "- [Alpha](concepts/alpha.qmd) — A synthetic page.\n\n"
        "## Reference\n\n"
        "- [Beta](concepts/beta.qmd) — A third synthetic page.\n"
    )
    assert page_catalog("wiki/**/*.qmd") == expected
    assert page_catalog("wiki/**/*.qmd") == expected


def test_page_catalog_is_empty_when_the_wiki_has_no_pages(
    tmp_path, monkeypatch
):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    (instance / "wiki" / "concepts" / "alpha.qmd").unlink()
    (instance / "wiki" / "sources" / "source.qmd").unlink()
    (instance / "AGENTS.md").unlink()

    assert page_catalog("wiki/**/*.qmd") == ""


def test_check_finds_stale_index_after_page_topics_change(tmp_path):
    instance, _ = make_instance(tmp_path)
    assert update_regions(instance) == []
    replace_page_topics(
        instance / "wiki" / "concepts" / "alpha.qmd", "topics:\n  - Reference\n"
    )

    result = check(instance)

    assert any(
        problem["document"] == "wiki/index.qmd"
        and "wiki-consistency update" in problem["message"]
        for problem in result["problems"]
    )


def test_source_provenance_renders_sorted_revisions_from_named_files(
    tmp_path, monkeypatch
):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    contents = ("first synthetic revision\n", "latest synthetic revision\n")
    lines = [
        f"- `{revision}`: modified `2026-09-26T12:34:56+00:00`, "
        f"{len(content.encode('utf-8'))} bytes, SHA-256 "
        f"`{hashlib.sha256(content.encode('utf-8')).hexdigest()}`\n"
        for revision, content in zip(REVISIONS, contents)
    ]
    expected = (
        f"Source `{SOURCE_ID}` (`files`), original file `document.txt`:\n\n"
        + "".join(lines)
    )

    assert (
        source_provenance(
            f"raw/files/{SOURCE_ID}/*/bag-info.txt",
            f"raw/files/{SOURCE_ID}/*/manifest-sha256.txt",
        )
        == expected
    )


@pytest.mark.parametrize(
    "generator, arguments",
    [
        (page_catalog, ("wiki/missing/**/*.qmd",)),
        (
            source_provenance,
            ("raw/missing/*/bag-info.txt", "raw/missing/*/manifest-sha256.txt"),
        ),
    ],
)
def test_generator_raises_for_missing_sources(
    tmp_path, generator, arguments, monkeypatch
):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    with pytest.raises(ValueError):
        generator(*arguments)


def test_generators_do_not_read_environment_or_clock(tmp_path, monkeypatch):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)

    class ForbiddenEnvironment:
        def __getattr__(self, name):
            raise AssertionError(f"environment access: {name}")

    def forbidden_clock(*args, **kwargs):
        del args, kwargs  # Unused.
        raise AssertionError("clock access")

    with monkeypatch.context() as patcher:
        patcher.setattr(os, "environ", ForbiddenEnvironment())
        patcher.setattr(time, "time", forbidden_clock)
        assert page_catalog("wiki/**/*.qmd")
        assert source_provenance(
            f"raw/files/{SOURCE_ID}/*/bag-info.txt",
            f"raw/files/{SOURCE_ID}/*/manifest-sha256.txt",
        )


def test_cog_catalog_consumes_actual_named_defaults_and_detects_changes(
    tmp_path,
):
    instance, _ = make_instance(tmp_path)
    page = instance / "wiki/concepts/alpha.qmd"
    page.write_text(
        page.read_text().replace("summary: A synthetic page.\n", "")
    )
    defaults = instance / "wiki/concepts/_metadata.yml"
    defaults.write_text("summary: Inherited summary.\n")
    index = instance / "wiki/index.qmd"
    index.write_text(
        index.read_text().replace(
            'page_catalog("wiki/**/*.qmd")',
            'page_catalog("wiki/**/*.qmd", "wiki/concepts/_metadata.yml")',
        )
    )
    assert update(instance) == {"problems": []}
    assert "Inherited summary." in index.read_text()
    assert check(instance)["problems"] == []
    defaults.write_text("summary: Changed inherited summary.\n")
    assert any(
        item["document"] == "wiki/index.qmd"
        for item in check(instance)["problems"]
    )
    assert update(instance) == {"problems": []}
    assert "Changed inherited summary." in index.read_text()


def test_catalog_refuses_unnamed_default_before_any_content_read(
    tmp_path, monkeypatch
):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    (instance / "wiki/_metadata.yml").write_text("profile: {checker: none}\n")
    with monkeypatch.context() as patcher:
        patcher.setattr(
            type(instance), "read_bytes", lambda *_: pytest.fail("unnamed read")
        )
        patcher.setattr(
            type(instance),
            "read_text",
            lambda *unused_args, **unused_kwargs: pytest.fail("unnamed read"),
        )
        with pytest.raises(
            ValueError, match="unnamed metadata source: wiki/_metadata.yml"
        ):
            page_catalog("wiki/**/*.qmd")


@pytest.mark.parametrize(
    "name",
    (
        "wiki/**/_metadata.yml",
        "wiki/absent/_metadata.yml",
        "../_metadata.yml",
        "/_metadata.yml",
        "AGENTS.md",
    ),
)
def test_catalog_refuses_nonliteral_or_missing_defaults(
    tmp_path, monkeypatch, name
):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    with pytest.raises(ValueError):
        page_catalog("wiki/**/*.qmd", name)
