import csv
import json

import pytest

from conftest import (
    REVISIONS,
    SOURCE_ID,
    add_revision,
    make_instance,
    tree_hash,
    update_regions,
)
from wiki_consistency.lint import check


STUDENTS = ("가라온", "나하늘", "다하늘")
GUARDIAN = "다누리"
SCHOOL = "가상별학교"
QUOTE_PAIRS = (('"', '"'), ("“", "”"), ("‘", "’"), ("「", "」"), ("『", "』"))


def _config_path(tmp_path):
    return (
        tmp_path
        / "xdg-config"
        / "verbose-broccoli"
        / "backfire"
        / "education.toml"
    )


def _roster_path(tmp_path):
    return tmp_path / "synthetic-roster" / "education-roster.csv"


def write_roster(tmp_path, rows=None):
    rows = rows or [
        (STUDENTS[0], SCHOOL, GUARDIAN),
        (STUDENTS[1], "", ""),
        (STUDENTS[2], "", ""),
    ]
    path = _roster_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("name", "school", "guardians"))
        writer.writerows(rows)
    config = _config_path(tmp_path)
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
    files = (instance, _config_path(tmp_path), _roster_path(tmp_path))
    before = tuple(tree_hash(path) for path in files)
    result = check(instance)
    assert tuple(tree_hash(path) for path in files) == before
    return result["problems"]


def assert_rule(problems, document, line, rule, matched):
    matches = [
        item
        for item in problems
        if item["document"] == document
        and item["line"] == line
        and f"page rule {rule}:" in item["message"]
    ]
    assert len(matches) == 1, problems
    assert matched not in matches[0]["message"]


def has_rule(problems, rule, document=None):
    return any(
        f"page rule {rule}:" in item["message"]
        and (document is None or item["document"] == document)
        for item in problems
    )


@pytest.mark.parametrize(
    "rule, body, matched",
    [
        pytest.param(
            "phone", "Call 010-0000-0000.", "010-0000-0000", id="phone"
        ),
        pytest.param(
            "email",
            "Write to synthetic@example.invalid.",
            "synthetic@example.invalid",
            id="email",
        ),
        pytest.param(
            "id-number",
            "Record 990101-1000000.",
            "990101-1000000",
            id="id-number",
        ),
        pytest.param(
            "address", "Meet at Fiction-ro 12.", "Fiction-ro 12", id="address"
        ),
        pytest.param(
            "english", "The page contains 學生.", "學生", id="english"
        ),
        pytest.param(
            "school", "Alpha Middle School.", "Alpha Middle School", id="school"
        ),
        pytest.param(
            "date", "Recorded on 2026.09.29.", "2026.09.29", id="date"
        ),
        pytest.param("time", "The class starts at 14:30.", "14:30", id="time"),
    ],
)
def test_page_rules_report_the_page_and_line_without_the_match(
    tmp_path, rule, body, matched
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, rule, matched)


def test_student_page_must_match_a_roster_name(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path, [(STUDENTS[0], "", "")])
    page = instance / "wiki" / "students" / f"{STUDENTS[1]}.md"
    page.parent.mkdir()
    page.write_text("# Student\n", encoding="utf-8")

    problems = checked(instance, tmp_path)

    assert_rule(
        problems,
        page.relative_to(instance).as_posix(),
        1,
        "student-roster",
        STUDENTS[1],
    )


@pytest.mark.parametrize(
    "rule, body",
    [
        pytest.param("phone", "Call extension 12345.", id="phone"),
        pytest.param("email", "Send a paper letter.", id="email"),
        pytest.param(
            "id-number", "Record 990232-1000000.", id="invalid-birth-date"
        ),
        pytest.param("address", "Meet at Fiction Road 12.", id="address"),
        pytest.param("english", STUDENTS[0], id="roster-name"),
        pytest.param("school", "Middle School alone.", id="school"),
        pytest.param(
            "date",
            "85/100, 3/4, September 2026; "
            "20260928T010203000000Z and 0199a0e2-7c1b-7d3e-9f00-000000000000.",
            id="not-dates",
        ),
        pytest.param("time", "2026-09-29T14:30:00-05:00.", id="zoned-iso-time"),
        pytest.param("time", "14:00–15:30 UTC+9.", id="zoned-range"),
    ],
)
def test_page_rules_allow_close_cases(tmp_path, rule, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, rule, "wiki/overview.md"), problems


