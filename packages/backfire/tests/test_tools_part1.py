"""Scripted checks against jev-mcp 0.9.0's published metadata and handlers."""

import asyncio
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

import pytest
from scripted_judge import ScriptedJudge

from backfire.tools import text
from backfire.tools.answers import validate_choice_answer
from backfire.tools.answers import validate_noul_answer
from backfire.tools.answers import validate_score_answer


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=True).encode()
    ).hexdigest()


@pytest.mark.parametrize(
    "name, expected",
    [
        (
            "verify",
            "8e6cd07886dcf4cfca1f4524215d2942d1e066a55b265429c0763f79a78e1900",
        ),
        (
            "screen",
            "acb387e610bcdf8a84ace2b670fe0addfd0265c07dbcd79f70de7e372b632438",
        ),
        (
            "noul",
            "691d3380c1601e8200bf481ab1b4cd6d3f0ac6d2ff9373288ef00c3a8f28c133",
        ),
        (
            "find",
            "f829dd9faaede71180b619ea76dbce0cf5099d7862293675f37b6b1cbcd76339",
        ),
        (
            "classify",
            "11ecf2a878ae33f2279d067a39ed808d69e4f157595df96b80ad4962f68b5344",
        ),
        (
            "decide",
            "3d3d2b3ee5caf47489e772732f4c28760de5a3b07f5f60ced82a012cf179075b",
        ),
    ],
)
def test_published_tool_metadata(name, expected):
    # Hashes of the captured tools/list after the two documented name mappings.
    module = importlib.import_module("backfire.tools." + name)
    actual = {
        "name": module.NAME,
        "title": module.TITLE,
        "description": module.DESCRIPTION,
        "inputSchema": module.INPUT_SCHEMA,
        "execution": module.EXECUTION,
    }
    assert digest(actual) == expected, actual


def test_text_matches_ecmascript_numbers_indentation_keys_and_unicode():
    assert text({"b": [1.0, -0.0, 1e-7, 1e-6, 1e20, 1e21], "a": {}}) == (
        '{\n  "b": [\n    1,\n    0,\n'
        "    1e-7,\n    0.000001,\n"
        "    100000000000000000000,\n"
        '    1e+21\n  ],\n  "a": {}\n}'
    )
    assert text({"10": "ten", "2": "two", "01": "한글 😀", "0": "zero"}) == (
        '{\n  "0": "zero",\n  "2": "two",\n  "10": "ten",\n  "01": "한글 😀"\n}'
    )
    assert text(
        [True, False, None, float("nan"), float("inf"), "\ud83d", '\n\t"']
    ) == (
        "[\n  true,\n  false,\n  null,\n"
        '  null,\n  null,\n  "\\ud83d",\n'
        '  "\\n\\t\\""\n]'
    )
    assert text([]) == "[]"
    assert text(9007199254740993) == "9007199254740992"
    assert text({"1" * 5000: 1}) == '{\n  "' + "1" * 5000 + '": 1\n}'


def pick(choice, keys, confidence=0.9):
    return {
        "type": "choice",
        "choice": choice,
        "confidence": confidence,
        "probabilities": {key: int(key == choice) for key in keys},
    }


def probability(value):
    return {"type": "noul", "noul": value}


@pytest.mark.parametrize(
    "answer",
    [
        None,
        [],
        {},
        True,
        {"noul": True},
        {"noul": "0.5"},
        {"noul": -0.01},
        {"noul": 1.01},
        {"noul": float("nan")},
        {"noul": float("inf")},
    ],
)
def test_noul_validator_rejects_malformed_values(answer):
    assert validate_noul_answer(answer) is None


@pytest.mark.parametrize("value", [0, 0.5, 1])
def test_noul_validator_preserves_real_probabilities(value):
    assert validate_noul_answer(probability(value)) == value


@pytest.mark.parametrize(
    "override",
    [
        {"choice": True},
        {"choice": "missing"},
        {"probabilities": None},
        {"probabilities": []},
        {"probabilities": {"a": 1}},
        {"probabilities": {"a": 1, "b": 0, "extra": 0}},
        {"probabilities": {"a": True, "b": 0}},
        {"probabilities": {"a": "1", "b": 0}},
        {"probabilities": {"a": float("nan"), "b": 0}},
        {"probabilities": {"a": float("inf"), "b": 0}},
        {"probabilities": {"a": 1.01, "b": -0.01}},
        {"probabilities": {"a": 0, "b": 0}},
        {"probabilities": {"a": 0.98, "b": 0}},
        {"probabilities": {"a": 0.4, "b": 0.6}},
    ],
)
def test_choice_validator_rejects_malformed_distributions(override):
    assert (
        validate_choice_answer(
            {**pick("a", ["a", "b"]), **override}, ["a", "b"]
        )
        is None
    )


