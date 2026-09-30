"""A provider receives no identifier, and a refused request sends nothing."""

import asyncio
import json
import re
import unicodedata

from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
from jev_judge_mcp.domain import NoulCriteria
from jev_judge_mcp.domain import NoulQuestion
from jev_judge_mcp.providers import ProviderError
import pytest

from backfire import providers
from backfire.providers import _OrderProvider
from backfire_education import pseudonymize as education

# Each kind: a request text that names it and the values that must not leave.
LEAKS = {
    "student": (
        "가라온 (Ga Raon, Raon, ga-raon, 7700101) joined the class.",
        ["가라온", "Ga Raon", "Raon", "ga-raon", "7700101"],
    ),
    "given": ("Haneul and 하늘 joined.", ["Haneul", "하늘"]),
    "guardian": ("다누리 called the school.", ["다누리"]),
    "school": (
        "가상별학교 and byeolbit-h and 바람숲학교.",
        ["가상별학교", "byeolbit-h", "바람숲학교"],
    ),
    "phone": ("Call 010-1234-5678.", ["010-1234-5678", "1234-5678"]),
    "email": ("Write to learner@example.test.", ["learner@example.test"]),
    "region": (
        "Lives in Jongno-gu, Gangneung-si City and North Chungcheong.",
        ["Jongno", "Gangneung", "Chungcheong"],
    ),
    "cohort": (
        "A 고1, in Grade 10, a high school sophomore.",
        ["고1", "Grade 10", "sophomore"],
    ),
    "birth": (
        "Born on March 15, 2009; DOB 09.03.15.",
        ["March 15, 2009", "09.03.15"],
    ),
    "address": (
        "Address: 12 Bijeon-ro, Seoul. Also Seo-dong 123-4.",
        ["Bijeon-ro", "Seo-dong", "123-4"],
    ),
}
QUESTIONS = {"q": NoulQuestion("Is it true?", NoulCriteria("true", "false"))}
HANGUL = [
    "한글",
    unicodedata.normalize("NFD", "한글"),
    "ㅎㅏㄴ",
    "한",
    "ꥠ",
    "ﾡ",
]


def profile(fake, retry=None):
    return {
        "name": "synthetic",
        "api": "openai",
        "base_url": fake.base_url,
        "model": "synthetic-model",
        "credential": "SYNTHETIC_API_KEY",
        "request": {},
        **({"retry": retry} if retry else {}),
    }


def send(
    monkeypatch, fake, state, questions=None, *, education=True, retry=None
):
    """Send one request to the fake provider; return its answer or error."""
    monkeypatch.setattr(providers, "load_credential", lambda _: "synthetic-key")

    async def run():
        client = _OrderProvider([profile(fake, retry)], education=education)
        try:
            return await client.evaluate(
                state, questions or QUESTIONS, "default-model", 3
            )
        finally:
            await client.aclose()

    try:
        return asyncio.run(run())
    except ProviderError as error:
        return error


def received(fake):
    """Return everything the fake provider received, as one string."""
    return json.dumps(fake.requests, ensure_ascii=False)


@pytest.mark.parametrize("kind", LEAKS)
def test_provider_receives_no_identifier_of_any_kind(
    synthetic_roster, monkeypatch, kind
):
    del synthetic_roster  # Unused.
    text, originals = LEAKS[kind]
    with FakeProvider([completion({"q": 0.5})]) as fake:
        questions = {"q": NoulQuestion(text, NoulCriteria(text, "false"))}
        result = send(monkeypatch, fake, {"note": text}, questions)
        assert not isinstance(result, Exception)
        sent = received(fake)
    assert len(fake.requests) == 1
    for original in originals:
        assert original not in sent
    assert not re.search(r"[가-힣]", sent)
    assert re.search(
        r"(Student|Guardian|School|Phone|Email) \d\d|Region \d\d|"
        r"Cohort \d\d|Birth date \d\d|Address \d\d",
        sent,
    )


