"""Read the selected provider profile and private key file."""

import os
from pathlib import Path
import re
import stat
import tomllib
from typing import Literal
from urllib.parse import urlsplit

from backfire.failures import JudgmentError

SHIPPED_CONFIG = Path(__file__).with_name("config.toml")
_CREDENTIAL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def _invalid(path: Path) -> None:
    raise JudgmentError("backend_not_configured", str(path))


def xdg_path(kind: Literal["config", "data"]) -> Path:
    """Return Backfire's XDG configuration or data directory."""
    default = ".config" if kind == "config" else ".local/share"
    root = Path(
        os.environ.get(f"XDG_{kind.upper()}_HOME", Path.home() / default)
    )
    if not root.is_absolute():
        raise JudgmentError(
            "backend_not_configured", f"XDG_{kind.upper()}_HOME"
        )
    return root / "verbose-broccoli"


def _read(path: Path, *, optional: bool = False) -> dict:
    try:
        with os.fdopen(
            os.open(path, os.O_RDONLY | os.O_NONBLOCK), "rb"
        ) as file:
            value = tomllib.load(file)
    except FileNotFoundError:
        if optional and not path.is_symlink():
            return {}
        _invalid(path)
    except (OSError, tomllib.TOMLDecodeError):
        _invalid(path)
    if not isinstance(value, dict):
        _invalid(path)
    return value


def load_profiles() -> list[dict]:
    """Load and validate the shared provider profiles in order."""
    shipped_path = SHIPPED_CONFIG
    shipped = _read(shipped_path)
    operator_path = xdg_path("config") / "backfire" / "config.toml"
    operator = _read(operator_path, optional=True)
    if set(operator) - {"order", "providers"}:
        _invalid(operator_path)
    shipped_profiles = shipped.get("providers", {})
    operator_profiles = operator.get("providers", {})
    if not isinstance(shipped_profiles, dict) or not isinstance(
        operator_profiles, dict
    ):
        _invalid(shipped_path)
    profiles = shipped_profiles | operator_profiles
    order = operator.get("order", shipped.get("order"))
    order_source = operator_path if "order" in operator else shipped_path
    if not isinstance(order, list) or any(
        not isinstance(name, str) or not name for name in order
    ):
        _invalid(order_source)
    result = []
    for name in order:
        source = operator_path if name in operator_profiles else order_source
        profile = profiles.get(name)
        if not isinstance(profile, dict) or profile.get("api") not in {
            "openai",
            "jev",
        }:
            _invalid(source)
        if (
            not isinstance(profile.get("credential"), str)
            or not _CREDENTIAL.fullmatch(profile["credential"])
            or profile["credential"] in {"HOME", "PATH"}
        ):
            _invalid(source)
        if "credential_file" in profile and (
            not isinstance(profile["credential_file"], str)
            or not profile["credential_file"].strip()
        ):
            _invalid(source)
        if "codexbar" in profile and (
            not isinstance(profile["codexbar"], str)
            or not profile["codexbar"].strip()
        ):
            _invalid(source)
        if "insufficient_balance" in profile and (
            not isinstance(profile["insufficient_balance"], list)
            or any(
                type(status) is not int or not 100 <= status <= 599
                for status in profile["insufficient_balance"]
            )
        ):
            _invalid(source)
        if profile["api"] == "openai" and any(
            not isinstance(profile.get(key), str) or not profile[key].strip()
            for key in ("base_url", "model")
        ):
            _invalid(source)
        if "base_url" in profile:
            try:
                endpoint = urlsplit(profile["base_url"])
                if (
                    endpoint.scheme not in {"http", "https"}
                    or not endpoint.hostname
                    or endpoint.username
                    or endpoint.password
                ):
                    _invalid(source)
            except (TypeError, ValueError):
                _invalid(source)
        result.append(
            {**profile, "name": name, "_config_dir": operator_path.parent}
        )
    return result


def load_credential(profile: dict) -> str:
    """Read the selected API key from its private environment file."""
    configured = profile.get("credential_file")
    path = (
        Path(configured).expanduser()
        if configured
        else profile["_config_dir"] / f"{profile['name']}.env"
    )
    if not path.is_absolute():
        # Normalize "..", so a shared key file resolves without this folder.
        path = Path(os.path.normpath(profile["_config_dir"] / path))
    try:
        with path.open(encoding="utf-8") as file:
            info = os.fstat(file.fileno())
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.getuid()
            ):
                _invalid(path)
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
        _invalid(path)
    if not key:
        _invalid(path)
    return key
