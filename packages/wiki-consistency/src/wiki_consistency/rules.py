"""Check agent-written Wiki text against the page-rule contract."""

from bisect import bisect_right
from datetime import date
from pathlib import Path
import re
import unicodedata

import yaml
from backfire.failures import JudgmentError
from backfire_education.pseudonymize import compile_roster_pattern, find_spans
from backfire_education.roster import load_roster
from doc_regions.config import files
from doc_regions.regions import scan
from yaml.nodes import MappingNode, ScalarNode


_MESSAGES = {
    "phone": "pages hold no phone numbers",
    "email": "pages hold no email addresses",
    "id-number": "pages hold no resident or foreign registration numbers",
    "address": "pages hold no postal addresses",
    "student-roster": "add the student to the backfire roster or fix the page name",
    "english": "write pages in English",
    "school": "write the school as its domain ID",
    "date": "write dates as YYYY-MM-DD",
    "time": "write the time with its time zone",
}
_CJK_PREFIXES = (
    "HANGUL", "CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH",
    "HIRAGANA", "KATAKANA", "HALFWIDTH HANGUL", "HALFWIDTH KATAKANA",
)
_QUOTES = (("\"", "\""), ("“", "”"), ("‘", "’"), ("「", "」"), ("『", "』"))
_QUOTE_OPENERS = frozenset(opening for opening, _ in _QUOTES)
_ID_NUMBER = re.compile(r"(?<![0-9])([0-9]{6})-?([1-8])([0-9]{6})(?![0-9])")
_HANGUL_ADDRESS = re.compile(r"(?<![가-힣])[가-힣]+(?:대로|로|길)[ ]*[0-9]+(?:-[0-9]+)?(?![0-9])")
_NUMBER = r"[0-9]+(?:-[0-9]+)?"
_ROAD = r"[A-Z][A-Za-z]*(?:-[A-Z][A-Za-z]*)*-(?:ro|daero|gil)"
_ROAD_ADDRESS = (
    re.compile(rf"(?<![A-Za-z0-9]){_NUMBER}[ ]*,?[ ]+{_ROAD}(?![A-Za-z0-9-])"),
    re.compile(rf"(?<![A-Za-z0-9-]){_ROAD}[ ]+{_NUMBER}(?![0-9])"),
)
_LOT_ADDRESS = re.compile(rf"(?<![0-9]){_NUMBER}[ ]*번지(?![0-9])")
_ROMANIZED_SCHOOL = re.compile(
    r"(?<![A-Za-z])(?:[A-Z][A-Za-z]*[ ]+)+(?:Elementary|Middle|High)[ ]+School(?![A-Za-z])"
)
_ISO_DATE = re.compile(r"(?<![0-9])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])")
_DATE_PATTERNS = (
    re.compile(r"(?<![0-9])[0-9]{4}[./][0-9]{1,2}[./][0-9]{1,2}(?![0-9])"),
    re.compile(r"(?<![0-9])([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9]{1,2}([./-])[0-9]{1,2}\1[0-9]{4}(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9]{1,2}/[0-9]{1,2}/[0-9]{2}(?![0-9])"),
    re.compile(
        r"(?<![A-Za-z0-9])(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December|Sept|Sep|Jan|Feb|Mar|Apr|Jun|Jul|"
        r"Aug|Oct|Nov|Dec)\.?[ ]+[0-9]{1,2}(?:st|nd|rd|th)?"
        r"(?:,?[ ]+[0-9]{4})?(?![A-Za-z0-9])"
    ),
    re.compile(
        r"(?<![A-Za-z0-9])[0-9]{1,2}(?:st|nd|rd|th)?[ ]+(?:of[ ]+)?"
        r"(?:January|February|March|April|May|June|July|August|September|"
        r"October|November|December|Sept|Sep|Jan|Feb|Mar|Apr|Jun|Jul|Aug|"
        r"Oct|Nov|Dec)\.?(?:,?[ ]+[0-9]{4})?(?![A-Za-z0-9])"
    ),
    re.compile(r"(?<![0-9])[0-9]{1,4}[ ]*년[ ]*[0-9]{1,2}[ ]*월(?:[ ]*[0-9]{1,2}[ ]*일)?(?![0-9])"),
    re.compile(r"(?<![0-9])[0-9]{1,2}[ ]*월[ ]*[0-9]{1,2}[ ]*일(?![0-9])"),
)
_DATE_SKIP = (
    re.compile(r"https?://\S+"),
    re.compile(r"<[^>\n]*>"),
    re.compile(r"\]\((?:\\.|[^)\n])*\)"),
)
_TIME = re.compile(
    r"(?<![0-9:])(?:(?P<clock_hour>[0-9]{1,2}):(?P<minute>[0-9]{2})"
    r"(?::(?P<second>[0-9]{2}))?(?:[ ]*(?P<clock_suffix>AM|PM|a\.m\.|p\.m\.))?"
    r"|(?P<meridiem_hour>[0-9]{1,2})[ ]*(?P<suffix>AM|PM|a\.m\.|p\.m\.))"
    r"(?![0-9:])"
)
_NUMERIC_ZONE = re.compile(r"[+-][0-9]{2}:?[0-9]{2}(?![0-9])")
_OFFSET_PREFIX = re.compile(
    r"(?P<clock>(?<![0-9:])(?:[0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?"
    r"|[0-9]{1,2}[ ]*(?:AM|PM|a\.m\.|p\.m\.))"
    r"(?:[ ]*(?:AM|PM|a\.m\.|p\.m\.))?)(?P<spaces>[ ]*)(?P<sign>[+-])$"
)
_UTC_ZONE = re.compile(r"(?:UTC(?:[+-][0-9]{1,2}(?::[0-9]{2})?)?|\(UTC(?:[+-][0-9]{1,2}(?::[0-9]{2})?)?\))(?![A-Za-z0-9])")
_RANGE_JOINER = re.compile(r"[ ]*(?:-|–|—|to)[ ]*")


