import asyncio
import csv
import json
import re
import sys

from jev_judge_mcp.domain import Usage
from jev_judge_mcp.domain.questions import ChoiceQuestion
from jev_judge_mcp.domain.questions import NoulCriteria
from jev_judge_mcp.domain.questions import NoulQuestion
from jev_judge_mcp.domain.questions import ScoreQuestion
from jev_judge_mcp.errors import Redactor
from jev_judge_mcp.providers import Evaluation
from jev_judge_mcp.providers import JevProvider
from jev_judge_mcp.settings import Settings
from jev_judge_mcp.tools import Runtime
from jev_judge_mcp.tools import Toolset
import pytest
from typesafe_sdk import Choice
from typesafe_sdk import Noul
from typesafe_sdk import Score

from backfire.config import SHIPPED_CONFIG
from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.noul import NOUL
from backfire.providers import _OrderProvider
from backfire_education.pseudonymize import compile_roster_pattern
from backfire_education.pseudonymize import find_spans
from backfire_education.pseudonymize import pseudonymize
from backfire_education.roster import load_roster


@pytest.fixture
def roster(tmp_path, monkeypatch):
    config_root, data_root = tmp_path / "config", tmp_path / "data"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_root))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_root))
    path = tmp_path / "roster.csv"
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("name", "school", "guardians", "grade"))
        writer.writerow(("가라온", "가상별학교", "다누리", "3"))
        writer.writerow(("나하늘", "가상별", "", "2"))
        writer.writerow(("다하늘", "바람숲학교", "다누리", "1"))
        writer.writerow(("Ann", "", "", "3"))
        writer.writerow(("Ann Lee", "", "", "3"))
        writer.writerow(("example.test Tail", "", "", "3"))
    config = xdg_path("config") / "backfire" / "education.toml"
    config.parent.mkdir(parents=True)
    config.write_text(f"roster = {json.dumps(str(path))}\n", encoding="utf-8")
    return path


def test_replaces_nested_state_and_rebuilds_each_question_type(roster):
    del roster  # Unused.
    state = {
        "summary": "가라온은 오늘 기록을 확인했다.",
        "nested": [{"다누리": "보호자", "school": "가상별학교에서 학습했다."}],
        "other": "날짜 2026-09-28, 범위 20-24, 26, 29-37번, 점수 1234567890.",
    }
    questions = {
        "가라온의 문항": Choice(
            instructions={"text": "라온이가 기록을 읽었다."},
            criteria={"가라온": "학생", "나하늘": "학생"},
        ),
        "다누리 확인": Noul(
            criteria={"true": "다누리가 확인", "false": "확인되지 않음"}
        ),
        "하늘 점수": Score(criteria=["가라온의 진전", "나하늘의 연습"]),
    }
    masked_state, masked_questions, _ = pseudonymize(state, questions)

    assert "가라온" not in json.dumps(masked_state, ensure_ascii=False)
    assert "라온이" not in json.dumps(
        masked_questions, ensure_ascii=False, default=str
    )
    assert "다누리" not in json.dumps(masked_state, ensure_ascii=False)
    assert "가상별학교" not in json.dumps(masked_state, ensure_ascii=False)
    assert (
        "날짜 2026-09-28, 범위 20-24, 26, 29-37번, 점수 1234567890."
        == masked_state["other"]
    )
    assert set(type(item) for item in masked_questions.values()) == {
        Choice,
        Noul,
        Score,
    }
    assert len(masked_questions) == len(questions)
    assert "Student" in masked_state["summary"]
    assert "School" in masked_state["nested"][0]["school"]


