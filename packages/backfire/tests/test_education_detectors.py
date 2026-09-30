"""Each detector finds its kind and leaves learning content alone."""

import pytest

from backfire_education.pseudonymize import compile_name_pattern
from backfire_education.pseudonymize import compile_roster_pattern
from backfire_education.pseudonymize import find_spans
from backfire_education.roster import load_roster


@pytest.fixture
def found(synthetic_roster):
    """Return a function from text to its (matched text, kind, value) spans."""
    del synthetic_roster  # Unused.
    identifiers = load_roster()
    patterns = (
        compile_roster_pattern(identifiers),
        compile_name_pattern(identifiers),
    )

    def find(text):
        return [
            (text[start:stop], *identifier)
            for start, stop, identifier in find_spans(
                text, identifiers, *patterns
            )
        ]

    return find


@pytest.mark.parametrize(
    "text",
    [
        "Ga Raon",
        "ga raon",
        "GA RAON",
        "Raon Ga",
        "Raon, Ga",
        "Ga Ra-on",
        "ga ra on",
        "Ga-Raon",
        "Raon",
        "ra-on",
        "7700101",
    ],
)
def test_one_student_has_one_identifier_in_every_form(found, text):
    assert found(text) == [(text, "student", "가라온")]


def test_shared_romanized_given_name_has_its_own_identifier(found):
    assert found("Haneul") == [("Haneul", "given", "하늘")]
    assert found("Haneul Na") == [("Haneul Na", "student", "나하늘")]
    assert found("da ha-neul") == [("da ha-neul", "student", "다하늘")]


@pytest.mark.parametrize(
    "text",
    ["Raonly", "Braon", "Ga Raonly", "17700101", "77001011", "Gale Raoni"],
)
def test_romanized_names_and_numbers_match_only_whole_words(found, text):
    assert found(text) == []


def test_roster_columns_are_optional(synthetic_roster):
    synthetic_roster.write_text("name\n가라온\n", encoding="utf-8")
    assert load_roster() == {
        "가라온": ("student", "가라온"),
        "라온": ("student", "가라온"),
    }


@pytest.mark.parametrize(
    ("text", "values"),
    [
        ("Grade 10", ["10"]),
        ("grade 12", ["12"]),
        ("10th grade", ["10"]),
        ("10th-grader", ["10"]),
        ("Year 11", ["year 11"]),
        ("first-year high school student", ["10"]),
        ("a high school sophomore", ["10"]),
        ("second-year middle school student", ["8"]),
        ("고1", ["10"]),
        ("중2", ["8"]),
        ("초6", ["6"]),
        ("예비 고1", ["10"]),
        ("2학년", ["year 2"]),
        ("Grade 10 and 고1 and 10th grade", ["10", "10", "10"]),
        ("Grade 9 and Grade 10", ["9", "10"]),
    ],
)
def test_school_years_share_one_identifier_per_grade(found, text, values):
    assert [value for _, kind, value in found(text) if kind == "cohort"] == (
        values
    )


@pytest.mark.parametrize(
    "text",
    [
        "2026학년도",
        "the 2026 school year",
        "school year 2026",
        "Year 2026",
        "Grade 100",
        "grade improved",
    ],
)
def test_academic_years_stay(found, text):
    assert found(text) == []


@pytest.mark.parametrize(
    ("text", "matched"),
    [
        ("Jongno-gu", "Jongno-gu"),
        ("jongno-gu", "jongno-gu"),
        ("Gangneung-si", "Gangneung-si"),
        ("Gangneung", "Gangneung"),
        ("Pyeongtaek", "Pyeongtaek"),
        ("Pyeongtaek-si", "Pyeongtaek-si"),
        ("North Chungcheong", "North Chungcheong"),
        ("North Chungcheong Province", "North Chungcheong Province"),
        ("Chungbuk", "Chungbuk"),
        ("Anyang", "Anyang"),
        ("Tongyeong-si", "Tongyeong-si"),
        ("Seoul City", "Seoul City"),
        ("Busan Metropolitan City", "Busan Metropolitan City"),
        (
            "Jeju Special Self-Governing Province",
            "Jeju Special Self-Governing Province",
        ),
        ("Gyeonggi-do", "Gyeonggi-do"),
        ("평택시", "평택시"),
        ("서울특별시", "서울특별시"),
    ],
)
def test_regions_come_from_the_generated_list(found, text, matched):
    assert [(m, kind) for m, kind, _ in found(f"He lives in {text}.")] == [
        (matched, "region")
    ]


