"""Pure helpers ported from jev-mcp 0.9.0; see UPSTREAM.md."""

import math
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Literal

import rfc8785

MAX_CANDIDATES = 250
MAX_CANDIDATE_CHARS = 2000
PROBABILITY_SUM_TOLERANCE = 0.01 + 1e-12
MAX_CLASSES = 250
MAX_ITEMS = 64
MAX_ITEM_CHARS = 2000
MAX_CANDIDATES_DECIDE = 6
MAX_REQUIREMENTS = 3
MAX_RERANK_CANDIDATES = 250
MAX_RERANK_TOTAL_CHARS = 100_000
MAX_PROPOSITIONS = 64
MAX_PROPOSITION_CHARS = 2000
MAX_NOUL_TOTAL_CHARS = 150_000
MAX_COMPARE_ASPECTS = 10
MAX_EXTRACT_FIELDS = 32
MAX_EXTRACT_CANDIDATES = 20
MAX_EXTRACT_CANDIDATE_CHARS = 2000
MAX_EXTRACT_TOTAL_CHARS = 50_000
REGEX_TIMEOUT_MS = 1000
MAX_GATE_CLAIMS = 16
MAX_GATE_EVIDENCE_ITEMS = 16
MAX_GATE_EVIDENCE_CHARS = 200_000
MAX_REVIEW_DOC_CHARS = 50_000
MAX_CLAIM_CHARS = 2000
SCORE_MEAN_TOLERANCE = 0.02 + 1e-12
DEFAULT_COMPOSITE_FLOOR = 0.7

RELATION_TO_VERDICT = {
    "supports": "verified",
    "contradicts": "contradicted",
    "says_nothing": "unsupported",
}
DECIDE_ESCAPE_HATCHES = {
    "ask_user": "A consequential user preference or requirement is missing; ask instead of inventing it",
    "investigate": "Gather missing technical or factual evidence before selecting a candidate",
    "none": "None of the supplied candidates fits the known requirements",
}
COMPARE_RELATIONS = {
    "same_fact": "Both passages state the same underlying fact or claim",
    "contradicts": "The passages state opposing facts about the same subject",
    "different_facts": "The passages discuss different subjects or make non-overlapping claims",
}
ASPECT_RELATIONS = {
    "same_fact": "Both passages make comparable assertions about this aspect and they agree",
    "contradicts": "Both passages address this aspect and their assertions conflict",
    "different_facts": "The passages do not both make a comparable assertion about this aspect: at least one does not address it, or their mentions do not overlap",
}
REVIEW_WEIGHTS = {
    "correctness": 0.4,
    "spec_match": 0.3,
    "test_gap": 0.15,
    "blast_radius": 0.15,
}
VERIFY_CLAIM_CRITERIA = {
    "verified": "The evidence clearly supports the claim",
    "contradicted": "The evidence contradicts the claim",
    "unsupported": "The evidence neither supports nor contradicts the claim",
}

PolicyAction = Literal["auto", "review", "escalate"]
ClaimVerdict = Literal["verified", "contradicted", "unsupported"]
Identifiable = dict[str, Any]
ReviewEvidenceInput = str | Identifiable | list[Identifiable]


def is_record(value: object) -> bool:
    return isinstance(value, dict)