def test_pymodel_question_dataclasses_mask_fields_and_restore_answers(roster):
    del roster  # Unused.
    questions = {
        "가라온 선택": ChoiceQuestion(
            "가라온 instructions",
            {"가라온": "다누리 label", "나하늘": "가상별학교 label"},
        ),
        "다누리 확인": NoulQuestion(
            "다하늘 instructions",
            NoulCriteria("다누리 true", "바람숲학교 false"),
        ),
        "다하늘 점수": ScoreQuestion(
            "가라온 score instructions", ["나하늘 level", "다하늘 level"]
        ),
    }
    state = {"claim": "가라온은 다누리와 가상별학교를 기록했다."}

    masked_state, masked, restore = pseudonymize(state, questions)
    serialized = json.dumps(
        {
            "state": masked_state,
            "questions": {
                key: question.to_wire() for key, question in masked.items()
            },
        },
        ensure_ascii=False,
    )
    assert all(
        name not in serialized
        for name in (
            "가라온",
            "나하늘",
            "다하늘",
            "다누리",
            "가상별학교",
            "바람숲학교",
        )
    )
    assert {type(question) for question in masked.values()} == {
        ChoiceQuestion,
        NoulQuestion,
        ScoreQuestion,
    }

    choice_key = next(
        key
        for key, question in masked.items()
        if isinstance(question, ChoiceQuestion)
    )
    noul_key = next(
        key
        for key, question in masked.items()
        if isinstance(question, NoulQuestion)
    )
    score_key = next(
        key
        for key, question in masked.items()
        if isinstance(question, ScoreQuestion)
    )
    choice_labels = list(masked[choice_key].criteria)
    score_levels = masked[score_key].criteria
    answers = {
        choice_key: {
            "type": "choice",
            "choice": choice_labels[0],
            "probabilities": {choice_labels[0]: 0.8, choice_labels[1]: 0.2},
        },
        noul_key: {"type": "noul", "noul": 0.8},
        score_key: {
            "type": "score",
            "score": 0.75,
            "probabilities": {"0": 0.2, "1": 0.8},
            "legend": {"0": score_levels[0], "1": score_levels[1]},
        },
    }
    restored = restore(answers)
    assert set(restored) == set(questions)
    assert restored["가라온 선택"]["choice"] == "가라온"
    assert restored["가라온 선택"]["probabilities"] == {
        "가라온": 0.8,
        "나하늘": 0.2,
    }
    assert restored["다하늘 점수"]["legend"] == {
        "0": "나하늘 level",
        "1": "다하늘 level",
    }
    assert restored["다누리 확인"] == answers[noul_key]


def test_pymodel_choice_labels_that_collide_fail(roster):
    del roster  # Unused.
    questions = {
        "q": ChoiceQuestion(
            "synthetic instructions", {"가라온": "first", "라온": "second"}
        )
    }

    with pytest.raises(JudgmentError) as caught:
        pseudonymize({}, questions)
    assert caught.value.error_type == "pseudonym_conflict"


def test_toolset_education_wrapper_masks_pymodel_questions_and_state(
    roster, monkeypatch
):
    del roster  # Unused.

    class RecordingProvider(JevProvider):
        name = "compatible"
        label = "synthetic"

        def __init__(self):
            super().__init__(Redactor(()))
            self.state = None
            self.questions = None

        async def _send(self, state, questions, model, timeout):
            del timeout
            self.state, self.questions = state, questions
            answers = {key: {"noul": 0.9} for key in questions}
            return Evaluation(answers, Usage(1, 2), self.name, model)

        async def aclose(self):
            return None

    backend = RecordingProvider()
    monkeypatch.setattr(
        "backfire.providers.load_credential", lambda _: "synthetic-key"
    )
    monkeypatch.setattr(
        "backfire.providers._build_provider", lambda *_: backend
    )
    wrapped = _OrderProvider(
        [{"name": "education", "credential": "SYNTHETIC_KEY"}],
        education=True,
    )
    tools = Toolset(
        Runtime(Settings.model_construct(), lambda _: wrapped), (NOUL,)
    )

    async def run():
        try:
            return await tools.call(
                "jev_noul",
                {
                    "propositions": ["가라온 checks the 다누리 record."],
                    "context": "가라온 wrote it at 가상별학교.",
                },
            )
        finally:
            await tools.aclose()

    result = asyncio.run(run())
    serialized = json.dumps(
        {"state": backend.state, "questions": backend.questions},
        ensure_ascii=False,
    )
    assert not result.is_error
    assert all(
        name not in serialized for name in ("가라온", "다누리", "가상별학교")
    )


