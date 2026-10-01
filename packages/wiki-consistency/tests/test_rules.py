"""Synthetic checks for Vale-backed Wiki page rules."""

import csv
import json
from pathlib import Path
from types import SimpleNamespace

from conftest import make_instance
from conftest import tree_hash
from conftest import update_regions
import pytest

from wiki_consistency.lint import check
import wiki_consistency.rules as rules

STUDENTS = ("가라온", "나하늘", "다하늘")
IDS = ("2100000001", "2100000002", "2100000003")
ROMANIZED = ("Ga Raon", "Na Haneul", "Da Haneul")
GUARDIAN = "다누리"
SCHOOL = "가상별학교"
QUOTES = (('"', '"'), ("“", "”"), ("‘", "’"), ("「", "」"), ("『", "』"))


@pytest.fixture(autouse=True)
def private_cache(monkeypatch, tmp_path):
    cache = tmp_path / "xdg-cache"
    (cache / "verbose-broccoli").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache))


def _config(tmp_path):
    return (
        tmp_path
        / "xdg-config"
        / "verbose-broccoli"
        / "backfire"
        / "education.toml"
    )


def _roster(tmp_path):
    return tmp_path / "synthetic-roster" / "education-roster.csv"


def write_roster(tmp_path, rows=None):
    rows = rows or [
        (STUDENTS[0], SCHOOL, GUARDIAN, IDS[0], ROMANIZED[0]),
        (STUDENTS[1], "", "", IDS[1], ROMANIZED[1]),
        (STUDENTS[2], "", "", IDS[2], ROMANIZED[2]),
    ]
    path = _roster(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("name", "school", "guardians", "id", "romanized"))
        writer.writerows(rows)
    config = _config(tmp_path)
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(f"roster = {json.dumps(str(path))}\n", encoding="utf-8")
    return path


def ready_vault(tmp_path):
    instance, _ = make_instance(tmp_path)
    assert update_regions(instance) == []
    return instance


def write_overview(instance, body):
    (instance / "wiki" / "overview.md").write_text(
        f"# Overview\n{body.rstrip()}\n", encoding="utf-8"
    )


def checked(instance, tmp_path):
    cache = tmp_path / "xdg-cache" / "verbose-broccoli"
    watched = (instance, cache, _config(tmp_path), _roster(tmp_path))
    before = tuple(tree_hash(path) for path in watched)
    result = check(instance)
    assert tuple(tree_hash(path) for path in watched) == before
    return result["problems"]


def checked_rules(instance, tmp_path):
    cache = tmp_path / "xdg-cache" / "verbose-broccoli"
    before = tree_hash(instance), tree_hash(cache)
    result = rules.check(instance)
    assert (tree_hash(instance), tree_hash(cache)) == before
    return result


def assert_rule(problems, document, line, rule, matched=None):
    matches = [
        item
        for item in problems
        if item["document"] == document
        and item["line"] == line
        and item["message"].startswith(f"page rule {rule}:")
    ]
    assert len(matches) == 1, problems
    if matched:
        assert matched not in matches[0]["message"]


def has_rule(problems, rule, document=None):
    return any(
        item["message"].startswith(f"page rule {rule}:")
        and (document is None or item["document"] == document)
        for item in problems
    )


@pytest.mark.parametrize(
    ("rule", "body", "matched"),
    [
        ("phone", "Call 010-0000-0000.", "010-0000-0000"),
        (
            "email",
            "Write to synthetic@example.invalid.",
            "synthetic@example.invalid",
        ),
        ("id-number", "Record 990101-1000000.", "990101-1000000"),
        ("address", "Meet at Fiction-ro 12.", "Fiction-ro 12"),
        ("address", "Meet at 무지개길 12.", "무지개길 12"),
        ("address", "Meet at 12, Fiction-ro.", "12, Fiction-ro"),
        ("address", "Meet at 12-3번지.", "12-3번지"),
        ("english", "The page contains 學生.", "學生"),
        ("english", "The page contains 学生です.", "学生です"),
        ("school", SCHOOL, SCHOOL),
        ("date", "Recorded on 2026.09.29.", "2026.09.29"),
        ("time", "The class starts at 14:30.", "14:30"),
    ],
)
def test_page_rules_report_page_and_line_without_the_match(
    tmp_path, rule, body, matched
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, rule, matched)


