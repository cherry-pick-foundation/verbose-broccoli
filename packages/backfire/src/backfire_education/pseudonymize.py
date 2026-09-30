"""Replace education identifiers before a judgment reaches its provider."""

from collections import defaultdict
from collections.abc import Callable, Mapping
import dataclasses
import functools
import itertools
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
# Dash-like and zero-width characters read as a hyphen when matching, one for
# one, so "Na‑bit" (U+2011) or "Miraebit‑ro" matches like "Na-bit".
_AS_HYPHEN = str.maketrans(
    dict.fromkeys(
        "\u00ad\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63"
        "\uff0d\u200b\u200c\u200d\u2060\ufeff",
        "-",
    )
)
# Grade number of the first year of each school level.
_LEVEL = {"초": 0, "중": 6, "고": 9, "elementary": 0, "middle": 6, "high": 9}
_ORDINAL = {
    word: number
    for number, word in enumerate(
        "first second third fourth fifth sixth seventh eighth ninth tenth "
        "eleventh twelfth".split(),
        1,
    )
}
_ORDINAL_WORDS = "|".join(_ORDINAL)
# A school year counts up to sixth in "sixth-year elementary school student".
_YEAR_WORDS = "|".join(list(_ORDINAL)[:6])
_UNITS = (
    "one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen"
).split()
# A school year spelled out, as in "Grade ten" or "year eleven".
_CARDINAL = {word: number for number, word in enumerate(_UNITS[:12], 1)}
_CARDINAL_WORDS = "|".join(_CARDINAL)
# Punctuation and Markdown or table markup that may sit between a keyword and
# its value.
_MARKUP = "|*_`~\"'“”‘’"
_PUNCT = "\\-–—:：=>→" + _MARKUP
_US_HIGH = {"freshman": 9, "sophomore": 10, "junior": 11, "senior": 12}
# A month name, capitalized or in capitals, so "may" and "Marching" are not.
_MONTH_NAMES = (
    "Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
    "|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
_MONTH = rf"(?-i:(?:{_MONTH_NAMES}|{_MONTH_NAMES.upper()})\.?)(?![A-Za-z])"
_NUMBER_WORD = (
    rf"(?:zero|nought|oh|{'|'.join(_UNITS)}"
    r"|(?:twen|thir|for|fif|six|seven|eigh|nine)ty|hundred|thousand)(?![A-Za-z])"
)
# A year in words has at least two: nineteen ninety-eight, two thousand and
# eleven, twenty oh one.
_WORD_YEAR = rf"{_NUMBER_WORD}(?:[\s,-]+(?:and[\s-]+)?{_NUMBER_WORD})+"
_ROMAN_YEAR = (
    r"(?-i:M{1,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3}))"
)
# After a birth keyword, the rest of its clause, up to a sentence end, a
# semicolon, a line break or a table cell end (|), is the birth date when it
# holds a digit, a month, a year in words or a Roman numeral year, so no way of
# writing a date escapes. A period inside a date does not end the clause: one
# with no space after it (A.D., 17.VI.2012), one after a month abbreviation
# (Jun. 17), one after a day or month number followed by a digit
# (17. 06. 2012), and one followed by a year or by a short number with no word
# after it (2012. 4. 23., 2012 . 06 . 17, A.D. 2012); "2012. 85 points" ends at
# the period.
_CLAUSE_CHAR = (
    r"(?:[^.!?;|\n\r]|\.(?=\S)"
    r"|(?:(?<=(?<![0-9])[0-9])|(?<=(?<![0-9])[0-9]{2}))\.(?=\s*[0-9])"
    r"|(?:(?<=Jan)|(?<=Feb)|(?<=Mar)|(?<=Apr)|(?<=Jun)|(?<=Jul)|(?<=Aug)|(?<=Sep)|(?<=Sept)|(?<=Oct)|(?<=Nov)|(?<=Dec))\."
    r"|\.(?=\s*(?:[0-9]{1,2}(?![0-9])(?!\s*[A-Za-z%])|[0-9]{4}(?![0-9]))))"
)
_LEADING_WORDS = re.compile(
    r"^(?:(?:on|in|the|is|was|of|year|around|about)\s+)+", re.IGNORECASE
)
_DATE_LIKE = rf"(?:\d|{_MONTH}|{_WORD_YEAR}|{_ROMAN_YEAR}(?![A-Za-z]))"
_BIRTH_CLAUSE = (
    rf"(?={_CLAUSE_CHAR}*?(?<![A-Za-z]){_DATE_LIKE}){_CLAUSE_CHAR}*(?<!\s)"
)
# A romanized road, sub-road, neighbourhood or unit: Ha-neul-ro, 12-gil,
# 45beon-gil, Seo-dong, 101-dong, 1203-ho, Jongno 1-ga.
_ADDRESS_PART = (
    r"(?:\d{1,4}(?:-(?:dong|ho|ga|gil)|beon-gil)"
    r"|[A-Za-z]+(?:-[A-Za-z]+){0,3}-(?:daero|ro|gil|dong|eup|myeon|ri))"
    r"(?![A-Za-z])"
)
# A building, lot or unit number or a postal code; not part of a date
# (Solbit-ro, 2026-09-28).
_ADDRESS_NUMBER = (
    r"(?:(?:apt|apartment|unit|room|rm|suite|ste|building|bldg|block|blk"
    r"|floor|fl|no|house)\.?\s*#?\s*|#\s*)?\d{1,5}(?:-\d{1,4})?"
    r"(?![0-9A-Za-z]|[-./][0-9A-Za-z])"
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


# Field names that say what their value is: DOB, home address, grade.
_QUALIFIER = (
    r"(?:(?:student|child|pupil|guardian|parent|home|current|mailing|street) )?"
)
_FIELDS = (
    (
        "birth",
        re.compile(
            _QUALIFIER
            + r"(?:dob|born|birth ?(?:date|day|year)?|(?:date|year) of birth"
            r"|생년월일|생일|출생)"
        ),
    ),
    ("address", re.compile(_QUALIFIER + r"(?:address|주소)")),
    (
        "cohort",
        re.compile(_QUALIFIER + r"(?:grade(?: level)?|(?:school )?year|학년)"),
    ),
    # A student-number field is not replaced for its name: after the swap its
    # value must be a roster number's stand-in, or the request is refused.
    (
        "number",
        re.compile(
            r"student ?(?:number|no|id)|edu ?ok ?(?:number|no|id)?|학번"
        ),
    ),
)
# A school year alone, as a field value; other numbers there are not one.
_YEAR = re.compile(
    rf"(?:(1[0-2]|[1-9])(?:\.0)?(?:st|nd|rd|th)?|({_ORDINAL_WORDS}"
    rf"|{_CARDINAL_WORDS}))",
    re.IGNORECASE,
)
# A birth-date, address or student-number field in text: the name, then a
# colon, pipe or equals sign, then the value up to the end of its line, cell
# or sentence, or a comma or semicolon.
_FIELD = re.compile(
    r"(?<![A-Za-z])(?<!mail[\s_-])(?:date[\s_-]?of[\s_-]?birth"
    r"|birth[\s_-]?(?:date|day)|dob|생년월일|생일|address|주소"
    r"|student[\s_-]?(?:number|no\.?|id)|edu[\s_-]?ok(?:[\s_-]?(?:number|no\.?"
    rf"|id))?|학번)[\s{_MARKUP}]*[:：|=][\s{_PUNCT}]*+"
    r"(?P<value>(?:[^|\n\r\t,;.]|\.(?!\s|\Z))*)",
    re.IGNORECASE,
)
# The delimiter row under a Markdown table's header row.
_DELIMITER = re.compile(r"(?=[^|]*\|)(?=[^-]*-)[ \t|:-]+")


def _cells(text: str) -> str:
    """Return text with each Markdown table's header row set on its cells.

    A header row becomes "name: cell" lines, one for each cell below it, so a
    field named in a header meets its values.
    """
    lines, cells = text.split("\n"), []
    for index, line in enumerate(lines[1:], 1):
        if "|" in lines[index - 1] and _DELIMITER.fullmatch(line):
            names = lines[index - 1].strip().strip("|").split("|")
            lines[index - 1] = ""
            for row in itertools.takewhile(
                lambda row: "|" in row, lines[index + 1 :]
            ):
                cells.extend(
                    f"{name}: {cell}"
                    for name, cell in zip(
                        names, row.strip().strip("|").split("|")
                    )
                )
    return "\n".join(lines + cells)


def _unfilled(text: str, kind: str | None) -> bool:
    """Return whether a swapped text keeps a birth date, address or number.

    A field keeps its value unless the value is empty, or holds a stand-in
    (blanked) and no digit. The value of a student-number field is the text.
    """
    values = [text] if kind == "number" else []
    values.extend(match["value"] for match in _FIELD.finditer(_cells(text)))
    return any(
        value.strip() and (_BLANK not in value or re.search("[0-9]", value))
        for value in values
    )


def _field_kind(name: object) -> str | None:
    """Return the identifier kind that a field name says its value is."""
    if not isinstance(name, str):
        return None
    words = re.sub(
        r"[\s_.-]+", " ", re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    ).lower()
    return next(
        (kind for kind, pattern in _FIELDS if pattern.fullmatch(words.strip())),
        None,
    )


def _field_spans(
    text: str, kind: str
) -> list[tuple[int, int, tuple[str, str]]]:
    """Return the whole value of a field whose name says it is of ``kind``."""
    match = re.fullmatch(
        rf"[\s{_BLANK}]*(.*?)[\s{_BLANK}]*",
        text,
        re.DOTALL,
    )
    value = match[1] if kind != "number" else None
    if kind == "cohort":
        year = _YEAR.fullmatch(value)
        value = year and (year[1] or _count(year[2]))
    return [(*match.span(1), (kind, _norm(value)))] if value else []


def _row_cells(line: str, separator: str) -> list[tuple[int, int]]:
    """Return the (start, stop) of each cell in a table or CSV row.

    In CSV and TSV a separator inside double quotes belongs to its cell.
    """
    cells, start, quoted = [], 0, False
    for index, char in enumerate(line):
        if char == '"' and separator != "|":
            quoted = not quoted
        elif char == separator and not quoted:
            cells.append((start, index))
            start = index + 1
    cells.append((start, len(line)))
    if separator == "|":
        # The edge cells of "| a | b |" are empty; drop them.
        cells = [
            cell
            for position, cell in enumerate(cells)
            if line[slice(*cell)].strip() or 0 < position < len(cells) - 1
        ]
    return cells


def _column_spans(text: str) -> list[tuple[int, int, tuple[str, str]]]:
    """Return the cells of named columns in Markdown tables, CSV or TSV.

    A header cell that names a school year, birth date, address or student
    number makes the cells below it that kind, row by row until a line
    without the separator: school-year cells when they read as one, the
    others whatever they hold.
    """
    lines, spans, offset = text.split("\n"), [], 0
    starts = []
    for line in lines:
        starts.append(offset)
        offset += len(line) + 1
    for index, header in enumerate(lines):
        for separator in ("|", "\t", ","):
            if separator not in header:
                continue
            # A header is a Markdown row above its delimiter row, or the
            # first line of a CSV or TSV block.
            if separator == "|":
                below = lines[index + 1] if index + 1 < len(lines) else ""
                if not _DELIMITER.fullmatch(below):
                    continue
            elif index and separator in lines[index - 1]:
                continue
            names = [
                _field_kind(header[slice(*cell)].strip(_MARKUP + " \t"))
                for cell in _row_cells(header, separator)
            ]
            if not any(names):
                continue
            for row, line in enumerate(lines[index + 1 :], index + 1):
                if separator not in line:
                    break
                if separator == "|" and _DELIMITER.fullmatch(line):
                    continue
                for kind, (start, stop) in zip(
                    names, _row_cells(line, separator)
                ):
                    cell = line[start:stop]
                    value = cell.strip(_MARKUP + " \t\r")
                    # A blanked stand-in is a value already replaced.
                    if not kind or not value or _BLANK in value:
                        continue
                    first = starts[row] + start + cell.index(value)
                    if kind == "cohort":
                        year = _YEAR.fullmatch(value)
                        if year:
                            spans.append(
                                (
                                    first,
                                    first + len(value),
                                    ("cohort", year[1] or _count(year[2])),
                                )
                            )
                    else:
                        spans.append(
                            (
                                first,
                                first + len(value),
                                (
                                    "student" if kind == "number" else kind,
                                    _norm(value),
                                ),
                            )
                        )
            break
    return spans


def _count(word: str) -> str:
    """Return the number that a numeral, ordinal or cardinal word names."""
    word = word.lower()
    return str(_ORDINAL.get(word) or _CARDINAL.get(word) or word)


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
        re.compile(
            _EDGE.format(
                # Grade 10, Grade: 11th, Grades 10 and 11.
                rf"grades?[\s{_PUNCT}]+(?:(1[0-2]|[1-9])(?:st|nd|rd|th)?"
                rf"|({_CARDINAL_WORDS}))(?![A-Za-z])"
                r"(?:\s*(?:,|and|&|or|to|-|–)\s*(?:1[0-2]|[1-9])(?:st|nd|rd|th)?"
                r"(?![A-Za-z0-9]))*"
            ),
            re.IGNORECASE,
        ),
        0,
        lambda match: _count(match[1] or match[2]),
    ),
    (
        "cohort",
        re.compile(
            _EDGE.format(
                rf"(?:(1[0-2]|[1-9])(?:st|nd|rd|th)|({_ORDINAL_WORDS}))"
                r"[\s-]+grade(?:r)?"
            ),
            re.IGNORECASE,
        ),
        0,
        lambda match: match[1] or str(_ORDINAL[match[2].lower()]),
    ),
    (
        "cohort",
        re.compile(
            _EDGE.format(rf"year[\s{_PUNCT}]+([0-9]{{1,2}}|{_CARDINAL_WORDS})")
            + r"(?![\s-]+(?:thousand|hundred))",
            re.IGNORECASE,
        ),
        0,
        lambda match: f"year {_count(match[1])}",
    ),
    (
        "cohort",
        re.compile(
            _EDGE.format(
                rf"({_YEAR_WORDS})[\s-]year\s+(elementary|middle|high)"
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
            r"(?<![A-Za-z])(?:date[\s_-]?of[\s_-]?birth"
            r"|birth[\s_-]?(?:date|day|year)|born|DOB|생년월일|생일|출생)"
            # Spaces, markup and field punctuation may sit between the keyword
            # and the rest of its clause, and a line break after a colon or
            # after "on", "in" or "the" ("born on" at the end of a line).
            r"(?:[ \t\u00a0\u3000:：=|*_~`>→\-–—,(\[{（［【「\"'“”‘’]"
            r"|(?<=[:：=|])\s*\n"
            r"|(?<![A-Za-z])(?:on|in|the|is|was)[ \t]*\r?\n)*"
            rf"(?P<date>{_BIRTH_CLAUSE})",
            re.IGNORECASE,
        ),
        "date",
        # The value leaves out leading words (on, in the year), so a date
        # gets the stand-in of the same date in a DOB field.
        lambda match: _norm(_LEADING_WORDS.sub("", match["date"])),
    ),
    ("birth", re.compile(r"(?<![0-9])(?:[0-9]{4}|[0-9]{2})년생"), 0, None),
    (
        "address",
        re.compile(
            rf"(?<![A-Za-z])(?:address|주소)[\s{_PUNCT}]*"
            rf"(?P<rest>[^\s{_PUNCT}{_BLANK}][^\n\r\t|{_BLANK}]*?)"
            rf"(?=[\s{_MARKUP}]*(?:[\n\r\t|{_BLANK}]|\Z))",
            re.IGNORECASE,
        ),
        "rest",
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


@functools.cache
def _address_pattern() -> re.Pattern[str]:
    """Build the regex for a romanized address run.

    A run is address parts with the numbers, postal codes and region names
    around them, separated by spaces or commas; it holds at least one part.
    """
    token = (
        rf"(?:{_ADDRESS_PART}|{_ADDRESS_NUMBER}|{_region_pattern().pattern})"
    )
    return re.compile(
        rf"(?<![A-Za-z0-9])(?:{token}[\s,]+){{0,6}}(?:{_ADDRESS_PART})"
        rf"(?:[\s,]+{token})*",
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
    kind: str | None = None,
) -> list[tuple[int, int, tuple[str, str]]]:
    """Find identifier spans, merging overlapping matches.

    Finds roster text, phone numbers, email addresses, school years, domain
    IDs, birth dates, addresses and regions.

    Args:
        text: Text to search.
        identifiers: Map from roster text to its identifier kind and value.
        roster_pattern: Compiled pattern for roster text, or None.
        name_pattern: Compiled pattern for flexible Latin names, or None.
        kind: The identifier kind that the text's field name says it is
            (birth, address, cohort or number), or None. The whole text is
            then one span of that kind; a number is found as any text is.

    Returns:
        A list of (start, stop, identifier) tuples; every value except a
        roster one is normalized.

    Raises:
        ImportError: If the optional phonenumbers package is unavailable.
    """
    # Optional dependency.
    import phonenumbers  # noqa: PLC0415

    if kind is not None and (span := _field_spans(text, kind)):
        return span
    text = text.translate(_AS_HYPHEN)
    # Roster matches (rank 0) win over column cells at the same place.
    candidates = [(*span, 2) for span in _column_spans(text)]
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
    detectors = [
        *_DETECTORS,
        ("address", _address_pattern(), 0, None),
        ("region", _region_pattern(), 0, None),
    ]
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


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _text(value):
    """Return the text of a key or number; 7700101.0 reads as 7700101."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _inner_kind(kind, key):
    """Return the kind of a value under ``key`` inside a value of ``kind``.

    Everything inside a birth date, an address or a student number is one; a
    field named inside a school year keeps the kind its name gives.
    """
    return (
        kind
        if kind in {"birth", "address", "number"}
        else (_field_kind(key) or kind)
    )


def fields(value, kind=None):
    """Yield (text, kind) for every string and number in a state or question.

    Numbers and other keys come as their text. A value or key under a key
    that names a kind (DOB, address, grade, student ID) carries it, at any
    depth.
    """
    if hasattr(value, "model_dump"):
        yield from fields(value.model_dump(mode="json"), kind)
    elif isinstance(value, str):
        yield value, kind
    elif _is_number(value):
        yield _text(value), kind
    elif isinstance(value, Mapping):
        for key, item in value.items():
            yield _text(key), kind
            yield from fields(item, _inner_kind(kind, key))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from fields(item, kind)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from fields(
                getattr(value, field.name), _inner_kind(kind, field.name)
            )


def strings(value):
    """Yield every string and number, as text, dictionary keys included."""
    return (text for text, _ in fields(value))


def _replace_tree(value, replace, kind=None):
    if isinstance(value, str):
        return replace(value, kind)
    if _is_number(value):
        text = _text(value)
        replaced = replace(text, kind)
        return value if replaced == text else replaced
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            text = _text(key)
            new_key = replace(text, kind)
            new_key = key if new_key == text else new_key
            if new_key in result:
                raise JudgmentError("pseudonym_conflict")
            result[new_key] = _replace_tree(
                item, replace, _inner_kind(kind, key)
            )
        return result
    if isinstance(value, list):
        return [_replace_tree(item, replace, kind) for item in value]
    if isinstance(value, tuple):
        return tuple(_replace_tree(item, replace, kind) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.replace(
            value,
            **{
                field.name: _replace_tree(
                    getattr(value, field.name),
                    replace,
                    _inner_kind(kind, field.name),
                )
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

    def cached_spans(text, kind):
        if (text, kind) not in spans_by_text:
            spans_by_text[text, kind] = find_spans(
                text, identifiers, roster_pattern, name_pattern, kind
            )
        return spans_by_text[text, kind]

    values = [state]
    for key, _, _, document in question_items:
        values.extend((key, document))
    seen, to_assign = set(), []
    for value in values:
        for text, kind in fields(value):
            for _, _, identifier in cached_spans(text, kind):
                if identifier not in seen:
                    seen.add(identifier)
                    to_assign.append(identifier)
    pseudonyms = assign(to_assign)

    def replace(text, kind=None):
        parts, offset = [], 0
        for start, stop, identifier in cached_spans(text, kind):
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
        for text, kind in fields(value):
            text = standin.sub(_BLANK, text) if pseudonyms else text
            if _unfilled(text, kind) or find_spans(
                text, identifiers, roster_pattern, name_pattern, kind
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