def test_choice_ties_tolerances_and_optional_confidence():
    for values in (
        {"a": 0.5, "b": 0.5},
        {"a": 0.4999999996, "b": 0.5000000004},
        {"a": 0.99, "b": 0},
    ):
        answer = {"choice": "a", "probabilities": values}
        assert validate_choice_answer(answer, ["a", "b"]) == {
            **answer,
            "confidence": None,
        }
    for invalid in (None, True, "0.9", -1, 2, float("inf"), float("nan")):
        answer = pick("a", ["a", "b"], invalid)
        assert validate_choice_answer(answer, ["a", "b"])["confidence"] is None
    assert (
        validate_choice_answer(pick("a", ["a", "b"], 0), ["a", "b"])[
            "confidence"
        ]
        == 0
    )


@pytest.mark.parametrize(
    "answer",
    [
        None,
        [],
        {},
        {"score": True},
        {"score": -1},
        {"score": 3},
        {"score": float("nan")},
        {"score": float("inf")},
        {"score": 1, "probabilities": []},
        {"score": 1, "probabilities": {"0": 0, "1": 1}},
        {"score": 1, "probabilities": {"0": 0, "1": 0, "2": 0}},
        {"score": 1, "probabilities": {"0": 0, "1": 0, "2": 1}},
    ],
)
def test_score_validator_rejects_malformed_values(answer):
    assert validate_score_answer(answer) is None


def test_score_distribution_is_optional_and_mean_is_not_rescaled():
    assert validate_score_answer({"score": 2}) == {
        "score": 2,
        "confidence": None,
        "probabilities": None,
    }
    answer = {
        "score": 1.98,
        "confidence": 0.9,
        "probabilities": {"0": 0, "1": 0, "2": 0.99},
    }
    assert validate_score_answer(answer) == answer
    assert validate_score_answer({**answer, "score": 2.0}) == {
        **answer,
        "score": 2.0,
    }
    assert validate_score_answer({**answer, "score": 1.95}) is None
    assert (
        validate_score_answer({**answer, "confidence": True})["confidence"]
        is None
    )


