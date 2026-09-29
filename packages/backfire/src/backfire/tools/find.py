"""Port of jev-mcp 0.9.0 find; see ../UPSTREAM.md."""

from decimal import ROUND_HALF_UP
from decimal import Decimal

from backfire.lib import MAX_CANDIDATE_CHARS
from backfire.lib import ensure_unique_ids
from backfire.lib import exists_verdict
from backfire.lib import rank_candidates
from backfire.lib import truncate
from backfire.tools import text
from backfire.tools.answers import PROVIDER
from backfire.tools.answers import validate_choice_answer
from backfire.tools.answers import validate_noul_answer

NAME = "backfire_find"

TITLE = "Semantic search over candidates"

DESCRIPTION = (
    "Rank candidates against a plain-language query with TypeSafe Jev "
    "\u2014 no embeddings needed. One "
    "Choice scores every candidate id by how well it answers the query, "
    "plus a Noul checks whether "
    "any candidate addresses the query at all (so a confident 'top hit' "
    "cannot masquerade as an "
    "answer). Pattern: docs.typesafe.ai/cookbooks/semantic_find. Use for "
    "'which file/note/line covers "
    "X' across up to 250 candidates."
)

INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "minLength": 1,
            "description": "What you are looking for, in natural language.",
        },
        "candidates": {
            "minItems": 1,
            "maxItems": 250,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "description": "Short identifier "
                        "for this candidate "
                        "(e.g. a file path, "
                        "note name, or line "
                        "id).",
                        "type": "string",
                    },
                    "text": {
                        "type": "string",
                        "description": "The candidate's text.",
                    },
                },
                "required": ["text"],
                "additionalProperties": False,
            },
            "description": "Candidates to search. Up to 250 in one call; texts "
            "are truncated at 2000 chars.",
        },
        "top_k": {
            "description": "How many ranked candidates to return. Default 5.",
            "type": "integer",
            "minimum": 1,
            "maximum": 50,
        },
    },
    "required": ["query", "candidates"],
    "additionalProperties": False,
}

EXECUTION = {"taskSupport": "forbidden"}


async def call(arguments, judge, *, deadline, record_file):
    """Rank candidates and assess whether any addresses the query."""
    query = arguments["query"]
    candidates = ensure_unique_ids(
        [
            {
                "id": item.get("id", ""),
                "text": truncate(item["text"], MAX_CANDIDATE_CHARS),
            }
            for item in arguments["candidates"]
        ],
        "candidate",
    )["items"]
    questions = {
        "best": {
            "type": "choice",
            (
                "instructions"
            ): f'Which candidate contains the best answer to: "{query}"?',
            "criteria": {item["id"]: None for item in candidates},
        },
        "exists": {
            "type": "noul",
            "instructions": f'Does any candidate address or answer: "{query}"?',
            "criteria": {
                "true": "At least one candidate states or directly implies the "
                "answer",
                "false": "No candidate addresses this",
            },
        },
    }
    result = await judge(
        {"query": query, "candidates": candidates},
        questions,
        deadline=deadline,
        record_file=record_file,
    )
    answers = (
        result["answers"] if isinstance(result.get("answers"), dict) else {}
    )
    exists = validate_noul_answer(answers.get("exists"))
    best = validate_choice_answer(
        answers.get("best"), [item["id"] for item in candidates]
    )
    if exists is None or best is None:
        return text(
            {
                "tool": NAME,
                "model": result["model"],
                "provider": PROVIDER,
                "query": query,
                "status": "invalid_response",
                "exists": exists,
                "exists_verdict": None,
                "top": [],
                "reason": (
                    "missing or malformed best or exists answer; cannot rank "
                    "safely"
                ),
                "usage": result["usage"],
            }
        ), False
    ranked = rank_candidates(candidates, best["probabilities"])[
        : arguments.get("top_k", 5)
    ]
    return text(
        {
            "tool": NAME,
            "model": result["model"],
            "provider": PROVIDER,
            "query": query,
            "exists": exists,
            "exists_verdict": exists_verdict(exists),
            "top": [
                {
                    "id": item["id"],
                    "probability": float(
                        Decimal.from_float(float(item["probability"])).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        )
                    ),
                    "text": item["text"],
                }
                for item in ranked
            ],
            "usage": result["usage"],
        }
    ), False
