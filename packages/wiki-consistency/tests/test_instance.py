from conftest import REVISIONS
from conftest import SOURCE_ID
from conftest import make_instance
from conftest import replace_page_topics
import pytest

from wiki_consistency.instance import _metadata
from wiki_consistency.instance import declared_topics
from wiki_consistency.instance import instance_path
from wiki_consistency.instance import mask_front_matter
from wiki_consistency.instance import metadata_sources
from wiki_consistency.instance import pages
from wiki_consistency.instance import read_metadata
from wiki_consistency.instance import revisions
from wiki_consistency.instance import roots


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
        {
            "HOME": str(home),
            "XDG_DATA_HOME": "relative",
            "XDG_CACHE_HOME": "relative",
        },
    ):
        assert roots(env) == expected


def test_instance_path_and_invalid_names(tmp_path):
    env = {"HOME": str(tmp_path), "XDG_DATA_HOME": str(tmp_path / "data")}
    assert instance_path("default", env) == (
        tmp_path / "data" / "verbose-broccoli" / "llm-wiki" / "default"
    )
    for name in ("", ".", "..", "two/names", "null\0name"):
        with pytest.raises(ValueError):
            instance_path(name, env)


@pytest.mark.parametrize("name", ("default", "chat", "code", "work"))
@pytest.mark.parametrize("configured", (None, "", "relative", "absolute"))
def test_instance_path_uses_llm_wiki_without_legacy_link(
    tmp_path, name, configured
):
    env = {"HOME": str(tmp_path)}
    data = tmp_path / ".local/share"
    if configured is not None:
        if configured == "absolute":
            data = tmp_path / "data"
            env["XDG_DATA_HOME"] = str(data)
        else:
            env["XDG_DATA_HOME"] = configured
    expected = data / "verbose-broccoli" / "llm-wiki" / name
    expected.mkdir(parents=True)
    assert instance_path(name, env) == expected
    assert not (data / "verbose-broccoli" / "vaults").exists()


def test_pages_parse_metadata_sort_paths_and_mark_special_pages(tmp_path):
    instance, _ = make_instance(tmp_path)
    result = pages(instance)

    assert [page["path"] for page in result] == [
        "wiki/concepts/alpha.qmd",
        "wiki/index.qmd",
        "wiki/log.qmd",
        "wiki/overview.qmd",
        "wiki/sources/source.qmd",
    ]
    alpha = result[0]
    assert alpha == {
        "path": "wiki/concepts/alpha.qmd",
        "title": "Alpha",
        "summary": "A synthetic page.",
        "topics": ["Algebra"],
        "sources": [{"id": SOURCE_ID, "revision": REVISIONS[-1]}],
        "special": False,
        "problems": [],
    }
    assert [page["path"] for page in result if page["special"]] == [
        "wiki/index.qmd",
        "wiki/log.qmd",
        "wiki/overview.qmd",
    ]


@pytest.mark.parametrize(
    "field",
    [
        pytest.param("", id="missing"),
        pytest.param("topics: Algebra\n", id="not-a-list"),
        pytest.param("topics: []\n", id="empty-list"),
        pytest.param("topics:\n  - 7\n", id="non-string-name"),
        pytest.param("topics:\n  - ''\n", id="empty-name"),
        pytest.param(
            'topics:\n  - "Algebra\\nvariant"\n', id="multi-line-name"
        ),
        pytest.param(
            "topics:\n  - Algebra\n  - Algebra\n", id="duplicate-name"
        ),
    ],
)
def test_metadata_rejects_invalid_topics(tmp_path, field):
    instance, _ = make_instance(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    replace_page_topics(page, field)

    metadata, problems = _metadata(page.read_text(encoding="utf-8"))

    assert metadata["topics"] == []
    assert any("topics" in problem["message"] for problem in problems)


def test_declared_topics_returns_names_and_accepts_empty_list(tmp_path):
    instance, _ = make_instance(tmp_path)

    assert declared_topics(instance) == (["Algebra", "Reference", "Unused"], [])

    (instance / "AGENTS.md").write_text(
        "---\ntopics: []\n---\n", encoding="utf-8"
    )
    assert declared_topics(instance) == ([], [])


@pytest.mark.parametrize(
    ("schema", "problem"),
    [
        pytest.param(None, "agents.md", id="missing-schema"),
        pytest.param(
            "Synthetic Wiki schema.\n",
            "front matter",
            id="missing-front-matter",
        ),
        pytest.param(
            "---\nname: Synthetic\n---\n", "topics", id="missing-topics"
        ),
        pytest.param("---\ntopics: Algebra\n---\n", "topics", id="not-a-list"),
        pytest.param(
            "---\ntopics:\n  - 7\n---\n", "topics", id="non-string-name"
        ),
        pytest.param("---\ntopics:\n  - ''\n---\n", "topics", id="empty-name"),
        pytest.param(
            "---\ntopics:\n  - |\n    Algebra\n    variant\n---\n",
            "topics",
            id="multi-line-name",
        ),
        pytest.param(
            "---\ntopics:\n  - Algebra\n  - Algebra\n---\n",
            "topics",
            id="duplicate-name",
        ),
    ],
)
def test_declared_topics_reports_bad_schema(tmp_path, schema, problem):
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
        {
            "kind": "files",
            "id": SOURCE_ID,
            "revision": revision,
            "path": f"raw/files/{SOURCE_ID}/{revision}",
        }
        for revision in REVISIONS
    ]