def test_given_name_particles_shared_given_name_and_longest_school_match(
    roster,
):
    del roster  # Unused.
    state = "가라온 and 라온 came; 하늘 saw 나하늘 and 다하늘 at 가상별학교."
    masked, _, _ = pseudonymize(state, {})
    full, given = re.findall(r"Student \d+", masked)[:2]
    assert full == given
    assert (
        "나하늘" not in masked
        and "다하늘" not in masked
        and "하늘이" not in masked
    )
    assert "가상별학교" not in masked
    assert masked.endswith("School 01.")
    # The shared given name has its own assignment, distinct from both students.
    raw, _, _ = pseudonymize("나하늘 다하늘 하늘", {})
    assert len(set(re.findall(r"Student \d+", raw))) == 3


def test_phone_email_normalization_and_pseudonym_like_text(roster):
    del roster  # Unused.
    source = (
        "+1 202-555-0123 and +12025550123; Synthetic.One+2@Example.test "
        "and synthetic.one+2@example.test; keep Student 10 people."
    )
    masked, _, _ = pseudonymize(source, {})
    phone_a, phone_b = (
        masked.split(" and ", 1)[0],
        masked.split(" and ", 1)[1].split(";", 1)[0],
    )
    assert phone_a == phone_b
    assert "+1 202-555-0123" not in masked and "+12025550123" not in masked
    assert "Synthetic.One+2@Example.test" not in masked
    assert masked.count("Email") == 2
    assert masked.endswith("keep Student 10 people.")


def test_longer_email_wins_roster_match_at_same_start(roster):
    del roster  # Unused.
    masked, _, _ = pseudonymize("Ann@example.test", {})
    assert masked == "Email 01"


def test_roster_overlap_masks_the_rest_of_an_email(roster):
    del roster  # Unused.
    masked, _, _ = pseudonymize("Ann Lee.one@example.test", {})
    assert masked == "Student 01"


def test_chain_of_overlaps_extends_the_kept_roster_span(roster):
    del roster  # Unused.
    masked, _, _ = pseudonymize("Ann Lee.one@example.test Tail!", {})
    assert masked == "Student 01!"


@pytest.mark.parametrize(
    ("text", "identifier"),
    [
        ("가라온", ("student", "가라온")),
        ("하늘", ("given", "하늘")),
        ("다누리", ("guardian", "다누리")),
        ("가상별학교", ("school", "가상별학교")),
    ],
)
def test_find_spans_keeps_roster_identifier_kinds(roster, text, identifier):
    del roster  # Unused.
    identifiers = load_roster()
    pattern = compile_roster_pattern(identifiers)

    assert find_spans(text, identifiers, pattern) == [
        (0, len(text), identifier)
    ]


def test_find_spans_normalizes_phone_spans(roster):
    del roster  # Unused.
    text = "010-1234-5678"
    assert find_spans(text, load_roster(), None) == [
        (0, len(text), ("phone", "+821012345678"))
    ]


def test_find_spans_normalizes_email_spans(roster):
    del roster  # Unused.
    text = "Synthetic.One+2@Example.test"
    assert find_spans(text, load_roster(), None) == [
        (0, len(text), ("email", "synthetic.one+2@example.test"))
    ]


def test_find_spans_merges_overlaps_and_keeps_first_identifier(roster):
    del roster  # Unused.
    identifiers = load_roster()
    text = "Ann Lee.one@example.test Tail!"
    pattern = compile_roster_pattern(identifiers)

    assert find_spans(text, identifiers, pattern) == [
        (0, text.index("!"), identifiers["Ann Lee"])
    ]


def test_find_spans_returns_empty_for_text_without_identifiers(roster):
    del roster  # Unused.
    text = "Date 2026-09-28, score 85/100."
    identifiers = load_roster()
    pattern = compile_roster_pattern(identifiers)

    assert find_spans(text, identifiers, pattern) == []


