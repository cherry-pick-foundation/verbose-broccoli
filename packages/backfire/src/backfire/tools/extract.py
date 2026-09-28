"""Ported from jev-mcp 0.9.0; see ../UPSTREAM.md."""

import re

from backfire import patterns
from backfire.lib import MAX_EXTRACT_TOTAL_CHARS
from backfire.lib import classification_decision
from backfire.lib import margin_of
from backfire.lib import truncate
from backfire.tools import text
from backfire.tools.answers import NO_JUDGMENT_MODEL
from backfire.tools.answers import NO_JUDGMENT_PROVIDER
from backfire.tools.answers import PROVIDER
from backfire.tools.answers import validate_choice_answer

NAME = "backfire_extract"
TITLE = "Extract fields by regex, Jev picks the right match"
DESCRIPTION = (
    "Extract structured fields from a document with TypeSafe Jev as the "
    "picker, not the "
    "generator: your regex finds candidate substrings in code, Jev chooses "
    "which candidate is the "
    "field's true value, and the result is returned verbatim \u2014 never "
    "model-generated text. Fields "
    "with zero regex matches never reach the model (not_found); if no "
    "field has matches, no API "
    "call is made. Ambiguous picks are flagged for review. Use for prices, "
    "dates, version "
    "numbers, IDs, and anything with a recognizable shape; keep documents "
    "bounded."
)
INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "document": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50000,
            "description": (
                "The document to extract from. Rejected above 50,000 "
                "characters."
            ),
        },
        "fields": {
            "minItems": 1,
            "maxItems": 32,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "maxLength": 64,
                        "pattern": "^[a-z][a-z0-9_-]*$",
                        "description": "Field name, e.g. 'price' or 'version'.",
                    },
                    "pattern": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 500,
                        "description": (
                            "Python regular expression source (without "
                            "delimiters) that matches candidate values, in "
                            "Python re syntax: for example (?P<name>...) for a "
                            "named group, not JavaScript's (?<name>...). Runs "
                            "in a child process with a hard "
                            "timeout."
                        ),
                    },
                    "flags": {
                        "description": (
                            "Regex flags (e.g. 'i'). 'g' is always added; "
                            "non-letters are "
                            "dropped."
                        ),
                        "type": "string",
                        "maxLength": 8,
                    },
                    "description": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 2000,
                        "description": (
                            "What the field is, so Jev can pick the right "
                            "candidate among regex "
                            "matches."
                        ),
                    },
                },
                "required": ["id", "pattern", "description"],
                "additionalProperties": False,
            },
            "description": (
                "Fields to extract. Up to 32 per call, all judged in one "
                "request."
            ),
        },
        "purpose": {
            "description": "What the extraction is for; shared across fields.",
            "type": "string",
        },
        "auto_accept": {
            "description": "Minimum top probability for auto. Default 0.85.",
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "minimum_margin": {
            "description": "Minimum winner-to-runner-up gap for auto. Default "
            "0.5.",
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["document", "fields"],
    "additionalProperties": False,
}
EXECUTION = {"taskSupport": "forbidden"}


async def call(arguments, judge, *, deadline, record_file):
    """Find regex matches and ask the judge to select field values."""
    auto_accept = arguments.get("auto_accept", 0.85)
    minimum_margin = arguments.get("minimum_margin", 0.5)
    document = truncate(arguments["document"], 50000)
    seen_ids = set()
    for field in arguments["fields"]:
        if field["id"] in seen_ids:
            raise ValueError(f"Duplicate field id: {field['id']}")
        seen_ids.add(field["id"])

    fields = []
    for index, field in enumerate(arguments["fields"]):
        flags = re.sub("[^a-z]|g", "", field.get("flags", "")) + "g"
        result = await patterns.run_regex(document, field["pattern"], flags)
        fields.append(
            {
                **field,
                "key": f"f{index}",
                **result,
                "candidates": []
                if result.get("error")
                else result["candidates"],
            }
        )
    total_chars = sum(
        len(candidate.encode("utf-16-le", "surrogatepass")) // 2
        for field in fields
        for candidate in field["candidates"]
    )
    if total_chars > MAX_EXTRACT_TOTAL_CHARS:
        raise ValueError(
            f"Batch too large: {total_chars} candidate characters exceeds "
            f"the {MAX_EXTRACT_TOTAL_CHARS} character budget. Tighten the "
            "patterns or split the call."
        )

    questions = {}
    state_fields = []
    for field in fields:
        if field.get("error") or not field["candidates"]:
            continue
        criteria = {
            f"c{index}": f"Candidate value: {text(candidate)}"
            for index, candidate in enumerate(field["candidates"])
        }
        criteria["none_of_them"] = (
            "None of the candidates is the value this field asks for"
        )
        questions[field["key"]] = {
            "type": "choice",
            "instructions": (
                "Which candidate is the correct value of the field "
                f'"{field["id"]}" '
                f"({field['description']}) in the document in the state? "
                "Pick the exact substring the document presents as this "
                "field's value."
            ),
            "criteria": criteria,
        }
        state_fields.append(
            {
                "id": field["key"],
                "description": field["description"],
                "pattern": field["pattern"],
            }
        )
    if state_fields:
        judgment = await judge(
            {
                "purpose": arguments.get("purpose"),
                "document": document,
                "fields": state_fields,
            },
            questions,
            deadline=deadline,
            record_file=record_file,
        )
        provider = PROVIDER
    else:
        judgment = {"answers": {}, "usage": None, "model": NO_JUDGMENT_MODEL}
        provider = NO_JUDGMENT_PROVIDER
    answers = (
        judgment["answers"] if isinstance(judgment["answers"], dict) else {}
    )

    results = []
    for field in fields:
        flags = {
            "candidates_truncated": field["truncated"],
            "matches_skipped_too_long": field["tooLong"],
        }
        incomplete = field["truncated"] or field["tooLong"] > 0
        base = {"id": field["id"], "value": None}
        count = len(field["candidates"])
        if field.get("error"):
            results.append(
                {
                    **base,
                    "status": "invalid_pattern",
                    "reason": field["error"],
                    "candidates_considered": 0,
                    **flags,
                }
            )
            continue
        if not count:
            results.append(
                {
                    **base,
                    "status": "review" if field["tooLong"] > 0 else "not_found",
                    "reason": "matches_too_long"
                    if field["tooLong"] > 0
                    else "no_regex_matches",
                    "candidates_considered": 0,
                    **flags,
                }
            )
            continue
        answer = validate_choice_answer(
            answers.get(field["key"]),
            [*(f"c{index}" for index in range(count)), "none_of_them"],
        )
        if answer is None:
            results.append(
                {
                    **base,
                    "status": "invalid_response",
                    "reason": None,
                    "candidates_considered": count,
                    **flags,
                }
            )
            continue
        margin = margin_of(answer["probabilities"])
        top_probability = answer["probabilities"][answer["choice"]]
        decision = classification_decision(
            top_probability, margin, auto_accept, minimum_margin
        )
        if answer["choice"] == "none_of_them":
            status = (
                "review" if incomplete or decision != "auto" else "not_found"
            )
            reason = (
                "candidate_limit"
                if incomplete
                else "none_matched"
                if decision == "auto"
                else "none_matched_ambiguous"
            )
        else:
            base["value"] = field["candidates"][int(answer["choice"][1:])]
            status = "review" if incomplete else decision
            reason = "candidate_limit" if incomplete else None
        results.append(
            {
                **base,
                "status": status,
                "reason": reason,
                "confidence": answer["confidence"],
                "top_probability": top_probability,
                "margin": margin,
                "candidates_considered": count,
                **flags,
            }
        )
    return text(
        {
            "tool": NAME,
            "model": judgment["model"],
            "provider": provider,
            "summary": {
                "fields": len(results),
                "extracted": sum(
                    result["value"] is not None for result in results
                ),
                "auto": sum(result["status"] == "auto" for result in results),
                "review": sum(
                    result["status"] == "review" for result in results
                ),
                "not_found": sum(
                    result["status"] == "not_found" for result in results
                ),
                "invalid": sum(
                    result["status"] in ("invalid_pattern", "invalid_response")
                    for result in results
                ),
            },
            "thresholds": {
                "auto_accept": auto_accept,
                "minimum_margin": minimum_margin,
            },
            "results": results,
            "usage": judgment["usage"],
        }
    ), False
