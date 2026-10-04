import json
from pathlib import Path
import re

from conftest import REVISIONS
from conftest import SOURCE_ID
from conftest import add_revision
from conftest import make_instance
from conftest import replace_page_topics
from conftest import tree_hash
from conftest import update_regions
import pytest

from doc_regions.regions import scan
from wiki_consistency.__main__ import main

TOPIC_FAILURES = [
    pytest.param(
        "page", "", "wiki/concepts/alpha.qmd", "topics", id="page-missing"
    ),
    pytest.param(
        "page",
        "topics: Algebra\n",
        "wiki/concepts/alpha.qmd",
        "topics",
        id="page-not-a-list",
    ),
    pytest.param(
        "page",
        "topics: []\n",
        "wiki/concepts/alpha.qmd",
        "topics",
        id="page-empty-list",
    ),
    pytest.param(
        "page",
        "topics:\n  - 7\n",
        "wiki/concepts/alpha.qmd",
        "topics",
        id="page-non-string-name",
    ),
    pytest.param(
        "page",
        "topics:\n  - ''\n",
        "wiki/concepts/alpha.qmd",
        "topics",
        id="page-empty-name",
    ),
    pytest.param(
        "page",
        'topics:\n  - "Algebra\\nvariant"\n',
        "wiki/concepts/alpha.qmd",
        "topics",
        id="page-multi-line-name",
    ),
    pytest.param(
        "page",
        "topics:\n  - Algebra\n  - Algebra\n",
        "wiki/concepts/alpha.qmd",
        "topics",
        id="page-duplicate-name",
    ),
    pytest.param(
        "page",
        "topics:\n  - Unlisted\n",
        "wiki/concepts/alpha.qmd",
        "Unlisted",
        id="undeclared-page-topic",
    ),
    pytest.param("schema", None, "AGENTS.md", "AGENTS.md", id="missing-schema"),
    pytest.param(
        "schema",
        "Synthetic Wiki schema.\n",
        "AGENTS.md",
        "front matter",
        id="schema-missing-front-matter",
    ),
    pytest.param(
        "schema",
        "---\nname: Synthetic\n---\n",
        "AGENTS.md",
        "topics",
        id="schema-missing-topics",
    ),
    pytest.param(
        "schema",
        "---\ntopics: Algebra\n---\n",
        "AGENTS.md",
        "topics",
        id="schema-not-a-list",
    ),
    pytest.param(
        "schema",
        "---\ntopics:\n  - 7\n---\n",
        "AGENTS.md",
        "topics",
        id="schema-non-string-name",
    ),
    pytest.param(
        "schema",
        "---\ntopics:\n  - ''\n---\n",
        "AGENTS.md",
        "topics",
        id="schema-empty-name",
    ),
    pytest.param(
        "schema",
        "---\ntopics:\n  - |\n    Algebra\n    variant\n---\n",
        "AGENTS.md",
        "topics",
        id="schema-multi-line-name",
    ),
    pytest.param(
        "schema",
        "---\ntopics:\n  - Algebra\n  - Algebra\n---\n",
        "AGENTS.md",
        "topics",
        id="schema-duplicate-name",
    ),
]


def set_topic_failure(instance, target, value):
    if target == "page":
        replace_page_topics(instance / "wiki" / "concepts" / "alpha.qmd", value)
    elif value is None:
        (instance / "AGENTS.md").unlink()
    else:
        (instance / "AGENTS.md").write_text(value, encoding="utf-8")


def ready_instance(tmp_path, *, commit=False):
    instance, env = make_instance(tmp_path, commit=commit)
    assert update_regions(instance) == []
    return instance, env


def run_check(instance, env, monkeypatch, capsys, *, explicit_wiki=True):
    with monkeypatch.context() as patcher:
        for name, value in env.items():
            patcher.setenv(name, value)
        cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
        before = tree_hash(instance), tree_hash(cache)
        args = ["check"]
        if explicit_wiki:
            args.extend(["--wiki", instance.name])
        status = main(args)
        output = capsys.readouterr()
        assert (tree_hash(instance), tree_hash(cache)) == before
    return status, output.out, output.err


def assert_problem(result, page, message):
    status, stdout, stderr = result
    assert status == 1
    assert stdout == ""
    assert re.search(rf"(?m)^{re.escape(page)}:\d+:", stderr), stderr
    assert message in stderr