def test_find_spans_checks_contacts_with_an_empty_identifier_map(roster):
    del roster  # Unused.
    text = "010-1234-5678; Synthetic.One+2@Example.test"

    assert find_spans(text, {}, None) == [
        (0, len("010-1234-5678"), ("phone", "+821012345678")),
        (
            text.index("Synthetic"),
            len(text),
            ("email", "synthetic.one+2@example.test"),
        ),
    ]


def test_korean_phone_formats_and_non_phone_numbers(roster):
    del roster  # Unused.
    phones = (
        "010-1234-5678",
        "01012345678",
        "010 1234 5678",
        "+82 10-1234-5678",
        "02-123-4567",
    )
    masked, _, _ = pseudonymize(" | ".join(phones), {})
    pseudonyms = masked.split(" | ")
    assert len(set(pseudonyms[:4])) == 1
    assert pseudonyms[4] != pseudonyms[0]

    nonphones = "2026.09.28 | 20260928 | 91점 | 3-5번 | 1/2"
    assert pseudonymize(nonphones, {})[0] == nonphones


def test_restore_question_keys_choice_labels_score_levels_and_noul(roster):
    del roster  # Unused.
    questions = {
        "가라온의 선택": Choice(criteria={"가라온": None, "나하늘": None}),
        "다하늘의 점수": Score(criteria=["가라온", "나하늘의 진전"]),
        "다누리의 확인": Noul(),
    }
    _, masked, restore = pseudonymize({}, questions)
    choice_key = next(key for key in masked if key.startswith("Student"))
    score_key = next(
        key
        for key in masked
        if key not in {choice_key} and key.startswith("Student")
    )
    noul_key = next(key for key in masked if key not in {choice_key, score_key})
    choice = masked[choice_key]
    labels = list(choice.criteria)
    score_levels = masked[score_key].criteria
    answers = {
        choice_key: {
            "type": "choice",
            "choice": labels[0],
            "confidence": 0.9,
            "probabilities": {labels[0]: 0.8, labels[1]: 0.2},
        },
        score_key: {
            "type": "score",
            "score": 0.5,
            "confidence": 0.9,
            "probabilities": {"0": 0.6, "1": 0.4},
            "legend": {"0": score_levels[0], "1": score_levels[1]},
        },
        noul_key: {"type": "noul", "noul": 0.8},
    }
    result = restore(answers)
    assert set(result) == set(questions)
    assert result["가라온의 선택"]["choice"] == "가라온"
    assert result["가라온의 선택"]["probabilities"] == {
        "가라온": 0.8,
        "나하늘": 0.2,
    }
    assert result["다하늘의 점수"]["legend"] == {
        "0": "가라온",
        "1": "나하늘의 진전",
    }
    assert result["다누리의 확인"] == answers[noul_key]
    assert "Student" not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize(
    "questions,state",
    [
        ({}, {"가라온": 1, "라온": 2}),
        ({"가라온": Noul(), "라온": Noul()}, {}),
        ({"q": Choice(criteria={"가라온": None, "라온": None})}, {}),
    ],
)
def test_key_and_option_collisions_fail_without_names(roster, questions, state):
    del roster  # Unused.
    with pytest.raises(JudgmentError) as caught:
        pseudonymize(state, questions)
    assert caught.value.error_type == "pseudonym_conflict"
    assert "가라온" not in str(caught.value) and "라온" not in str(caught.value)


def test_missing_phone_library_names_only_shipped_profile(roster, monkeypatch):
    del roster  # Unused.
    monkeypatch.setitem(sys.modules, "phonenumbers", None)
    with pytest.raises(JudgmentError) as caught:
        pseudonymize("synthetic record", {})
    assert caught.value.error_type == "backend_not_configured"
    assert caught.value.detail == str(SHIPPED_CONFIG)


def _sent(state, questions):
    """Return what the provider would receive, as one string."""
    masked_state, masked, _ = pseudonymize(state, questions)
    return json.dumps(
        {
            "state": masked_state,
            "questions": {key: q.to_wire() for key, q in masked.items()},
        },
        ensure_ascii=False,
    )


