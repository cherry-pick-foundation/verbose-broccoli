"""Port of jev-mcp 0.9.0 noul; see ../UPSTREAM.md."""

from backfire.lib import (
    MAX_NOUL_TOTAL_CHARS,
    ensure_unique_ids,
    has_non_empty_evidence,
)
from backfire.tools import text
from backfire.tools.answers import PROVIDER, validate_noul_answer

NAME = "backfire_noul"

TITLE = "Calibrated probability for propositions"

DESCRIPTION = (
    "Return a calibrated probability for each stated proposition with TypeSafe Jev, in one batched "
    "request: high means likely, low means unlikely, middling means genuinely uncertain. Supplied "
    "context informs the judgment but is not a proof guarantee; to test claims strictly against "
    "evidence, including whether the evidence is merely silent, use backfire_verify instead."
)

INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "propositions": {
            "minItems": 1,
            "maxItems": 64,
            "type": "array",
            "items": {"type": "string", "minLength": 1, "maxLength": 2000},
            "description": "Propositions to judge, each a single testable "
            "statement. Up to 64 per call, 2000 chars each.",
        },
        "context": {
            "description": "Optional context the propositions are judged against: "
            "one document or evidence items. When omitted, the "
            "model's own knowledge applies.",
            "anyOf": [
                {
                    "type": "string",
                    "description": "A single evidence document.",
                },
                {
                    "type": "object",
                    "properties": {
                        "id": {
                            "description": "Short identifier for "
                            "this evidence item.",
                            "type": "string",
                        },
                        "text": {
                            "type": "string",
                            "description": "The evidence text.",
                        },
                    },
                    "required": ["text"],
                    "additionalProperties": False,
                    "description": "A single evidence item.",
                },
                {
                    "minItems": 1,
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "description": "Short "
                                "identifier "
                                "for this "
                                "evidence "
                                "item (e.g. "
                                "'site-html', "
                                "'rfc-4.1.3').",
                                "type": "string",
                            },
                            "text": {
                                "type": "string",
                                "description": "The evidence text.",
                            },
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                    "description": "Multiple evidence items; each claim is also "
                    "matched to the item it rests on.",
                },
            ],
        },
        "auto_accept": {
            "description": "Decisiveness threshold: probability at or above "
            "this marks the proposition likely, at or below (1 "
            "- this) unlikely, between them uncertain. Must "
            "exceed 0.5. Default 0.85.",
            "type": "number",
            "exclusiveMinimum": 0.5,
            "maximum": 1,
        },
    },
    "required": ["propositions"],
    "additionalProperties": False,
}

EXECUTION = {"taskSupport": "forbidden"}


async def call(arguments, judge, *, deadline, record_file):
    if not all(
        has_non_empty_evidence([{"text": value}])
        for value in arguments["propositions"]
    ):
        raise ValueError(
            "MCP error -32602: Input validation error: Invalid arguments for tool backfire_noul: propositions must not be blank at propositions"
        )
    auto_accept = arguments.get("auto_accept", 0.85)
    raw_context = arguments.get("context")
    context = (
        [{"id": "context", "text": raw_context}]
        if isinstance(raw_context, str)
        else raw_context
        if isinstance(raw_context, list)
        else [raw_context]
        if raw_context is not None
        else []
    )
    propositions = ensure_unique_ids(
        [{"text": value} for value in arguments["propositions"]], "proposition"
    )["items"]
    total_chars = sum(
        len(item["text"].encode("utf-16-le", "surrogatepass")) // 2
        for item in propositions + context
    )
    if total_chars > MAX_NOUL_TOTAL_CHARS:
        raise ValueError(
            f"Batch too large: {total_chars} proposition and context characters exceeds the {MAX_NOUL_TOTAL_CHARS} character budget. Split the batch."
        )
    questions = {
        f"p_{item['id']}": {
            "type": "noul",
            "instructions": f"proposition `{item['id']}`: {item['text']}",
            "criteria": {
                "true": "The proposition is likely true, given the supplied context (when present) and general knowledge",
                "false": "The proposition is likely not true",
            },
        }
        for item in propositions
    }
    result = await judge(
        {"propositions": propositions, "context": context or None},
        questions,
        deadline=deadline,
        record_file=record_file,
    )
    answers = (
        result["answers"] if isinstance(result.get("answers"), dict) else {}
    )
    rows = [
        {
            "id": item["id"],
            "proposition": item["text"],
            "probability": validate_noul_answer(answers.get(f"p_{item['id']}")),
        }
        for item in propositions
    ]
    invalid = [row["id"] for row in rows if row["probability"] is None]
    for row in rows:
        probability = row["probability"]
        label = (
            None
            if invalid
            else "likely"
            if probability >= auto_accept
            else "unlikely"
            if probability + auto_accept <= 1
            else "uncertain"
        )
        row.update(label=label, auto=not invalid and label != "uncertain")
    return text(
        {
            "tool": NAME,
            "model": result["model"],
            "provider": PROVIDER,
            "status": "invalid_response" if invalid else "ok",
            "results": rows,
            **({"invalid": invalid} if invalid else {}),
            "thresholds": {"auto_accept": auto_accept},
            "usage": result["usage"],
        }
    ), False
