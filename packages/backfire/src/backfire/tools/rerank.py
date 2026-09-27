"""Ported from jev-mcp 0.9.0; see ../UPSTREAM.md."""

from decimal import Decimal, ROUND_HALF_UP

from backfire.lib import MAX_CANDIDATE_CHARS, MAX_RERANK_TOTAL_CHARS, rerank_by_score, truncate
from backfire.tools import text
from backfire.tools.answers import PROVIDER, validate_noul_answer

NAME = 'backfire_rerank'
TITLE = "Score every candidate's relevance and return them sorted"
DESCRIPTION = ('Rerank candidates against a query with TypeSafe Jev: one independent relevance probability '
 'per candidate, all in a single request, then sorted by score. Unlike backfire_find (which '
 'picks one best answer), rerank scores every candidate so the full ordering survives. '
 "TypeSafe's rerank cookbook reports that on the CLERC benchmark this pattern lifted top-1 "
 'from 5% to 18% and top-10 from 38% to 62% (docs.typesafe.ai/cookbooks). Use for retrieval '
 'ordering, dedup triage, or feed ranking across up to 250 candidates.')
INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "minLength": 1,
            "maxLength": 2000,
            "description": "What relevance is measured against, in natural language."
        },
        "candidates": {
            "minItems": 1,
            "maxItems": 250,
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "description": "Short identifier for this candidate (e.g. a file path, note name, or line id).",
                        "type": "string"
                    },
                    "text": {
                        "type": "string",
                        "description": "The candidate's text."
                    }
                },
                "required": [
                    "text"
                ],
                "additionalProperties": False
            },
            "description": "Candidates to search. Up to 250 in one call; texts are truncated at 2000 chars."
        },
        "top_k": {
            "description": "How many ranked candidates to return. Default: all.",
            "type": "integer",
            "minimum": 1,
            "maximum": 250
        }
    },
    "required": [
        "query",
        "candidates"
    ],
    "additionalProperties": False
}
EXECUTION = {
    "taskSupport": "forbidden"
}


async def call(arguments, judge, *, deadline, record_file):
    query = arguments["query"]
    raw_candidates = arguments["candidates"]
    supplied_ids = set()
    for candidate in raw_candidates:
        if candidate.get("id") is not None:
            if candidate["id"] in supplied_ids:
                raise ValueError(f"Duplicate candidate id: {candidate['id']}")
            supplied_ids.add(candidate["id"])
    used_ids = set(supplied_ids)
    candidates = []
    for index, candidate in enumerate(raw_candidates):
        external = candidate.get("id")
        if external is None:
            external = f"candidate{index}"
            suffix = 2
            while external in used_ids:
                external = f"candidate{index}_{suffix}"
                suffix += 1
        used_ids.add(external)
        candidates.append({"id": external, "text": truncate(candidate["text"], MAX_CANDIDATE_CHARS)})
    total_chars = sum(len(candidate["text"].encode("utf-16-le", "surrogatepass")) // 2 for candidate in candidates)
    if total_chars > MAX_RERANK_TOTAL_CHARS:
        raise ValueError(
            f"Batch too large: {total_chars} candidate characters exceeds the {MAX_RERANK_TOTAL_CHARS} character budget. Split the batch."
        )
    questions = {
        f"rel_{index}": {
            "type": "noul",
            "instructions": f"Is candidate c{index} relevant to the query in the state? Candidate c{index}: {candidate['text']}",
            "criteria": {
                "true": "The candidate addresses the subject the query asks about, or provides what it seeks",
                "false": "The candidate is about a different subject, or only shares vocabulary with the query",
            },
        }
        for index, candidate in enumerate(candidates)
    }
    judgment = await judge({"query": query}, questions, deadline=deadline, record_file=record_file)
    answers = judgment["answers"] if isinstance(judgment["answers"], dict) else {}
    scores = [validate_noul_answer(answers.get(f"rel_{index}")) for index in range(len(candidates))]
    base = {"tool": NAME, "model": judgment["model"], "provider": PROVIDER, "query": query}
    if any(score is None for score in scores):
        return text({**base, "status": "invalid_response", "ranked": None, "usage": judgment["usage"]}), False
    ranked = rerank_by_score(candidates, scores)
    returned = ranked[:arguments["top_k"]] if arguments.get("top_k") else ranked
    return text({
        **base,
        "summary": {"candidates": len(candidates), "returned": len(returned)},
        "ranked": [{
            "rank": index + 1, "id": candidate["id"],
            "relevance": float(Decimal.from_float(float(candidate["relevance"])).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
            "text": candidate["text"],
        } for index, candidate in enumerate(returned)],
        "usage": judgment["usage"],
    }), False
