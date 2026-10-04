"""Synthetic invented identities test the call boundary without a provider."""

from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from education_privacy_gate.masking import Masker
from education_privacy_gate.roster import GateError
from education_privacy_gate.roster import Registry


def registry(extra=()):
    return Registry.from_data(
        {
            "version": 1,
            "entries": [
                {"kind": "person", "full": "가라온", "romanized": ["Ga Raon"]},
                {
                    "kind": "person",
                    "full": "남궁누리",
                    "romanized": ["Namgung Nuri"],
                    "aliases": ["별누리"],
                },
                {
                    "kind": "school",
                    "spellings": [
                        "가상별빛고등학교",
                        "가상별빛고",
                        "synthetic-school",
                    ],
                },
                *extra,
            ],
        }
    )


class Names:
    def __init__(self, *names):
        self.names = iter(names)
        self.calls = 0

    def first_name(self):
        self.calls += 1
        return next(self.names, "Avery")


def gate(*names, extra=()):
    masker = Masker(registry(extra))
    masker.faker = Names(*names)
    return masker


@pytest.mark.parametrize(
    "text",
    [
        "가라온은",
        "라온이",
        "Ga Raon",
        "ra-on,GA",
        "GARAON",
        "r a o n ga",
        "Raon",
        "남궁누리는",
        "누리와",
        "Namgung Nuri",
        "Nuri Namgung",
        "별누리",
        "Ga Ra‑on",
        "GA RAON",
    ],
)
def test_every_form(text):
    with gate("Avery") as masker:
        masked = masker.mask({"text": text})
        assert "Avery" in masked["text"]
        assert masker.restore(masked) == {"text": text}


def test_one_first_name_mixed_forms():
    text = "가라온 / 라온 / Ga Raon / RAON GA / Raon"
    with gate("Avery") as masker:
        masked = masker.mask({"text": text})
        assert masked["text"] == "Avery / Avery / Avery / Avery / Avery"
        assert masker.faker.calls == 1
        assert masker.restore(masked) == {"text": text}
        assert masker.restore("Avery is ready") == "Ga Raon is ready"


def test_ambiguous_echo_uses_registered_default():
    with gate("Avery") as masker:
        masked = masker.mask(["가라온", "GA RAON"])
        assert masked == ["Avery", "Avery"]
        assert masker.restore(masked) == ["Ga Raon", "Ga Raon"]
    with gate("Avery", extra=[{"kind": "person", "full": "다새봄"}]) as masker:
        masker.mask("다새봄")
        assert masker.restore("Avery is ready") == "다새봄 is ready"


def test_shared_given_has_separate_identity():
    with gate(
        "Avery",
        "Blair",
        "Casey",
        extra=[{"kind": "person", "full": "나라온", "romanized": ["Na Raon"]}],
    ) as masker:
        masked = masker.mask(["가라온", "나라온", "라온"])
        assert len(set(masked)) == 3
        assert masker.restore(masked) == ["가라온", "나라온", "라온"]


def test_schools_variants_and_boundaries():
    text = "가상별빛고등학교 가상별빛고 synthetic-school synthetic-schoolx"
    with gate() as masker:
        masked = masker.mask(text)
        assert masked == "School 01 School 02 School 03 synthetic-schoolx"
        assert masker.restore(masked) == text
        assert (
            masker.restore("School 03 elsewhere")
            == "synthetic-school elsewhere"
        )


def test_latin_boundaries():
    text = (
        "xGaRaon GARAONx 1Raon raon2 ordinary Korean "
        "가나다 2학년 3반 2026학년도 85점"
    )
    with gate() as masker:
        assert masker.mask(text) == text


@pytest.mark.parametrize(
    "text,label",
    [
        ("010-2345-6789", "Phone 01"),
        ("+82 10 2345 6789", "Phone 01"),
        ("fictional+tag@example.invalid", "Email 01"),
        ("EduOK: 1234567890", "EduOK: EduOK 01"),
        ("student number=1234567890", "student number=EduOK 01"),
        ("학번: 1234567890", "학번: EduOK 01"),
        ("s-1234567890.md", "s-EduOK 01.md"),
        ("1234567890", "EduOK 01"),
        ("991399-1234567", "Resident number 01"),
        ("9913991234567", "Resident number 01"),
    ],
)
def test_patterns(text, label):
    with gate() as masker:
        assert masker.mask(text) == label
        assert masker.restore(label) == text


