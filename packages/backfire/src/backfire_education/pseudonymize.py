"""Replace education identifiers before a judgment reaches its provider."""

from collections import defaultdict
from collections.abc import Callable, Mapping
import dataclasses
import functools
import json
from pathlib import Path
import re
from typing import Any

from backfire.config import SHIPPED_CONFIG
from backfire.failures import JudgmentError
from backfire_education.roster import load_roster
from backfire_education.table import assign

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
__all__ = [
    "compile_name_pattern",
    "compile_roster_pattern",
    "find_spans",
    "pseudonymize",
    "strings",
]

# A Latin pattern never matches inside a longer word or number.
_EDGE = r"(?<![A-Za-z0-9]){}(?![A-Za-z0-9])"
_LATIN_NAME = re.compile(r"[A-Za-z]+(?:[ -][A-Za-z]+)*")
_SEPARATOR = r"[\s,-]*"
# The re-scan blanks each stand-in with this; keyword patterns skip it.
_BLANK = "\x00"
# Grade number of the first year of each school level.
_LEVEL = {"초": 0, "중": 6, "고": 9, "elementary": 0, "middle": 6, "high": 9}
_ORDINAL = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
_US_HIGH = {"freshman": 9, "sophomore": 10, "junior": 11, "senior": 12}
_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
_DATE = (
    r"\d{4}[-./]\d{1,2}[-./]\d{1,2}|\d{2}[-./]\d{1,2}[-./]\d{1,2}"
    rf"|{_MONTH}\s+(?:\d{{1,2}}(?:st|nd|rd|th)?,?\s+)?\d{{4}}"
    rf"|\d{{1,2}}(?:st|nd|rd|th)?\s+(?:of\s+)?{_MONTH},?\s+\d{{4}}"
    r"|\d{4}년\s*\d{1,2}월\s*\d{1,2}일|\d{4}년?"
)
_ADDRESS_PART = (
    r"\d{1,4}-(?:dong|ho)"
    r"|(?:[A-Za-z]+|\d+beon)-(?:daero|ro|gil|dong|eup|myeon|ri)"
    r"(?:\s*\d+(?:-\d+)?(?![0-9]|beon))?"
)
_REGION_UNITS = (
    "special self-governing province",
    "special self-governing city",
    "metropolitan city",
    "special city",
    "province",
    "county",
    "district",
    "city",
    "state",
)


def _norm(text: str) -> str:
    return " ".join(text.split()).lower()


def _first_group(match: re.Match[str]) -> str:
    return match[1]


# (kind, pattern, group that is replaced, value of a match; None: the
# replaced text, normalized)
_DETECTORS = [
    (
        "cohort",
        re.compile(r"(?<![0-9])(?:예비\s*)?([초중고])([1-6])(?![0-9])"),
        0,
        lambda match: str(_LEVEL[match[1]] + int(match[2])),
    ),
    (
        "cohort",
        re.compile(r"(?<![0-9])([1-6])학년(?!도)"),
        0,
        lambda match: f"year {match[1]}",
    ),
    (
        "cohort",
        re.compile(_EDGE.format(r"grade\s+(1[0-2]|[1-9])"), re.IGNORECASE),
        0,
        _first_group,
    ),
    (
        "cohort",
        re.compile(
            _EDGE.format(r"(1[0-2]|[1-9])(?:st|nd|rd|th)[\s-]+grade(?:r)?"),
            re.IGNORECASE,
        ),
        0,
        _first_group,
    ),
    (
        "cohort",
        re.compile(_EDGE.format(r"year\s+([0-9]{1,2})"), re.IGNORECASE),
        0,
        lambda match: f"year {match[1]}",
    ),
    (
        "cohort",
        re.compile(
            _EDGE.format(
                r"(first|second|third)[\s-]year\s+(elementary|middle|high)"
                r"[\s-]school(?:\s+student)?"
            ),
            re.IGNORECASE,
        ),
        0,
        lambda match: str(
            _LEVEL[match[2].lower()] + _ORDINAL[match[1].lower()]
        ),
    ),
    (
        "cohort",
        re.compile(
            _EDGE.format(
                r"high[\s-]school\s+(freshman|sophomore|junior|senior)"
            ),
            re.IGNORECASE,
        ),
        0,
        lambda match: str(_US_HIGH[match[1].lower()]),
    ),
    (
        "school",
        re.compile(
            r"(?<![A-Za-z0-9-])[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[hme]"
            r"(?![A-Za-z0-9-])"
        ),
        0,
        None,
    ),
    (
        "birth",
        re.compile(
            r"(?<![A-Za-z])(?:date of birth|birthday|born|DOB|"
            r"생년월일|생일|출생)"
            r"[\s:：,(-]{0,6}(?:(?:is|was|on|in)\s+)?"
            rf"(?P<date>{_DATE})(?![0-9])",
            re.IGNORECASE,
        ),
        "date",
        None,
    ),
    ("birth", re.compile(r"(?<![0-9])(?:[0-9]{4}|[0-9]{2})년생"), 0, None),
    (
        "address",
        re.compile(
            r"(?<![A-Za-z])(?:address|주소)\s*[:：=]?\s*"
            rf"(?P<rest>[^\s|:：={_BLANK}][^\n\r\t|{_BLANK}]*)",
            re.IGNORECASE,
        ),
        "rest",
        None,
    ),
    (
        "address",
        re.compile(
            rf"(?<![A-Za-z0-9])(?:\d{{5}}[\s,]+)?(?:{_ADDRESS_PART})"
            rf"(?:[\s,]+(?:{_ADDRESS_PART}))*(?:[\s,]+\d{{5}}(?![0-9]))?",
            re.IGNORECASE,
        ),
        0,
        None,
    ),
]


