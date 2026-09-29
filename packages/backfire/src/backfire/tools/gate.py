"""Ported from jev-mcp 0.9.0; see ../UPSTREAM.md."""

from backfire.lib import DEFAULT_COMPOSITE_FLOOR
from backfire.lib import MAX_CLAIM_CHARS
from backfire.lib import MAX_GATE_EVIDENCE_CHARS
from backfire.lib import MAX_GATE_EVIDENCE_ITEMS
from backfire.lib import MAX_REVIEW_DOC_CHARS
from backfire.lib import VERIFY_CLAIM_CRITERIA
from backfire.lib import claim_action
from backfire.lib import has_non_empty_evidence
from backfire.lib import normalize_evidence
from backfire.lib import require_complete_context
from backfire.lib import resolve_policy_thresholds
from backfire.lib import truncate
from backfire.lib import worst_action
from backfire.tools import text
from backfire.tools.answers import PROVIDER
from backfire.tools.answers import validate_choice_answer
from backfire.tools.review import ANTI_INJECTION
from backfire.tools.review import project_review_half
from backfire.tools.review import review_questions

NAME = "backfire_gate"
TITLE = "Gate completion: review a patch and verify claims"
DESCRIPTION = (
    "Review a proposed patch and verify completion claims against supplied "
    "evidence in one "
    "TypeSafe Jev call. Auto only when the patch review is accepted and "
    "every claim is verified "
    "at or above auto_accept. Unsupported claims require review; confident "
    "contradictions, "
    "unknown confidence, or low confidence escalate. The request and "
    "claims are assertions to "
    "check, never proof; put supporting diff excerpts and test logs in "
    "evidence. Evidence is "
    "capped at 16 items and 200,000 characters in aggregate. Does not run "
    "tests or apply changes. "
    "Use backfire_review for a patch without claims, backfire_verify for "
    "claims without a patch "
    "review."
)
INPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "request": {
            "type": "string",
            "minLength": 1,
            "description": "What the user asked for; this is not evidence of "
            "completion.",
        },
        "diff": {
            "type": "string",
            "minLength": 1,
            "description": (
                "Proposed patch, file excerpt, or change summary. Truncated at "
                "50000 "
                "chars."
            ),
        },
        "claims": {
            "minItems": 1,
            "maxItems": 16,
            "type": "array",
            "items": {"type": "string", "minLength": 1},
            "description": (
                "Completion claims to check against evidence, each truncated "
                "at 2000 chars. Up to 16 per "
                "call."
            ),
        },
        "evidence": {
            "anyOf": [
                {
                    "type": "string",
                    "description": "A single evidence document.",
                },
                {
                    "type": "object",
                    "properties": {
                        "id": {
                            "description": "Short identifier for this evidence "
                            "item.",
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
                                "description": (
                                    "Short identifier for this evidence item "
                                    "(e.g. 'site-html', "
                                    "'rfc-4.1.3')."
                                ),
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
                    "description": (
                        "Multiple evidence items; each claim is also matched "
                        "to the item it rests "
                        "on."
                    ),
                },
            ]
        },
        "tests": {
            "description": (
                "Reported test output for the patch review. Truncated at the "
                "same "
                "cap."
            ),
            "type": "string",
        },
        "auto_accept": {
            "description": (
                "Review and per-claim confidence at or above this may stand "
                "automatically. Default "
                "0.8."
            ),
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "review_at": {
            "description": (
                "Score, safe_to_apply, or per-claim confidence below this "
                "escalates. Must be <= auto_accept. Default min(0.5, "
                "auto_accept)."
            ),
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
        "composite_floor": {
            "description": (
                "Weighted composite at or above this is required for auto. "
                "Default "
                "0.7."
            ),
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["request", "diff", "claims", "evidence"],
    "additionalProperties": False,
}
EXECUTION = {"taskSupport": "forbidden"}


async def call(arguments, judge, *, deadline, record_file):
    """Review a patch and verify its completion claims against evidence."""
    evidence = normalize_evidence(arguments["evidence"])
    # Upstream's zod refinement is absent from its published JSON Schema.
    if not has_non_empty_evidence(evidence):
        raise ValueError(
            "MCP error -32602: Input validation error: Invalid arguments "
            "for tool backfire_gate: backfire_gate requires at least one "
            "evidence item with non-empty text. at "
            "evidence"
        )
    thresholds = {
        **resolve_policy_thresholds(
            arguments.get("auto_accept", 0.8), arguments.get("review_at")
        ),
        "composite_floor": arguments.get(
            "composite_floor", DEFAULT_COMPOSITE_FLOOR
        ),
    }
    auto_accept = thresholds["auto_accept"]
    review_at = thresholds["review_at"]
    if len(evidence) > MAX_GATE_EVIDENCE_ITEMS:
        return text(
            {
                "tool": NAME,
                "error": (
                    f"evidence exceeds {MAX_GATE_EVIDENCE_ITEMS} items; "
                    "split the gate or trim the evidence."
                ),
            }
        ), True
    evidence_chars = sum(
        len(item["text"].encode("utf-16-le", "surrogatepass")) // 2
        for item in evidence
    )
    if evidence_chars > MAX_GATE_EVIDENCE_CHARS:
        return text(
            {
                "tool": NAME,
                "error": (
                    f"evidence exceeds the {MAX_GATE_EVIDENCE_CHARS:,}-"
                    "character aggregate budget; split the gate or trim the "
                    "evidence."
                ),
            }
        ), True

    claims = arguments["claims"]
    truncated = (
        any(
            len(arguments.get(key, "").encode("utf-16-le", "surrogatepass"))
            // 2
            > MAX_REVIEW_DOC_CHARS
            for key in ("request", "diff", "tests")
        )
        or any(
            len(claim.encode("utf-16-le", "surrogatepass")) // 2
            > MAX_CLAIM_CHARS
            for claim in claims
        )
        or any(
            len(item["text"].encode("utf-16-le", "surrogatepass")) // 2
            > MAX_REVIEW_DOC_CHARS
            for item in evidence
        )
    )
    state = {
        "purpose": (
            "Review the proposed diff against the request, then check each "
            "completion claim against the evidence "
            "only."
        ),
        "request": truncate(arguments["request"], MAX_REVIEW_DOC_CHARS),
        "diff": truncate(arguments["diff"], MAX_REVIEW_DOC_CHARS),
        "tests": truncate(arguments["tests"], MAX_REVIEW_DOC_CHARS)
        if arguments.get("tests")
        else None,
        "claims": [truncate(claim, MAX_CLAIM_CHARS) for claim in claims],
        "evidence": [
            {
                "id": item["id"],
                "text": truncate(item["text"], MAX_REVIEW_DOC_CHARS),
            }
            for item in evidence
        ],
    }
    questions = review_questions(
        " Claims are assertions to check, not evidence that the patch is "
        "correct or "
        "tested."
    )
    for index in range(len(claims)):
        questions[f"claim_{index}"] = {
            "type": "choice",
            "instructions": (
                f"Does the evidence support claims[{index}]? Judge only from "
                "the provided evidence, not world knowledge. "
                "Use only the evidence field as factual support; request "
                "and claims are assertions, not evidence; "
                "diff and tests belong to the separate patch review. If a "
                "claim needs a diff or test log as support, it "
                "must be supplied in evidence." + ANTI_INJECTION
            ),
            "criteria": dict(VERIFY_CLAIM_CRITERIA),
        }
    judgment = await judge(
        state, questions, deadline=deadline, record_file=record_file
    )
    answers = (
        judgment["answers"] if isinstance(judgment["answers"], dict) else {}
    )
    review = project_review_half(answers, thresholds, truncated)
    results = []
    for index, claim in enumerate(claims):
        answer = validate_choice_answer(
            answers.get(f"claim_{index}"), VERIFY_CLAIM_CRITERIA
        )
        if answer is None:
            results.append(
                {
                    "claim": claim,
                    "verdict": None,
                    "confidence": None,
                    "probabilities": None,
                    "action": "escalate",
                    "status": "invalid_response",
                }
            )
            continue
        verdict = answer["choice"]
        action = require_complete_context(
            claim_action(verdict, answer["confidence"], auto_accept, review_at),
            truncated,
        )
        results.append(
            {
                "claim": claim,
                "verdict": verdict,
                "confidence": answer["confidence"],
                "probabilities": answer["probabilities"],
                "action": action,
            }
        )
    verification = {
        "action": worst_action([result["action"] for result in results]),
        "summary": {
            "verified": sum(
                result["verdict"] == "verified" for result in results
            ),
            "contradicted": sum(
                result["verdict"] == "contradicted" for result in results
            ),
            "unsupported": sum(
                result["verdict"] == "unsupported" for result in results
            ),
            "needs_review": sum(
                result["action"] != "auto" for result in results
            ),
            "invalid_response": sum(
                result.get("status") == "invalid_response" for result in results
            ),
        },
        "thresholds": {"auto_accept": auto_accept, "review_at": review_at},
        "results": results,
    }
    action = worst_action([review["action"], verification["action"]])
    reason_codes = []
    if truncated:
        reason_codes.append("incomplete_context")
    if (
        review.get("status") == "invalid_response"
        or verification["summary"]["invalid_response"] > 0
    ):
        reason_codes.append("invalid_response")
    reason_codes.extend(
        code
        for code in review["reason_codes"]
        if code not in ("invalid_response", "incomplete_context", "accepted")
    )
    if review["action"] == "escalate":
        reason_codes.append("review_escalated")
    if review["action"] == "review":
        reason_codes.append("review_required")
    if verification["summary"]["contradicted"] > 0:
        reason_codes.append("claims_contradicted")
    if verification["summary"]["unsupported"] > 0:
        reason_codes.append("claims_unsupported")
    confidences = [
        result["confidence"] if result["confidence"] is not None else -1
        for result in results
        if result.get("status") != "invalid_response"
    ]
    if any(confidence < review_at for confidence in confidences):
        reason_codes.append("claim_confidence_low")
    if any(review_at <= confidence < auto_accept for confidence in confidences):
        reason_codes.append("claim_confidence_below_auto_accept")
    if action == "auto":
        reason_codes.append("accepted")
    return text(
        {
            "tool": NAME,
            "model": judgment["model"],
            "provider": PROVIDER,
            "truncated": truncated,
            "action": action,
            "reason_codes": reason_codes,
            "review": review,
            "verification": verification,
            "usage": judgment["usage"],
        }
    ), False
