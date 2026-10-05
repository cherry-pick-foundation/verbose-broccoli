"""Per-call masking for JSON trees, including dictionary keys and result text.

Use ``with Masker(registry) as call`` around preflight, forwarding and restore.
``mask(arguments, constrained=predicate)`` calls predicate(path) for each string
value or key; paths contain original keys/list indices. A schema-pattern field
containing an identifier rejects, otherwise stays unchanged. The proxy owns
schema lookup/validation and converts MCP models to/from JSON-compatible dicts.
``restore(result)`` covers text blocks, structured content, meta and arbitrary
usage by walking the complete JSON tree, decoding nested JSON strings too.
A unique complete echoed string/key anchors exact restoration; ambiguous echoes
and newly composed prose use registered Latin spelling, then Hangul fallback.
Ten-digit JSON integers (excluding bools/floats) become EduOK label strings;
restoration returns their decimal text. Typed numeric fields therefore fail the
proxy's unchanged upstream schema validation. Other numeric values keep types.
Never log request/result/error objects; clear maps in finally on every exit.
"""

from bisect import bisect_left
from collections import Counter
import json
import math
import re
from unicodedata import normalize

from faker import Faker
import phonenumbers

from education_privacy_gate.roster import GateError

_PATTERNS = [
    (
        "Resident number",
        re.compile(r"(?<![0-9])[0-9]{6}[- ]?[0-9]{7}(?![0-9])"),
        0,
        0,
    ),
    (
        "EduOK",
        re.compile(
            r"(?<![0-9])[0-9]{10}(?![0-9])",
            re.I,
        ),
        0,
        1,
    ),
    (
        "Email",
        re.compile(
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
        ),
        0,
        3,
    ),
]
_HYPHENS = str.maketrans(
    dict.fromkeys(
        "\u00ad\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63"
        "\uff0d\u200b\u200c\u200d\u2060\ufeff",
        "-",
    )
)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GateError()
        result[key] = value
    return result


def _walk(value, replace, path=(), depth=0, decode=False, numbers=False):
    if depth > 64:
        raise GateError()
    if isinstance(value, str):
        value.encode("utf-8")
        if decode:
            try:
                parsed = json.loads(value, object_pairs_hook=_pairs)
            except ValueError, RecursionError:
                parsed = None
            if parsed is not None:
                restored = _walk(parsed, replace, path, depth + 1, True)
                return (
                    value
                    if restored == parsed
                    else json.dumps(
                        restored, ensure_ascii=False, allow_nan=False
                    )
                )
        return replace(value, path, False)
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise GateError()
            new_key = _walk(
                key, replace, path + (key,), depth + 1, decode, numbers
            )
            if new_key in result:
                raise GateError()
            result[new_key] = _walk(
                item, replace, path + (key,), depth + 1, decode, numbers
            )
        return result
    if isinstance(value, list):
        return [
            _walk(item, replace, path + (i,), depth + 1, decode, numbers)
            for i, item in enumerate(value)
        ]
    if numbers and type(value) is int and 10**9 <= abs(value) < 10**10:
        return replace(str(value), path, True)
    if (
        value is None
        or type(value) in (bool, int)
        or (type(value) is float and math.isfinite(value))
    ):
        return value
    raise GateError()