def _is_cjk(character):
    return character.isalpha() and unicodedata.name(character, "").startswith(_CJK_PREFIXES)


def _is_latin(character):
    return character.isalpha() and unicodedata.name(character, "").startswith("LATIN ")


def _sources_lines(text):
    lines = text.split("\n")
    if not lines or lines[0].removesuffix("\r") != "---":
        return None
    end = next((index for index in range(1, len(lines))
                if lines[index].removesuffix("\r") == "---"), None)
    if end is None:
        return None
    try:
        node = yaml.compose("\n".join(lines[1:end]))
    except yaml.YAMLError:
        return None
    if not isinstance(node, MappingNode):
        return None
    for key, value in node.value:
        if isinstance(key, ScalarNode) and key.value == "sources":
            start = 1 + key.start_mark.line
            stop = 1 + value.end_mark.line + bool(value.end_mark.column)
            return start, stop
    return None


def _blank_lines(text, ranges):
    lines = text.split("\n")
    for start, stop in ranges:
        for index in range(start, min(stop, len(lines))):
            lines[index] = "\r" if lines[index].endswith("\r") else ""
    return "\n".join(lines)


def _checked_text(document, text):
    spans, _ = scan(document, text)
    ranges = [(span["start"], span["end"]) for span in spans]
    source_lines = _sources_lines(text)
    if source_lines is not None:
        ranges.append(source_lines)
    return _blank_lines(text, ranges)


def _line_starts(text):
    return [0, *(index + 1 for index, character in enumerate(text) if character == "\n")]


def _line_number(starts, offset):
    return bisect_right(starts, offset)


def _mark(length, spans):
    marked = bytearray(length)
    for start, stop in spans:
        marked[start:stop] = b"\x01" * (stop - start)
    return marked


def _quoted_at(line, start):
    for opening, closing in _QUOTES:
        if line.startswith(opening, start):
            content_start = start + len(opening)
            content_end = line.find(closing, content_start)
            if content_end >= 0:
                return start, content_end + len(closing), content_start, content_end
    return None


def _space_end(line, position):
    while position < len(line) and line[position] == " ":
        position += 1
    return position


def _translation_ok(text, start, stop, name_marks):
    value = text[start:stop]
    return (any(_is_latin(character) for character in value)
            and not any(_is_cjk(character) and not name_marks[index]
                        for index, character in enumerate(value, start)))


