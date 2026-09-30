"""Assign stable pseudonyms in a private, locked, bounded mapping table."""

from contextlib import contextmanager
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile

from backfire.config import xdg_path
from backfire.failures import JudgmentError

BUDGET_BYTES = 1024 * 1024
PREFIXES = {
    "student": "Student",
    "given": "Student",
    "guardian": "Guardian",
    "school": "School",
    "phone": "Phone",
    "email": "Email",
    "region": "Region",
    "cohort": "Cohort",
    "birth": "Birth date",
    "address": "Address",
}
# Tables written before the English stand-ins hold these prefixes.
_LEGACY = {
    "학생": "Student",
    "보호자": "Guardian",
    "학교": "School",
    "연락처": "Phone",
    "이메일": "Email",
}
_HEX = re.compile(r"[0-9a-f]{64}")
_PSEUDONYM = re.compile(
    "(" + "|".join(set(PREFIXES.values())) + r") ([0-9]{2,})"
)
_LEGACY_PSEUDONYM = re.compile("(" + "|".join(_LEGACY) + ")([0-9]{2,})")


@contextmanager
def _private_file(path: Path, *, create=False):
    flags = os.O_RDWR | os.O_NONBLOCK | os.O_NOFOLLOW
    with os.fdopen(
        os.open(path, flags | (os.O_CREAT if create else 0), 0o600), "r+b"
    ) as file:
        info = os.fstat(file.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid != os.getuid()
        ):
            raise ValueError
        yield file


def _english(table):
    """Read the old Korean prefixes (학생01) as English ones (Student 01)."""
    if not (
        isinstance(table, dict)
        and isinstance(table.get("counters"), dict)
        and isinstance(table.get("entries"), dict)
    ):
        return
    counters = {
        _LEGACY.get(prefix, prefix): count
        for prefix, count in table["counters"].items()
    }
    if len(counters) != len(table["counters"]):
        raise ValueError
    table["counters"] = counters
    for digest, pseudonym in table["entries"].items():
        match = (
            _LEGACY_PSEUDONYM.fullmatch(pseudonym)
            if isinstance(pseudonym, str)
            else None
        )
        if match:
            table["entries"][digest] = f"{_LEGACY[match[1]]} {match[2]}"


def _validate(table):
    if (
        not isinstance(table, dict)
        or set(table) != {"version", "key", "counters", "entries"}
        or type(table["version"]) is not int
        or table["version"] != 1
        or not isinstance(table["key"], str)
        or not _HEX.fullmatch(table["key"])
        or not isinstance(table["counters"], dict)
        or not isinstance(table["entries"], dict)
    ):
        raise ValueError
    for prefix, count in table["counters"].items():
        if (
            prefix not in PREFIXES.values()
            or type(count) is not int
            or count < 0
        ):
            raise ValueError
    seen = set()
    for digest, pseudonym in table["entries"].items():
        match = (
            _PSEUDONYM.fullmatch(pseudonym)
            if isinstance(pseudonym, str)
            else None
        )
        if not _HEX.fullmatch(digest) or match is None or pseudonym in seen:
            raise ValueError
        prefix, number = match[1], int(match[2])
        if (
            number < 1
            or pseudonym != f"{prefix} {number:02d}"
            or number > table["counters"].get(prefix, 0)
        ):
            raise ValueError
        seen.add(pseudonym)


def _read(path):
    try:
        with _private_file(path) as file:
            raw = file.read(BUDGET_BYTES + 1)
    except FileNotFoundError:
        return {
            "version": 1,
            "key": secrets.token_hex(32),
            "counters": {},
            "entries": {},
        }
    if len(raw) > BUDGET_BYTES:
        raise ValueError
    table = json.loads(raw)
    _english(table)
    _validate(table)
    return table


def _write(path, table):
    data = json.dumps(table, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    if len(data) > BUDGET_BYTES:
        raise ValueError
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=".pseudonyms-", delete=False
        ) as file:
            temporary = Path(file.name)
            os.fchmod(file.fileno(), 0o600)
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def assign(identifiers) -> dict[tuple[str, str], str]:
    """Resolve one call's identifiers, persisting only new assignments."""
    directory = xdg_path("data") / "backfire"
    path = directory / "pseudonyms.lock"
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        with _private_file(path, create=True) as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if os.fstat(lock.fileno()).st_size:
                raise ValueError
            path = directory / "pseudonyms.json"
            table = _read(path)
            key = bytes.fromhex(table["key"])
            result, changed = {}, False
            for kind, value in identifiers:
                digest = hmac.new(
                    key, f"{kind}:{value}".encode("utf-8"), hashlib.sha256
                ).hexdigest()
                if digest not in table["entries"]:
                    prefix = PREFIXES[kind]
                    number = table["counters"].get(prefix, 0) + 1
                    table["counters"][prefix] = number
                    table["entries"][digest] = f"{prefix} {number:02d}"
                    changed = True
                result[kind, value] = table["entries"][digest]
            if changed:
                _write(path, table)
            return result
    except (OSError, ValueError):
        raise JudgmentError("backend_not_configured", str(path)) from None
