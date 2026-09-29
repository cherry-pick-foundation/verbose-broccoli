"""Project parsed results onto the fixed decision vocabulary."""

_FIELDS = {
    "backfire_gate": {
        "action": ("auto", "review", "escalate"),
        "truncated": (True, False),
    },
    "backfire_review": {
        "action": ("auto", "review", "escalate"),
        "truncated": (True, False),
    },
    "backfire_verify": {
        "verdict": ("verified", "contradicted", "unsupported", "unknown"),
        "action": ("auto", "review"),
    },
    "backfire_screen": {"action": ("pass", "review", "block", "skip")},
    "backfire_noul": {
        "label": ("likely", "unlikely", "uncertain", None),
        "auto": (True, False),
    },
    "backfire_extract": {
        "status": (
            "auto",
            "review",
            "not_found",
            "invalid_pattern",
            "invalid_response",
        )
    },
    "backfire_compare": {
        "relation": ("same_fact", "contradicts", "different_facts", None),
        "decision": ("auto", "review"),
    },
    "backfire_classify": {"decision": ("auto", "review")},
    "backfire_decide": {"escaped": (True, False, None)},
    "backfire_find": {
        "exists_verdict": ("answered", "partial", "absent", None)
    },
    "backfire_rerank": {},
}
_MISSING = object()


def _value(value, vocabulary):
    # Equality alone would admit 0 and 1 as booleans.
    return next(
        (
            allowed
            for allowed in vocabulary
            if type(value) is type(allowed) and value == allowed
        ),
        "other",
    )


def decision_units(
    tool: str, result: object
) -> list[dict[str, str | bool | None]] | None:
    """Keep unit order and read only fixed fields, never caller ids or text.

    The caller parses the tool's JSON text. Unknown tools, non-object results
    and malformed unit containers have no parsable decisions and return None.
    Missing fields become other; absent optional status stays absent.
    """
    fields = _FIELDS.get(tool)
    if fields is None or not isinstance(result, dict):
        return None
    if tool in (
        "backfire_gate",
        "backfire_review",
        "backfire_find",
        "backfire_rerank",
    ):
        rows = [result]
    elif tool in ("backfire_screen", "backfire_decide"):
        rows = [result.get("recommendation")]
    elif tool == "backfire_compare":
        aspects = result.get("aspects", [])
        if not isinstance(aspects, list):
            return None
        rows = [result.get("overall"), *aspects]
    else:
        rows = result.get("results")
    if not isinstance(rows, list) or not all(
        isinstance(row, dict) for row in rows
    ):
        return None

    units = []
    for row in rows:
        unit = {
            field: _value(row.get(field, _MISSING), vocabulary)
            for field, vocabulary in fields.items()
        }
        if "status" not in fields:
            status = row.get("status", result.get("status", _MISSING))
            if status is not _MISSING:
                unit["status"] = _value(status, ("ok", "invalid_response"))
        units.append(unit)
    return units
