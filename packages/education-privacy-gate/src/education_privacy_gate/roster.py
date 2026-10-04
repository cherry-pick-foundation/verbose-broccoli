"""Strict, bounded, names-and-school-spellings-only registry snapshots."""

from collections import defaultdict
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat

_COMPOUND = {"남궁", "황보", "제갈", "선우", "서문", "독고", "사공"}
_LATIN = re.compile(r"[A-Za-z]+(?:[ -][A-Za-z]+)*")
_EDGE = r"(?<![A-Za-z0-9]){}(?![A-Za-z0-9])"


class GateError(Exception):
    """Expose only fixed text, never an identifier or filesystem path."""

    def __init__(self):
        super().__init__("Privacy gate rejected the call.")


def registry_config_dir() -> Path:
    """Return the single XDG configuration seam for the gate registry."""
    config = Path(os.environ.get("XDG_CONFIG_HOME") or "relative")
    if not config.is_absolute():
        config = Path.home() / ".config"
    return config / "verbose-broccoli" / "education-privacy-gate"


def _given(name):
    if not re.fullmatch(r"[가-힣]{3,}", name):
        return None
    return name[2:] if len(name) >= 4 and name[:2] in _COMPOUND else name[1:]


def _spelling(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise GateError()
    return value


def _array(value):
    if not isinstance(value, list):
        raise GateError()
    return [_spelling(item) for item in value]


@dataclass(frozen=True)
class Match:
    """A derived matcher and its call-local identity grouping."""

    pattern: re.Pattern
    identity: tuple
    rank: int


@dataclass(frozen=True)
class Registry:
    """Immutable admitted spellings, matchers and default restored names."""

    spellings: tuple[str, ...]
    matches: tuple[Match, ...]
    defaults: tuple[tuple[tuple, str], ...]

    @classmethod
    def from_data(cls, data):
        """Validate the strict public shape using synthetic or admitted data."""
        if (
            not isinstance(data, dict)
            or set(data) != {"version", "entries"}
            or type(data["version"]) is not int
            or data["version"] != 1
            or not isinstance(data["entries"], list)
        ):
            raise GateError()
        full, given, defaults = {}, defaultdict(set), {}
        latin_owners = {}
        for index, entry in enumerate(data["entries"]):
            if not isinstance(entry, dict):
                raise GateError()
            kind = entry.get("kind")
            identity = (kind, index)
            if kind == "person":
                if set(entry) - {
                    "kind",
                    "full",
                    "given",
                    "romanized",
                    "aliases",
                }:
                    raise GateError()
                name = _spelling(entry.get("full"))
                short = (
                    _spelling(entry["given"])
                    if "given" in entry
                    else _given(name)
                )
                if short is not None and (
                    not name.endswith(_spelling(short)) or short == name
                ):
                    raise GateError()
                latin = _array(entry.get("romanized", []))
                if any(not _LATIN.fullmatch(item) for item in latin):
                    raise GateError()
                defaults[identity] = latin[0] if latin else name
                spellings = [name, *_array(entry.get("aliases", [])), *latin]
                if short:
                    given[short].add(identity)
                for spelling in latin:
                    _, separator, rest = spelling.partition(" ")
                    if separator:
                        given[rest.lower()].add(
                            ("given", short) if short else identity
                        )
            elif kind == "school" and set(entry) == {"kind", "spellings"}:
                spellings = _array(entry["spellings"])
                if not spellings:
                    raise GateError()
            else:
                raise GateError()
            for spelling in spellings:
                if kind == "person" and _LATIN.fullmatch(spelling):
                    surname, *rest = re.split(r"[ -]", spelling)
                    tail = "".join(rest)
                    for form in {surname + tail, tail + surname}:
                        prior = latin_owners.setdefault(form.lower(), identity)
                        if prior != identity:
                            raise GateError()
                key = spelling.lower() if spelling.isascii() else spelling
                if key in full and full[key][0] != identity:
                    raise GateError()
                rank = (
                    4 if kind == "person" and spelling == entry["full"] else 5
                )
                full[key] = (
                    identity,
                    6 if kind == "school" else rank,
                    spelling,
                )
        # Shared Hangul given names and their Latin forms cannot pick a person.
        for spelling, owners in list(given.items()):
            resolved = set()
            for owner in owners:
                resolved.update(
                    given[owner[1]] if owner[0] == "given" else {owner}
                )
            ambiguous = {owner for owner in owners if owner[0] == "given"}
            identity = (
                next(iter(resolved))
                if len(resolved) == 1
                else next(iter(ambiguous))
                if len(ambiguous) == 1
                else ("given", spelling)
            )
            defaults.setdefault(identity, spelling)
            key = spelling.lower() if spelling.isascii() else spelling
            full.setdefault(key, (identity, 7, spelling))
        matches, explicit = [], []
        for identity, rank, spelling in full.values():
            explicit.append(spelling)
            if identity[0] != "school" and _LATIN.fullmatch(spelling):
                surname, *rest = re.split(r"[ -]", spelling)
                short = r"[-\s]*".join("".join(rest) or surname)
                forms = (
                    [surname + r"[\s,-]*" + short, short + r"[\s,-]*" + surname]
                    if rest
                    else [short]
                )
                patterns = [_EDGE.format(form) for form in forms]
            elif spelling.isascii():
                patterns = [_EDGE.format(re.escape(spelling))]
            else:
                patterns = [re.escape(spelling)]
            matches.extend(
                Match(re.compile(p, re.IGNORECASE), identity, rank)
                for p in patterns
            )
            if len(matches) > 4096:
                raise GateError()
        return cls(tuple(explicit), tuple(matches), tuple(defaults.items()))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GateError()
        result[key] = value
    return result


def _constant(unused_value):
    raise GateError()


def load_registry(directory=None) -> Registry:
    """Read one safe snapshot; never create, populate or update a list."""
    directory = (
        Path(directory) if directory is not None else registry_config_dir()
    )
    descriptor = None
    try:
        if not directory.is_absolute() or ".." in directory.parts:
            raise GateError()
        descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        for part in directory.parts[1:]:
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        info = os.fstat(descriptor)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise GateError()
        child = os.open(
            "registered-list.json",
            os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
            dir_fd=descriptor,
        )
        with os.fdopen(child, "rb") as handle:
            info = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                raise GateError()
            raw = handle.read(1048577)
        if len(raw) > 1048576:
            raise GateError()
        return Registry.from_data(
            json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        )
    except OSError, ValueError, TypeError, RecursionError:
        raise GateError() from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