def test_pattern_overlaps_boundaries_and_plain_numbers():
    text = "EduOK: 9913991234567 s-1234567890123 199139912345678 85 2026 3학년"
    with gate() as masker:
        masked = masker.mask(text)
        assert masked == (
            "EduOK: Resident number 01 s-Resident number 02 "
            "199139912345678 85 2026 3학년"
        )
        assert masker.restore(masked) == text
    with gate() as masker:
        assert masker.mask({"grade": 3, "score": 85, "year": 2026}) == {
            "grade": 3,
            "score": 85,
            "year": 2026,
        }


def test_nested_keys_values_json_errors_usage():
    original = {
        "가라온": [{"text": "가라온 learns"}],
        "usage": {"tokens": "라온"},
    }
    with gate("Avery") as masker:
        masked = masker.mask(original)
        assert "Avery" in masked
        encoded = json.dumps(masked)
        result = {
            "content": [{"type": "text", "text": encoded}],
            "structuredContent": masked,
            "_meta": {"usage": masked},
            "isError": True,
        }
        restored = masker.restore(result)
        expected = {
            "Ga Raon": [{"text": "가라온 learns"}],
            "usage": {"tokens": "Ga Raon"},
        }
        assert json.loads(restored["content"][0]["text"]) == expected
        assert restored["structuredContent"] == expected
        assert restored["_meta"]["usage"] == expected
        assert restored["isError"] is True
        nested = json.dumps({"encoded": json.dumps(masked)})
        assert (
            json.loads(json.loads(masker.restore(nested))["encoded"])
            == expected
        )
        assert masker.restore("Error: Avery") == "Error: Ga Raon"


def test_pattern_constrained_fields():
    with gate() as masker, pytest.raises(GateError):
        masker.mask(
            {"items": [{"id": "Ga Raon"}]},
            constrained=lambda path: path == ("items", 0, "id"),
        )
    with gate() as masker:
        assert masker.mask({"id": "safe-id"}, constrained=bool) == {
            "id": "safe-id"
        }


def test_collision_redraw_request_registry_other_standin():
    with gate("Raon", "Blair", "Avery", "Avery", "Casey") as masker:
        masked = masker.mask(["가라온", "Blair", "남궁누리"])
        assert masked == ["Avery", "Blair", "Casey"]
        assert masker.faker.calls == 5
    with gate("very", "Avery") as masker:
        assert masker.mask(["가라온", "everywhere"]) == ["Avery", "everywhere"]


def test_exhaustion_and_clear_on_error():
    with gate("라온") as masker:
        masker.faker = Names(*(["라온"] * 256))
        with pytest.raises(
            GateError, match="^Privacy gate rejected the call\\.$"
        ):
            masker.mask("가라온")
        assert masker.faker.calls == 256
        assert not masker.reverse


def test_fixed_label_collision_and_reverse_key_collision():
    with gate() as masker, pytest.raises(GateError):
        masker.mask("가상별빛고 School 01")
    with gate("Avery") as masker:
        masker.mask("가라온")
        with pytest.raises(GateError):
            masker.restore({"Avery": 1, "가라온": 2})
    with gate("Avery") as masker, pytest.raises(GateError):
        masker.mask({"가라온": 1, "라온": 2})


def test_no_custom_body_limits():
    with gate() as masker:
        assert len(masker.mask("x" * 262145)) == 262145
        assert len(masker.restore("x" * 2097153)) == 2097153


def test_tree_bounds_and_invalid_types():
    tree = "safe"
    for unused_index in range(64):
        tree = [tree]
    with gate() as masker:
        assert masker.mask(tree) == tree
    with gate() as masker, pytest.raises(GateError):
        masker.mask([tree])
    with gate() as masker:
        assert len(masker.mask([0] * 49999)) == 49999
    with gate() as masker:
        assert len(masker.mask([0] * 50000)) == 50000
    for value in ({1: "safe"}, float("nan"), object()):
        with gate() as masker, pytest.raises(GateError):
            masker.mask(value)


def test_identity_bounds():
    data = [
        {"kind": "school", "spellings": [f"school-{i:04d}"]} for i in range(129)
    ]
    with gate(extra=data) as masker:
        assert "School 128" in masker.mask(
            " ".join(f"school-{i:04d}" for i in range(128))
        )
    with gate(extra=data) as masker, pytest.raises(GateError):
        masker.mask(" ".join(f"school-{i:04d}" for i in range(129)))


def test_two_concurrent_calls_and_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.rglob("*"))

    def run(fake):
        with gate(fake) as masker:
            masked = masker.mask("가라온")
            assert masked == fake
            assert masker.restore(masked) == "가라온"
        assert not masker.reverse
        return fake

    with ThreadPoolExecutor(2) as pool:
        assert list(pool.map(run, ["Avery", "Blair"])) == ["Avery", "Blair"]
    assert list(tmp_path.rglob("*")) == before


