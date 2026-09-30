"""Backfire's retained Noul tool on PyModel's framework.

The definition, questions and decision logic come from jev-mcp 0.9.0
(src/index.ts at a1fcc1e47fc696614f081e23a66ff48a890f22fd, MIT, Copyright (c)
2026 Joey Kudish; see licenses/third-party-notices.md).
"""

from typing import cast

from jev_judge_mcp.domain import NoulCriteria
from jev_judge_mcp.domain import NoulQuestion
from jev_judge_mcp.domain import Question
from jev_judge_mcp.ids import ensure_unique_ids
from jev_judge_mcp.text import length
from jev_judge_mcp.tools.arguments import Refinement
from jev_judge_mcp.tools.base import JevTool
from jev_judge_mcp.tools.base import Runtime
from jev_judge_mcp.tools.base import ToolResult
from jev_judge_mcp.tools.base import define
from jev_judge_mcp.tools.base import frame
from jev_judge_mcp.tools.common import has_non_empty_evidence
from jev_judge_mcp.validation import validate_noul

NAME = "jev_noul"
TITLE = "Calibrated probability for propositions"
DESCRIPTION = (
    "Return a calibrated probability for each stated proposition with TypeSafe Jev, in one batched "  # noqa: E501 - published tool text
    "request: high means likely, low means unlikely, middling means genuinely uncertain. Supplied "  # noqa: E501 - published tool text
    "context informs the judgment but is not a proof guarantee; to test claims strictly against "  # noqa: E501 - published tool text
    "evidence, including whether the evidence is merely silent, use jev_verify instead."  # noqa: E501 - published tool text
)
MAX_NOUL_TOTAL_CHARS = 150_000
_EVIDENCE = {
    "properties": {
        "id": {
            "description": "Short identifier for this evidence item.",
            "type": "string",
        },
        "text": {"description": "The evidence text.", "type": "string"},
    },
    "required": ["text"],
    "additionalProperties": False,
}
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "propositions": {
            "minItems": 1,
            "maxItems": 64,
            "type": "array",
            "items": {"type": "string", "minLength": 1, "maxLength": 2000},
            "description": "Propositions to judge, each a single testable statement. Up to 64 per call, 2000 chars each.",  # noqa: E501 - published tool text
        },
        "context": {
            "description": "Optional context the propositions are judged against: one document or evidence items. When omitted, the model's own knowledge applies.",  # noqa: E501 - published tool text
            "anyOf": [
                {
                    "type": "string",
                    "description": "A single evidence document.",
                },
                {
                    "type": "object",
                    "description": "A single evidence item.",
                    "properties": _EVIDENCE["properties"],
                    "required": ["text"],
                    "additionalProperties": False,
                },
                {
                    "minItems": 1,
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "description": "Short identifier for this evidence item (e.g. 'site-html', 'rfc-4.1.3').",  # noqa: E501 - published tool text
                                "type": "string",
                            },
                            "text": {
                                "description": "The evidence text.",
                                "type": "string",
                            },
                        },
                        "required": ["text"],
                        "additionalProperties": False,
                    },
                    "description": "Multiple evidence items; each claim is also matched to the item it rests on.",  # noqa: E501 - published tool text
                },
            ],
        },
        "auto_accept": {
            "description": "Decisiveness threshold: probability at or above this marks the proposition likely, at or below (1 - this) unlikely, between them uncertain. Must exceed 0.5. Default 0.85.",  # noqa: E501 - published tool text
            "type": "number",
            "maximum": 1,
        },
    },
    "required": ["propositions"],
    "additionalProperties": False,
}


def _nonblank(value: object) -> bool:
    return isinstance(value, list) and all(
        has_non_empty_evidence([{"text": text}])
        for text in cast(list[str], value)
    )


def _over_half(value: object) -> bool:
    return type(value) in (int, float) and value > 0.5


async def _handle(arguments: dict[str, object], runtime: Runtime) -> ToolResult:
    propositions = ensure_unique_ids(
        [{"text": text} for text in cast(list[str], arguments["propositions"])],
        "proposition",
    ).items
    raw_context = arguments.get("context")
    context = (
        [{"id": "context", "text": raw_context}]
        if isinstance(raw_context, str)
        else cast(list[dict[str, object]], raw_context)
        if isinstance(raw_context, list)
        else [cast(dict[str, object], raw_context)]
        if raw_context is not None
        else []
    )
    total_chars = sum(
        length(cast(str, item["text"])) for item in propositions + context
    )
    if total_chars > MAX_NOUL_TOTAL_CHARS:
        raise ValueError(
            f"Batch too large: {total_chars} proposition and context "
            f"characters exceeds the {MAX_NOUL_TOTAL_CHARS} character "
            "budget. Split the batch."
        )
    questions: dict[str, Question] = {
        f"p_{item['id']}": NoulQuestion(
            f"proposition `{item['id']}`: {item['text']}",
            NoulCriteria(
                "The proposition is likely true, given the supplied context (when present) and general knowledge",  # noqa: E501 - published question text
                "The proposition is likely not true",
            ),
        )
        for item in propositions
    }
    evaluation = await runtime.ask(
        {"propositions": propositions, "context": context or None}, questions
    )
    auto_accept = cast(float, arguments.get("auto_accept", 0.85))
    probabilities = [
        validate_noul(evaluation.answers.get(f"p_{item['id']}"))
        for item in propositions
    ]
    invalid = [
        item["id"]
        for item, probability in zip(propositions, probabilities, strict=True)
        if probability is None
    ]
    rows = [
        {
            "id": item["id"],
            "proposition": item["text"],
            "probability": probability,
            "label": None
            if invalid
            else "likely"
            if probability >= auto_accept
            else "unlikely"
            if probability + auto_accept <= 1
            else "uncertain",
            "auto": not invalid
            and (
                "likely"
                if probability >= auto_accept
                else "unlikely"
                if probability + auto_accept <= 1
                else "uncertain"
            )
            != "uncertain",
        }
        for item, probability in zip(propositions, probabilities, strict=True)
    ]
    return ToolResult(
        frame(
            NAME,
            evaluation,
            {
                "status": "invalid_response" if invalid else "ok",
                "results": rows,
                **({"invalid": invalid} if invalid else {}),
                "thresholds": {"auto_accept": auto_accept},
            },
        )
    )


NOUL = JevTool(
    define(NAME, TITLE, DESCRIPTION, INPUT_SCHEMA),
    _handle,
    {
        "propositions": Refinement(_nonblank, "propositions must not be blank"),
        "auto_accept": Refinement(_over_half, "auto_accept must exceed 0.5"),
    },
)
