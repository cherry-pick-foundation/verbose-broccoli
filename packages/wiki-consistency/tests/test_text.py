"""Synthetic retained-text, exact-locator and run-cache regressions."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal

from conftest import SOURCE_ID
from conftest import add_revision
import pytest
import yaml

from wiki_consistency import evidence
from wiki_consistency.instance import revisions

BODY = (
    "uncited preamble SENTINEL\n"
    "## Page 25 {#p-25}\n"
    "합성 본문 Alpha.\n\n"
    "## Page 26 {#p-26}\n"
    "Texte synthétique Beta.\n"
    "## Page 27 {#p-27}\n"
    "uncited tail SENTINEL\n"
)


def retained(tmp_path, body=BODY):
    root = tmp_path / "vault"
    add_revision(root, "r1", body)
    selected = revisions(root)
    evidence.convert(root, "synthetic", tmp_path / "cache", selected)
    return root, root / "text" / SOURCE_ID / "r1.qmd", selected


def change_header(path, **fields):
    document = path.read_bytes().decode()
    front, body = document.split("---\n", 2)[1:]
    metadata = yaml.safe_load(front)
    metadata.update(fields)
    path.write_text("---\n" + yaml.safe_dump(metadata) + "---\n" + body)


def test_retention_reuse_original_language_revisions_and_cache_deletion(
    tmp_path, monkeypatch
):
    root, path, selected = retained(tmp_path)
    original = path.read_bytes()
    raw = root / selected[SOURCE_ID][0]["path"] / "data/document.txt"
    before = raw.read_bytes()

    def forbidden():
        raise AssertionError(
            "existing retained text must not construct a converter"
        )

    monkeypatch.setattr(evidence, "MarkItDown", forbidden)
    result = evidence.convert(root, "synthetic", tmp_path / "cache", selected)
    assert result["present"] == 1
    assert evidence.read(root, SOURCE_ID, "r1")["text"] == BODY
    assert (
        evidence.read(root, SOURCE_ID, "r1")["checked-against-original"]
        is False
    )
    assert path.read_bytes() == original
    assert raw.read_bytes() == before
    add_revision(root, "r2", "新しい合成テキスト\n")
    evidence.convert(root, "synthetic", tmp_path / "cache", revisions(root))
    assert (path.parent / "r2.qmd").is_file()
    assert path.read_bytes() == original
    shutil.rmtree(tmp_path / "cache", ignore_errors=True)
    assert evidence.read(root, SOURCE_ID, "r1")["text"] == BODY


def test_actual_converter_runs_once_and_corrections_are_reused(
    tmp_path, monkeypatch
):
    root = tmp_path / "vault"
    bag = add_revision(root, "r1", '{"text":"Texte synthétique"}')
    # Select the existing JSON converter using a truthful synthetic manifest.
    payload = bag / "data/document.txt"
    payload.rename(payload.with_suffix(".json"))
    manifest = bag / "manifest-sha256.txt"
    manifest.write_text(
        manifest.read_text().replace("document.txt", "document.json")
    )
    original_convert = evidence.MarkItDown.convert
    calls = []

    def counted_convert(converter, path):
        calls.append(path)
        return original_convert(converter, path)

    monkeypatch.setattr(evidence.MarkItDown, "convert", counted_convert)
    evidence.convert(root, "synthetic", tmp_path / "cache", revisions(root))
    path = root / "text" / SOURCE_ID / "r1.qmd"
    path.write_text(path.read_text().replace("synthétique", "corrigé"))
    before = path.read_bytes()
    shutil.rmtree(tmp_path / "cache", ignore_errors=True)
    result = evidence.convert(
        root, "synthetic", tmp_path / "cache", revisions(root)
    )
    assert calls == [bag / "data/document.json"]
    assert result["present"] == 1
    assert path.read_bytes() == before
    assert "corrigé" in evidence.read(root, SOURCE_ID, "r1")["text"]


@pytest.mark.parametrize(
    "locator,expected",
    [
        ("p.25", "합성 본문 Alpha.\n\n"),
        (
            "pp.25-26",
            "합성 본문 Alpha.\n\n## Page 26 {#p-26}\nTexte synthétique Beta.\n",
        ),
    ],
)
def test_exact_pages_and_line_ranges_without_front_matter_or_sentinel(
    tmp_path, locator, expected
):
    root, path, _ = retained(tmp_path)
    item = evidence.read_located(root, SOURCE_ID, "r1", locator, max_chars=1000)
    assert item["text"] == expected
    assert "SENTINEL" not in item["text"]
    assert "checked-against-original:" not in item["text"]
    assert item["sha256"] == hashlib.sha256(BODY.encode()).hexdigest()
    assert (
        item["extraction-sha256"]
        == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert item["id"] == f"{SOURCE_ID}/r1"
    assert item["locator"] == locator
    assert (
        "".join(
            path.read_text().splitlines(keepends=True)[
                item["first_line"] - 1 : item["last_line"]
            ]
        )
        == expected
    )


def test_sections_stop_at_next_same_or_higher_heading(tmp_path):
    body = (
        "# Root\n## Purpose {#sec-purpose}\nSelected.\n"
        "### Detail\nIncluded.\n## Next\nSENTINEL\n"
    )
    root, _, _ = retained(tmp_path, body)
    item = evidence.read_located(
        root, SOURCE_ID, "r1", "sec.purpose", max_chars=100
    )
    assert item["locator_ids"] == ["sec-purpose"]
    assert item["text"] == "Selected.\n### Detail\nIncluded.\n"


def test_fenced_page_markers_and_fake_code_markers(tmp_path):
    body = (
        "```markdown\n## Fake {#p-25}\n```\n::: {#p-25}\n"
        "Selected.\n:::\n::: {#p-26}\nSENTINEL\n:::\n"
    )
    root, _, _ = retained(tmp_path, body)
    item = evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=100)
    assert item["text"] == "Selected.\n"


@pytest.mark.parametrize("ending", ["", "::: {.nested}\nMore.\n:::\n:::\n"])
def test_ambiguous_page_div_bounds_fail(tmp_path, ending):
    root, _, _ = retained(tmp_path, "::: {#p-25}\nSelected.\n" + ending)
    with pytest.raises(ValueError, match="ambiguous page div"):
        evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=100)


def test_page_div_range_is_one_exact_slice_with_final_delimiter_excluded(
    tmp_path,
):
    body = "::: {#p-25}\nAlpha.\n:::\n\n::: {#p-26}\nBeta.\n:::\nOUTSIDE\n"
    root, path, _ = retained(tmp_path, body)
    item = evidence.read_located(
        root, SOURCE_ID, "r1", "pp.25-26", max_chars=100
    )
    assert item["text"] == "Alpha.\n:::\n\n::: {#p-26}\nBeta.\n"
    assert (
        "".join(
            path.read_bytes()
            .decode()
            .splitlines(keepends=True)[
                item["first_line"] - 1 : item["last_line"]
            ]
        )
        == item["text"]
    )


@pytest.mark.parametrize(
    "locator,body,error",
    [
        ("p.24", BODY, "missing"),
        ("p.0", BODY, "out-of-range"),
        ("pp.26-25", BODY, "out-of-range"),
        ("pp.25-27", BODY.replace("{#p-26}", "{#p-28}"), "missing"),
        (
            "pp.25-26",
            BODY.replace(
                "## Page 26", "## Insert {#p-40}\nUnexpected.\n## Page 26"
            ),
            "noncontiguous",
        ),
        ("p.25", BODY + "## Duplicate {#p-25}\nDup.\n", "duplicate"),
        ("p.25", "## Empty {#p-25}\n## Next {#p-26}\nBody\n", "absent located"),
        ("chapter.25", BODY, "unsupported"),
    ],
)
def test_missing_duplicate_range_empty_and_unsupported_locators(
    tmp_path, locator, body, error
):
    root, _, _ = retained(tmp_path, body)
    with pytest.raises(ValueError, match=error):
        evidence.read_located(root, SOURCE_ID, "r1", locator, max_chars=1000)


def test_span_budget_and_absent_text_fail_without_fallback(tmp_path):
    root, path, _ = retained(tmp_path)
    with pytest.raises(ValueError, match="oversized"):
        evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=1)
    path.unlink()
    with pytest.raises(LookupError, match="absent"):
        evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=100)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source-id", "other"),
        ("revision", "r2"),
        ("sha256", "a" * 64),
    ],
)
def test_header_identity_mismatch_does_not_clobber(tmp_path, field, value):
    root, path, selected = retained(tmp_path)
    change_header(path, **{field: value})
    before = path.read_bytes()
    with pytest.raises(ValueError, match="identity mismatch"):
        evidence.convert(root, "synthetic", tmp_path / "cache", selected)
    assert path.read_bytes() == before


def test_unknown_legacy_fields_and_partial_output_are_not_proven_evidence(
    tmp_path,
):
    root, path, _ = retained(tmp_path)
    change_header(
        path,
        converter=None,
        **{"checked-against-original": None, "conversion-status": None},
    )
    item = evidence.read(root, SOURCE_ID, "r1")
    assert item["converter"] == {"name": None, "version": None}
    assert item["checked-against-original"] is None
    assert len(item["problems"]) == 4
    with pytest.raises(ValueError, match="unknown"):
        evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=100)
    change_header(
        path,
        converter={"name": "known", "version": "1"},
        **{"checked-against-original": False, "conversion-status": "partial"},
    )
    with pytest.raises(ValueError, match="partial"):
        evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=100)


@pytest.mark.parametrize("correction", ["body", "header"])
def test_correction_changes_hash_and_invalidates_review(tmp_path, correction):
    root, path, _ = retained(tmp_path)
    change_header(path, **{"checked-against-original": True})
    item = evidence.read(root, SOURCE_ID, "r1")
    assert item["checked-against-original"] is None
    review = {
        "sha256": item["sha256"],
        "extraction-sha256": item["extraction-sha256"],
        "evidence": "Synthetic explicit original-review receipt",
    }
    checked = evidence.read(root, SOURCE_ID, "r1", review=review)
    assert checked["checked-against-original"] is True
    evidence.read_located(
        root, SOURCE_ID, "r1", "p.25", max_chars=100, review=review
    )
    if correction == "body":
        path.write_text(path.read_text().replace("Alpha.", "Corrected."))
    else:
        change_header(path, **{"conversion-warning": "Synthetic correction"})
    corrected = evidence.read(root, SOURCE_ID, "r1", review=review)
    assert corrected["extraction-sha256"] != checked["extraction-sha256"]
    assert corrected["checked-against-original"] is None
    with pytest.raises(ValueError, match="review evidence"):
        evidence.read_located(
            root, SOURCE_ID, "r1", "p.25", max_chars=100, review=review
        )


@pytest.mark.parametrize(
    "component", ["..", "../escape", "a/b", "a\\b", "", "\0"]
)
def test_invalid_text_path_components(tmp_path, component):
    with pytest.raises(ValueError, match="component"):
        evidence.read(tmp_path, component, "r1")


@pytest.mark.parametrize(
    "part", ["text", "text/source", "raw", "payload", "header"]
)
def test_symlink_paths_fail_without_following(tmp_path, part):
    root, path, selected = retained(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = {
        "text": root / "text",
        "text/source": path.parent,
        "raw": root / "raw",
        "payload": root / selected[SOURCE_ID][0]["path"] / "data/document.txt",
        "header": path,
    }[part]
    moved = outside / "moved"
    victim.rename(moved)
    victim.symlink_to(moved, target_is_directory=moved.is_dir())
    with pytest.raises(ValueError, match="symlink"):
        evidence.read(root, SOURCE_ID, "r1")


def test_escaping_raw_records_and_changed_hash_fail(tmp_path):
    root, _, selected = retained(tmp_path)
    item = selected[SOURCE_ID][0]
    with pytest.raises(ValueError, match="escapes"):
        evidence._payload_path(root, {**item, "path": "../outside"})
    (root / item["path"] / "data/document.txt").write_text("changed raw")
    with pytest.raises(ValueError, match="raw SHA-256 changed"):
        evidence.read(root, SOURCE_ID, "r1")


@pytest.mark.parametrize(
    "field,value",
    [
        ("External-Identifier", "other"),
        ("Admission-Time", "r2"),
    ],
)
def test_raw_record_identity_mismatch(tmp_path, field, value):
    root, _, selected = retained(tmp_path)
    info = root / selected[SOURCE_ID][0]["path"] / "bag-info.txt"
    before = SOURCE_ID if field == "External-Identifier" else "r1"
    info.write_text(
        info.read_text().replace(f"{field}: {before}", f"{field}: {value}")
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        evidence.read(root, SOURCE_ID, "r1")


def test_ambiguous_raw_identity_fails_before_retaining(tmp_path):
    root = tmp_path / "vault"
    bag = add_revision(root, "r1", BODY)
    selected = revisions(root)
    shutil.copytree(bag, root / "raw/another-kind" / SOURCE_ID / "r1")
    with pytest.raises(ValueError, match="ambiguous"):
        evidence.convert(root, "synthetic", tmp_path / "cache", selected)
    assert not (root / "text" / SOURCE_ID / "r1.qmd").exists()


def test_pdf_boundaries_are_preserved_without_invented_page_numbers(tmp_path):
    body = "Texte synthétique\fAutre page\f"
    root, _, _ = retained(tmp_path, body)
    item = evidence.read(root, SOURCE_ID, "r1")
    assert item["text"] == body
    assert item["problems"] == ["missing locator evidence"]
    with pytest.raises(ValueError, match="locator evidence"):
        evidence.read_located(root, SOURCE_ID, "r1", "p.1", max_chars=100)


def test_formfeeds_do_not_change_marker_line_numbers(tmp_path):
    body = "## First {#p-25}\nTexte\fencore.\n## Next {#p-26}\nSENTINEL\n"
    root, path, _ = retained(tmp_path, body)
    item = evidence.read_located(root, SOURCE_ID, "r1", "p.25", max_chars=100)
    assert item["text"] == "Texte\fencore.\n"
    lines = path.read_bytes().decode().split("\n")
    assert lines[item["first_line"] - 1] == "Texte\fencore."
    assert item["first_line"] == item["last_line"]


def test_atomic_conflict_keeps_winner(tmp_path, monkeypatch):
    target = tmp_path / "target.qmd"
    link = os.link

    def racing_link(source, destination):
        Path(destination).write_bytes(b"existing correction")
        return link(source, destination)

    monkeypatch.setattr(evidence.os, "link", racing_link)
    assert not evidence._write_immutable(target, b"conversion", tmp_path, 100)
    assert target.read_bytes() == b"existing correction"
    assert not list(tmp_path.glob(f"*{evidence.TEMP_SUFFIX}"))


def test_old_cache_is_preserved_without_automatic_promotion(tmp_path):
    root = tmp_path / "vault"
    add_revision(root, "r1", BODY)
    old = (
        tmp_path
        / "cache/wiki-evidence/synthetic"
        / f"markitdown-{evidence.CONVERTER_VERSION}"
        / SOURCE_ID
        / "r1.md"
    )
    old.parent.mkdir(parents=True)
    old.write_text("Unknown old cache SENTINEL")
    evidence.convert(root, "synthetic", tmp_path / "cache", revisions(root))
    assert old.read_text() == "Unknown old cache SENTINEL"
    assert evidence.read(root, SOURCE_ID, "r1")["text"] == BODY


def test_bibliography_fresh_deterministic_private_cache_and_cleanup(tmp_path):
    root, _, selected = retained(tmp_path)
    env = {"XDG_CACHE_HOME": str(tmp_path / "xdg-cache")}
    outputs = []
    for _ in range(2):
        with evidence.bibliography(
            root, selected, budget_bytes=10000, env=env
        ) as path:
            assert path.is_relative_to(
                tmp_path / "xdg-cache/verbose-broccoli/wiki-bibliography"
            )
            assert path.stat().st_mode & 0o777 == 0o600
            assert path.parent.stat().st_mode & 0o777 == 0o700
            content = path.read_bytes()
            entries = json.loads(content)
            assert set(entries[0]) == {"id", "type", "title", "custom"}
            assert entries[0]["id"] == f"{SOURCE_ID}/r1"
            assert entries[0]["custom"]["source-id"] == SOURCE_ID
            assert entries[0]["custom"]["revision"] == "r1"
            assert (
                entries[0]["custom"]["sha256"]
                == hashlib.sha256(BODY.encode()).hexdigest()
            )
            assert entries[0]["custom"]["raw-provenance"] == {
                "kind": "files",
                "payload": "data/document.txt",
            }
            assert not any(
                key in entries[0]
                for key in ("author", "issued", "Internal-Sender-Identifier")
            )
            assert str(root).encode() not in content
            assert b"/synthetic/" not in content
            outputs.append((path, content))
        assert not path.parent.exists()
    assert outputs[0][0] != outputs[1][0]
    assert outputs[0][1] == outputs[1][1]
    assert not list(root.rglob("sources.json"))


@pytest.mark.parametrize("failure", ["budget", "exception", "interrupt"])
def test_bibliography_cleans_failure_and_interruption(tmp_path, failure):
    root, _, selected = retained(tmp_path)
    env = {"XDG_CACHE_HOME": str(tmp_path / "xdg-cache")}
    expected = {
        "budget": ValueError,
        "exception": RuntimeError,
        "interrupt": SystemExit,
    }[failure]
    with pytest.raises(expected):
        with evidence.bibliography(
            root,
            selected,
            budget_bytes=1 if failure == "budget" else 10000,
            env=env,
        ):
            if failure == "exception":
                raise RuntimeError("synthetic consumer failure")
            os.kill(os.getpid(), signal.SIGTERM)
    assert not list((tmp_path / "xdg-cache").rglob("run-*"))


@pytest.mark.parametrize("budget", [0, -1])
def test_positive_bibliography_budget_required(tmp_path, budget):
    with pytest.raises(ValueError, match="positive"):
        with evidence.bibliography(tmp_path, {}, budget_bytes=budget):
            pytest.fail("must not yield")


def test_bibliography_rejects_symlink_namespace(tmp_path):
    cache = tmp_path / "xdg-cache/verbose-broccoli"
    cache.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (cache / "wiki-bibliography").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        with evidence.bibliography(
            tmp_path,
            {},
            budget_bytes=100,
            env={"XDG_CACHE_HOME": str(cache.parent)},
        ):
            pytest.fail("must not yield")
    assert not list(outside.iterdir())
