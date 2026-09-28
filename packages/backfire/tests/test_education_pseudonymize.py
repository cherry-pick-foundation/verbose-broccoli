import csv
import json
import sys

import pytest
from typesafe_sdk import Choice, Noul, Score

from backfire.config import SHIPPED_CONFIG, xdg_path
from backfire.failures import JudgmentError
from backfire_education.roster import load_roster
from backfire_education.pseudonymize import compile_roster_pattern, find_spans, pseudonymize


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
        "다누리 확인": Noul(criteria={"true": "다누리가 확인", "false": "확인되지 않음"}),
        "하늘 점수": Score(criteria=["가라온의 진전", "나하늘의 연습"]),
    }
    masked_state, masked_questions, _ = pseudonymize(state, questions)

    assert "가라온" not in json.dumps(masked_state, ensure_ascii=False)
    assert "라온이" not in json.dumps(masked_questions, ensure_ascii=False, default=str)
    assert "다누리" not in json.dumps(masked_state, ensure_ascii=False)
    assert "가상별학교" not in json.dumps(masked_state, ensure_ascii=False)
    assert "날짜 2026-09-28, 범위 20-24, 26, 29-37번, 점수 1234567890." == masked_state["other"]
    assert set(type(item) for item in masked_questions.values()) == {Choice, Noul, Score}
    assert len(masked_questions) == len(questions)
    assert "학생" in masked_state["summary"]
    assert "학교" in masked_state["nested"][0]["school"]


def test_given_name_particles_shared_given_name_and_longest_school_match(roster):
    state = "가라온은 라온이가 왔고, 하늘이는 나하늘과 다하늘을 봤다. 가상별학교."
    masked, _, _ = pseudonymize(state, {})
    full, given = masked.split("은 ", 1)[0], masked.split("은 ", 1)[1].split("이가", 1)[0]
    assert full == given
    assert "나하늘" not in masked and "다하늘" not in masked and "하늘이" not in masked
    assert "가상별학교" not in masked
    assert masked.endswith("학교01.")
    # The shared given name has its own assignment, distinct from both students.
    raw, _, _ = pseudonymize("나하늘 다하늘 하늘", {})
    student_a, student_b, shared = raw.split()
    assert len({student_a, student_b, shared}) == 3


def test_phone_email_normalization_and_pseudonym_like_text(roster):
    source = (
        "+1 202-555-0123 and +12025550123; Synthetic.One+2@Example.test "
        "and synthetic.one+2@example.test; keep 학생10명."
    )
    masked, _, _ = pseudonymize(source, {})
    phone_a, phone_b = masked.split(" and ", 1)[0], masked.split(" and ", 1)[1].split(";", 1)[0]
    assert phone_a == phone_b
    assert "+1 202-555-0123" not in masked and "+12025550123" not in masked
    assert "Synthetic.One+2@Example.test" not in masked
    assert masked.count("이메일") == 2
    assert masked.endswith("keep 학생10명.")


def test_longer_email_wins_roster_match_at_same_start(roster):
    masked, _, _ = pseudonymize("Ann@example.test", {})
    assert masked == "이메일01"


def test_roster_overlap_masks_the_rest_of_an_email(roster):
    masked, _, _ = pseudonymize("Ann Lee.one@example.test", {})
    assert masked == "학생01"


def test_chain_of_overlaps_extends_the_kept_roster_span(roster):
    masked, _, _ = pseudonymize("Ann Lee.one@example.test Tail!", {})
    assert masked == "학생01!"


@pytest.mark.parametrize(("text", "identifier"), [
    ("가라온", ("student", "가라온")),
    ("하늘", ("given", "하늘")),
    ("다누리", ("guardian", "다누리")),
    ("가상별학교", ("school", "가상별학교")),
])
def test_find_spans_keeps_roster_identifier_kinds(roster, text, identifier):
    identifiers = load_roster()
    pattern = compile_roster_pattern(identifiers)

    assert find_spans(text, identifiers, pattern) == [
        (0, len(text), identifier)
    ]


def test_find_spans_normalizes_phone_spans(roster):
    text = "010-1234-5678"
    assert find_spans(text, load_roster(), None) == [
        (0, len(text), ("phone", "+821012345678"))
    ]