# A value in each request field that can hold one.
PLACES = {
    "state": lambda value: ({"note": value}, {}),
    "nested state": lambda value: ({"a": [{"b": value}]}, {}),
    "instructions": lambda value: (
        {},
        {"q": NoulQuestion({"a": [value]}, NoulCriteria("yes", "no"))},
    ),
    "noul criterion": lambda value: (
        {},
        {"q": NoulQuestion("Is it true?", NoulCriteria(value, "no"))},
    ),
    "choice description": lambda value: (
        {},
        {"q": ChoiceQuestion("Choose.", {"x": {"a": [value]}, "y": "no"})},
    ),
    "rubric level": lambda value: (
        {},
        {"q": ScoreQuestion("Assess.", ["base", {"a": [value]}])},
    ),
}


@pytest.mark.parametrize("place", PLACES)
@pytest.mark.parametrize("number", [7700101, 7700101.0])
def test_student_numbers_given_as_json_numbers_are_replaced(
    synthetic_roster, place, number
):
    del synthetic_roster  # Unused.
    sent = _sent(*PLACES[place](number))
    assert "7700101" not in sent
    assert "Student 01" in sent


def test_a_json_number_gets_the_stand_in_of_its_string_form(synthetic_roster):
    del synthetic_roster  # Unused.
    assert _sent({"id": 7700101}, {}) == _sent({"id": "7700101"}, {})


def test_other_numbers_keep_their_value_and_type(synthetic_roster):
    del synthetic_roster  # Unused.
    state = {
        "score": 85,
        "probability": 0.75,
        "year": 2026,
        "date": 20260928,
        "count": 12,
        "flag": True,
        "nothing": None,
        "list": [1, 2.5, 1234567890],
    }
    masked, _, _ = pseudonymize(state, {})
    assert masked == state
    assert [type(value) for value in masked.values()] == [
        type(value) for value in state.values()
    ]


# (field name, its value, text that must not reach the provider, stand-in)
FIELDS = [
    ("DOB", "2011-04-23", "2011", "Birth date"),
    ("dob", 20110423, "20110423", "Birth date"),
    ("date of birth", "April 23, 2011", "April", "Birth date"),
    ("Date_Of_Birth", "23/04/2011", "23/04", "Birth date"),
    ("dateOfBirth", "2011-04-23", "2011", "Birth date"),
    ("birthday", "April 23", "April", "Birth date"),
    ("birth-date", "2011.04.23", "2011", "Birth date"),
    ("born", 2011, "2011", "Birth date"),
    ("address", "487 Imaginary Street", "487", "Address"),
    ("Home Address", "Imaginary Street", "Imaginary", "Address"),
    ("student_dob", "2011-04-23", "2011", "Birth date"),
    ("guardian address", "Imaginary Street", "Imaginary", "Address"),
    ("Student Grade", 10, "10", "Cohort"),
    ("grade", 10, "10", "Cohort"),
    ("grade", "10", "10", "Cohort"),
    ("Grade Level", "10th", "10", "Cohort"),
    ("school year", 10, "10", "Cohort"),
    ("year", "11", "11", "Cohort"),
    ("year", "tenth", "tenth", "Cohort"),
    ("grade", "Grade 10", "10", "Cohort"),
]


@pytest.mark.parametrize(("field", "value", "hidden", "standin"), FIELDS)
def test_a_field_named_for_its_meaning_makes_its_value_an_identifier(
    synthetic_roster, field, value, hidden, standin
):
    del synthetic_roster  # Unused.
    sent = _sent({field: value}, {})
    assert hidden not in sent
    assert standin in sent


@pytest.mark.parametrize("place", PLACES)
@pytest.mark.parametrize(
    ("field", "value", "hidden"),
    [
        ("DOB", "2011-04-23", "2011"),
        ("address", "487 Imaginary Street", "487"),
        ("grade", 10, "10"),
    ],
)
def test_field_names_apply_in_every_request_field(
    synthetic_roster, place, field, value, hidden
):
    del synthetic_roster  # Unused.
    sent = _sent(*PLACES[place]({field: value}))
    assert hidden not in sent