def _quote_origin(line, base, first, name_marks):
    first_content = line[first[2]:first[3]]
    is_original = (len(first_content) <= 100
                   and any(_is_cjk(character) for character in first_content))
    position = _space_end(line, first[1])
    if position >= len(line) or line[position] != "(":
        return None
    inside = _space_end(line, position + 1)
    quoted = _quoted_at(line, inside)
    if is_original:
        if quoted:
            translation_start, translation_stop = quoted[2], quoted[3]
            after = _space_end(line, quoted[1])
            if after >= len(line) or line[after] != ")":
                return None
        else:
            close = line.find(")", inside)
            if close < 0:
                return None
            translation_start = inside
            translation_stop = close
            while translation_stop > translation_start and line[translation_stop - 1] == " ":
                translation_stop -= 1
        if _translation_ok(line, translation_start, translation_stop,
                           name_marks[base:base + len(line)]):
            return base + first[2], base + first[3]
        return None
    if not quoted:
        return None
    after = _space_end(line, quoted[1])
    if after >= len(line) or line[after] != ")":
        return None
    if not _translation_ok(line, first[2], first[3], name_marks[base:base + len(line)]):
        return None
    original = line[quoted[2]:quoted[3]]
    if len(original) <= 100 and any(_is_cjk(character) for character in original):
        return base + quoted[2], base + quoted[3]
    return None


def _allowed_originals(text, name_marks):
    result = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        for position, character in enumerate(line):
            if character not in _QUOTE_OPENERS:
                continue
            quoted = _quoted_at(line, position)
            if quoted:
                original = _quote_origin(line, offset, quoted, name_marks)
                if original is not None:
                    result.append(original)
        offset += len(raw_line)
    return result


def _dates(text):
    masked = list(text)
    for pattern in _DATE_SKIP:
        for match in pattern.finditer(text):
            start, stop = match.span()
            if pattern is _DATE_SKIP[2]:
                start += 2
                stop -= 1
            for index in range(start, stop):
                if masked[index] not in "\r\n":
                    masked[index] = " "
    source = "".join(masked)
    for match in _ISO_DATE.finditer(source):
        try:
            date.fromisoformat(match[0])
        except ValueError:
            yield match.start()
    for index, pattern in enumerate(_DATE_PATTERNS):
        for match in pattern.finditer(source):
            if index == 1 and len(match[2]) == len(match[3]) == 2:
                continue
            yield match.start()


def _time_tokens(text):
    for match in _TIME.finditer(text):
        prefix_text = text[max(0, match.start() - 32):match.start()]
        prefix = _OFFSET_PREFIX.search(prefix_text)
        if prefix:
            follows_t = (prefix.start("clock") > 0
                         and prefix_text[prefix.start("clock") - 1] == "T")
            if prefix["sign"] == "+" or prefix["spaces"] or follows_t:
                continue
        hour = int(match["clock_hour"] or match["meridiem_hour"])
        minute = int(match["minute"] or 0)
        second = int(match["second"] or 0)
        if match["minute"] is None:
            if not 1 <= hour <= 12:
                continue
        elif hour > 23 or minute > 59 or second > 59:
            continue
        yield match.start(), match.end()


def _has_zone(text, start, stop):
    suffix = text[stop:]
    spaces = len(suffix) - len(suffix.lstrip(" "))
    tail = suffix[spaces:]
    direct = spaces == 0
    if direct and tail.startswith("Z") and (len(tail) == 1 or not tail[1].isalnum()):
        return True
    numeric = _NUMERIC_ZONE.match(tail)
    if numeric and (numeric.end() == len(tail)
                    or not tail[numeric.end()].isalnum()):
        follows_t = start > 0 and text[start - 1] == "T"
        if tail[0] != "-" or not direct or follows_t:
            return True
    utc = _UTC_ZONE.match(tail)
    return utc is not None


def _range_end_is_zoned(text, tokens, index):
    if index + 1 >= len(tokens):
        return False
    _, stop = tokens[index]
    start, end = tokens[index + 1]
    return (_RANGE_JOINER.fullmatch(text[stop:start]) is not None
            and _has_zone(text, start, end))