def test_metadata_inherits_nested_defaults_and_keeps_full_page_mapping(
    tmp_path,
):
    instance, _ = make_instance(tmp_path)
    (instance / "wiki/_metadata.yml").write_text(
        "summary: Root default.\ntopics: [Algebra]\n"
        f"sources: [{{id: {SOURCE_ID}, revision: {REVISIONS[-1]}}}]\n"
        "profile:\n  inventory: ../inventories/shared.qmd\n"
        "  checker: checked\n  flags: [base, common]\n"
        "  clear: [base]\n  nullable: [base]\n"
        "  scalar: [base]\n  options: {keep: true, override: root}\n"
    )
    (instance / "wiki/concepts/_metadata.yml").write_text(
        "summary: Folder default.\ntopics: [Reference]\n"
        "profile:\n  options: {override: folder}\n"
    )
    document = "wiki/concepts/alpha.qmd"
    (instance / document).write_text(
        "---\ntitle: Page override\nsummary: Page summary.\n"
        "topics: [Algebra, Unused]\nprofile:\n  checker: none\n"
        "  flags: [common, page]\n  clear: []\n  nullable: null\n"
        "  scalar: page\n  options: {extra: page}\n---\nOriginal body.\n"
    )
    before = (instance / document).read_bytes()
    metadata, problems = read_metadata(instance, document)
    assert problems == []
    assert metadata["summary"] == "Page summary."
    assert metadata["topics"] == ["Algebra", "Reference", "Unused"]
    assert metadata["sources"] == [{"id": SOURCE_ID, "revision": REVISIONS[-1]}]
    assert metadata["profile"] == {
        "inventory": "../inventories/shared.qmd",
        "checker": "none",
        "flags": ["base", "common", "page"],
        "clear": ["base"],
        "nullable": ["base"],
        "scalar": ["base", "page"],
        "options": {"keep": True, "override": "folder", "extra": "page"},
    }
    assert metadata_sources(instance, document) == [
        "wiki/_metadata.yml",
        "wiki/concepts/_metadata.yml",
    ]
    assert (instance / document).read_bytes() == before


@pytest.mark.parametrize("value", ("[]\n", "profile: [\n", "", "null\n"))
def test_metadata_reports_bad_default_at_its_source(tmp_path, value):
    instance, _ = make_instance(tmp_path)
    (instance / "wiki/_metadata.yml").write_text(value)
    metadata, problems = read_metadata(instance, "wiki/concepts/alpha.qmd")
    assert metadata == {}
    assert problems and problems[0]["document"] == "wiki/_metadata.yml"
    assert problems[0]["line"] >= 1


@pytest.mark.parametrize(
    "document",
    (
        "../outside.qmd",
        "/outside.qmd",
        "text/original.qmd",
        "wiki/**/*.qmd",
        "wiki/concepts/alpha.md",
        "wiki/missing.qmd",
    ),
)
def test_metadata_refuses_unsafe_or_missing_page_paths(tmp_path, document):
    instance, _ = make_instance(tmp_path)
    assert read_metadata(instance, document)[1]


def test_metadata_refuses_escaping_defaults_before_reading(
    tmp_path, monkeypatch
):
    instance, _ = make_instance(tmp_path)
    outside = tmp_path / "outside.yml"
    outside.write_text("secret: unread\n")
    (instance / "wiki/_metadata.yml").symlink_to(outside)
    with monkeypatch.context() as patcher:
        patcher.setattr(
            type(outside), "read_bytes", lambda *_: pytest.fail("unsafe read")
        )
        assert "leaves root" in str(
            read_metadata(instance, "wiki/concepts/alpha.qmd")[1]
        )


def test_qmd_discovery_ignores_other_roles_and_reports_suffix_collision(
    tmp_path,
):
    instance, _ = make_instance(tmp_path)
    (instance / "text").mkdir()
    (instance / "text/original.qmd").write_text("Original-language text.\n")
    (instance / "wiki/legacy.md").write_text("Old page.\n")
    assert len(pages(instance)) == 5
    (instance / "wiki/concepts/alpha.md").write_text("Old page.\n")
    assert "collision" in str(pages(instance)[0]["problems"])


def test_full_metadata_cannot_override_discovery_bookkeeping(tmp_path):
    instance, _ = make_instance(tmp_path)
    page = instance / "wiki/concepts/alpha.qmd"
    page.write_text(
        page.read_text().replace(
            "title: Alpha",
            "title: Alpha\npath: outside\nspecial: true\nproblems: []",
        )
    )
    metadata, problems = read_metadata(instance, "wiki/concepts/alpha.qmd")
    assert problems == [] and metadata["path"] == "outside"
    found = pages(instance)[0]
    assert found["path"] == "wiki/concepts/alpha.qmd" and not found["special"]