def test_context_exit_exception_clears():
    masker = gate("Avery")
    with pytest.raises(RuntimeError), masker:
        masker.mask("가라온")
        raise RuntimeError("synthetic failure")
    assert not masker.reverse


def test_shared_latin_given_keeps_ambiguous_identity():
    with gate(
        "Avery",
        extra=[{"kind": "person", "full": "나라온", "romanized": ["Na Raon"]}],
    ) as masker:
        assert masker.mask("라온 Raon") == "Avery Avery"
        assert masker.faker.calls == 1


def test_last_allowed_draw():
    with gate(*(["Raon"] * 255), "Avery") as masker:
        assert masker.mask("가라온") == "Avery"
        assert masker.faker.calls == 256


def test_json_keys_escaping_numeric_usage_and_duplicate_rejection():
    with gate("Avery") as masker:
        masker.mask("가라온")
        escaped = '{"\\u0041very":"\\u0041very","usage":"1e1"}'
        assert json.loads(masker.restore(escaped)) == {
            "가라온": "가라온",
            "usage": "1e1",
        }
        with pytest.raises(GateError):
            masker.restore('{"Avery":1,"Avery":2}')


def test_unsupported_result_type():
    with gate() as masker:
        masker.mask("safe")
        with pytest.raises(GateError):
            masker.restore({"content": b"opaque"})


def test_default_faker_and_fresh_generators_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    before = list(tmp_path.rglob("*"))
    with Masker(registry()) as first, Masker(registry()) as second:
        assert first.faker.locales == ["en_US"]
        assert first.faker.random is not second.faker.random
        masked = first.mask("가라온")
        assert masked.isascii() and masked.isalpha()
        assert first.restore(masked) == "가라온"
    assert not first.anchors and not first.assigned and not first.reverse
    assert list(tmp_path.rglob("*")) == before


def test_ten_digit_boundary_and_phone_precedence():
    with gate() as masker:
        assert masker.mask("0212345678") == "Phone 01"
    with gate() as masker:
        assert masker.mask("123456789 12345678901 1234567890123") == (
            "123456789 12345678901 Resident number 01"
        )
    with gate() as masker:
        assert masker.mask("x1234567890x") == "xEduOK 01x"


def test_restore_tokens_have_boundaries_and_json_keys_decode():
    with gate("Avery") as masker:
        masker.mask("가라온")
        assert masker.restore("Averyx xAvery Avery는") == (
            "Averyx xAvery Ga Raon는"
        )
        encoded_key = json.dumps({"who": "Avery"})
        result = masker.restore({encoded_key: True})
        assert json.loads(next(iter(result))) == {"who": "가라온"}
    data = [
        {"kind": "school", "spellings": [f"school-{i:04d}"]} for i in range(128)
    ]
    with gate(extra=data) as masker:
        masker.mask(" ".join(f"school-{i:04d}" for i in range(128)))
        assert masker.restore("School 12 / School 128 / School 1289") == (
            "school-0011 / school-0127 / School 1289"
        )


def test_numeric_ten_digit_ids_open_context_nested_and_types():
    with gate() as masker:
        original = {
            "context": [1234567890, {"id": -1234567890}],
            "other": [True, 1234567890.0, 85, 2026, 12345678901],
        }
        masked = masker.mask(original)
        assert masked["context"] == ["EduOK 01", {"id": "EduOK 02"}]
        assert masked["other"] == original["other"]
        assert masker.restore(masked)["context"] == [
            "1234567890",
            {"id": "-1234567890"},
        ]
    with gate() as masker:
        # The same digits as text are a recognized phone; an integer is an ID.
        assert masker.mask(["0212345678", 2123456789]) == [
            "Phone 01",
            "EduOK 01",
        ]


def test_numeric_typed_field_fails_unchanged_schema():
    from jsonschema import ValidationError  # noqa: PLC0415
    from jsonschema import validate  # noqa: PLC0415

    schema = {"type": "object", "properties": {"top_k": {"type": "integer"}}}
    with gate() as masker:
        masked = masker.mask({"top_k": 1234567890})
        assert masked == {"top_k": "EduOK 01"}
        with pytest.raises(ValidationError):
            validate(masked, schema)


def test_labels_cannot_reintroduce_registered_spelling_case_variant():
    with gate(extra=[{"kind": "school", "spellings": ["SCHOOL"]}]) as masker:
        with pytest.raises(GateError):
            masker.mask("가상별빛고")


def test_cancelled_context_clears_maps():
    import asyncio  # noqa: PLC0415

    masker = gate("Avery")
    with pytest.raises(asyncio.CancelledError), masker:
        masker.mask("가라온")
        raise asyncio.CancelledError()
    assert not masker.reverse and not masker.anchors and not masker.assigned