def fidelity_cases():
    """Inputs to the pinned upstream capture; no provider calls are needed."""
    cases = []

    def add(identifier, module, arguments, answers):
        cases.append(
            {
                "id": identifier,
                "module": module,
                "arguments": arguments,
                "answers": answers,
            }
        )

    relation = ["supports", "contradicts", "says_nothing"]
    add(
        "verify_verdicts",
        "verify",
        {"claims": ["A", "B", "C"], "evidence": "Document"},
        {
            f"relation_claim{index}": pick(
                key, relation, [0.8, 0.79, None][index]
            )
            for index, key in enumerate(relation)
        },
    )
    add(
        "verify_sources",
        "verify",
        {
            "claims": ["한글", "Empty"],
            "evidence": [{"id": "x?", "text": "A"}, {"id": "x!", "text": "B"}],
        },
        {
            "relation_claim0": pick("supports", relation),
            "source_claim0": pick("x_1", ["x", "x_1", "none"]),
            "relation_claim1": {
                **pick("supports", relation),
                "confidence": "bad",
            },
        },
    )
    add(
        "verify_missing_source",
        "verify",
        {"claims": ["A"], "evidence": [{"text": "A"}, {"text": "B"}]},
        {
            "relation_claim0": pick("supports", relation, None),
        },
    )
    add(
        "verify_invalid_source",
        "verify",
        {"claims": ["A"], "evidence": {"text": "A"}},
        {
            "relation_claim0": pick("says_nothing", relation),
            "source_claim0": pick("absent", ["absent", "none"]),
        },
    )
    add("verify_missing", "verify", {"claims": ["A"], "evidence": "A"}, {})

    for name, values, purpose in [
        ("pass", (0, 1, None), None),
        ("block", (0.75, 1, None), None),
        ("review", (0.25, 1, None), ""),
        ("skip", (0, 0.3, 0.29), "Find X"),
        ("empty", (0, 0.29, None), None),
        ("malformed", (False, 1, None), None),
    ]:
        args = {
            "text": "Content",
            **({"purpose": purpose} if purpose is not None else {}),
        }
        answers = {
            key: probability(value)
            for key, value in zip(
                ("injection", "substance", "relevance"), values
            )
            if value is not None
        }
        add("screen_" + name, "screen", args, answers)
    add(
        "screen_missing_relevance",
        "screen",
        {"text": "Content", "purpose": "Find X"},
        {"injection": probability(0), "substance": probability(1)},
    )

    add(
        "noul_boundaries",
        "noul",
        {
            "propositions": ["A", "B", "C"],
            "auto_accept": 0.9,
            "context": "한국어",
        },
        {
            f"p_proposition{index}": probability(value)
            for index, value in enumerate([0.9, 0.1, 0.5])
        },
    )
    add(
        "noul_missing",
        "noul",
        {"propositions": ["A", "B"]},
        {"p_proposition0": probability(1)},
    )
    add(
        "noul_context_ids",
        "noul",
        {
            "propositions": ["A"],
            "context": [
                {"id": "same?", "text": "A"},
                {"id": "same?", "text": "B"},
            ],
        },
        {"p_proposition0": probability(0)},
    )
    add(
        "noul_empty_context",
        "noul",
        {"propositions": ["A"], "context": ""},
        {"p_proposition0": probability(1)},
    )
    add("noul_blank", "noul", {"propositions": ["\ufeff\u2029 \t"]}, {})
    add(
        "noul_non_js_whitespace",
        "noul",
        {"propositions": ["\u0085"]},
        {"p_proposition0": probability(1)},
    )
    add(
        "noul_budget",
        "noul",
        {"propositions": ["A"], "context": "😀" * 75000},
        {},
    )
    add(
        "noul_budget_boundary",
        "noul",
        {"propositions": ["A"], "context": {"text": "x" * 149999}},
        {"p_proposition0": probability(0.5)},
    )

    candidates = [
        {"id": "same?", "text": "x" * 1999 + "😀"},
        {"id": "same!", "text": "B"},
    ]
    for name, exists in [("rounding", 0.7), ("partial", 0.35), ("absent", 0)]:
        add(
            "find_" + name,
            "find",
            {"query": "Which?", "candidates": candidates},
            {
                "best": {
                    "choice": "same",
                    "probabilities": {"same": 0.96875, "same_1": 0.03125},
                },
                "exists": probability(exists),
            },
        )
    add(
        "find_tie",
        "find",
        {
            "query": "Which?",
            "candidates": [{"id": "10", "text": "A"}, {"id": "2", "text": "B"}],
            "top_k": 1,
        },
        {
            "best": {"choice": "2", "probabilities": {"10": 0.5, "2": 0.5}},
            "exists": probability(1),
        },
    )
    add(
        "find_missing",
        "find",
        {"query": "Which?", "candidates": [{"text": "A"}]},
        {"exists": probability(0)},
    )

    classify_args = {
        "items": [
            {"id": "한글/1", "text": "x" * 1999 + "😀"},
            {"id": "", "text": "B"},
            {"text": "C"},
        ],
        "classes": [
            {"id": "10", "description": "A"},
            {"id": "2", "description": "B"},
        ],
        "purpose": "",
        "context": {"catalog": ["A", "B"]},
    }
    add(
        "classify_mixed",
        "classify",
        classify_args,
        {
            "i0": pick("c0", ["c0", "c1"], None),
            "i1": {
                "choice": "c1",
                "probabilities": {"c0": 0.5, "c1": 0.5},
                "confidence": True,
            },
            "i2": {"choice": "c0", "probabilities": {"c0": 0.4, "c1": 0.6}},
        },
    )
    add(
        "classify_duplicate_item",
        "classify",
        {
            **classify_args,
            "items": [{"id": "", "text": "A"}, {"id": "", "text": "B"}],
        },
        {},
    )
    add(
        "classify_duplicate_class",
        "classify",
        {
            **classify_args,
            "classes": [
                {"id": "x", "description": "A"},
                {"id": "x", "description": "B"},
            ],
        },
        {},
    )
    add(
        "classify_default_collision",
        "classify",
        {
            "items": [{"text": "A"}, {"id": "item0", "text": "B"}],
            "classes": [
                {"description": "A"},
                {"id": "class0", "description": "B"},
            ],
        },
        {"i0": pick("c0", ["c0", "c1"]), "i1": pick("c1", ["c0", "c1"])},
    )
    add(
        "classify_budget",
        "classify",
        {
            "items": [{"text": "A"}] * 33,
            "classes": [{"description": "B"}] * 250,
        },
        {},
    )
    for name in (
        "__proto__",
        "constructor",
        "toString",
        "valueOf",
        "__defineGetter__",
        "__defineSetter__",
        "hasOwnProperty",
        "__lookupGetter__",
        "__lookupSetter__",
        "isPrototypeOf",
        "propertyIsEnumerable",
        "toLocaleString",
    ):
        add(
            "classify_" + name,
            "classify",
            {
                "items": [{"text": "A"}],
                "classes": [
                    {"id": name, "description": "A"},
                    {"id": "other", "description": "B"},
                ],
            },
            {"i0": pick("c0", ["c0", "c1"])},
        )

    decide_args = {
        "decision": "Choose",
        "evidence": "Facts",
        "priorities": "Small",
        "candidates": [
            {"id": "constructor", "description": "A"},
            {"id": "b", "description": "B"},
        ],
    }
    rec_keys = ["option_0", "option_1", "ask_user", "investigate", "none"]
    check_keys = ["supported", "contradicted", "unknown"]
    add(
        "decide_checks",
        "decide",
        {**decide_args, "requirements": ["R1", "R2"]},
        {
            "recommendation": pick("option_0", rec_keys),
            **{
                f"check_{i}_{j}": pick(
                    "contradicted" if i == 0 else "unknown", check_keys
                )
                for i in range(2)
                for j in range(2)
            },
        },
    )
    add(
        "decide_escaped",
        "decide",
        decide_args,
        {"recommendation": pick("ask_user", rec_keys, None)},
    )
    add("decide_missing", "decide", {**decide_args, "requirements": ["R"]}, {})
    add(
        "decide_without_hatches",
        "decide",
        {
            **decide_args,
            "escape_hatches": False,
            "candidates": [
                {"id": "ask_user", "description": "A"},
                {"id": "b", "description": "B"},
            ],
        },
        {"recommendation": pick("option_0", ["option_0", "option_1"])},
    )
    add(
        "decide_duplicate",
        "decide",
        {**decide_args, "candidates": [{"id": "a", "description": "A"}] * 2},
        {},
    )
    add(
        "decide_collision",
        "decide",
        {
            **decide_args,
            "candidates": [
                {"id": "none", "description": "A"},
                {"id": "b", "description": "B"},
            ],
        },
        {},
    )
    return cases


