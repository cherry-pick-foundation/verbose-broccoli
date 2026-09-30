"""Replace education identifiers before a judgment reaches its provider."""

from collections.abc import Callable, Mapping
import dataclasses
import re
from typing import Any

from backfire.config import SHIPPED_CONFIG
from backfire.failures import JudgmentError
from backfire_education.roster import load_roster
from backfire_education.table import assign

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
__all__ = ["compile_roster_pattern", "find_spans", "pseudonymize"]


def compile_roster_pattern(
    identifiers: Mapping[str, tuple[str, str]],
) -> re.Pattern[str] | None:
    """Build a longest-first regex for roster identifiers.

    Args:
        identifiers: Map from roster text to its identifier kind and value.

    Returns:
        A compiled regex, or None when there are no identifiers.
    """
    return (
        re.compile(
            "|".join(
                re.escape(value)
                for value in sorted(
                    identifiers, key=lambda item: (-len(item), item)
                )
            )
        )
        if identifiers
        else None
    )


def find_spans(
    text: str,
    identifiers: Mapping[str, tuple[str, str]],
    roster_pattern: re.Pattern[str] | None,
) -> list[tuple[int, int, tuple[str, str]]]:
    """Find roster, phone, and email spans, merging overlapping matches.

    Args:
        text: Text to search.
        identifiers: Map from roster text to its identifier kind and value.
        roster_pattern: Compiled pattern for roster text, or None.

    Returns:
        A list of (start, stop, identifier) tuples; phone and email values are
        normalized.

    Raises:
        ImportError: If the optional phonenumbers package is unavailable.
    """
    # Optional dependency.
    import phonenumbers  # noqa: PLC0415

    candidates = []
    if roster_pattern is not None:
        candidates.extend(
            (match.start(), match.end(), identifiers[match.group()], 0)
            for match in roster_pattern.finditer(text)
        )
    for match in phonenumbers.PhoneNumberMatcher(text, "KR"):
        value = phonenumbers.format_number(
            match.number, phonenumbers.PhoneNumberFormat.E164
        )
        candidates.append((match.start, match.end, ("phone", value), 1))
    candidates.extend(
        (match.start(), match.end(), ("email", match.group().lower()), 2)
        for match in _EMAIL.finditer(text)
    )
    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[3]))
    selected, end = [], -1
    for start, stop, identifier, _ in candidates:
        if start >= end:
            selected.append((start, stop, identifier))
            end = stop
        else:
            kept_start, _, kept_identifier = selected[-1]
            end = max(end, stop)
            selected[-1] = (kept_start, end, kept_identifier)
    return selected


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _strings(getattr(value, field.name))


def _replace_tree(value, replace):
    if isinstance(value, str):
        return replace(value)
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            new_key = replace(key) if isinstance(key, str) else key
            if new_key in result:
                raise JudgmentError("pseudonym_conflict")
            result[new_key] = _replace_tree(item, replace)
        return result
    if isinstance(value, list):
        return [_replace_tree(item, replace) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_tree(item, replace) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.replace(
            value,
            **{
                field.name: _replace_tree(getattr(value, field.name), replace)
                for field in dataclasses.fields(value)
            },
        )
    return value


def pseudonymize(
    state: Any,
    questions: Mapping[str, Any],
) -> tuple[Any, dict[str, Any], Callable[[dict], dict]]:
    """Return masked inputs and a call-local answer restoration function."""
    try:
        # Availability check for the optional dependency.
        import phonenumbers  # noqa: F401, PLC0415
    except ImportError:
        raise JudgmentError(
            "backend_not_configured", str(SHIPPED_CONFIG)
        ) from None

    identifiers = load_roster()
    roster_pattern = compile_roster_pattern(identifiers)
    question_items = []
    for key, question in questions.items():
        if hasattr(question, "model_dump"):
            question_items.append(
                (
                    key,
                    question,
                    type(question),
                    question.model_dump(mode="json"),
                )
            )
        else:
            question_items.append((key, question, None, question))

    spans_by_text = {}

    def cached_spans(text):
        if text in spans_by_text:
            return spans_by_text[text]
        spans_by_text[text] = find_spans(text, identifiers, roster_pattern)
        return spans_by_text[text]

    values = [state]
    for key, _, _, document in question_items:
        values.extend((key, document))
    seen, to_assign = set(), []
    for value in values:
        for text in _strings(value):
            for _, _, identifier in cached_spans(text):
                if identifier not in seen:
                    seen.add(identifier)
                    to_assign.append(identifier)
    pseudonyms = assign(to_assign)

    def replace(text):
        parts, offset = [], 0
        for start, stop, identifier in cached_spans(text):
            parts.extend((text[offset:start], pseudonyms[identifier]))
            offset = stop
        if not parts:
            return text
        parts.append(text[offset:])
        return "".join(parts)

    provider_state = _replace_tree(state, replace)
    provider_questions = {}
    question_restore = {}
    answer_restore = {}
    for key, _, question_class, document in question_items:
        provider_key = replace(key)
        if provider_key in provider_questions:
            raise JudgmentError("pseudonym_conflict")
        provider_document = _replace_tree(document, replace)
        provider_questions[provider_key] = (
            question_class.model_validate(provider_document)
            if question_class is not None
            else provider_document
        )
        question_restore[provider_key] = key
        labels, levels = {}, {}
        criteria = (
            document.get("criteria")
            if isinstance(document, Mapping)
            else getattr(document, "criteria", None)
        )
        question_type = (
            document.get("type")
            if isinstance(document, Mapping)
            else getattr(document, "type", None)
        )
        if question_type == "choice" and isinstance(criteria, Mapping):
            labels = {replace(label): label for label in criteria}
        elif question_type == "score" and isinstance(criteria, list):
            levels = {str(index): level for index, level in enumerate(criteria)}
        answer_restore[key] = (labels, levels)

    def restore(answers_json: dict) -> dict:
        restored = {}
        for provider_key, answer in answers_json.items():
            key = question_restore.get(provider_key, provider_key)
            labels, levels = answer_restore.get(key, ({}, {}))
            item = dict(answer)
            if item.get("type") == "choice":
                item["choice"] = labels.get(
                    item.get("choice"), item.get("choice")
                )
            if isinstance(item.get("probabilities"), dict):
                item["probabilities"] = {
                    labels.get(label, label): probability
                    for label, probability in item["probabilities"].items()
                }
            if item.get("type") == "score" and isinstance(
                item.get("legend"), dict
            ):
                item["legend"] = {
                    label: levels.get(label, description)
                    for label, description in item["legend"].items()
                }
            restored[key] = item
        return restored

    return provider_state, provider_questions, restore
