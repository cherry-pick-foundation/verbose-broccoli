from copy import deepcopy

import pytest

from backfire.decisions import decision_units


CASES = [
    (
        "backfire_gate",
        {
            "action": "review",
            "truncated": True,
            "verification": {
                "results": [{"claim": "private", "action": "escalate"}]
            },
        },
        [{"action": "review", "truncated": True}],
    ),
    (
        "backfire_review",
        {
            "action": "escalate",
            "truncated": False,
            "status": "invalid_response",
            "scores": {"correctness": {"score": None}},
        },
        [
            {
                "action": "escalate",
                "truncated": False,
                "status": "invalid_response",
            }
        ],
    ),
    (
        "backfire_verify",
        {
            "results": [
                {
                    "id": "private-id",
                    "claim": "private",
                    "verdict": "verified",
                    "action": "auto",
                },
                {"verdict": "contradicted", "action": "review"},
                {"verdict": "unsupported", "action": "auto"},
                {
                    "verdict": "unknown",
                    "action": "review",
                    "status": "invalid_response",
                },
            ]
        },
        [
            {"verdict": "verified", "action": "auto"},
            {"verdict": "contradicted", "action": "review"},
            {"verdict": "unsupported", "action": "auto"},
            {
                "verdict": "unknown",
                "action": "review",
                "status": "invalid_response",
            },
        ],
    ),
    (
        "backfire_screen",
        {
            "status": "invalid_response",
            "recommendation": {"action": "review", "reason": "private"},
        },
        [{"action": "review", "status": "invalid_response"}],
    ),
    (
        "backfire_noul",
        {
            "status": "ok",
            "results": [
                {
                    "id": "private-id",
                    "proposition": "private",
                    "label": "likely",
                    "auto": True,
                },
                {"label": "unlikely", "auto": True},
                {"label": "uncertain", "auto": False},
            ],
        },
        [
            {"label": "likely", "auto": True, "status": "ok"},
            {"label": "unlikely", "auto": True, "status": "ok"},
            {"label": "uncertain", "auto": False, "status": "ok"},
        ],
    ),
    (
        "backfire_extract",
        {
            "results": [
                {"id": "private-id", "value": "private", "status": "auto"},
                {"status": "review"},
                {"status": "not_found"},
                {"status": "invalid_pattern", "reason": "private"},
                {"status": "invalid_response"},
            ]
        },
        [
            {"status": "auto"},
            {"status": "review"},
            {"status": "not_found"},
            {"status": "invalid_pattern"},
            {"status": "invalid_response"},
        ],
    ),
    (
        "backfire_compare",
        {
            "overall": {"relation": "same_fact", "decision": "auto"},
            "aspects": [
                {
                    "aspect": "private",
                    "relation": "contradicts",
                    "decision": "review",
                },
                {"relation": "different_facts", "decision": "auto"},
                {
                    "relation": None,
                    "decision": "review",
                    "status": "invalid_response",
                },
            ],
        },
        [
            {"relation": "same_fact", "decision": "auto"},
            {"relation": "contradicts", "decision": "review"},
            {"relation": "different_facts", "decision": "auto"},
            {
                "relation": None,
                "decision": "review",
                "status": "invalid_response",
            },
        ],
    ),
    (
        "backfire_classify",
        {
            "results": [
                {
                    "id": "private-id",
                    "classification": "private",
                    "decision": "auto",
                },
                {"decision": "review", "status": "invalid_response"},
            ],
            "summary": {"by_class": {"private": 1}},
        },
        [
            {"decision": "auto"},
            {"decision": "review", "status": "invalid_response"},
        ],
    ),
    (
        "backfire_decide",
        {
            "recommendation": {
                "selected": "private",
                "escaped": False,
                "confidence": 0,
                "probabilities": {"private": 0.5},
            },
            "warnings": ["private"],
            "checks": [{"candidate": "private"}],
        },
        [{"escaped": False}],
    ),
    (
        "backfire_find",
        {
            "exists_verdict": "answered",
            "query": "private",
            "top": [{"id": "private-id", "text": "private"}],
        },
        [{"exists_verdict": "answered"}],
    ),
    (
        "backfire_rerank",
        {"ranked": [{"id": "private-id", "text": "private"}]},
        [{}],
    ),
]


class ReadGuard(dict):
    """Fail on a forbidden field read, even if its value would be discarded."""

    def __getitem__(self, key):
        assert key in {
            "action",
            "truncated",
            "status",
            "results",
            "recommendation",
            "overall",
            "aspects",
            "verdict",
            "label",
            "auto",
            "relation",
            "decision",
            "escaped",
            "exists_verdict",
        }, key
        return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self):
        raise AssertionError("Do not enumerate a tool result")

    items = values = __iter__


def guard(value):
    if isinstance(value, dict):
        return ReadGuard({key: guard(item) for key, item in value.items()})
    if isinstance(value, list):
        return [guard(item) for item in value]
    return value