@functools.cache
def _region_pattern() -> re.Pattern[str]:
    """Build the regex for the generated list of province and district names."""
    path = Path(__file__).with_name("regions.json")
    forms = sorted(
        json.loads(path.read_text(encoding="utf-8")),
        key=lambda form: (-len(form), form),
    )
    latin = "|".join(re.escape(form) for form in forms if form.isascii())
    korean = "|".join(re.escape(form) for form in forms if not form.isascii())
    units = "|".join(re.escape(unit) for unit in _REGION_UNITS)
    return re.compile(
        _EDGE.format(rf"(?:{latin})(?:\s+(?:{units}))?") + f"|{korean}",
        re.IGNORECASE,
    )


def _forms(name: str) -> list[str]:
    """Return patterns for a Latin name, hyphenated or not, surname either end.

    Args:
        name: Letters in words separated by spaces or hyphens; the first word
            is the surname, or the whole name when there is one word.

    Returns:
        Patterns that each start with a letter.
    """
    surname, *rest = re.split(r"[ -]", name)
    given = "[- ]?".join("".join(rest) or surname)
    if not rest:
        return [given]
    return [
        f"{surname}{_SEPARATOR}{given}",
        f"{given}{_SEPARATOR}{surname}",
    ]


def compile_name_pattern(
    identifiers: Mapping[str, tuple[str, str]],
) -> re.Pattern[str] | None:
    """Build a regex for Latin student names in their flexible spellings.

    A name matches in any case, with or without a hyphen or space inside the
    given name, and with the surname first or last, only as whole words. Each
    spelling is a group named after its roster text in hex, so find_spans can
    look the identifier up.

    Args:
        identifiers: Map from roster text to its identifier kind and value.

    Returns:
        A compiled regex, or None when the roster has no Latin student names.
    """
    names = sorted(
        (
            value
            for value, (kind, _) in identifiers.items()
            if kind in {"student", "given"} and _LATIN_NAME.fullmatch(value)
        ),
        # Names of several words first, so a surname is not left behind.
        key=lambda value: (value.isalpha(), -len(value), value),
    )
    # Bucketing by first letter keeps matching fast: the regex engine skips a
    # bucket whose letter is not the next one.
    buckets = defaultdict(list)
    for value in names:
        for index, form in enumerate(_forms(value)):
            buckets[form[0].lower()].append(
                f"(?P<n{value.encode().hex()}_{index}>{form[1:]})"
            )
    if not buckets:
        return None
    return re.compile(
        _EDGE.format(
            "(?:"
            + "|".join(
                f"[{letter}{letter.upper()}](?i:{'|'.join(forms)})"
                for letter, forms in buckets.items()
            )
            + ")"
        )
    )


