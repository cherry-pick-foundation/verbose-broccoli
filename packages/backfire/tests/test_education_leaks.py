"""A provider receives no identifier, and a refused request sends nothing."""

import asyncio
import json
import re
import unicodedata

from fake_provider import FakeProvider
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


def profile(fake):
    return {
        "name": "synthetic",
        "api": "openai",
        "base_url": fake.base_url,
        "model": "synthetic-model",
        "credential": "SYNTHETIC_API_KEY",
        "request": {},
    }


def send(monkeypatch, fake, state, questions=None, *, education=True):
    """Send one request to the fake provider; return its answer or error."""
    monkeypatch.setattr(providers, "load_credential", lambda _: "synthetic-key")

    async def run():
        client = _OrderProvider([profile(fake)], education=education)
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