def test_provider_receives_one_stand_in_per_student(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    text = "가라온, Ga Raon, raon ga and 7700101; 나하늘 and Na Haneul."
    with FakeProvider([completion({"q": 0.5})]) as fake:
        send(monkeypatch, fake, {"note": text})
        sent = received(fake)
    assert re.findall(r"Student \d\d", sent) == [
        "Student 01",
        "Student 01",
        "Student 01",
        "Student 01",
        "Student 02",
        "Student 02",
    ]


def test_learning_content_reaches_the_provider(synthetic_roster, monkeypatch):
    del synthetic_roster  # Unused.
    text = "Scores 85 and 90; lesson on 2026-09-28; 2026학년도 unit 3."
    with FakeProvider([completion({"q": 0.5})]) as fake:
        assert isinstance(
            send(monkeypatch, fake, {"note": text}), ProviderError
        )
        assert fake.requests == []  # 학년도 is Hangul, refused.
    text = "Scores 85 and 90; lesson on 2026-09-28; the 2026 school year."
    with FakeProvider([completion({"q": 0.5})]) as fake:
        assert not isinstance(
            send(monkeypatch, fake, {"note": text}), Exception
        )
        assert text in received(fake)


@pytest.mark.parametrize("education_mode", [True, False])
@pytest.mark.parametrize("hangul", HANGUL)
@pytest.mark.parametrize("place", ["state", "key", "question"])
def test_hangul_is_refused_in_both_modes_and_nothing_is_sent(
    synthetic_roster, monkeypatch, education_mode, hangul, place
):
    del synthetic_roster  # Unused.
    state, questions = {"note": "marker"}, QUESTIONS
    if place == "state":
        state = {"note": f"marker {hangul}"}
    elif place == "key":
        state = {f"key {hangul}": "marker"}
    else:
        questions = {
            "q": NoulQuestion(f"Is {hangul} true?", NoulCriteria("t", "f"))
        }
    with FakeProvider([completion({"q": 0.5})]) as fake:
        error = send(
            monkeypatch, fake, state, questions, education=education_mode
        )
    assert isinstance(error, ProviderError)
    assert str(error).startswith("hangul_remaining:")
    assert hangul not in str(error) and "marker" not in str(error)
    assert error.__cause__ is None and error.__context__ is None
    assert fake.requests == []


@pytest.mark.parametrize("education_mode", [True, False])
def test_english_requests_pass_the_hangul_check(
    synthetic_roster, monkeypatch, education_mode
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(
            monkeypatch,
            fake,
            {"note": "Plain English only."},
            education=education_mode,
        )
    assert not isinstance(result, Exception) and len(fake.requests) == 1


def test_a_name_missing_from_the_roster_is_refused_as_hangul(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        error = send(monkeypatch, fake, {"note": "라마루 joined 가라온."})
    assert str(error).startswith("hangul_remaining:")
    assert "라마루" not in str(error) and "가라온" not in str(error)
    assert fake.requests == []


def test_a_surviving_identifier_is_refused_without_its_value(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    real, seen = education.find_spans, set()

    def miss_once(text, identifiers, *patterns):
        """Miss every text the first time, as a detector gap would."""
        if text not in seen:
            seen.add(text)
            return []
        return real(text, identifiers, *patterns)

    monkeypatch.setattr(education, "find_spans", miss_once)
    with FakeProvider([completion({"q": 0.5})]) as fake:
        error = send(monkeypatch, fake, {"note": "Ga Raon and 7700101."})
    assert str(error).startswith("identifier_remaining:")
    assert "Raon" not in str(error) and "7700101" not in str(error)
    assert error.__cause__ is None and error.__suppress_context__
    assert fake.requests == []


@pytest.mark.parametrize(
    "state",
    [
        {"student_id": 7700101},
        {"student_id": 7700101.0},
        {"DOB": "2011-04-23"},
        {"born": 2011},
        {"address": "487 Imaginary Street"},
        {"grade": 10},
        {"DOB": {"year": 2011, "month": 4, "day": 23}},
        {"address": [{"line1": "487 Imaginary Street", "zip": "12345"}]},
        {7700101: "record"},
    ],
)
def test_the_scan_after_the_swap_covers_numbers_and_field_names(
    synthetic_roster, monkeypatch, state
):
    del synthetic_roster  # Unused.
    real, seen = education.find_spans, set()

    def miss_once(text, identifiers, *patterns):
        """Miss every text the first time, as a detector gap would."""
        if text not in seen:
            seen.add(text)
            return []
        return real(text, identifiers, *patterns)

    monkeypatch.setattr(education, "find_spans", miss_once)
    with FakeProvider([completion({"q": 0.5})]) as fake:
        error = send(monkeypatch, fake, state)
    assert str(error).startswith("identifier_remaining:")
    assert fake.requests == []


@pytest.mark.parametrize(
    "state",
    [
        {"student_id": 7700101},
        {"student_id": 7700101.0},
        {"DOB": "2011-04-23"},
        {"born": 2011},
        {"address": "487 Imaginary Street"},
        {"grade": 10},
        {"DOB": {"year": 2011, "month": 4, "day": 23}},
        {"address": [{"line1": "487 Imaginary Street", "zip": "12345"}]},
        {7700101: "record"},
    ],
)
def test_provider_receives_no_number_or_field_value_identifier(
    synthetic_roster, monkeypatch, state
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, state)
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"])
    assert not re.search(r"7700101|2011|487|Imaginary|\b10\b", sent)


@pytest.mark.parametrize(
    "text",
    [
        "born on June 17 (2012)",
        "DOB: June 17, (2012)",
        "born on 17. 06. 2012",
        "born on June 17th of 2012",
        "DOB: June 17, year 2012",
        "born on June 17 in 2012",
        "DOB: June 17, [ 2012 ]",
        "born on 17.  06.  2012",
        "born on 2012 . 06 . 17",
        "born on June 2012, on the 17th",
        "born on [June 17, 2012]",
    ],
)
def test_provider_receives_no_part_of_a_birth_date(
    synthetic_roster, monkeypatch, text
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"])
    assert not re.search(r"2012|June|\b17\b|\b06\b", sent)


@pytest.mark.parametrize(
    ("text", "hidden"),
    [
        ("born on 2012-06-17T00:00:00", ["2012", "06", "17", "00:00"]),
        ("born on 2012-06-17T00:00:00Z", ["2012", "17", "00:00"]),
        ("born on 2012-06-17 at 09:30", ["2012", "09:30"]),
        ("DOB: June 17, AD 2012", ["2012", "June"]),
        ("born on June 17, A.D. 2012", ["2012", "June"]),
        ("born on June 17 in circa 2012", ["2012", "June"]),
        ("DOB: June 17, two thousand and zero one", ["two", "zero", "June"]),
        ("born on June 17, two thousand nought one", ["nought", "June"]),
        ("born on 17 June MMXII", ["MMXII", "June"]),
        ("born on 17.VI.2012", ["VI", "2012"]),
        ("born on 2012-06-17Tuesday", ["2012", "17"]),
        ("born in two thousand, twelve", ["thousand", "twelve"]),
        ("born on June seventeen, 2012", ["seventeen", "2012"]),
        ("DOB: 17 June (Sunday), 2012", ["2012", "June"]),
        ("born on June 17 in the summer of 2012", ["2012", "June"]),
        ("born on June17th2012", ["2012", "June"]),
        ("born on １７／０６／２０１２", ["２０１２", "１７"]),
        ("born on ١٧/٠٦/٢٠١٢", ["٢٠١٢"]),
        ("born on June 17\u200b2012", ["2012", "June"]),
        ("born on 2012_06_17", ["2012"]),
        ("DOB: June 17, in and of the year 2012", ["2012", "June"]),
        ("born on 17–06–2012", ["2012", "17"]),
        ("born on 17 06 2012", ["2012", "17"]),
        ("DOB: 2012\t06\t17", ["2012", "17"]),
        ("born on 2012, on the 17th of June", ["2012", "June"]),
        ("born on June 17, '12", ["'12", "June"]),
        ("DOB: June 17, 12", ["June", "12"]),
    ],
)
def test_provider_receives_no_birth_date_in_other_forms(
    synthetic_roster, monkeypatch, text, hidden
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"], ensure_ascii=False)
    assert not [
        word for word in hidden if re.search(rf"\b{re.escape(word)}", sent)
    ]


@pytest.mark.parametrize(
    ("text", "kept"),
    [
        ("born on June 17, 2012; 85/100 on the reading test.", "85/100"),
        ("born on June 17, 2012. 85 points on the reading test.", "85 points"),
        ("born on June 17, 2012\n85/100 on the reading test.", "85/100"),
        ("DOB: 2012-06-17 | 85/100 on the reading test.", "85/100"),
        (
            "born on June 17, 2012; on 2026-09-30 completed the lesson.",
            "2026-09-30",
        ),
        (
            "born on June 17, 2012. On September 30, 2026 finished the unit.",
            "On September 30, 2026",
        ),
        ("born on June 17, 2012. May need reading support.", "May need"),
        ("DOB: [2012-06-17]; 85/100 on the reading test.", "85/100"),
        ("She was born. May need reading support.", "May need"),
        ("She was born. December lessons went well.", "December lessons"),
        ("She was born. First in the spelling contest.", "First in"),
        ("The idea was born in Marching practice.", "Marching"),
        ("Her birthday may improve attendance.", "may improve"),
        ("She was born first in her family.", "first in her"),
    ],
)
def test_learning_content_beside_a_birth_date_is_sent(
    synthetic_roster, monkeypatch, text, kept
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"], ensure_ascii=False)
    assert kept in sent
    assert "2012" not in sent and "June 17" not in sent


@pytest.mark.parametrize(
    ("text", "hidden"),
    [
        (
            "born on June 17, 2012, and one of the strongest readers.",
            "strongest",
        ),
        ("born on June 17, 85 points on the reading test.", "85 points"),
        ("born in June 2012, 85 points on the reading test.", "85 points"),
    ],
)
def test_content_in_the_clause_of_a_birth_date_is_hidden_with_it(
    synthetic_roster, monkeypatch, text, hidden
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"], ensure_ascii=False)
    assert hidden not in sent and "June" not in sent


@pytest.mark.parametrize(
    ("text", "hidden"),
    [
        ("Ga Ra\u2011on came today.", ["Ra\u2011on", "Raon"]),
        ("Lives at Solbit\u2011ro 487.", ["Solbit", "487"]),
        ("Lives at Solbit-ro 487, Apt #1203.", ["487", "1203"]),
        ("Lives at Solbit-ro 487, building 101, unit 1203.", ["101", "1203"]),
        ("Grade: 11th this year.", ["11th"]),
        ("Ga Ra\u00a0on came today.", ["Ra\u00a0on"]),
        ("Ga Ra  on came today.", ["Ra  on"]),
        ("born in june", ["june"]),
        ("born on november nineteenth", ["november"]),
        ("born in mmxiii", ["mmxiii"]),
        ("Lives at Solbit-ro 487 (Apt 2317)", ["2317"]),
        ("Lives at Solbit-ro 487, apt. no. 2317", ["2317"]),
        ("Lives at Solbit-ro 487, 103/2317", ["103", "2317"]),
        ("| Ga Raon | Grade |\n|---|---|\n| x | 11 |", ["Raon", "| 11"]),
        ("Ga Raon,2013-08-27\nx,y", ["Raon"]),
        ("date  of  birth 2013-08-27", ["2013"]),
        ("Grades ten and eleven", ["ten", "eleven"]),
        ("Years 10 and 11", ["10", "11"]),
        ("Grade 10/11", ["10/11"]),
        ("Lives at Solbit-ro 731, Unit 27B", ["731", "27B"]),
        ("Grades 10 and 11 share a room.", ["10", "11"]),
        ("born on September 23, '13 and enjoys reading", ["'13", "September"]),
        ("born on the 23rd day of September 2013", ["2013", "September"]),
    ],
)
def test_provider_receives_no_identifier_in_these_forms(
    synthetic_roster, monkeypatch, text, hidden
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"], ensure_ascii=False)
    assert not [
        word
        for word in hidden
        if re.search(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", sent)
    ]


def test_education_provider_error_keeps_only_profile_and_status(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    marker = "PRIVATE_REQUEST_MARKER"
    body = {"error": {"message": f"invalid request {marker}"}}
    with FakeProvider([Reply(body, status=400)]) as fake:
        error = send(monkeypatch, fake, {"note": marker})
        assert len(fake.requests) == 1
    assert isinstance(error, ProviderError)
    assert str(error) == "backfire profile 400"
    assert error.__cause__ is None and error.__suppress_context__


def test_education_error_after_retries_keeps_only_profile_and_last_status(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    marker = "PRIVATE_RESPONSE_MARKER"
    retry = {"max_attempts": 2, "backoff_initial": 0.001, "backoff_max": 0.001}
    replies = [Reply(f"<html>{marker}</html>".encode(), status=500)] * 2
    with FakeProvider(replies) as fake:
        error = send(monkeypatch, fake, {"note": "plain"}, retry=retry)
        assert len(fake.requests) == 2
    assert isinstance(error, ProviderError)
    assert str(error) == "backfire profile 500"


def test_education_error_without_status_names_only_the_profile(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    marker = "PRIVATE_RESPONSE_MARKER"

    async def fail(*_):
        raise RuntimeError(f"unexpected {marker}")

    monkeypatch.setattr(providers._OpenAIProvider, "_send", fail)
    with FakeProvider([completion({"q": 0.5})]) as fake:
        error = send(monkeypatch, fake, {"note": "plain"})
    assert isinstance(error, ProviderError)
    assert str(error) == "backfire profile request failed"


def test_code_mode_provider_error_is_left_as_it_is(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    body = {"error": {"message": "invalid request SYNTHETIC_BODY"}}
    with FakeProvider([Reply(body, status=400)]) as fake:
        error = send(monkeypatch, fake, {"note": "plain"}, education=False)
    assert str(error).startswith("backfire profile 400: ")
    assert "SYNTHETIC_BODY" in str(error)


def test_stand_ins_and_their_keywords_are_not_refused(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    text = (
        "Address: 12 Bijeon-ro.\nBorn on March 15, 2009.\nIn Grade 10, in "
        "Jongno-gu. Student 01 and School 02 are labels."
    )
    with FakeProvider([completion({"q": 0.5}), completion({"q": 0.5})]) as fake:
        first = send(monkeypatch, fake, {"note": text})
        second = send(monkeypatch, fake, {"note": text})
        assert not isinstance(first, Exception)
        assert not isinstance(second, Exception)
        assert fake.requests[0]["body"] == fake.requests[1]["body"]
        sent = received(fake)
    assert "Address 01" in sent and "Birth date 01" in sent
    assert "Cohort 01" in sent and "Region 01" in sent
    assert "Bijeon" not in sent and "Jongno" not in sent


@pytest.mark.parametrize(
    ("text", "hidden"),
    [
        ("| Name | Grade |\n| --- | --- |\n| Ga Raon | 11 |", ["11", "Raon"]),
        (
            "| Name | DOB |\n| --- | --- |\n| Ga Raon | 23.IV.2011 |",
            ["IV", "2011"],
        ),
        (
            "| Address | Grade |\n|---|---|\n| 487 Imaginary St | 10 |",
            ["487", "| 10"],
        ),
        ("| StudentNo | Score |\n|---|---|\n| 7799999 | 85 |", ["7799999"]),
        ("Name,Grade,DOB\nGa Raon,11,2011-04-23", ["11", "2011"]),
        ('Name,StudentNo,Grade\n"Ga, Raon",7799999,11', ["7799999", "11"]),
        (
            'Name,Note,DOB\nGa Raon,"Likes reading\nand drawing",2013-11-19',
            ["2013"],
        ),
        (
            "| Name | Note | DOB |\n|---|---|---|\n"
            "|Ga Raon|A \\| B|2013-11-19|",
            ["2013"],
        ),
        (
            "Name\tAddress\tStudent ID\nGa Raon\t487 Imaginary St\t7799999",
            ["487", "7799999"],
        ),
    ],
)
def test_named_table_and_csv_columns_are_replaced(
    synthetic_roster, monkeypatch, text, hidden
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"], ensure_ascii=False)
    assert not [word for word in hidden if word in sent]


def test_letter_grades_and_scores_in_a_grade_column_stay(
    synthetic_roster, monkeypatch
):
    del synthetic_roster  # Unused.
    text = "| Name | Grade | Score |\n|---|---|---|\n| Ga Raon | B+ | 85 |"
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
        assert not isinstance(result, Exception)
        sent = json.dumps(fake.requests[0]["body"], ensure_ascii=False)
    assert "B+" in sent and "85" in sent


@pytest.mark.parametrize(
    "state",
    [
        {"note": "DOB: around Easter"},
        {"note": "**Date of birth** = sometime in spring"},
        {"note": "Student ID: 7799999"},
        {"note": "EduOK number = 7799999"},
        {"student_id": 7799999},
        {"StudentNo": "N/A"},
    ],
)
def test_a_named_field_that_keeps_its_value_is_refused(
    synthetic_roster, monkeypatch, state
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        error = send(monkeypatch, fake, state)
    assert str(error).startswith("identifier_remaining:")
    assert "7799999" not in str(error) and "2011" not in str(error)
    assert fake.requests == []


@pytest.mark.parametrize(
    "text",
    [
        "We checked the address of the lesson.",
        "She was born in a small town and loved stories.",
        "Her birthday party was fun.",
        "Every student number is unique; the student ID card is blue.",
        "The DOB: 2011-04-23 was checked.",
        "DOB: 2011-04-23, Grade: 10, Student ID: 7700101; DOB:",
        "| Student ID | Score |\n|---|---|\n| 7700101 | 85 |",
        "| Field | Value |\n|---|---|\n| DOB | 2011-04-23 |\n"
        "| Address | Solbit-ro 487 |",
        "| Name | Email address |\n|---|---|\n| Ga Raon | none |",
    ],
)
def test_ordinary_prose_and_replaced_fields_are_sent(
    synthetic_roster, monkeypatch, text
):
    del synthetic_roster  # Unused.
    with FakeProvider([completion({"q": 0.5})]) as fake:
        result = send(monkeypatch, fake, {"note": text})
    assert not isinstance(result, Exception)
    assert len(fake.requests) == 1