def sanitize_id(identifier: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", identifier).strip("_")[:64]


def ensure_unique_ids(items: list[Identifiable], fallback_prefix: str) -> dict:
    """Keep upstream IDs and order, without rescanning used suffixes."""
    used: set[str] = set()
    renamed: dict[str, str] = {}
    next_suffix: dict[str, int] = {}
    out = []
    for index, item in enumerate(items):
        raw = item.get("id") or ""
        base = sanitize_id(raw) or f"{fallback_prefix}{index}"
        identifier = base
        suffix = next_suffix.get(base, 1)
        while identifier in used:
            identifier = f"{base}_{suffix}"
            suffix += 1
        next_suffix[base] = suffix
        used.add(identifier)
        if raw and raw != identifier:
            renamed[raw] = identifier
        out.append({**item, "id": identifier})
    return {"items": out, "renamed": renamed}


def truncate(text: str, max_chars: int) -> str:
    # Upstream length and slice count UTF-16 code units, including split pairs.
    encoded = text.encode("utf-16-le", errors="surrogatepass")
    if len(encoded) <= max_chars * 2:
        return text
    return (
        encoded[: max_chars * 2].decode("utf-16-le", errors="surrogatepass")
        + " […truncated]"
    )


def verify_action(
    confidence: float, auto_accept: float
) -> Literal["auto", "review"]:
    return "auto" if confidence >= auto_accept else "review"


def screen_recommendation(
    *,
    injection: float,
    block_at: float,
    review_at: float,
    relevance: float | None = None,
    substance: float | None = None,
) -> dict[str, str]:
    # Decimal preserves JS toFixed's tie rounding; RFC 8785 preserves number text.
    def fixed(value: float) -> str:
        return str(
            Decimal.from_float(value or 0).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )

    if injection >= block_at:
        return {
            "action": "block",
            "reason": f"injection probability {fixed(injection)} >= block threshold {rfc8785.dumps(block_at).decode()}",
        }
    if injection >= review_at:
        return {
            "action": "review",
            "reason": f"injection probability {fixed(injection)} >= review threshold {rfc8785.dumps(review_at).decode()}",
        }
    if substance is not None and substance < 0.3:
        return {
            "action": "skip",
            "reason": f"little substantive content (substance {fixed(substance)})",
        }
    if relevance is not None and relevance < 0.3:
        return {
            "action": "skip",
            "reason": f"not relevant to the stated purpose (relevance {fixed(relevance)})",
        }
    return {"action": "pass", "reason": "no signals above thresholds"}


def exists_verdict(
    exists: float, found: float = 0.7, absent: float = 0.35
) -> str:
    if exists >= found:
        return "answered"
    return "absent" if exists < absent else "partial"


def rank_candidates(
    candidates: list[Identifiable], probabilities: dict[str, float]
) -> list[dict]:
    return sorted(
        (
            {
                **candidate,
                "probability": probabilities.get(candidate["id"]) or 0,
            }
            for candidate in candidates
        ),
        key=lambda candidate: candidate["probability"],
        reverse=True,
    )


def margin_of(probabilities: dict[str, float] | None) -> float:
    ranked = sorted((probabilities or {}).values(), reverse=True)
    return ranked[0] - ranked[1] if len(ranked) >= 2 else 0


def classification_decision(
    top_probability: float,
    margin: float,
    auto_accept: float,
    minimum_margin: float,
) -> Literal["auto", "review"]:
    return (
        "auto"
        if top_probability >= auto_accept and margin >= minimum_margin
        else "review"
    )


def contradicts_recommendation(
    checks: list[dict], recommended: str
) -> list[int]:
    return [
        check["requirement"]
        for check in checks
        if check["candidate"] == recommended
        and check["answer"] == "contradicted"
    ]


def rerank_by_score(candidates: list[dict], scores: list[float]) -> list[dict]:
    return sorted(
        (
            {
                **candidate,
                "relevance": (scores[index] or 0) if index < len(scores) else 0,
            }
            for index, candidate in enumerate(candidates)
        ),
        key=lambda candidate: candidate["relevance"],
        reverse=True,
    )


def validate_policy_thresholds(auto_accept: float, review_at: float) -> None:
    if (
        not all(
            type(value) in (int, float) and math.isfinite(value)
            for value in (auto_accept, review_at)
        )
        or not 0 <= review_at <= auto_accept <= 1
    ):
        raise ValueError(
            "Thresholds must satisfy 0 <= review_at <= auto_accept <= 1."
        )


def resolve_policy_thresholds(
    auto_accept: float = 0.8, review_at: float | None = None
) -> dict[str, float]:
    resolved = min(0.5, auto_accept) if review_at is None else review_at
    validate_policy_thresholds(auto_accept, resolved)
    return {"auto_accept": auto_accept, "review_at": resolved}


def require_complete_context(
    action: PolicyAction, truncated: bool
) -> PolicyAction:
    return "review" if truncated and action == "auto" else action


def review_composite(
    *,
    correctness: float,
    spec_match: float,
    test_gap: float,
    blast_radius: float,
) -> float:
    def normalized(value: float) -> float:
        return min(max(value, 0), 2) / 2

    return (
        REVIEW_WEIGHTS["correctness"] * normalized(correctness)
        + REVIEW_WEIGHTS["spec_match"] * normalized(spec_match)
        + REVIEW_WEIGHTS["test_gap"] * (1 - normalized(test_gap))
        + REVIEW_WEIGHTS["blast_radius"] * (1 - normalized(blast_radius))
    )


def review_action(
    *,
    composite: float,
    safe_to_apply: float,
    min_confidence: float | None,
    auto_accept: float,
    review_at: float,
    composite_floor: float,
) -> PolicyAction:
    if (
        min_confidence is None
        or min_confidence < review_at
        or safe_to_apply < review_at
    ):
        return "escalate"
    if (
        safe_to_apply >= auto_accept
        and composite >= composite_floor
        and min_confidence >= auto_accept
    ):
        return "auto"
    return "review"


def claim_action(
    verdict: ClaimVerdict,
    confidence: float | None,
    auto_accept: float,
    review_at: float,
) -> PolicyAction:
    if confidence is None or confidence < review_at:
        return "escalate"
    if verdict == "contradicted" and confidence >= auto_accept:
        return "escalate"
    return (
        "auto"
        if verdict == "verified" and confidence >= auto_accept
        else "review"
    )


def worst_action(actions: list[PolicyAction]) -> PolicyAction:
    if "escalate" in actions:
        return "escalate"
    return "review" if "review" in actions else "auto"


def normalize_evidence(raw: ReviewEvidenceInput) -> list[Identifiable]:
    items = (
        [{"id": "evidence", "text": raw}]
        if isinstance(raw, str)
        else raw
        if isinstance(raw, list)
        else [raw]
    )
    return ensure_unique_ids(items, "evidence")["items"]


def has_non_empty_evidence(items: list[Identifiable]) -> bool:
    # ECMAScript trim whitespace differs from Python's default strip set.
    whitespace = "\u0009\u000b\u000c\u0020\u00a0\ufeff\u000a\u000d\u2028\u2029\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u202f\u205f\u3000"
    return any(item["text"].strip(whitespace) for item in items)