def test_student_page_matches_roster_exactly(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "students" / f"{STUDENTS[0]}.md"
    page.parent.mkdir()
    page.write_text("# Student\n", encoding="utf-8")

    problems = checked(instance, tmp_path)

    assert not has_rule(
        problems, "student-roster", page.relative_to(instance).as_posix()
    ), problems


@pytest.mark.parametrize("opening, closing", QUOTE_PAIRS)
@pytest.mark.parametrize("form", ("original-first", "translation-first"))
def test_allowed_quotes_cover_both_forms_and_all_quote_pairs(
    tmp_path, opening, closing, form
):
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

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "english", "wiki/overview.md"), problems


def test_original_quote_may_have_an_unquoted_translation(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "“學生” (meaning)")

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "english", "wiki/overview.md"), problems


def test_quote_over_100_characters_fails_english(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    original = "學" * 101
    write_overview(instance, f"“{original}” (meaning)")

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "english", original)


def test_translation_with_cjk_outside_roster_names_fails_english(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "“學生” (meaning 学生)")

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "english", "学生")


def test_roster_student_given_and_guardian_names_are_allowed(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"{STUDENTS[0]}; 하늘; {GUARDIAN}.")

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "english", "wiki/overview.md"), problems


def test_roster_school_name_and_romanized_school_fail_school_rule(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"{SCHOOL}; Alpha Middle School.")

    problems = checked(instance, tmp_path)

    assert has_rule(problems, "school", "wiki/overview.md"), problems
    assert has_rule(problems, "english", "wiki/overview.md"), problems
    for item in problems:
        if "page rule school:" in item["message"]:
            assert (
                SCHOOL not in item["message"]
                and "Alpha Middle School" not in item["message"]
            )


def test_contact_rules_still_apply_inside_allowed_quotes(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "“學生 010-0000-0000” (meaning)")

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "phone", "010-0000-0000")


def test_sources_front_matter_and_log_are_not_checked(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    text = alpha.read_text(encoding="utf-8").replace(
        f"revision: {REVISIONS[-1]}",
        f"revision: {REVISIONS[-1]}\n    note: synthetic@example.invalid",
    )
    alpha.write_text(text, encoding="utf-8")
    (instance / "wiki" / "log.md").write_text(
        "## [2026-09-28] synthetic\n010-0000-0000 synthetic@example.invalid\n",
        encoding="utf-8",
    )

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "email", "wiki/concepts/alpha.md"), problems
    assert not has_rule(problems, "phone", "wiki/log.md"), problems
    assert not has_rule(problems, "email", "wiki/log.md"), problems


def test_other_front_matter_fields_are_checked(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    alpha = instance / "wiki" / "concepts" / "alpha.md"
    alpha.write_text(
        alpha.read_text(encoding="utf-8").replace(
            "title: Alpha", "title: 2026.09.29"
        ),
        encoding="utf-8",
    )
    assert update_regions(instance) == []

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/concepts/alpha.md", 2, "date", "2026.09.29")


def test_well_formed_mechanical_region_is_not_checked(tmp_path):
    instance = ready_vault(tmp_path)
    synthetic_phone_id = "010-0000-0000"
    add_revision(
        instance,
        "20260929T000000000000Z",
        "synthetic revision\n",
        source_id=synthetic_phone_id,
    )
    source = instance / "wiki" / "sources" / "source.md"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            f"raw/files/{SOURCE_ID}/*", f"raw/files/{synthetic_phone_id}/*"
        ),
        encoding="utf-8",
    )
    assert update_regions(instance) == []

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "phone", "wiki/sources/source.md"), problems


def test_student_pages_are_only_direct_markdown_files(tmp_path):
    instance = ready_vault(tmp_path)
    nested = instance / "wiki" / "students" / "nested"
    nested.mkdir(parents=True)
    (nested / f"{STUDENTS[1]}.md").write_text("# Student\n", encoding="utf-8")
    (instance / "wiki" / "students" / f"{STUDENTS[1]}.txt").write_text(
        "Not a Markdown page.\n", encoding="utf-8"
    )

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "roster"), problems
    assert not has_rule(problems, "student-roster"), problems


