"""Read the operator's roster in place and derive exact-match identifiers."""

from collections import defaultdict
import csv
import os
from pathlib import Path
import re
import stat
import tomllib

from backfire.config import xdg_path
from backfire.failures import JudgmentError

_COMPOUND = {"남궁", "황보", "제갈", "선우", "서문", "독고", "사공"}


def given_name(name: str) -> str | None:
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
    path = xdg_path("config") / "backfire" / "education.toml"
    try:
        with _open_regular(path, mode="rb") as file:
            config = tomllib.load(file)
        if (set(config) != {"roster"} or not isinstance(config["roster"], str)
                or not Path(config["roster"]).is_absolute()):
            raise ValueError
    except (OSError, ValueError):
        raise JudgmentError("backend_not_configured", str(path)) from None

    path = Path(config["roster"])
    students, guardians, schools = {}, {}, {}
    try:
        with _open_regular(path, mode="r", encoding="utf-8-sig", newline="") as file:
            rows = csv.DictReader(file, strict=True)
            if not rows.fieldnames or "name" not in rows.fieldnames:
                raise ValueError
            for row in rows:
                name = (row["name"] or "").strip()
                if not name:
                    raise ValueError
                students[name] = ("student", name)
                school = (row.get("school") or "").strip()
                if school:
                    schools[school] = ("school", school)
                for guardian in (row.get("guardians") or "").split(";"):
                    guardian = guardian.strip()
                    if guardian:
                        guardians[guardian] = ("guardian", guardian)
    except (OSError, ValueError, csv.Error):
        raise JudgmentError("backend_not_configured", str(path)) from None

    given = defaultdict(list)
    for name in students:
        short = given_name(name)
        if short:
            given[short].append(name)
    identifiers = dict(students)
    for short, names in given.items():
        identifiers.setdefault(short, ("student", names[0]) if len(names) == 1 else ("given", short))
    for values in (guardians, schools):
        for value, identifier in values.items():
            identifiers.setdefault(value, identifier)
    return identifiers
