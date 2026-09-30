"""Run the Wiki page rules with the local Vale style."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unicodedata

from backfire.failures import JudgmentError
from backfire_education.roster import load_roster
from doc_regions.config import files
from doc_regions.regions import scan

_STYLE = Path(__file__).parents[2] / "vale" / "styles"
_CONFIG = Path(__file__).parents[2] / "vale" / ".vale.ini"
_OUTPUT = re.compile(r"^(.+):([0-9]+):[0-9]+:Wiki\.[A-Za-z]+:(.+)$")
_CJK = r"\p{Hangul}\p{Han}\p{Hiragana}\p{Katakana}"
_CJK_NAMES = (
    "HANGUL",
    "CJK UNIFIED IDEOGRAPH",
    "CJK COMPATIBILITY IDEOGRAPH",
    "HIRAGANA",
    "KATAKANA",
    "HALFWIDTH HANGUL",
    "HALFWIDTH KATAKANA",
)
_HANGUL = re.compile("[\\u1100-\\u11ff\\u3130-\\u318f\\uac00-\\ud7af]")
_QUOTES = (('"', '"'), ("“", "”"), ("‘", "’"), ("「", "」"), ("『", "』"))


def _pages(root):
    try:
        paths = files(root, "wiki/**/*.md")
    except ValueError:
        # ponytail: one escaping link skips the Wiki; add per-file filtering
        # if needed.
        return {}
    pages = {}
    for path in paths:
        document = path.relative_to(root).as_posix()
        if document == "wiki/log.md" or path.resolve() != path:
            continue
        try:
            pages[document] = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return pages


def _front_matter_end(lines):
    if lines and lines[0].strip() == "---":
        return next(
            (
                number
                for number, line in enumerate(lines[1:], 2)
                if line.strip() in {"---", "..."}
            ),
            None,
        )
    return None


def _front_matter_lines(text):
    end = _front_matter_end(text.splitlines())
    return set(range(1, end + 1)) if end is not None else set()


def _ignored_lines(document, text):
    lines, ignored = text.splitlines(), set()
    end = _front_matter_end(lines)
    if end is not None:
        in_sources = False
        for number, line in enumerate(lines[1 : end - 1], 2):
            if line.strip() and not line[0].isspace():
                in_sources = bool(re.match(r"^sources\s*:", line))
            if in_sources:
                ignored.add(number)
    spans, errors = scan(document, text)
    if not errors:
        for span in spans:
            ignored.update(range(span["start"] + 1, span["end"] + 1))
    return ignored


def _run(root, pages, config):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("VALE_")
    }
    ignored = {page: _ignored_lines(page, text) for page, text in pages.items()}
    front_matter = {
        page: _front_matter_lines(text) for page, text in pages.items()
    }
    result = subprocess.run(
        [
            "vale",
            "--config",
            str(config.resolve()),
            "--no-global",
            "--output=line",
            *pages,
        ],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("Vale could not check Wiki pages")
    problems, seen = [], set()
    for line in result.stdout.splitlines():
        match = _OUTPUT.match(line)
        if (
            not match
            or match[1] not in pages
            or not match[3].startswith("page rule ")
        ):
            raise RuntimeError("Vale returned an unexpected result")
        document, number, message = match[1], int(match[2]), match[3]
        key = document, number, message
        if (
            number not in ignored[document]
            and not (
                message.startswith("page rule time:")
                and number in front_matter[document]
            )
            and key not in seen
        ):
            seen.add(key)
            problems.append(
                {"document": document, "line": number, "message": message}
            )
    return problems


def _is_cjk(character):
    return character.isalpha() and unicodedata.name(character, "").startswith(
        _CJK_NAMES
    )


def _outside_quotes(token):
    allowed = []
    for opening, closing in _QUOTES:
        opening, closing = map(re.escape, (opening, closing))
        allowed.extend(
            (
                rf"(?<={opening}[^\r\n{closing}]{{0,50}}){token}"
                rf"(?=[^\r\n{closing}]{{0,49}}{closing}[ \t]+\("
                rf"[^\r\n){_CJK}]*[A-Za-z][^\r\n){_CJK}]*\))",
                rf"(?<={opening}[^\r\n{closing}{_CJK}]{{0,50}}[A-Za-z]"
                rf"[^\r\n{closing}{_CJK}]{{0,49}}{closing}[ \t]+\([ \t]*"
                rf"{opening}"
                rf"[^\r\n{closing}]{{0,50}}){token}"
                rf"(?=[^\r\n{closing}]{{0,49}}{closing}[ \t]*\))",
            )
        )
    return f"(?!(?:{'|'.join(allowed)})){token}"


def _school_rule(identifiers, styles):
    schools = sorted(
        {
            value
            for kind, value in identifiers.values()
            if kind == "school"
            and _HANGUL.search(value)
            and "\n" not in value
            and "\r" not in value
        }
    )
    if schools:
        pattern = (
            "(?:"
            + "|".join(_outside_quotes(re.escape(name)) for name in schools)
            + ")"
        )
        (styles / "Wiki" / "School.yml").write_text(
            "extends: existence\n"
            'message: "page rule school: write the school as its domain ID"\n'
            "level: error\nscope: text & ~frontmatter\nvocab: false\n"
            f"raw:\n  - {json.dumps(pattern)}\n",
            encoding="utf-8",
        )


def check(root):
    """Return page-rule violations for regular Markdown files in a Wiki."""
    root = Path(root).resolve()
    pages = _pages(root)
    if not pages:
        return []
    student_pages = [
        page for page in pages if Path(page).parent == Path("wiki/students")
    ]
    identifiers, roster_error = {}, None
    if student_pages or any(
        _is_cjk(char) for text in pages.values() for char in text
    ):
        try:
            identifiers = load_roster()
        except JudgmentError as error:
            roster_error = error.detail
    with TemporaryDirectory(prefix="wiki-consistency-vale-") as temp:
        private = Path(temp)
        styles = private / "styles"
        shutil.copytree(_STYLE, styles)
        vocab = styles / "config" / "vocabularies" / "Roster" / "accept.txt"
        vocab.parent.mkdir(parents=True, exist_ok=True)
        names = sorted(
            re.escape(name)
            for name, (kind, _) in identifiers.items()
            if kind in {"student", "given", "guardian"}
            and "\n" not in name
            and "\r" not in name
        )
        vocab.write_text(
            "\n".join(names) + ("\n" if names else ""), encoding="utf-8"
        )
        if not roster_error:
            _school_rule(identifiers, styles)
        config = private / ".vale.ini"
        config.write_text(
            _CONFIG.read_text(encoding="utf-8").replace(
                "StylesPath = styles", f"StylesPath = {styles}"
            ),
            encoding="utf-8",
        )
        problems = _run(root, pages, config)
    if roster_error:
        return [
            {
                "document": "wiki",
                "line": 1,
                "message": f"page rule roster: cannot read the roster: "
                f"{roster_error}",
            },
            *(
                item
                for item in problems
                if not item["message"].startswith("page rule english:")
            ),
        ]
    students = {
        name
        for name, (kind, value) in identifiers.items()
        if kind == "student" and name == value
    }
    problems.extend(
        {
            "document": page,
            "line": 1,
            "message": (
                "page rule student-roster: add the student to the backfire "
                "roster or fix the page name"
            ),
        }
        for page in student_pages
        if Path(page).stem not in students
    )
    return problems
