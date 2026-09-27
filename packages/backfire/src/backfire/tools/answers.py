"""Answer validation ported from jev-mcp 0.9.0's src/index.ts."""

import math

from backfire.lib import PROBABILITY_SUM_TOLERANCE, SCORE_MEAN_TOLERANCE

PROVIDER = "compatible"
NO_JUDGMENT_PROVIDER = "none"
NO_JUDGMENT_MODEL = "jev-latest"


def _probability(value):
    return type(value) in (int, float) and 0 <= value <= 1 and math.isfinite(value)


def _distribution(probabilities, expected_keys):
    if not isinstance(probabilities, dict) or set(probabilities) != set(expected_keys):
        return False
    if not all(_probability(value) for value in probabilities.values()):
        return False
    # Match Object.values and its left-to-right sum, including numeric IDs.
    keys = sorted(probabilities, key=lambda key: (
        int(key) if len(key) <= 10 and key.isascii() and key.isdecimal()
        and str(int(key)) == key and int(key) < 2**32 - 1 else math.inf
    ))
    total = 0
    for key in keys:
        total += probabilities[key]
    return abs(total - 1) <= PROBABILITY_SUM_TOLERANCE


def validate_choice_answer(answer, expected_keys):
    if not isinstance(answer, dict) or not isinstance(answer.get("choice"), str):
        return None
    probabilities = answer.get("probabilities")
    expected = set(expected_keys)
    choice = answer["choice"]
    if choice not in expected or not _distribution(probabilities, expected):
        return None
    if probabilities[choice] < max(probabilities.values()) - 1e-9:
        return None
    confidence = answer.get("confidence")
    return {"choice": choice, "probabilities": probabilities,
            "confidence": confidence if _probability(confidence) else None}


def validate_score_answer(answer):
    if not isinstance(answer, dict):
        return None
    score = answer.get("score")
    if type(score) not in (int, float) or not 0 <= score <= 2 or not math.isfinite(score):
        return None
    confidence = answer.get("confidence")
    probabilities = answer.get("probabilities")
    if probabilities is not None:
        if not _distribution(probabilities, ("0", "1", "2")):
            return None
        mean = 0
        for index in range(3):
            mean += index * probabilities[str(index)]
        if abs(mean - score) > SCORE_MEAN_TOLERANCE:
            return None
    return {"score": score, "confidence": confidence if _probability(confidence) else None,
            "probabilities": probabilities}


def validate_noul_answer(answer):
    value = answer.get("noul") if isinstance(answer, dict) else None
    return value if _probability(value) else None