def test_a_field_name_gives_the_same_stand_in_as_the_text_form(
    synthetic_roster,
):
    del synthetic_roster  # Unused.
    assert _sent({"note": "born on 2011-04-23"}, {}).count("Birth date 01") == 1
    assert _sent({"DOB": "2011-04-23"}, {}) == json.dumps(
        {"state": {"DOB": "Birth date 01"}, "questions": {}}
    )


@pytest.mark.parametrize(
    "state",
    [
        {"year": 2026},
        {"school year": "2026"},
        {"academic year": 3},
        {"grade": 85},
        {"grade": "B+"},
        {"score": 10},
        {"lesson": "2026-09-28"},
        {"born": None},
        {"DOB": ""},
        {"grades": [10, 11]},
        {"grade": {"math": "B+"}},
        {"grades": {"math": 10}},
        {"student_id": ""},
    ],
)
def test_fields_that_are_not_identifiers_stay(synthetic_roster, state):
    del synthetic_roster  # Unused.
    masked, _, _ = pseudonymize(state, {})
    assert masked == state


def test_korean_field_names_are_known_too(synthetic_roster):
    del synthetic_roster  # Unused.
    state = {
        "생년월일": "2011-04-23",
        "생일": 20110423,
        "출생": 2011,
        "주소": "487 Imaginary Street",
        "학년": 3,
        "학년도": 2026,
    }
    masked, _, _ = pseudonymize(state, {})
    assert masked == {
        "생년월일": "Birth date 01",
        "생일": "Birth date 02",
        "출생": "Birth date 03",
        "주소": "Address 01",
        "학년": "Cohort 01",
        "학년도": 2026,
    }


@pytest.mark.parametrize(
    ("state", "hidden"),
    [
        ({"DOB": {"year": 2011, "month": 4, "day": 23}}, ["2011", "year"]),
        (
            {"address": {"line1": "487 Imaginary Street", "zip": "12345"}},
            ["Imaginary", "12345", "line1"],
        ),
        ({"home_address": [{"street": ["Imaginary Street"]}]}, ["Imaginary"]),
        ({"DOB": {"2011-04-23": True}}, ["2011"]),
        ({"grade": {"level": 10}}, ["10"]),
        ({"grade": {"DOB": "2011-04-23"}}, ["2011"]),
        ({"student": {"dateOfBirth": [{"y": 2011}]}}, ["2011"]),
    ],
)
def test_every_value_and_key_inside_a_named_field_is_replaced(
    synthetic_roster, state, hidden
):
    del synthetic_roster  # Unused.
    sent = _sent(state, {})
    for text in hidden:
        assert text not in sent


@pytest.mark.parametrize("key", [7700101, 7700101.0])
def test_keys_that_are_not_strings_are_replaced_as_their_text(
    synthetic_roster, key
):
    del synthetic_roster  # Unused.
    masked, _, _ = pseudonymize({key: "record", "a": [{key: 1}]}, {})
    assert masked == {"Student 01": "record", "a": [{"Student 01": 1}]}


@pytest.mark.parametrize(
    "text",
    [
        "Solbit-ro 12-gil 487",
        "Ha-neul-ro 487",
        "487 Solbit-ro, Jongno-gu, Seoul 03000",
    ],
)
def test_a_romanized_address_leaves_no_fragment(synthetic_roster, text):
    del synthetic_roster  # Unused.
    assert pseudonymize({"note": text}, {})[0] == {"note": "Address 01"}


@pytest.mark.parametrize(
    "text",
    [
        "생년월일: 이천십일년",
        "학번 = 7799999",
        "| 이름 | 주소 |\n|---|---|\n| 가라온 | 어딘가 |",
    ],
)
def test_korean_field_names_that_keep_their_value_are_refused(
    synthetic_roster, text
):
    del synthetic_roster  # Unused.
    with pytest.raises(JudgmentError) as caught:
        pseudonymize({"note": text}, {})
    assert caught.value.error_type == "identifier_remaining"