def run_case(case):
    module = importlib.import_module("backfire.tools." + case["module"])
    response = {
        "model": "scripted-model",
        "answers": case["answers"],
        "usage": {"input_tokens": 42, "output_tokens": 7},
    }
    judge = ScriptedJudge([response])
    arguments = deepcopy(case["arguments"])
    try:
        result_text, is_error = asyncio.run(
            module.call(
                arguments,
                judge,
                deadline=12345.5,
                record_file=Path("session.jsonl"),
            )
        )
    except ValueError as error:
        result_text, is_error = str(error), True
    assert arguments == case["arguments"]
    assert not judge.requests or len(judge.requests) == 1
    for request in judge.requests:
        assert request["deadline"] == 12345.5
        assert request["record_file"] == Path("session.jsonl")
    return {
        "text": result_text,
        "is_error": is_error,
        "requests": [
            {"state": request["state"], "questions": request["questions"]}
            for request in judge.requests
        ],
    }


@pytest.mark.parametrize(
    "module_name", ["verify", "screen", "noul", "find", "classify", "decide"]
)
def test_judgment_failures_and_cancellation_propagate(module_name):
    case = next(
        case for case in fidelity_cases() if case["module"] == module_name
    )
    module = importlib.import_module("backfire.tools." + module_name)

    async def fail(*args, **kwargs):
        del args, kwargs  # Unused.
        raise RuntimeError("malformed_output: fixed error")

    async def cancel(*args, **kwargs):
        del args, kwargs  # Unused.
        raise asyncio.CancelledError()

    with pytest.raises(RuntimeError, match="^malformed_output: fixed error$"):
        asyncio.run(
            module.call(
                case["arguments"], fail, deadline=12345.5, record_file=None
            )
        )
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(
            module.call(
                case["arguments"], cancel, deadline=12345.5, record_file=None
            )
        )


