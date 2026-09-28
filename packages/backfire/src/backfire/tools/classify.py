"""Port of jev-mcp 0.9.0 classify; see ../UPSTREAM.md."""

from backfire.lib import MAX_ITEM_CHARS
from backfire.lib import classification_decision
from backfire.lib import margin_of
from backfire.lib import truncate
from backfire.tools import text
from backfire.tools.answers import PROVIDER
from backfire.tools.answers import validate_choice_answer

NAME = "backfire_classify"

TITLE = "Classify items against a shared label set"

DESCRIPTION = (
    "Assign each item to one class from a shared catalog with TypeSafe "
    "Jev, in one batched request: "
    "the class catalog is sent once and every item becomes an independent "
    "Choice question. Returns "
    "per item: the chosen class, the full distribution, confidence, "
    "winner-to-runner-up margin, and "
    "an auto-versus-review decision. Auto requires both a high top "
    "probability (default 0.85) and a "
    "clear margin (default 0.50); everything else is flagged for review. "
    "Include a manual_review "
    "class in the catalog if you want an explicit escape hatch; the tool "
    "never invents "
    "one."
)

INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "items": {
            "minItems": 1,
            "maxItems": 64,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["text"],
                "additionalProperties": False,
            },
            "description": (
                "Items to classify. Text is truncated at 2000 characters; send "
                "bounded excerpts, not whole "
                "documents."
            ),
        },
        "classes": {
            "minItems": 2,
            "maxItems": 250,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["description"],
                "additionalProperties": False,
            },
            "description": (
                "Shared class catalog. Strong descriptions carry the decision: "
                "a precise definition, what belongs, what does not, precedence "
                "over overlapping classes, and a short "
                "example."
            ),
        },
        "purpose": {
            "description": "What this classification is for; shared across all "
            "items.",
            "type": "string",
        },
        "context": {
            "description": "Shared context available to every item's judgment: "
            "policies, catalogs, anything stable.",
            "anyOf": [
                {"type": "string"},
                {
                    "type": "object",
                    "propertyNames": {"type": "string"},
                    "additionalProperties": {},
                },
            ],
        },
        "auto_accept": {
            "description": "Minimum top probability for auto. Default 0.85.",
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "minimum_margin": {
            "description": "Minimum winner-to-runner-up gap for auto. "
            "Default 0.5.",
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["items", "classes"],
    "additionalProperties": False,
}

EXECUTION = {"taskSupport": "forbidden"}


async def call(arguments, judge, *, deadline, record_file):
    """Classify items against shared classes in one judgment request."""
    auto_accept = arguments.get("auto_accept", 0.85)
    minimum_margin = arguments.get("minimum_margin", 0.5)
    items, classes = [], []
    for raw, output, prefix, field, key_prefix in (
        (arguments["items"], items, "item", "text", "i"),
        (arguments["classes"], classes, "class", "description", "c"),
    ):
        seen = set()
        for index, item in enumerate(raw):
            external = item.get("id", f"{prefix}{index}")
            if "id" in item:
                if item["id"] in seen:
                    raise ValueError(f"Duplicate {prefix} id: {item['id']}")
                seen.add(item["id"])
            output.append(
                {
                    "external": external,
                    "key": f"{key_prefix}{index}",
                    field: truncate(item[field], MAX_ITEM_CHARS),
                }
            )
    if len(items) * len(classes) > 8000:
        raise ValueError(
            f"Batch too large: {len(items)} items x {len(classes)} classes "
            "exceeds the 8,000 item-class budget. Split the batch."
        )
    state = {
        "purpose": arguments.get(
            "purpose", "Assign each item to exactly one class."
        ),
        "context": arguments.get("context"),
        "classes": [
            {"id": item["key"], "description": item["description"]}
            for item in classes
        ],
    }
    criteria = {item["key"]: None for item in classes}
    questions = {
        item["key"]: {
            "type": "choice",
            "instructions": {
                "task": "Which class does this item belong to?",
                "item": {"id": item["key"], "text": item["text"]},
            },
            "criteria": criteria,
        }
        for item in items
    }
    result = await judge(
        state, questions, deadline=deadline, record_file=record_file
    )
    answers = (
        result["answers"] if isinstance(result.get("answers"), dict) else {}
    )
    key_to_external = {item["key"]: item["external"] for item in classes}
    rows = []
    for item in items:
        answer = validate_choice_answer(answers.get(item["key"]), criteria)
        if answer is None:
            rows.append(
                {
                    "id": item["external"],
                    "status": "invalid_response",
                    "classification": None,
                    "probabilities": None,
                    "confidence": None,
                    "margin": None,
                    "decision": "review",
                }
            )
            continue
        margin = margin_of(answer["probabilities"])
        top = answer["probabilities"][answer["choice"]]
        rows.append(
            {
                "id": item["external"],
                "classification": key_to_external[answer["choice"]],
                "probabilities": {
                    label["external"]: answer["probabilities"][label["key"]]
                    for label in classes
                },
                "confidence": answer["confidence"],
                "margin": margin,
                "top_probability": top,
                "decision": classification_decision(
                    top, margin, auto_accept, minimum_margin
                ),
            }
        )
    by_class = {}
    for row in rows:
        label = row["classification"]
        if label is not None:
            by_class[label] = by_class.get(label, 0) + 1
    return text(
        {
            "tool": NAME,
            "model": result["model"],
            "provider": PROVIDER,
            "summary": {
                "items": len(rows),
                "auto": sum(row["decision"] == "auto" for row in rows),
                "review": sum(
                    row["decision"] == "review"
                    and row.get("status") != "invalid_response"
                    for row in rows
                ),
                "invalid_response": sum(
                    row.get("status") == "invalid_response" for row in rows
                ),
                "by_class": by_class,
            },
            "thresholds": {
                "auto_accept": auto_accept,
                "minimum_margin": minimum_margin,
            },
            "results": rows,
            "usage": result["usage"],
        }
    ), False
