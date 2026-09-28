import pytest

from conftest import REVISIONS, SOURCE_ID, make_instance, replace_page_topics
from wiki_consistency.instance import (
    _metadata,
    instance_path,
    mask_front_matter,
    pages,
    revisions,
    roots,
)


def test_roots_use_absolute_xdg_paths_with_namespace(tmp_path):
    home = tmp_path / "home"
    env = {
        "HOME": str(home),
        "XDG_DATA_HOME": str(tmp_path / "data"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
    }
    assert roots(env) == {
        "data": tmp_path / "data" / "verbose-broccoli",
        "cache": tmp_path / "cache" / "verbose-broccoli",
    }


def test_roots_fall_back_for_unset_empty_or_relative_xdg_values(tmp_path):
    home = tmp_path / "home"
    expected = {
        "data": home / ".local" / "share" / "verbose-broccoli",
        "cache": home / ".cache" / "verbose-broccoli",
    }
    for env in (
        {"HOME": str(home)},
        {"HOME": str(home), "XDG_DATA_HOME": "", "XDG_CACHE_HOME": ""},
        {"HOME": str(home), "XDG_DATA_HOME": "relative", "XDG_CACHE_HOME": "relative"},
    ):
        assert roots(env) == expected


def test_instance_path_and_invalid_names(tmp_path):
    env = {"HOME": str(tmp_path), "XDG_DATA_HOME": str(tmp_path / "data")}
    assert instance_path("default", env) == (
        tmp_path / "data" / "verbose-broccoli" / "vaults" / "default")
    for name in ("", ".", "..", "two/names", "null\0name"):
        with pytest.raises(ValueError):
            instance_path(name, env)


def test_instance_path_uses_vaults_for_work(tmp_path):
    env = {"HOME": str(tmp_path), "XDG_DATA_HOME": str(tmp_path / "data")}

    assert instance_path("work", env) == (
        tmp_path / "data" / "verbose-broccoli" / "vaults" / "work")


def test_pages_parse_metadata_sort_paths_and_mark_special_pages(tmp_path):
    instance, _ = make_instance(tmp_path)
    result = pages(instance)

    assert [page["path"] for page in result] == [
        "wiki/concepts/alpha.md", "wiki/index.md", "wiki/log.md",
        "wiki/overview.md", "wiki/sources/source.md",
    ]
    alpha = result[0]
    assert alpha == {
        "path": "wiki/concepts/alpha.md",
        "title": "Alpha",
        "summary": "A synthetic page.",
        "topics": ["Algebra"],
        "sources": [{"id": SOURCE_ID, "revision": REVISIONS[-1]}],
        "special": False,
        "problems": [],
    }
    assert [page["path"] for page in result if page["special"]] == [
        "wiki/index.md", "wiki/log.md", "wiki/overview.md",
    ]


@pytest.mark.parametrize("field", [
    pytest.param("", id="missing"),
    pytest.param("topics: Algebra\n", id="not-a-list"),
    pytest.param("topics: []\n", id="empty-list"),
    pytest.param("topics:\n  - 7\n", id="non-string-name"),
    pytest.param("topics:\n  - ''\n", id="empty-name"),
    pytest.param('topics:\n  - "Algebra\\nvariant"\n', id="multi-line-name"),
    pytest.param("topics:\n  - Algebra\n  - Algebra\n", id="duplicate-name"),
])
def test_metadata_rejects_invalid_topics(tmp_path, field):
    instance, _ = make_instance(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.md"
    replace_page_topics(page, field)

    metadata, problems = _metadata(page.read_text(encoding="utf-8"))

    assert metadata["topics"] == []
    assert any("topics" in problem["message"] for problem in problems)


def test_declared_topics_returns_names_and_accepts_empty_list(tmp_path):
    from wiki_consistency.instance import declared_topics

    instance, _ = make_instance(tmp_path)

    assert declared_topics(instance) == (["Algebra", "Reference", "Unused"], [])

    (instance / "AGENTS.md").write_text("---\ntopics: []\n---\n", encoding="utf-8")
    assert declared_topics(instance) == ([], [])


@pytest.mark.parametrize(("schema", "problem"), [
    pytest.param(None, "agents.md", id="missing-schema"),
    pytest.param("Synthetic Wiki schema.\n", "front matter", id="missing-front-matter"),
    pytest.param("---\nname: Synthetic\n---\n", "topics", id="missing-topics"),
    pytest.param("---\ntopics: Algebra\n---\n", "topics", id="not-a-list"),
    pytest.param("---\ntopics:\n  - 7\n---\n", "topics", id="non-string-name"),
    pytest.param("---\ntopics:\n  - ''\n---\n", "topics", id="empty-name"),
    pytest.param(
        '---\ntopics:\n  - |\n    Algebra\n    variant\n---\n',
        "topics", id="multi-line-name"),
    pytest.param(
        "---\ntopics:\n  - Algebra\n  - Algebra\n---\n",
        "topics", id="duplicate-name"),
])
def test_declared_topics_reports_bad_schema(tmp_path, schema, problem):
    from wiki_consistency.instance import declared_topics

    instance, _ = make_instance(tmp_path)
    path = instance / "AGENTS.md"
    if schema is None:
        path.unlink()
    else:
        path.write_text(schema, encoding="utf-8")

    topics, problems = declared_topics(instance)

    assert topics == []
    assert problems
    assert any(problem in item["message"].lower() for item in problems)


def test_mask_front_matter_keeps_lf_line_numbers():
    text = "---\ntitle: Alpha\nsummary: A page.\nsources: []\n---\n# Alpha\n"
    assert mask_front_matter(text) == "\n\n\n\n\n# Alpha\n"


def test_revisions_are_discovered_from_raw_and_sorted_by_name(tmp_path):
    instance, _ = make_instance(tmp_path)
    result = revisions(instance)

    assert list(result) == [SOURCE_ID]
    assert result[SOURCE_ID] == [
        {"kind": "files", "id": SOURCE_ID, "revision": revision,
         "path": f"raw/files/{SOURCE_ID}/{revision}"}
        for revision in REVISIONS
    ]
