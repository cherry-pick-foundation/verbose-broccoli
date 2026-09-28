"""Ported from jev-mcp 0.9.0; see ../UPSTREAM.md."""

from backfire.lib import (
    ASPECT_RELATIONS,
    COMPARE_RELATIONS,
    classification_decision,
    margin_of,
    truncate,
)
from backfire.tools import text
from backfire.tools.answers import PROVIDER, validate_choice_answer

NAME = "backfire_compare"
TITLE = "Compare two passages for factual agreement"
DESCRIPTION = (
    "Judge the relation between two passages with TypeSafe Jev: same_fact, contradicts, or "
    "different_facts, with the full probability distribution, confidence, and an "
    "auto-versus-review decision. Optionally supply aspects (price, date, method, …) and each "
    "gets an independent per-aspect judgment in the same single request. Use for source "
    "reconciliation, changelog-vs-code drift, or merge sanity checks. The request supplies no "
    "evidence beyond the two passages, so a same_fact verdict means they agree with each other, "
    "not that they are true."
)
INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "passage_a": {
            "type": "string",
            "minLength": 1,
            "maxLength": 20000,
            "description": "First passage. Rejected above 20,000 characters.",
        },
        "passage_b": {
            "type": "string",
            "minLength": 1,
            "maxLength": 20000,
            "description": "Second passage. Rejected above 20,000 characters.",
        },
        "aspects": {
            "description": "Named aspects to judge independently (e.g. 'price', 'launch date'). Each tests one property.",
            "maxItems": 10,
            "type": "array",
            "items": {"type": "string", "minLength": 1, "maxLength": 200},
        },
        "purpose": {
            "description": "What this comparison is for; helps disambiguate overlap.",
            "type": "string",
        },
        "auto_accept": {
            "description": "Minimum top probability for auto. Default 0.85.",
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "minimum_margin": {
            "description": "Minimum winner-to-runner-up gap for auto. Default 0.5.",
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["passage_a", "passage_b"],
    "additionalProperties": False,
}
EXECUTION = {"taskSupport": "forbidden"}


async def call(arguments, judge, *, deadline, record_file):
    auto_accept = arguments.get("auto_accept", 0.85)
    minimum_margin = arguments.get("minimum_margin", 0.5)
    aspects = arguments.get("aspects", [])
    questions = {
        "overall": {
            "type": "choice",
            "instructions": "Do the two passages state the same underlying fact, contradict each other, or discuss different facts?",
            "criteria": dict(COMPARE_RELATIONS),
        }
    }
    for index, aspect in enumerate(aspects):
        questions[f"aspect_{index}"] = {
            "type": "choice",
            "instructions": f'Judging only the aspect "{aspect}" of the two passages in the state, which relation holds?',
            "criteria": dict(ASPECT_RELATIONS),
        }
    state = {
        "purpose": arguments.get("purpose"),
        "passage_a": truncate(arguments["passage_a"], 20000),
        "passage_b": truncate(arguments["passage_b"], 20000),
        "aspects": aspects,
    }
    judgment = await judge(
        state, questions, deadline=deadline, record_file=record_file
    )
    answers = (
        judgment["answers"] if isinstance(judgment["answers"], dict) else {}
    )

    def shape(raw):
        answer = validate_choice_answer(raw, COMPARE_RELATIONS)
        if answer is None:
            return {
                "relation": None,
                "probabilities": None,
                "confidence": None,
                "margin": None,
                "decision": "review",
                "status": "invalid_response",
            }
        margin = margin_of(answer["probabilities"])
        return {
            "relation": answer["choice"],
            "probabilities": answer["probabilities"],
            "confidence": answer["confidence"],
            "margin": margin,
            "decision": classification_decision(
                answer["probabilities"][answer["choice"]],
                margin,
                auto_accept,
                minimum_margin,
            ),
        }

    return text(
        {
            "tool": NAME,
            "model": judgment["model"],
            "provider": PROVIDER,
            "overall": shape(answers.get("overall")),
            "aspects": [
                {"aspect": aspect, **shape(answers.get(f"aspect_{index}"))}
                for index, aspect in enumerate(aspects)
            ],
            "thresholds": {
                "auto_accept": auto_accept,
                "minimum_margin": minimum_margin,
            },
            "usage": judgment["usage"],
        }
    ), False