class Masker:
    """One isolated Faker generator and memory-only reversible call map."""

    def __init__(self, registry):
        self.registry = registry
        self.faker = Faker()
        self.faker.seed_instance(None)
        self.reverse = {}
        self.anchors = {}
        self.assigned = {}
        self.originals = ()
        self.masked = False

    def __enter__(self):
        return self

    def __exit__(self, unused_type, unused_error, unused_traceback):
        self.clear()

    def clear(self):
        """Release all per-call original/fake pairs, including echo anchors."""
        self.reverse.clear()
        self.anchors.clear()
        self.assigned.clear()
        self.originals = ()

    def _spans(self, text):
        candidates = []
        normalized = text.translate(_HYPHENS)
        for matcher in self.registry.matches:
            for match in matcher.pattern.finditer(normalized):
                identity = matcher.identity
                if identity[0] == "school":
                    identity = ("School", text[match.start() : match.end()])
                candidates.append((*match.span(), identity, matcher.rank))
        for label, pattern, group, rank in _PATTERNS:
            candidates.extend(
                (*m.span(group), (label, m[group]), rank)
                for m in pattern.finditer(text)
            )
        selected = [
            (m.start, m.end, ("Phone", m.raw_string))
            for m in phonenumbers.PhoneNumberMatcher(text, "KR")
        ]
        selected.sort()
        for start, end, identity, unused_rank in sorted(
            candidates,
            key=lambda item: (-(item[1] - item[0]), item[3], item[0]),
        ):
            position = bisect_left(selected, (start,))
            if (position == 0 or selected[position - 1][1] <= start) and (
                position == len(selected) or end <= selected[position][0]
            ):
                # ponytail: list insertion; interval index if profiling demands.
                selected.insert(position, (start, end, identity))
        return selected

    def _collision(self, candidate):
        texts = (
            *self.registry.spellings,
            *(
                token
                for token in self.reverse
                if not (candidate[-1:].isdigit() and token[-1:].isdigit())
            ),
        )
        folded = normalize("NFC", candidate).casefold()
        return (
            not candidate
            or bool(self._spans(candidate))
            or any(
                folded in normalize("NFC", text).casefold()
                for text in self.originals
            )
            or any(
                folded in normalize("NFC", text).casefold()
                or normalize("NFC", text).casefold() in folded
                for text in texts
                if text
            )
        )

    def mask(self, arguments, constrained=lambda unused_path: False):
        """Preflight the whole request before creating the forwarded tree."""
        try:
            if self.masked:
                raise GateError()
            self.masked = True
            texts, spans = [], {}

            def collect(text, path, number):
                found = (
                    [(0, len(text), ("EduOK", text))]
                    if number
                    else self._spans(text)
                )
                if found and constrained(path):
                    raise GateError()
                texts.append(text)
                spans[text, number] = found
                return text

            _walk(arguments, collect, numbers=True)
            self.originals = tuple(texts)
            defaults = dict(self.registry.defaults)
            counts = Counter()
            for found in spans.values():
                for unused_start, unused_end, identity in found:
                    if identity in self.assigned:
                        continue
                    if len(self.assigned) >= 128:
                        raise GateError()
                    numbered = identity[0] not in {"person", "given"}
                    original = identity[1] if numbered else defaults[identity]
                    for unused_attempt in range(256):
                        if numbered:
                            counts[identity[0]] += 1
                            candidate = (
                                f"{identity[0]} {counts[identity[0]]:02d}"
                            )
                            # Number reversal uses digit boundaries.
                        else:
                            candidate = self.faker.first_name()
                        if not self._collision(candidate):
                            break
                    else:
                        raise GateError()
                    self.assigned[identity] = candidate
                    self.reverse[candidate] = original

            def replace(text, unused_path, number):
                parts, offset = [], 0
                for start, end, identity in spans[text, number]:
                    parts.extend((text[offset:start], self.assigned[identity]))
                    offset = end
                masked = "".join([*parts, text[offset:]])
                prior = self.anchors.get(masked, text)
                self.anchors[masked] = text if prior == text else None
                return masked

            masked = _walk(arguments, replace, numbers=True)
            self.originals = ()
            return masked
        except GateError, ValueError, TypeError, RecursionError, UnicodeError:
            self.clear()
            raise GateError() from None

    def restore(self, result):
        """Restore every string/key, decoding JSON text before matching."""
        try:
            if not self.masked:
                raise GateError()
            # Bound the tree before serialization and JSON-text decoding.
            _walk(result, lambda text, unused_path, unused_number: text)
            pattern = (
                re.compile(
                    "|".join(
                        (
                            re.escape(token) + r"(?![0-9])"
                            if token[-1:].isdigit()
                            else r"(?<![A-Za-z0-9])"
                            + re.escape(token)
                            + r"(?![A-Za-z0-9])"
                        )
                        for token in sorted(self.reverse, key=len, reverse=True)
                    )
                )
                if self.reverse
                else None
            )

            def replace(text, unused_path, unused_number):
                anchor = self.anchors.get(text)
                if anchor is not None:
                    return anchor
                return (
                    pattern.sub(lambda m: self.reverse[m[0]], text)
                    if pattern
                    else text
                )

            restored = _walk(result, replace, decode=True)
            return restored
        except GateError, ValueError, TypeError, RecursionError, UnicodeError:
            self.clear()
            raise GateError() from None