def test_roster_is_not_read_without_student_pages_or_cjk(tmp_path):
    instance = ready_vault(tmp_path)
    _config_path(tmp_path).unlink(missing_ok=True)
    write_overview(instance, "Ordinary English text.")

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "roster"), problems
    assert not has_rule(problems, "english"), problems


@pytest.mark.parametrize(
    "failure",
    ("missing-config", "relative-path", "missing-csv", "missing-name"),
)
def test_roster_failures_report_once_on_wiki_line_one(tmp_path, failure):
    instance = ready_vault(tmp_path)
    write_overview(instance, "學生")
    config = _config_path(tmp_path)
    roster = _roster_path(tmp_path)
    if failure != "missing-config":
        config.parent.mkdir(parents=True, exist_ok=True)
        if failure == "relative-path":
            config.write_text('roster = "relative.csv"\n', encoding="utf-8")
        else:
            if failure == "missing-csv":
                config.write_text(
                    f"roster = {json.dumps(str(roster))}\n", encoding="utf-8"
                )
            else:
                roster.parent.mkdir(parents=True, exist_ok=True)
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
        and "page rule roster: cannot read the roster:" in item["message"]
    ]

    assert len(roster_problems) == 1, problems
    expected = (
        str(config)
        if failure in {"missing-config", "relative-path"}
        else str(roster)
    )
    assert expected in roster_problems[0]["message"]
    assert sum("page rule" in item["message"] for item in problems) == 1, (
        problems
    )


def test_english_reports_each_line_with_cjk(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, "\n\n\n한국어\n한국어")

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 5, "english", "한국어")
    assert_rule(problems, "wiki/overview.md", 6, "english", "한국어")


@pytest.mark.parametrize(
    "body",
    [
        "At 14:30 (UTC+09:00).",
        "At 14:30 UTC+09:00.",
        "At 14:30 (UTC-05:00).",
    ],
)
def test_time_rule_allows_utc_offsets_with_minutes(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "time", "wiki/overview.md"), problems


@pytest.mark.parametrize(
    ("student", "body", "rule", "matched"),
    [
        pytest.param(
            "Ann Lee",
            "Ann Lee.one@example.test",
            "email",
            "Lee.one@example.test",
            id="email-overlap",
        ),
        pytest.param(
            "A 010",
            "A 010-1234-5678",
            "phone",
            "010-1234-5678",
            id="phone-overlap",
        ),
    ],
)
def test_roster_spans_do_not_hide_contact_rules(
    tmp_path, student, body, rule, matched
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path, [(student, "", ""), (STUDENTS[0], "", "")])
    body = f"{body} {STUDENTS[0]}"
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, rule, matched)


@pytest.mark.parametrize(
    ("rule", "body", "matched"),
    [
        pytest.param(
            "address", "Meet at 무지개길 12.", "무지개길 12", id="hangul-road"
        ),
        pytest.param(
            "address",
            "Meet at 12, Fiction-ro.",
            "12, Fiction-ro",
            id="number-first-road",
        ),
        pytest.param(
            "address", "Meet at 12-3번지.", "12-3번지", id="lot-number"
        ),
        pytest.param(
            "id-number",
            "Record 000229-3000000.",
            "000229-3000000",
            id="century-2000-3",
        ),
        pytest.param(
            "id-number",
            "Record 000229-4000000.",
            "000229-4000000",
            id="century-2000-4",
        ),
        pytest.param(
            "id-number",
            "Record 000229-7000000.",
            "000229-7000000",
            id="century-2000-7",
        ),
        pytest.param(
            "id-number",
            "Record 000229-8000000.",
            "000229-8000000",
            id="century-2000-8",
        ),
        pytest.param(
            "date", "Recorded 2026-02-30.", "2026-02-30", id="invalid-iso"
        ),
        pytest.param(
            "date", "Recorded 2026-9-29.", "2026-9-29", id="unpadded-iso"
        ),
        pytest.param(
            "date", "Recorded 29.09.2026.", "29.09.2026", id="day-first"
        ),
        pytest.param(
            "date", "Recorded 9/29/26.", "9/29/26", id="two-digit-year"
        ),
        pytest.param(
            "date",
            "Recorded September 29, 2026.",
            "September 29, 2026",
            id="month-first",
        ),
        pytest.param(
            "date",
            "Recorded 29th of September.",
            "29th of September",
            id="day-month-name",
        ),
        pytest.param(
            "date",
            "Recorded 2026년 9월 29일.",
            "2026년 9월 29일",
            id="korean-year-month-day",
        ),
        pytest.param(
            "date", "Recorded 9월 29일.", "9월 29일", id="korean-month-day"
        ),
    ],
)
def test_page_rules_report_additional_contract_forms(
    tmp_path, rule, body, matched
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, rule, matched)