def test_regions_do_not_match_inside_longer_words(found):
    assert found("Seoulful Busanese Pyeongtaeks") == []


@pytest.mark.parametrize(
    ("text", "matched"),
    [
        ("byeolbit-h", "byeolbit-h"),
        ("saeum-m", "saeum-m"),
        ("hana-e2-h", "hana-e2-h"),
    ],
)
def test_school_domain_ids(found, text, matched):
    assert found(f"School {text}.") == [(matched, "school", matched)]


@pytest.mark.parametrize("text", ["e-mail", "well-known", "Byeolbit-h", "x-hi"])
def test_domain_id_lookalikes_stay(found, text):
    assert found(text) == []


@pytest.mark.parametrize(
    ("text", "matched"),
    [
        ("born on 2009-03-15", "2009-03-15"),
        ("Born: 2009.3.15", "2009.3.15"),
        ("DOB 09.03.15", "09.03.15"),
        ("date of birth: March 15, 2009", "March 15, 2009"),
        ("birthday 15 March 2009", "15 March 2009"),
        ("born in 2009", "2009"),
        ("생년월일: 2009년 3월 15일", "2009년 3월 15일"),
        ("생일 2009-03-15", "2009-03-15"),
        ("출생 2009", "2009"),
        ("a 2009년생 student", "2009년생"),
        ("a 09년생 student", "09년생"),
    ],
)
def test_birth_dates_follow_a_keyword_or_end_in_nyeonsaeng(
    found, text, matched
):
    assert [(m, kind) for m, kind, _ in found(text)] == [(matched, "birth")]


@pytest.mark.parametrize(
    "text",
    [
        "lesson on 2026-09-28",
        "score 2026 points",
        "newborn 2009-03-15",
        "born to run",
    ],
)
def test_other_dates_stay(found, text):
    assert found(text) == []


@pytest.mark.parametrize(
    ("text", "matched"),
    [
        ("Address: 12 Bijeon-ro, Seoul", "12 Bijeon-ro, Seoul"),
        ("address 12 Bijeon-ro", "12 Bijeon-ro"),
        ("주소: 서울시 어딘가", "서울시 어딘가"),
        ("lives at Bijeon-ro 12", "Bijeon-ro 12"),
        ("lives at Seo-dong 123-4", "Seo-dong 123-4"),
        ("lives at 101-dong 1203-ho", "101-dong 1203-ho"),
        (
            "lives at Jungang-daero 45beon-gil 7",
            "Jungang-daero 45beon-gil 7",
        ),
        ("lives at 12345 Bijeon-ro 12", "12345 Bijeon-ro 12"),
        ("lives at Bijeon-ro 12, 12345", "Bijeon-ro 12, 12345"),
        ("lives at Gaya-eup, Bo-ri 3", "Gaya-eup, Bo-ri 3"),
    ],
)
def test_addresses_follow_a_keyword_or_have_romanized_parts(
    found, text, matched
):
    assert [m for m, kind, _ in found(text) if kind == "address"] == [matched]


def test_address_keyword_takes_the_rest_of_the_line_only(found):
    text = "Address: 12 Bijeon-ro, Seoul\nScore 85"
    assert [m for m, kind, _ in found(text) if kind == "address"] == [
        "12 Bijeon-ro, Seoul"
    ]


def test_learning_content_is_kept(found):
    text = (
        "Scores 85 and 90 out of 100; lessons on 2026-09-28 and 2026-10-05; "
        "2026학년도 unit 3, page 12, 29-37번."
    )
    assert found(text) == []
