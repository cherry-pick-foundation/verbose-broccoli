"""Read provider profiles and private credentials afresh for each judgment."""

import json
import os
from pathlib import Path
import stat
import tomllib
from typing import Literal
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

from backfire.failures import JudgmentError

SHIPPED_CONFIG = Path(__file__).with_name("config.toml")
_NAME = {"type": "string", "pattern": r"^[a-z0-9-]+\Z"}
_TEXT = {"type": "string", "pattern": r"\S"}
_PATH = {"type": "string", "pattern": r"^[^.]+(?:\.[^.]+)*\Z"}
_CONFIG = Draft202012Validator(
    {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "pseudonymize": {"type": "boolean"},
            "provider": _NAME,
            "providers": {
                "type": "object",
                "propertyNames": _NAME,
                "additionalProperties": {"type": "object"},
            },
        },
    }
)
_PROFILE = Draft202012Validator(
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["api", "base_url", "model", "credential", "thinking"],
        "properties": {
            "api": {"enum": ["openai", "anthropic"]},
            "base_url": {"type": "string", "pattern": r"^https?://\S+\Z"},
            "model": _TEXT,
            "credential": {
                "type": "string",
                "pattern": r"^[A-Za-z_][A-Za-z0-9_]*\Z",
            },
            "rate_limit_per_second": {"type": "number", "minimum": 0},
            "request": {
                "type": "object",
                "properties": {
                    "model": False,
                    "messages": False,
                    "stream": False,
                    "n": False,
                    "max_tokens": {"type": "integer", "minimum": 1},
                },
            },
            "thinking": {
                "type": "object",
                "additionalProperties": False,
                "required": ["requested"],
                "properties": {
                    "requested": {"enum": ["on", "off"]},
                    "content_path": _PATH,
                    "token_path": _PATH,
                },
                "if": {"properties": {"requested": {"const": "on"}}},
                "then": {
                    "anyOf": [
                        {"required": ["content_path"]},
                        {"required": ["token_path"]},
                    ]
                },
                "else": {
                    "not": {
                        "anyOf": [
                            {"required": ["content_path"]},
                            {"required": ["token_path"]},
                        ]
                    }
                },
            },
            "statuses": {
                "type": "object",
                "propertyNames": {"pattern": r"^[45][0-9]{2}\Z"},
                "additionalProperties": {
                    "enum": [
                        "credential_rejected",
                        "balance_exhausted",
                        "request_rejected",
                        "rate_limited",
                    ]
                },
            },
        },
    }
)


def xdg_path(kind: Literal["config", "state", "cache", "data"]) -> Path:
    """Return the namespace root without creating or reading any directory."""
    defaults = {
        "config": ".config",
        "state": ".local/state",
        "cache": ".cache",
        "data": ".local/share",
    }
    variable = f"XDG_{kind.upper()}_HOME"
    value = os.environ.get(variable)
    root = Path(value) if value else Path.home() / defaults[kind]
    if not root.is_absolute():
        raise JudgmentError("backend_not_configured", variable)
    return root / "verbose-broccoli"


def _read_config(
    path: Path, *, optional: bool = False, shipped: bool = False
) -> dict:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as file:
            if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                raise JudgmentError("backend_not_configured", str(path))
            value = tomllib.load(file)
    except FileNotFoundError:
        if optional and not path.is_symlink():
            return {}
        raise JudgmentError("backend_not_configured", str(path)) from None
    except (OSError, ValueError):
        raise JudgmentError("backend_not_configured", str(path)) from None
    if not _CONFIG.is_valid(value) or ("pseudonymize" in value and not shipped):
        raise JudgmentError("backend_not_configured", str(path))
    return value


def load_pseudonymize() -> bool:
    """The shipped build alone decides whether judgments use pseudonyms."""
    return _read_config(SHIPPED_CONFIG, shipped=True).get("pseudonymize", False)


def load_profile() -> dict:
    """Select data from two files; operator tables replace shipped tables whole."""
    operator_path = xdg_path("config") / "backfire" / "config.toml"
    shipped = _read_config(SHIPPED_CONFIG, shipped=True)
    operator = _read_config(operator_path, optional=True)
    providers = {
        **shipped.get("providers", {}),
        **operator.get("providers", {}),
    }
    # Check both explicit selections; a later override cannot hide a bad file.
    for path, document in (
        (SHIPPED_CONFIG, shipped),
        (operator_path, operator),
    ):
        if "provider" in document and document["provider"] not in providers:
            raise JudgmentError("backend_not_configured", str(path))
    name = operator.get("provider", shipped.get("provider"))
    if name is None:
        raise JudgmentError("backend_not_configured", str(SHIPPED_CONFIG))
    source = (
        operator_path
        if name in operator.get("providers", {})
        else SHIPPED_CONFIG
    )
    detail = f"{source} [providers.{name}]"
    profile = providers[name]
    _validate_profile(profile, detail)
    if "BACKFIRE_TEST_PROVIDER_BASE_URL" in os.environ:
        profile = {
            **profile,
            "base_url": os.environ["BACKFIRE_TEST_PROVIDER_BASE_URL"],
        }
        _validate_profile(profile, f"{detail} BACKFIRE_TEST_PROVIDER_BASE_URL")
    return {"name": name, "request": {}, "statuses": {}, **profile}


def _validate_profile(profile: dict, detail: str) -> None:
    try:
        # TOML dates and non-finite numbers cannot be sent as JSON request fields.
        json.dumps(profile, allow_nan=False)
        error = next(_PROFILE.iter_errors(profile), None)
        if error is not None:
            if error.path:
                detail += " " + ".".join(str(part) for part in error.path)
                if (
                    list(error.path) == ["statuses"]
                    and isinstance(error.instance, str)
                    and error.instance.isascii()
                    and error.instance.isdecimal()
                ):
                    detail += f".{error.instance}"
            raise ValueError
        endpoint = urlsplit(profile["base_url"])
        if not endpoint.hostname:
            raise ValueError
        endpoint.port  # Validate a supplied port before handing the URL to the client.
    except (TypeError, ValueError):
        raise JudgmentError("backend_not_configured", detail) from None
    if profile["api"] == "anthropic":
        raise JudgmentError(
            "backend_not_configured",
            f"{detail}: api anthropic is not supported yet",
        )


def load_credential(profile: dict) -> str:
    """Read only the selected assignment, without sourcing it or changing env."""
    path = xdg_path("config") / "backfire" / f"{profile['name']}.env"
    try:
        # Inspect the opened file, not a path that could be replaced before reading.
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        with os.fdopen(descriptor, encoding="utf-8") as file:
            info = os.fstat(file.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()
                or not info.st_size
            ):
                raise JudgmentError("backend_not_configured", str(path))
            prefix = f"{profile['credential']}="
            key = next(
                (
                    line[len(prefix) :].strip()
                    for line in file
                    if line.startswith(prefix)
                ),
                "",
            )
    except (OSError, UnicodeError):
        raise JudgmentError("backend_not_configured", str(path)) from None
    if not key:
        raise JudgmentError("backend_not_configured", str(path))
    return key