def _is_student_page(document):
    parts = Path(document).parts
    return len(parts) == 3 and parts[:2] == ("wiki", "students") and parts[2].endswith(".md")


def check(root):
    root = Path(root).resolve()
    try:
        paths = files(root, "wiki/**/*.md")
    except ValueError:
        return []

    pages = []
    for path in paths:
        document = path.relative_to(root).as_posix()
        if document == "wiki/log.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        checked = _checked_text(document, text)
        pages.append((path, document, checked))

    student_pages = [page for page in pages if _is_student_page(page[1])]
    roster_needed = bool(student_pages) or any(
        _is_cjk(character) for _, _, text in pages for character in text)
    identifiers = {}
    roster_error = None
    roster_failed = False
    if roster_needed:
        try:
            identifiers = load_roster()
        except JudgmentError as error:
            roster_error = error.detail
            roster_failed = True
    pattern = compile_roster_pattern(identifiers)
    problems = []
    seen = set()
    if roster_error is not None:
        problems.append({
            "document": "wiki",
            "line": 1,
            "message": f"page rule roster: cannot read the roster: {roster_error}",
        })
    student_names = ({key for key, (kind, value) in identifiers.items()
                      if kind == "student" and key == value}
                     if not roster_failed else set())
    if not roster_failed:
        for _, document, _ in student_pages:
            if Path(document).name[:-3] not in student_names:
                _add(problems, seen, document, 1, "student-roster")

    for _, document, text in pages:
        starts = _line_starts(text)
        spans = find_spans(text, identifiers, pattern)
        name_ranges = [(start, stop) for start, stop, (kind, _) in spans
                       if kind in {"student", "given", "guardian"}]
        school_ranges = [(start, stop) for start, stop, (kind, _) in spans if kind == "school"]
        name_marks = _mark(len(text), name_ranges)
        quote_ranges = _allowed_originals(text, name_marks)
        quote_marks = _mark(len(text), quote_ranges)

        for start, _, (kind, _) in spans:
            if kind in {"phone", "email"}:
                rule = kind
                _add(problems, seen, document, _line_number(starts, start), rule)

        for match in _ID_NUMBER.finditer(text):
            birth, gender = match[1], match[2]
            year = (1900 if gender in "1256" else 2000) + int(birth[:2])
            try:
                date(year, int(birth[2:4]), int(birth[4:]))
            except ValueError:
                continue
            _add(problems, seen, document, _line_number(starts, match.start()), "id-number")

        for regex in (_HANGUL_ADDRESS, *_ROAD_ADDRESS, _LOT_ADDRESS):
            for match in regex.finditer(text):
                _add(problems, seen, document, _line_number(starts, match.start()), "address")

        if not roster_failed:
            for index, character in enumerate(text):
                if (_is_cjk(character) and not name_marks[index]
                        and not quote_marks[index]):
                    _add(problems, seen, document, _line_number(starts, index), "english")
                    break

            for start, stop in school_ranges:
                if any(_is_cjk(text[index]) and not quote_marks[index]
                       for index in range(start, stop)):
                    _add(problems, seen, document, _line_number(starts, start), "school")
            for match in _ROMANIZED_SCHOOL.finditer(text):
                _add(problems, seen, document, _line_number(starts, match.start()), "school")
        else:
            for match in _ROMANIZED_SCHOOL.finditer(text):
                _add(problems, seen, document, _line_number(starts, match.start()), "school")

        for offset in _dates(text):
            _add(problems, seen, document, _line_number(starts, offset), "date")

        tokens = list(_time_tokens(text))
        zoned = [_has_zone(text, start, stop) for start, stop in tokens]
        for index, (start, _) in enumerate(tokens):
            if not zoned[index] and not _range_end_is_zoned(text, tokens, index):
                _add(problems, seen, document, _line_number(starts, start), "time")

    return problems


def _add(problems, seen, document, line, rule):
    key = document, line, rule
    if key in seen:
        return
    seen.add(key)
    problems.append({
        "document": document,
        "line": line,
        "message": f"page rule {rule}: {_MESSAGES[rule]}",
    })