@pytest.mark.parametrize(
    "tool,result,expected", CASES, ids=[case[0] for case in CASES]
)
def test_each_tool_keeps_only_fixed_decisions_without_reading_caller_fields(
    tool, result, expected
):
    original = deepcopy(result)
    protected = guard(
        {
            **result,
            "tool": "private",
            "model": "private",
            "usage": {"private": 1},
        }
    )
    assert decision_units(tool, protected) == expected
    assert protected == {
        **original,
        "tool": "private",
        "model": "private",
        "usage": {"private": 1},
    }


@pytest.mark.parametrize(
    "tool,result,expected",
    [
        (
            "backfire_gate",
            {"action": "auto", "truncated": False},
            [{"action": "auto", "truncated": False}],
        ),
        (
            "backfire_screen",
            {"recommendation": {"action": "pass"}},
            [{"action": "pass"}],
        ),
        (
            "backfire_screen",
            {"recommendation": {"action": "block"}},
            [{"action": "block"}],
        ),
        (
            "backfire_screen",
            {"recommendation": {"action": "skip"}},
            [{"action": "skip"}],
        ),
        (
            "backfire_noul",
            {
                "status": "invalid_response",
                "results": [{"label": None, "auto": False}],
            },
            [{"label": None, "auto": False, "status": "invalid_response"}],
        ),
        (
            "backfire_compare",
            {
                "overall": {
                    "relation": None,
                    "decision": "review",
                    "status": "invalid_response",
                }
            },
            [
                {
                    "relation": None,
                    "decision": "review",
                    "status": "invalid_response",
                }
            ],
        ),
        (
            "backfire_decide",
            {"recommendation": {"escaped": True}},
            [{"escaped": True}],
        ),
        (
            "backfire_decide",
            {"recommendation": {"escaped": None, "status": "invalid_response"}},
            [{"escaped": None, "status": "invalid_response"}],
        ),
        (
            "backfire_find",
            {"exists_verdict": "partial"},
            [{"exists_verdict": "partial"}],
        ),
        (
            "backfire_find",
            {"exists_verdict": "absent"},
            [{"exists_verdict": "absent"}],
        ),
        (
            "backfire_find",
            {"exists_verdict": None, "status": "invalid_response"},
            [{"exists_verdict": None, "status": "invalid_response"}],
        ),
        (
            "backfire_rerank",
            {"status": "invalid_response"},
            [{"status": "invalid_response"}],
        ),
    ],
)
def test_nullable_values_and_reported_statuses(tool, result, expected):
    assert decision_units(tool, result) == expected


@pytest.mark.parametrize(
    "unexpected", ["private", 0, 1, 0.0, 1.0, [], {}, None, True, False]
)
@pytest.mark.parametrize(
    "tool,result,expected", CASES, ids=[case[0] for case in CASES]
)
def test_out_of_vocabulary_values_never_enter_records(
    tool, result, expected, unexpected
):
    # Replace decision values at every depth, leaving the structural containers intact.
    def replace(value):
        if isinstance(value, list):
            return [replace(item) for item in value]
        if isinstance(value, dict):
            return {
                key: unexpected if key in fields else replace(item)
                for key, item in value.items()
            }
        return value

    fields = {key for unit in expected for key in unit}
    actual = decision_units(tool, replace(result))
    assert len(actual) == len(expected)
    for unit, before in zip(actual, expected):
        for field in before:
            nullable = field in {
                "label",
                "relation",
                "escaped",
                "exists_verdict",
            }
            boolean = field in {"auto", "truncated", "escaped"}
            allowed = (unexpected is None and nullable) or (
                type(unexpected) is bool and boolean
            )
            assert unit[field] == (unexpected if allowed else "other")
            if allowed:
                assert type(unit[field]) is type(unexpected)


@pytest.mark.parametrize(
    "tool,result",
    [
        ("unknown", {"action": "auto"}),
        ("backfire_gate", None),
        ("backfire_gate", []),
        ("backfire_gate", "{}"),
        ("backfire_verify", {}),
        ("backfire_verify", {"results": {}}),
        ("backfire_verify", {"results": [{"action": "auto"}, None]}),
        ("backfire_screen", {"recommendation": "pass"}),
        ("backfire_decide", {}),
        ("backfire_compare", {"overall": {}, "aspects": None}),
        ("backfire_compare", {"overall": {}, "aspects": ["private"]}),
    ],
)
def test_unparsable_units_return_none_without_partial_decisions(tool, result):
    assert decision_units(tool, result) is None


def test_empty_units_and_missing_values_are_not_invented():
    assert decision_units("backfire_verify", {"results": []}) == []
    assert decision_units("backfire_gate", {}) == [
        {"action": "other", "truncated": "other"}
    ]
    assert decision_units("backfire_noul", {"results": [{}]}) == [
        {"label": "other", "auto": "other"}
    ]