@pytest.mark.parametrize(
    "body",
    [
        "Record 000229-1000000.",
        "Record 000229-2000000.",
        "Record 000229-5000000.",
        "Record 000229-6000000.",
    ],
)
def test_registration_number_century_digits_use_the_1900s(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "id-number", "wiki/overview.md"), problems


@pytest.mark.parametrize(
    "body",
    [
        "At 14:30 +99:99.",
        "At 14:30 +15:00.",
        "At 14:30 +14:60.",
        "At 14:30 -05:00.",
        "At 14:00 -15:30.",
        "From 9:00 -10:00 today.",
        "At 14:30 KST.",
        "At 3 PM.",
    ],
)
def test_page_rules_reject_unzoned_or_invalid_time_forms(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert has_rule(problems, "time", "wiki/overview.md"), problems


@pytest.mark.parametrize(
    "body",
    [
        "At 14:30Z.",
        "At 14:30 +09:00.",
        "At 14:30 +0900.",
        "At 14:30 +14:59.",
        "At 3 PM UTC.",
        "At 2026-09-29T14:30:00-05:00.",
    ],
)
def test_page_rules_allow_more_zoned_time_forms(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "time", "wiki/overview.md"), problems


@pytest.mark.parametrize(
    "body",
    [
        "<!-- 2026.09.29 -->",
        "x < 2026.09.29 > y",
    ],
)
def test_non_autolink_angle_text_does_not_hide_dates(tmp_path, body):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "date", "2026.09.29")


@pytest.mark.parametrize(
    "body",
    [
        "<https://example.com/2026/09/29>",
        "<urn:synthetic:2026.09.29>",
        "[synthetic date](https://example.invalid/2026/09/29)",
    ],
)
def test_page_rules_skip_autolinks_and_link_destinations_for_dates(
    tmp_path, body
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, body)

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "date", "wiki/overview.md"), problems


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("<!-- [[[cog malformed -->", "<!-- [[[end]]] -->"),
        ("<!-- [[[cog synthetic ]]] -->", "<!-- [[[end] ] -->"),
    ],
)
def test_malformed_mechanical_region_markers_do_not_hide_page_rules(
    tmp_path, start, end
):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    page = instance / "wiki" / "overview.md"
    page.write_text(
        f"# Overview\n{start}\n010-1234-5678\n{end}\n", encoding="utf-8"
    )

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 3, "phone", "010-1234-5678")


def test_roster_name_followed_by_a_particle_still_fails_english(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"{STUDENTS[0]}은 good.")

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "english", "은")


def test_hangul_school_inside_an_allowed_quote_passes_school(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"“{SCHOOL}” (fiction)")

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "school", "wiki/overview.md"), problems


def test_original_quote_of_100_characters_passes_english(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, f"“{'學' * 100}” (meaning)")

    problems = checked(instance, tmp_path)

    assert not has_rule(problems, "english", "wiki/overview.md"), problems


def test_closing_quote_does_not_open_a_quote(tmp_path):
    instance = ready_vault(tmp_path)
    write_roster(tmp_path)
    write_overview(instance, 'The word "x" 한국어 " (meaning)')

    problems = checked(instance, tmp_path)

    assert_rule(problems, "wiki/overview.md", 2, "english", "한국어")