def test_find_spans_normalizes_email_spans(roster):
    text = "Synthetic.One+2@Example.test"
    assert find_spans(text, load_roster(), None) == [
        (0, len(text), ("email", "synthetic.one+2@example.test"))
    ]


def test_find_spans_merges_overlaps_and_keeps_first_identifier(roster):
    identifiers = load_roster()
    text = "Ann Lee.one@example.test Tail!"
    pattern = compile_roster_pattern(identifiers)

    assert find_spans(text, identifiers, pattern) == [
        (0, text.index("!"), identifiers["Ann Lee"])
    ]


def test_find_spans_returns_empty_for_text_without_identifiers(roster):
    text = "Date 2026-09-28, score 85/100."
    identifiers = load_roster()
    pattern = compile_roster_pattern(identifiers)

    assert find_spans(text, identifiers, pattern) == []


def test_find_spans_checks_contacts_with_an_empty_identifier_map(roster):
    text = "010-1234-5678; Synthetic.One+2@Example.test"

    assert find_spans(text, {}, None) == [
        (0, len("010-1234-5678"), ("phone", "+821012345678")),
        (text.index("Synthetic"), len(text), ("email", "synthetic.one+2@example.test")),
    ]


def test_korean_phone_formats_and_non_phone_numbers(roster):
    phones = ("010-1234-5678", "01012345678", "010 1234 5678", "+82 10-1234-5678", "02-123-4567")
    masked, _, _ = pseudonymize(" | ".join(phones), {})
    pseudonyms = masked.split(" | ")
    assert len(set(pseudonyms[:4])) == 1
    assert pseudonyms[4] != pseudonyms[0]

    nonphones = "2026.09.28 | 20260928 | 91점 | 3-5번 | 1/2"
    assert pseudonymize(nonphones, {})[0] == nonphones


def test_restore_question_keys_choice_labels_score_levels_and_noul(roster):
    questions = {
        "가라온의 선택": Choice(criteria={"가라온": None, "나하늘": None}),
        "다하늘의 점수": Score(criteria=["가라온", "나하늘의 진전"]),
        "다누리의 확인": Noul(),
    }
    _, masked, restore = pseudonymize({}, questions)
    choice_key = next(key for key in masked if key.startswith("학생"))
    score_key = next(key for key in masked if key not in {choice_key} and key.startswith("학생"))
    noul_key = next(key for key in masked if key not in {choice_key, score_key})
    choice = masked[choice_key]
    labels = list(choice.criteria)
    score_levels = masked[score_key].criteria
    answers = {
        choice_key: {"type": "choice", "choice": labels[0], "confidence": 0.9,
                     "probabilities": {labels[0]: 0.8, labels[1]: 0.2}},
        score_key: {"type": "score", "score": 0.5, "confidence": 0.9,
                    "probabilities": {"0": 0.6, "1": 0.4},
                    "legend": {"0": score_levels[0], "1": score_levels[1]}},
        noul_key: {"type": "noul", "noul": 0.8},
    }
    result = restore(answers)
    assert set(result) == set(questions)
    assert result["가라온의 선택"]["choice"] == "가라온"
    assert result["가라온의 선택"]["probabilities"] == {"가라온": 0.8, "나하늘": 0.2}
    assert result["다하늘의 점수"]["legend"] == {"0": "가라온", "1": "나하늘의 진전"}
    assert result["다누리의 확인"] == answers[noul_key]
    assert "학생" not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize("questions,state", [
    ({}, {"가라온": 1, "라온": 2}),
    ({"가라온": Noul(), "라온": Noul()}, {}),
    ({"q": Choice(criteria={"가라온": None, "라온": None})}, {}),
])
def test_key_and_option_collisions_fail_without_names(roster, questions, state):
    with pytest.raises(JudgmentError) as caught:
        pseudonymize(state, questions)
    assert caught.value.error_type == "pseudonym_conflict"
    assert "가라온" not in str(caught.value) and "라온" not in str(caught.value)


def test_missing_phone_library_names_only_shipped_profile(roster, monkeypatch):
    monkeypatch.setitem(sys.modules, "phonenumbers", None)
    with pytest.raises(JudgmentError) as caught:
        pseudonymize("synthetic record", {})
    assert caught.value.error_type == "backend_not_configured"
    assert caught.value.detail == str(SHIPPED_CONFIG)
