"""Read the source-backed Wiki domain roster, separate from the privacy list."""

from collections import defaultdict
import csv
import os
from pathlib import Path
import re
import stat
import tomllib


class RosterError(Exception):
    """Report a missing or invalid roster without revealing source content."""

    def __init__(self):
        super().__init__(
            "The Wiki roster configuration or source is missing or invalid."
        )


def _config_path():
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    if not root.is_absolute():
        raise RosterError
    # Keep the operator's domain-roster location; the gate has its own list.
    return root / "verbose-broccoli" / "backfire" / "education.toml"


_COMPOUND = {"남궁", "황보", "제갈", "선우", "서문", "독고", "사공"}


def given_name(name: str) -> str | None:
    """Return the detected given name for a Korean name."""
    if not re.fullmatch(r"[가-힣]{3,}", name):
        return None
    return name[2:] if len(name) >= 4 and name[:2] in _COMPOUND else name[1:]


def _open_regular(path: Path, **kwargs):
    descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    file = os.fdopen(descriptor, **kwargs)
    if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
        file.close()
        raise ValueError
    return file


def load_roster() -> dict[str, tuple[str, str]]:
    """Map matched text to (kind, normalized value), in contract precedence."""
    path = _config_path()
    try:
        with _open_regular(path, mode="rb") as file:
            config = tomllib.load(file)
        if (
            set(config) != {"roster"}
            or not isinstance(config["roster"], str)
            or not Path(config["roster"]).is_absolute()
        ):
            raise ValueError
    except OSError, ValueError:
        raise RosterError from None

    path = Path(config["roster"])
    students, guardians, schools, ids, romanized = {}, {}, {}, {}, {}
    try:
        with _open_regular(
            path, mode="r", encoding="utf-8-sig", newline=""
        ) as file:
            rows = csv.DictReader(file, strict=True)
            if not rows.fieldnames or "name" not in rows.fieldnames:
                raise ValueError
            for row in rows:
                name = (row["name"] or "").strip()
                if not name:
                    raise ValueError
                students[name] = ("student", name)
                number = (row.get("id") or "").strip()
                if number:
                    ids[number] = students[name]
                spelling = " ".join((row.get("romanized") or "").split())
                if spelling:
                    romanized[name] = spelling
                school = (row.get("school") or "").strip()
                if school:
                    schools[school] = ("school", school)
                for guardian in (row.get("guardians") or "").split(";"):
                    guardian = guardian.strip()
                    if guardian:
                        guardians[guardian] = ("guardian", guardian)
    except OSError, ValueError, csv.Error:
        raise RosterError from None

    given = defaultdict(list)
    for name in students:
        short = given_name(name)
        if short:
            given[short].append(name)
    identifiers = dict(students)
    for name, spelling in romanized.items():
        identifiers.setdefault(spelling, students[name])
    for short, names in given.items():
        identifier = (
            ("student", names[0]) if len(names) == 1 else ("given", short)
        )
        identifiers.setdefault(short, identifier)
        # The romanized given name is the spelling without its surname.
        for name in names:
            _, _, latin = romanized.get(name, "").partition(" ")
            if latin:
                identifiers.setdefault(latin, identifier)
    for values in (ids, guardians, schools):
        for value, identifier in values.items():
            identifiers.setdefault(value, identifier)
    return identifiers