@pytest.mark.parametrize(
    "module_name", ["verify", "screen", "noul", "find", "classify", "decide"]
)
def test_non_object_answers_follow_the_invalid_response_path(module_name):
    case = next(
        case for case in fidelity_cases() if case["module"] == module_name
    )
    baseline = run_case({**case, "answers": {}})
    for answers in (None, [], False, "invalid"):
        assert run_case({**case, "answers": answers}) == baseline


# SHA-256 of exact result text, error flag and ordered judgment requests from
# the pinned Node build, captured on 2026-09-27 against a local scripted
# endpoint.
# Recorded difference 5 replaces prototype-name artifacts with integer class
# counts.
UPSTREAM_CASE_DIGESTS = {
    "verify_verdicts": (
        "0ad8aa58a1121195d4d1ad7c3a0ae20f03e1bb080840978822049c90a24c350a"
    ),
    "verify_sources": (
        "799a44088d07b4cf8b08643425f9bc2ad57ea7b83c696c62299de0aee1fcb33c"
    ),
    "verify_missing_source": (
        "9ec79125885d4c892bdb0d9c6e87c530504e8816244f3076e35d869083f6a634"
    ),
    "verify_invalid_source": (
        "3ae346b8db6d8d1f4257f64d8f3fc87890fcdae9d0fbc8ad949d39037a993447"
    ),
    "verify_missing": (
        "dbbbc553cb9a19d763f457c9d62847364d0413f85a7d3b794ac5a37465fb5120"
    ),
    "screen_pass": (
        "ee949e37b2a276d1609c0b6c6ca914fa0c4ac8ac860d5a982235123e607d199e"
    ),
    "screen_block": (
        "28165b5247bb899f147c11524a121d3ee0b2c4785ab978b8cc19382ca50a1c0e"
    ),
    "screen_review": (
        "b532462dce22a758df964a88ff2c812c92536c0f341ae6100a4a88b0d085d1ba"
    ),
    "screen_skip": (
        "a2f37681ceea244179016378ee9f98c3446f52301b4b48d5b46e2bfea4d3697a"
    ),
    "screen_empty": (
        "83dd82aaa84b97f135a9bbb97fb69dbe6e9bc70320df76bfb6d6683672a4d733"
    ),
    "screen_malformed": (
        "b865f2778548b1b3ca43124128c4cc494f56838eb774c3d18ac2b9d87e78a51f"
    ),
    "screen_missing_relevance": (
        "fef6fedea2cb5d9a1a4b2defad45c1a07dc60adbcc4f206eefb7e3df8199ab55"
    ),
    "noul_boundaries": (
        "bc808516e66c874fbaffc6c4a3483a95419778490a3bdad28e9189009b9178df"
    ),
    "noul_missing": (
        "7a3164667f4d792d940b364e777efb699bd2a1bb807da76f2417638fe4092e4a"
    ),
    "noul_context_ids": (
        "11ee1a7390c57aef7658d64e73bb1b45e5dd20ea1373e92026c81791d94b1d2e"
    ),
    "noul_empty_context": (
        "259cd698e1828a610a97604a04e39d76c14e1cf5703950de43cc9fecb6be526d"
    ),
    "noul_blank": (
        "7c6cdfc153721ac92c0612dcf86962d7f35675fad30d72da2e5dd1275650a53e"
    ),
    "noul_non_js_whitespace": (
        "95e7d62fef284ae664769a305cd83c86279fb6dd16c919c59401e9c26427e6c5"
    ),
    "noul_budget": (
        "6c4ad12ffcbff66c018de4b5ba97ba027746c3b0d2e90e4b85d4c7039c57354a"
    ),
    "noul_budget_boundary": (
        "b94e31a2868a2424541d5d1e343e33cece1595ccd1a3e02c4566cfe90aadc739"
    ),
    "find_rounding": (
        "03f1ffc59e4bc7d187bdce9f1414fe8dc5a686d418c78ed189372fc44aedc3ea"
    ),
    "find_partial": (
        "d19f10c0864e4979ab1d98597ce5baf0930e5bfd37386dc8d69390505cccb28a"
    ),
    "find_absent": (
        "14f7aaa2e603d8cc760af3f9eba9668163e474542723cd4205be67ea1490485e"
    ),
    "find_tie": (
        "b7ad3debf0e9d0c2aca7de9dd6a42dfaa16fe86b97ed46d434066b04fc13c493"
    ),
    "find_missing": (
        "988421bae4e31f7298a6c738c53f82a6110a9767eb60af5122c4518c0d9f783c"
    ),
    "classify_mixed": (
        "e98140409f0f51582e7e648ae6d2a55092bb32f8d64782a0c0caf8575484f62e"
    ),
    "classify_duplicate_item": (
        "9fd5604fdc23581ed8fc41194346efb98b73187a049854faa8b207551be53d9a"
    ),
    "classify_duplicate_class": (
        "65a40a1a48f012f14bd9f8b90b4dae3e7ca4d4ebe1426dc52597b27e4f4664bb"
    ),
    "classify_default_collision": (
        "7b27d1e852f304bde36d77610ae45484898439051f65dd2ea265bfb46822d21e"
    ),
    "classify_budget": (
        "9f5487df496fdd1ad9907589ab4591d6940115142b1ef251d7bfb305f47f1a61"
    ),
    "classify___proto__": (
        "cc285ec19fe6f700e36fde12a4f485c64f2767408b32f342ab755bbeb12053b8"
    ),
    "classify_constructor": (
        "f2b2e968e117d05206ec2a1b06c2bf13047366e63fea807199f93e930aa8c2c9"
    ),
    "classify_toString": (
        "4364f31dfbe970c031a3df52c0291ecb8aeea958defdd5b45a39af7fef033762"
    ),
    "classify_valueOf": (
        "3380b5c7f14e5d8bc59dbe07d2bb5d1544807377bb4c8af9836ffefa9a2a8128"
    ),
    "classify___defineGetter__": (
        "82e6225cd3400940029b61b34c8ca0ea76943d88e90da1fa48f0def3a78f1ba7"
    ),
    "classify___defineSetter__": (
        "ff690be92197751ff92adbbd01aa733e99bc062f43b0d1cacababf6453f6d9d0"
    ),
    "classify_hasOwnProperty": (
        "a7c3445dc658529dcab94d0b4a1cbc5eedb32cea5389a64439cd9c2e65972d4b"
    ),
    "classify___lookupGetter__": (
        "b63d552fe8a95e2aab6376afab338d12fd7076f08e411bef84e1760f8c223a82"
    ),
    "classify___lookupSetter__": (
        "a633e32a6a78d7c6387427851ce3d66a263eef36e5c3b2288f95b6f39313287b"
    ),
    "classify_isPrototypeOf": (
        "201a2bb0e72895c74977da792bd719f0e3cbf569e93da7440ea9a12aca95be2c"
    ),
    "classify_propertyIsEnumerable": (
        "46ab5e8f22c89abfd05ecaf62d421a52d0b7f11ff9580b8a9c594fb485bf25b1"
    ),
    "classify_toLocaleString": (
        "09bcfde85033f19ba5dc696f61332c4f5ae69e2fbf89a0a5aad6a965c06ee1b8"
    ),
    "decide_checks": (
        "0ee73b7bb225cc48456e5f5823c0de857b50db9a75b4c75fb2ad189dc8cc5148"
    ),
    "decide_escaped": (
        "47a892d90420066deb7fab61b12bb9196bf8c80f57d66b03ba285892ef199aea"
    ),
    "decide_missing": (
        "1dcc3140858fa2d56bd16f4866441b78db2f1489013ce5fad13abd497703d85b"
    ),
    "decide_without_hatches": (
        "966ce252223bc8800d3a280874b6cc43ef2471796b614732f9fd13d9fe643cae"
    ),
    "decide_duplicate": (
        "3b93bdede90048c4cecc5d2dda289bbeb8cf20955700cbf05ca4df1b9c77f31d"
    ),
    "decide_collision": (
        "4e5a1273af3c65ec9aa1cb85807bfc027de8df6995c14f414f726397705f4541"
    ),
}


@pytest.mark.parametrize("case", fidelity_cases(), ids=lambda case: case["id"])
def test_handlers_match_upstream_capture(case):
    actual = run_case(case)
    assert digest(actual) == UPSTREAM_CASE_DIGESTS[case["id"]], actual


@pytest.mark.parametrize("name", ["__proto__", "constructor", "toString"])
def test_classify_prototype_names_count_normally(name):
    # Recorded difference 5: each supplied class ID is an ordinary dictionary
    # key.
    case = next(
        case for case in fidelity_cases() if case["id"] == "classify_" + name
    )
    assert json.loads(run_case(case)["text"])["summary"]["by_class"] == {
        name: 1
    }