def test_check_passes_with_unused_declared_topic_and_prints_one_json_object(
    tmp_path, monkeypatch, capsys
):
    instance, env = ready_instance(tmp_path)

    status, stdout, stderr = run_check(
        instance, env, monkeypatch, capsys, explicit_wiki=False
    )

    assert status == 0
    assert stderr == ""
    assert stdout.count("\n") == 1
    assert json.loads(stdout) == {
        "orphans": [],
        "problems": [],
        "stale_citations": [],
    }


@pytest.mark.parametrize("target, value, document, message", TOPIC_FAILURES)
def test_check_fails_on_topic_problems(
    tmp_path, monkeypatch, capsys, target, value, document, message
):
    instance, env = ready_instance(tmp_path)
    set_topic_failure(instance, target, value)

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, document, message)


@pytest.mark.parametrize("target, value, document, message", TOPIC_FAILURES)
def test_update_refuses_topic_problems_without_writing(
    tmp_path, monkeypatch, capsys, target, value, document, message
):
    instance, env = make_instance(tmp_path)
    assert update_regions(instance) == []
    set_topic_failure(instance, target, value)
    cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
    before = tree_hash(instance), tree_hash(cache)

    with monkeypatch.context() as patcher:
        for name, value in env.items():
            patcher.setenv(name, value)
        status = main(["update", "--wiki", instance.name])
        output = capsys.readouterr()

    assert_problem((status, output.out, output.err), document, message)
    assert (tree_hash(instance), tree_hash(cache)) == before


def test_check_passes_for_an_empty_vault(tmp_path, monkeypatch, capsys):
    instance, env = ready_instance(tmp_path)
    for folder in ("concepts", "sources"):
        for page in (instance / "wiki" / folder).glob("*.qmd"):
            page.unlink()
    (instance / "wiki" / "overview.qmd").write_text(
        "# Overview\n", encoding="utf-8"
    )
    assert update_regions(instance) == []

    status, stdout, stderr = run_check(instance, env, monkeypatch, capsys)

    assert status == 0, stderr
    assert json.loads(stdout) == {
        "orphans": [],
        "problems": [],
        "stale_citations": [],
    }


def test_check_fails_on_stale_region_and_names_update(
    tmp_path, monkeypatch, capsys
):
    instance, env = ready_instance(tmp_path)
    add_revision(instance, "20260929T000000000000Z", "new synthetic revision\n")

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/sources/source.qmd", "wiki-consistency update")


def test_check_fails_on_malformed_region(tmp_path, monkeypatch, capsys):
    instance, env = ready_instance(tmp_path)
    source = instance / "wiki" / "sources" / "source.qmd"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "<!-- [[[end]]] -->", "<!-- [[end]] -->"
        ),
        encoding="utf-8",
    )

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/sources/source.qmd", "unclosed Cog region")


@pytest.mark.parametrize(
    "mutation, message",
    [
        ("raw/files", "No files match"),
        ("source_provenance", "unknown generator function"),
    ],
)
def test_check_fails_on_missing_region_source_or_generator(
    tmp_path, monkeypatch, capsys, mutation, message
):
    instance, env = ready_instance(tmp_path)
    source = instance / "wiki" / "sources" / "source.qmd"
    text = source.read_text(encoding="utf-8")
    if mutation == "raw/files":
        text = text.replace(f"raw/files/{SOURCE_ID}", "raw/files/missing")
    else:
        text = text.replace("source_provenance", "unknown_generator")
    source.write_text(text, encoding="utf-8")

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/sources/source.qmd", message)


