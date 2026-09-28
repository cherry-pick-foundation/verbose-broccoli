import hashlib
import os
import time

import pytest

from conftest import REVISIONS, SOURCE_ID, _page, make_instance
from conftest import replace_page_topics, update_regions
from wiki_consistency.lint import check
from wiki_consistency.sources import page_catalog, source_provenance


def test_page_catalog_groups_sorted_pages_by_topic_without_reading_schema(
        tmp_path, monkeypatch):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    replace_page_topics(alpha, "topics:\n  - Algebra\n  - Geometry\n")
    source = instance / "wiki" / "sources" / "source.md"
    replace_page_topics(source, "topics:\n  - Algebra\n")
    (instance / "wiki" / "concepts" / "beta.md").write_text(
        _page("Beta", "A third synthetic page.", REVISIONS[-1], topics=("Reference",)),
        encoding="utf-8")
    (instance / "AGENTS.md").unlink()

    expected = (
        "## Algebra\n\n"
        "- [Alpha](concepts/alpha.md) — A synthetic page.\n"
        "- [Source](sources/source.md) — A synthetic source.\n\n"
        "## Geometry\n\n"
        "- [Alpha](concepts/alpha.md) — A synthetic page.\n\n"
        "## Reference\n\n"
        "- [Beta](concepts/beta.md) — A third synthetic page.\n"
    )
    assert page_catalog("wiki/**/*.md") == expected
    assert page_catalog("wiki/**/*.md") == expected


def test_page_catalog_is_empty_when_the_vault_has_no_pages(tmp_path, monkeypatch):
    instance, _ = make_instance(tmp_path)
    monkeypatch.chdir(instance)
    (instance / "wiki" / "concepts" / "alpha.md").unlink()
    (instance / "wiki" / "sources" / "source.md").unlink()
    (instance / "AGENTS.md").unlink()

    assert page_catalog("wiki/**/*.md") == ""


def test_check_finds_stale_index_after_page_topics_change(tmp_path):
    instance, _ = make_instance(tmp_path)
    assert update_regions(instance) == []
    replace_page_topics(
        instance / "wiki" / "concepts" / "alpha.md", "topics:\n  - Reference\n")

    result = check(instance)

    assert any(problem["document"] == "wiki/index.md"
               and "wiki-consistency update" in problem["message"]
               for problem in result["problems"])


def test_source_provenance_renders_sorted_revisions_from_named_files(tmp_path, monkeypatch):
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

    assert source_provenance(
        f"raw/files/{SOURCE_ID}/*/bag-info.txt",
        f"raw/files/{SOURCE_ID}/*/manifest-sha256.txt",
    ) == expected


@pytest.mark.parametrize("generator, arguments", [
    (page_catalog, ("wiki/missing/**/*.md",)),
    (source_provenance, ("raw/missing/*/bag-info.txt", "raw/missing/*/manifest-sha256.txt")),
])
def test_generator_raises_for_missing_sources(tmp_path, generator, arguments, monkeypatch):
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
        raise AssertionError("clock access")

    with monkeypatch.context() as patcher:
        patcher.setattr(os, "environ", ForbiddenEnvironment())
        patcher.setattr(time, "time", forbidden_clock)
        assert page_catalog("wiki/**/*.md")
        assert source_provenance(
            f"raw/files/{SOURCE_ID}/*/bag-info.txt",
            f"raw/files/{SOURCE_ID}/*/manifest-sha256.txt",
        )