def compile_roster_pattern(
    identifiers: Mapping[str, tuple[str, str]],
) -> re.Pattern[str] | None:
    """Build a regex for roster identifiers.

    Latin names match only as whole words, and numbers only as whole digit
    runs. Everything else is exact. Alternatives are longest first.

    Args:
        identifiers: Map from roster text to its identifier kind and value.

    Returns:
        A compiled regex, or None when there are no identifiers.
    """
    if not identifiers:
        return None
    ordered = sorted(identifiers, key=lambda item: (-len(item), item))
    groups = [
        (r"(?<![A-Za-z0-9]){}(?![A-Za-z0-9])", _LATIN_NAME.fullmatch),
        (
            r"(?<![0-9]){}(?![0-9])",
            lambda value: value.isascii() and value.isdigit(),
        ),
    ]
    alternatives = []
    for edge, belongs in groups:
        members = [value for value in ordered if belongs(value)]
        if members:
            alternatives.append(
                edge.format("(?:" + "|".join(map(re.escape, members)) + ")")
            )
            ordered = [value for value in ordered if value not in members]
    alternatives.extend(map(re.escape, ordered))
    return re.compile("|".join(alternatives))


def find_spans(
    text: str,
    identifiers: Mapping[str, tuple[str, str]],
    roster_pattern: re.Pattern[str] | None,
    name_pattern: re.Pattern[str] | None = None,
) -> list[tuple[int, int, tuple[str, str]]]:
    """Find identifier spans, merging overlapping matches.

    Finds roster text, phone numbers, email addresses, school years, domain
    IDs, birth dates, addresses and regions.

    Args:
        text: Text to search.
        identifiers: Map from roster text to its identifier kind and value.
        roster_pattern: Compiled pattern for roster text, or None.
        name_pattern: Compiled pattern for flexible Latin names, or None.

    Returns:
        A list of (start, stop, identifier) tuples; every value except a
        roster one is normalized.

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
    if name_pattern is not None:
        for match in name_pattern.finditer(text):
            roster_text = bytes.fromhex(match.lastgroup[1:].split("_")[0])
            candidates.append(
                (
                    match.start(),
                    match.end(),
                    identifiers[roster_text.decode()],
                    0,
                )
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
    detectors = [*_DETECTORS, ("region", _region_pattern(), 0, None)]
    for rank, (kind, pattern, group, value) in enumerate(detectors, 3):
        candidates.extend(
            (
                *match.span(group),
                (kind, value(match) if value else _norm(match[group])),
                rank,
            )
            for match in pattern.finditer(text)
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


def strings(value):
    """Yield every string in a state or question, dictionary keys included."""
    if hasattr(value, "model_dump"):
        yield from strings(value.model_dump(mode="json"))
    elif isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from strings(item)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from strings(getattr(value, field.name))


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
    name_pattern = compile_name_pattern(identifiers)
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
        spans_by_text[text] = find_spans(
            text, identifiers, roster_pattern, name_pattern
        )
        return spans_by_text[text]

    values = [state]
    for key, _, _, document in question_items:
        values.extend((key, document))
    seen, to_assign = set(), []
    for value in values:
        for text in strings(value):
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
    provider_documents = []
    question_restore = {}
    answer_restore = {}
    for key, _, question_class, document in question_items:
        provider_key = replace(key)
        if provider_key in provider_questions:
            raise JudgmentError("pseudonym_conflict")
        provider_document = _replace_tree(document, replace)
        provider_documents.append((provider_key, provider_document))
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

    # Scan the swapped request again, with this call's stand-ins blanked out.
    standin = re.compile(
        "|".join(
            re.escape(label)
            for label in sorted(set(pseudonyms.values()), key=len, reverse=True)
        )
    )
    for value in (provider_state, provider_documents):
        for text in strings(value):
            if find_spans(
                standin.sub(_BLANK, text) if pseudonyms else text,
                identifiers,
                roster_pattern,
                name_pattern,
            ):
                raise JudgmentError("identifier_remaining")

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