@pytest.mark.parametrize(
    "target, message",
    [
        ("missing.qmd", "missing.qmd"),
        ("../sources/source.qmd#missing-heading", "missing-heading"),
    ],
)
def test_check_fails_on_missing_local_link_or_heading(
    tmp_path, monkeypatch, capsys, target, message
):
    instance, env = ready_instance(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    text = page.read_text(encoding="utf-8").replace(
        "../sources/source.qmd", target
    )
    page.write_text(text, encoding="utf-8")

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/concepts/alpha.qmd", message)


@pytest.mark.parametrize(
    "field, field_line",
    [
        ("title", "title must be a non-empty single line"),
        ("summary", "summary must be a non-empty single line"),
        ("sources", "sources must be a non-empty list"),
    ],
)
def test_check_fails_when_page_metadata_is_missing(
    tmp_path, monkeypatch, capsys, field, field_line
):
    instance, env = ready_instance(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    lines = page.read_text(encoding="utf-8").splitlines()
    remove = {"title": {1}, "summary": {2}, "sources": {5, 6, 7}}[field]
    page.write_text(
        "\n".join(
            line for number, line in enumerate(lines) if number not in remove
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/concepts/alpha.qmd", field_line)


@pytest.mark.parametrize(
    "citation",
    [
        ("0188a0e2-7c1b-7d3e-9f00-000000000000", REVISIONS[-1]),
        (SOURCE_ID, "20260926T000000000000Z"),
    ],
)
def test_check_fails_when_citation_names_no_bag(
    tmp_path, monkeypatch, capsys, citation
):
    instance, env = ready_instance(tmp_path)
    page = instance / "wiki" / "concepts" / "alpha.qmd"
    text = (
        page.read_text(encoding="utf-8")
        .replace(f"id: {SOURCE_ID}", f"id: {citation[0]}")
        .replace(f"revision: {REVISIONS[-1]}", f"revision: {citation[1]}")
    )
    page.write_text(text, encoding="utf-8")

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/concepts/alpha.qmd", "citation")


def test_check_fails_when_cited_bag_fails_fast_validation(
    tmp_path, monkeypatch, capsys
):
    instance, env = ready_instance(tmp_path)
    payload = (
        instance
        / "raw"
        / "files"
        / SOURCE_ID
        / REVISIONS[-1]
        / "data"
        / "document.txt"
    )
    payload.unlink()

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/concepts/alpha.qmd", "BagIt")


@pytest.mark.parametrize(
    "replacement",
    [
        "## [2026-09-28] lint | changed\n\n0 changed pages.\n",
        "",
    ],
)
def test_check_fails_when_committed_log_text_changes_or_is_removed(
    tmp_path, monkeypatch, capsys, replacement
):
    instance, env = ready_instance(tmp_path, commit=True)
    (instance / "wiki" / "log.qmd").write_text(replacement, encoding="utf-8")

    result = run_check(instance, env, monkeypatch, capsys)

    assert_problem(result, "wiki/log.qmd", "prefix")


def test_check_accepts_appended_log_entry_and_lists_findings(
    tmp_path, monkeypatch, capsys
):
    instance, env = ready_instance(tmp_path, commit=True)
    log = instance / "wiki" / "log.qmd"
    log.write_text(
        log.read_text(encoding="utf-8")
        + "## [2026-09-28] lint | synthetic\n\n0 changed pages.\n",
        encoding="utf-8",
    )
    orphan = instance / "wiki" / "concepts" / "orphan.qmd"
    orphan.write_text(
        "---\ntitle: Orphan\nsummary: An unlinked synthetic page.\n"
        "topics:\n  - Algebra\nsources:\n"
        f"  - id: {SOURCE_ID}\n    revision: {REVISIONS[0]}\n---\n",
        encoding="utf-8",
    )
    assert update_regions(instance) == []

    status, stdout, stderr = run_check(instance, env, monkeypatch, capsys)

    assert status == 0, stderr
    result = json.loads(stdout)
    assert result["orphans"] == ["wiki/concepts/orphan.qmd"]
    assert result["stale_citations"][0]["page"] == "wiki/concepts/orphan.qmd"


def _outside_regions(instance):
    result = {}
    for path in sorted((instance / "wiki").rglob("*.qmd")):
        data = path.read_bytes()
        spans, _ = scan(
            path.relative_to(instance).as_posix(), data.decode("utf-8")
        )
        lines = data.splitlines(keepends=True)
        for span in reversed(spans):
            del lines[span["start"] + 1 : span["end"] - 1]
        result[path.relative_to(instance).as_posix()] = b"".join(lines)
    return result


def test_update_changes_only_region_text_and_is_idempotent(
    tmp_path, monkeypatch, capsys
):
    instance, env = make_instance(tmp_path)
    with monkeypatch.context() as patcher:
        for name, value in env.items():
            patcher.setenv(name, value)
        cache = Path(env["XDG_CACHE_HOME"]) / "verbose-broccoli"
        cache_before = tree_hash(cache)
        outside_before = _outside_regions(instance)
        assert main(["update", "--wiki", instance.name]) == 0
        output = capsys.readouterr()
        assert output.err == ""
        assert json.loads(output.out) == {"problems": []}
        assert _outside_regions(instance) == outside_before
        assert tree_hash(cache) == cache_before
        after_first = tree_hash(instance)
        assert main(["update", "--wiki", instance.name]) == 0
        capsys.readouterr()
        assert tree_hash(instance) == after_first


def test_invalid_wiki_name_is_an_argument_error(tmp_path, monkeypatch, capsys):
    del capsys  # Unused.
    _, env = make_instance(tmp_path)
    with monkeypatch.context() as patcher:
        for name, value in env.items():
            patcher.setenv(name, value)
        with pytest.raises(SystemExit) as error:
            main(["check", "--wiki", "../invalid"])
    assert error.value.code == 2