@pytest.mark.parametrize(
    "stem",
    (
        "s-2100000009",
        f"s-{ROMANIZED[0]}",
        IDS[0],
        f"S-{IDS[0]}",
        STUDENTS[0],
    ),
)
def test_student_page_must_be_named_by_a_roster_id(tmp_path, stem):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "students" / f"{stem}.md"
    page.parent.mkdir()
    page.write_text("# Student\n", encoding="utf-8")

    problems = checked(instance, tmp_path)

    assert_rule(
        problems, page.relative_to(instance).as_posix(), 1, "student-roster"
    )


def test_student_page_named_by_a_roster_id_passes(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "students" / f"s-{IDS[0]}.md"
    page.parent.mkdir()
    page.write_text("# Student\n", encoding="utf-8")

    assert checked_rules(instance, tmp_path) == []


@pytest.mark.parametrize("opening, closing", QUOTES)
@pytest.mark.parametrize("form", ("original-first", "translation-first"))
def test_short_translated_quotes_allow_cjk(tmp_path, opening, closing, form):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    original = f"{opening}學生{closing}"
    translation = f"{opening}meaning{closing}"
    body = (
        f"{original} ({translation})"
        if form == "original-first"
        else f"{translation} ({original})"
    )
    write_overview(instance, body)

    assert not has_rule(checked(instance, tmp_path), "english"), (
        "translated quote should pass"
    )


def test_unquoted_translation_after_original_is_allowed(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "“學生” (meaning)")

    assert not has_rule(checked(instance, tmp_path), "english"), (
        "translation may be unquoted"
    )


def test_overlong_quote_and_cjk_in_translation_fail(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(
        instance, f"“{'學' * 101}” (meaning)\n\n“學生” (meaning 学生)"
    )

    problems = checked(instance, tmp_path)

    assert has_rule(problems, "english", "wiki/overview.md")


def test_translated_quote_of_100_characters_passes(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"“{'學' * 100}” (meaning)")

    assert not has_rule(
        checked(instance, tmp_path), "english", "wiki/overview.md"
    )


@pytest.mark.parametrize("name", (STUDENTS[0], "하늘", GUARDIAN))
@pytest.mark.parametrize(
    "template",
    (
        "{}.",
        "“{}” (meaning)",
        "“meaning” (“{}”)",
    ),
)
def test_korean_roster_names_fail_even_in_translated_quotes(
    tmp_path, name, template
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, template.format(name))

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "student-name", name)
    assert name not in json.dumps(problems, ensure_ascii=False)


def test_korean_roster_name_fails_in_front_matter_and_sources(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "overview.md"
    page.write_text(
        f"---\ntitle: {STUDENTS[0]}\nsources:\n  - {GUARDIAN}\n---\n"
        "# Overview\n",
        encoding="utf-8",
    )

    problems = checked_rules(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "student-name", STUDENTS[0])
    assert_rule(problems, "wiki/overview.md", 4, "student-name", GUARDIAN)


def test_romanized_roster_names_and_other_hangul_pass_the_name_rule(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"{ROMANIZED[0]}; Haneul; 가상인물.")

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "student-name")
    assert has_rule(problems, "english", "wiki/overview.md")


def test_roster_regex_metacharacters_do_not_break_vale(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path, [("나[하늘", "", "")])
    write_overview(instance, "나[하늘")

    assert has_rule(checked(instance, tmp_path), "english", "wiki/overview.md")


def test_roster_regex_metacharacters_do_not_match_loosely(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path, [("가.온", "", "")])
    write_overview(instance, "가x온")

    assert has_rule(checked(instance, tmp_path), "english", "wiki/overview.md")


def test_roster_name_followed_by_a_particle_still_fails_english(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"{STUDENTS[0]}은 good.")

    assert has_rule(checked(instance, tmp_path), "english", "wiki/overview.md")


def test_roster_school_name_is_flagged_but_a_translated_quote_passes(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, SCHOOL)

    problems = checked(instance, tmp_path)

    assert has_rule(problems, "school", "wiki/overview.md")
    assert has_rule(problems, "english", "wiki/overview.md")
    assert SCHOOL not in json.dumps(problems, ensure_ascii=False)

    write_overview(instance, f"“{SCHOOL}” (fiction)\n\n學生")
    problems = checked(instance, tmp_path)
    assert not has_rule(problems, "school"), "quoted school should pass"
    assert has_rule(problems, "english"), "unquoted CJK should still be checked"


@pytest.mark.parametrize(
    ("rule", "body", "matched"),
    [
        ("time", "[a](https://example.invalid/15:54:00.420)", "15:54:00.420"),
        (
            "phone",
            "[a](https://example.invalid/010-0000-0000)",
            "010-0000-0000",
        ),
        (
            "email",
            "[a](https://example.invalid/synthetic@example.test)",
            "synthetic@example.test",
        ),
        ("phone", "“學生” (meaning 010-1234-5678)", "010-1234-5678"),
        (
            "id-number",
            "[a](https://example.invalid/000229-3000000)",
            "000229-3000000",
        ),
        ("address", "[a](</home/user/무지개길 12.pdf>)", "무지개길 12"),
        ("phone", "Use `010-0000-0000` in a code sample.", "010-0000-0000"),
        ("time", "Use `15:54:00.420` in a code sample.", "15:54:00.420"),
    ],
)
def test_privacy_and_time_rules_check_code_and_link_targets(
    tmp_path, rule, body, matched
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    assert_rule(
        checked(instance, tmp_path), "wiki/overview.md", 2, rule, matched
    )


def test_language_school_and_date_skip_link_targets(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(
        instance,
        f"[Original](/home/user/Documents/{SCHOOL}/기록.pdf) "
        "[Date](https://example.invalid/2026/09/29)",
    )

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "english", "wiki/overview.md")
    assert not has_rule(problems, "school", "wiki/overview.md")
    assert not has_rule(problems, "date", "wiki/overview.md")


def test_phone_rule_skips_slack_link_numbers_but_not_other_phones(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    skipped = (
        "[a](https://w1012345678-iwc1.slack.invalid/archives/C1/p1)",
        "[b](https://w1-iwc1012345678.slack.invalid/archives/C1/p1)",
        "[c](https://slack.invalid/p?thread_ts=1712345678.123456)",
        "[d](https://slack.invalid/p?a=1&latest=1712345678%2E123456)",
    )
    reported = (
        "Call 010-1234-5678.",
        "Call010-1234-5678.",
        "[e](https://example.invalid/c?thread_ts=010-1234-5678)",
        "[f](https://example.invalid/c?ts=010-1234-5678)",
        "`contacts=01012345678`",
        "[g](/w010-1234-5678)",
    )
    write_overview(instance, "\n".join(skipped) + "\n\n" + "\n".join(reported))

    problems = checked(instance, tmp_path)

    for line in range(7, 7 + len(reported)):
        assert_rule(problems, "wiki/overview.md", line, "phone")
    assert sum(has_rule([item], "phone") for item in problems) == len(reported)


def test_hangul_link_text_still_fails_english(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(
        instance, f"[{SCHOOL}](https://example.invalid/original.pdf)"
    )

    assert has_rule(checked(instance, tmp_path), "english", "wiki/overview.md")


@pytest.mark.parametrize(
    ("rule", "body"),
    [
        ("english", f"Keep `{SCHOOL}` as code."),
        ("date", "Recorded `2026.09.29`."),
        ("english", f"\n\n```text\n{SCHOOL}\n```"),
        ("date", "\n\n```text\n2026.09.29\n```"),
    ],
)
def test_text_rules_skip_code(tmp_path, rule, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    assert not has_rule(checked(instance, tmp_path), rule, "wiki/overview.md")


def test_date_rule_flags_common_non_iso_forms(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(
        instance,
        "2026.09.29; 2026/9/29; 2026-9-29; 29.09.2026; "
        "9/29/26; September 29, 2026; 29th of September; "
        "2026년 9월 29일; 9월 29일",
    )

    problems = checked(instance, tmp_path)

    assert has_rule(problems, "date", "wiki/overview.md")


def test_iso_shaped_impossible_date_passes_and_valid_iso_dates_pass(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "2026-02-30; 2026-09-29")

    assert not has_rule(checked(instance, tmp_path), "date", "wiki/overview.md")


def test_fraction_and_partial_dates_pass(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(
        instance,
        "85/100, 3/4, September 2026; 20260928T010203000000Z "
        "and 0199a0e2-7c1b-7d3e-9f00-000000000000.",
    )

    assert not has_rule(checked(instance, tmp_path), "date", "wiki/overview.md")


def test_invalid_registration_birth_date_is_still_flagged(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "Record 990232-1000000.")

    assert_rule(
        checked(instance, tmp_path),
        "wiki/overview.md",
        2,
        "id-number",
        "990232-1000000",
    )


@pytest.mark.parametrize(
    "body",
    [
        "At 14:30Z.",
        "At 14:30 +09:00.",
        "At 14:30 +0900.",
        "At 14:30 UTC+09:00.",
        "At 14:30 (UTC+09:00).",
        "At 14:30 (UTC-05:00).",
        "At 14:30 +14:59.",
        "At 3 PM UTC.",
        "At 2026-09-29T14:30:00-05:00.",
        "At 14:00–15:30 UTC+9.",
    ],
)
def test_time_rule_allows_zoned_forms_and_ranges(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    assert not has_rule(checked(instance, tmp_path), "time", "wiki/overview.md")


@pytest.mark.parametrize(
    "body",
    [
        "At 14:30.",
        "At 14:30 +99:99.",
        "At 14:30 +15:00.",
        "At 14:30 +14:60.",
        "At 14:30 -05:00.",
        "From 9:00 -10:00 today.",
        "At 14:30 KST.",
        "At 3 PM.",
        "At 14:00–15:30.",
    ],
)
def test_time_rule_flags_unzoned_or_invalid_forms(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    assert has_rule(checked(instance, tmp_path), "time", "wiki/overview.md")


def test_fractional_seconds_require_a_zone(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "Retrieved 15:54:00.420.")

    assert has_rule(checked(instance, tmp_path), "time", "wiki/overview.md")


@pytest.mark.parametrize("zone", ("Z", "+09:00"))
def test_fractional_iso_seconds_with_zone_pass(tmp_path, zone):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"Retrieved 2026-09-27T15:54:00.420{zone}.")

    assert not has_rule(checked(instance, tmp_path), "time", "wiki/overview.md")


def test_text_scope_front_matter_and_log_are_skipped_by_page_rules(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    alpha.write_text(
        alpha.read_text(encoding="utf-8").replace(
            "title: Alpha",
            "title: 2026.09.29",
        ),
        encoding="utf-8",
    )
    (instance / "wiki" / "log.md").write_text(
        "010-0000-0000 synthetic@example.invalid 2026.09.29\n",
        encoding="utf-8",
    )

    assert checked_rules(instance, tmp_path) == []


def test_non_privacy_rules_skip_front_matter(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "overview.md"
    page.write_text(
        "---\ntitle: 2026.09.29 14:30 學生 가상별학교\n---\n# Overview\n",
        encoding="utf-8",
    )

    problems = checked_rules(instance, tmp_path)

    for rule in ("date", "time", "english", "school"):
        assert not has_rule(problems, rule, "wiki/overview.md")


def test_privacy_rules_check_page_title_but_skip_sources(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "overview.md"
    page.write_text(
        "---\ntitle: 010-0000-0000\nsources:\n"
        "  - 010-0000-0000\n---\n# Overview\n",
        encoding="utf-8",
    )

    problems = checked_rules(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "phone", "010-0000-0000")
    assert not any(
        item["document"] == "wiki/overview.md"
        and item["line"] == 4
        and item["message"].startswith("page rule phone:")
        for item in problems
    )


def test_privacy_rules_skip_unindented_sources_list(tmp_path):
    instance = ready_vault(tmp_path)
    page = instance / "wiki" / "overview.md"
    # PyYAML writes a list under a key without indenting its items.
    page.write_text(
        "---\ntitle: Overview\nsources:\n- id: 010-0000-0000\n"
        "summary: 010-0000-0000\n---\n# Overview\n",
        encoding="utf-8",
    )

    problems = checked_rules(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 5, "phone", "010-0000-0000")
    assert not any(
        item["document"] == "wiki/overview.md"
        and item["line"] == 4
        and item["message"].startswith("page rule phone:")
        for item in problems
    )


def test_raw_scope_finds_front_matter_and_cog_without_python_filter(
    monkeypatch, tmp_path
):
    instance = ready_vault(tmp_path)
    page = instance / "wiki" / "overview.md"
    page.write_text(
        "---\ntitle: 010-0000-0000\n---\n\n"
        "<!-- [[[cog synthetic ]]] -->\n010-0000-0000\n<!-- [[[end]]] -->\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(rules, "_ignored_lines", lambda *_: set())

    problems = rules.check(instance)

    assert_rule(problems, "wiki/overview.md", 2, "phone", "010-0000-0000")
    assert_rule(problems, "wiki/overview.md", 6, "phone", "010-0000-0000")


def test_cog_regions_are_skipped_but_malformed_markers_are_checked(tmp_path):
    instance = ready_vault(tmp_path)
    page = instance / "wiki" / "overview.md"
    page.write_text(
        "# Overview\n<!-- [[[cog synthetic ]]] -->\n"
        "010-0000-0000\n<!-- [[[end]]] -->\n",
        encoding="utf-8",
    )
    assert not has_rule(checked(instance, tmp_path), "phone")

    page.write_text(
        "# Overview\n<!-- [[[cog synthetic ]]] -->\n"
        "010-0000-0000\n<!-- [[[end] ] -->\n",
        encoding="utf-8",
    )
    assert has_rule(checked(instance, tmp_path), "phone")


def test_roster_is_not_read_without_a_student_page_or_untranslated_cjk(
    tmp_path,
):
    instance = ready_vault(tmp_path)
    _config(tmp_path).unlink(missing_ok=True)
    write_overview(instance, "Ordinary English text.")

    assert not has_rule(checked(instance, tmp_path), "roster")


@pytest.mark.parametrize(
    "failure",
    ("missing-config", "relative-path", "missing-csv", "missing-name"),
)
def test_roster_failures_report_once_and_hide_language_findings(
    tmp_path, failure
):
    instance = ready_vault(tmp_path)
    write_overview(instance, "學生")
    config, roster = _config(tmp_path), _roster(tmp_path)
    if failure != "missing-config":
        config.parent.mkdir(parents=True, exist_ok=True)
        if failure == "relative-path":
            config.write_text('roster = "relative.csv"\n', encoding="utf-8")
        elif failure == "missing-csv":
            config.write_text(
                f"roster = {json.dumps(str(roster))}\n", encoding="utf-8"
            )
        else:
            roster.parent.mkdir(parents=True)
            roster.write_text(f"student\n{STUDENTS[0]}\n", encoding="utf-8")
            config.write_text(
                f"roster = {json.dumps(str(roster))}\n", encoding="utf-8"
            )

    problems = checked(instance, tmp_path)
    roster_problems = [
        item
        for item in problems
        if item["document"] == "wiki"
        and item["line"] == 1
        and item["message"].startswith("page rule roster:")
    ]

    assert len(roster_problems) == 1, problems
    expected = (
        str(config)
        if failure in {"missing-config", "relative-path"}
        else str(roster)
    )
    assert expected in roster_problems[0]["message"]
    assert sum("page rule" in item["message"] for item in problems) == 1


def test_cache_temp_is_private_and_cleaned(monkeypatch, tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "Ordinary English text.")
    seen = []
    temporary = []

    def run(command, **kwargs):
        config = Path(command[2])
        temporary.append(config.parent)
        seen.append(config.parent.stat().st_mode & 0o777)
        seen.append(
            tuple(key for key in kwargs["env"] if key.startswith("VALE_"))
        )
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setenv("VALE_CONFIG_PATH", "/untrusted/config")
    monkeypatch.setenv("VALE_CPUPROFILE", "/untrusted/profile")
    monkeypatch.setattr(rules.subprocess, "run", run)

    assert checked_rules(instance, tmp_path) == []
    assert seen == [0o700, ()]
    assert len(temporary) == 1 and not temporary[0].exists()


def test_vale_arguments_use_explicit_config_and_verified_files(
    monkeypatch, tmp_path
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "學生")
    seen = []
    loaded = []
    original_load = rules.load_roster

    def load_roster():
        loaded.append(True)
        return original_load()

    def run(command, **kwargs):
        seen.append((command, kwargs["cwd"]))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(rules.subprocess, "run", run)
    monkeypatch.setattr(rules, "load_roster", load_roster)
    assert checked_rules(instance, tmp_path) == []

    assert loaded == [True]
    assert len(seen) == 1
    command, cwd = seen[0]
    assert command[:5] == [
        "vale",
        "--config",
        command[2],
        "--no-global",
        "--output=line",
    ]
    assert Path(command[2]).is_absolute()
    assert cwd == instance
    assert command[5:]
    assert all((instance / path).is_file() for path in command[5:])
    assert all(
        (instance / path).resolve().is_relative_to(instance / "wiki")
        for path in command[5:]
    )


def test_canary_output_never_contains_synthetic_phone_or_name(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "Call 010-0000-0000 about 가상인물.")

    output = json.dumps(checked(instance, tmp_path), ensure_ascii=False)

    assert "010-0000-0000" not in output
    assert "가상인물" not in output


def test_symlinked_markdown_and_directories_are_not_linted(tmp_path):
    instance = ready_vault(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("Call 010-0000-0000.", encoding="utf-8")
    (instance / "wiki" / "linked.md").symlink_to(outside)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "nested.md").write_text(
        "Call 010-0000-0000.", encoding="utf-8"
    )
    (instance / "wiki" / "linked-dir").symlink_to(outside_dir)

    assert not has_rule(checked_rules(instance, tmp_path), "phone")


def test_a_link_leaving_the_wiki_does_not_skip_the_other_pages(tmp_path):
    instance = ready_vault(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("Nothing here.", encoding="utf-8")
    (instance / "wiki" / "linked.md").symlink_to(outside)
    write_overview(instance, "Call 010-0000-0000.")

    assert has_rule(
        checked_rules(instance, tmp_path), "phone", "wiki/overview.md"
    )
