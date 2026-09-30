"""Read provider credit from CodexBar's JSON output."""

from decimal import Decimal
from decimal import InvalidOperation
import json
import math
import os
import re
import subprocess

_DOLLAR = re.compile(r"-?\$[\d,]+(?:\.\d+)?|\$-[\d,]+(?:\.\d+)?")


def _number(value: object) -> bool:
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _detail_balance(details: object) -> Decimal | None:
    if not isinstance(details, list):
        return None
    for section in details:
        if not isinstance(section, dict) or not isinstance(
            section.get("rows"), list
        ):
            continue
        for row in section["rows"]:
            if not isinstance(row, dict):
                continue
            label = row.get("label")
            eligible = label == "Available balance" or (
                section.get("title") == "Credits" and label == "Remaining"
            )
            if eligible and isinstance(row.get("value"), str):
                match = _DOLLAR.search(row["value"])
                if match:
                    try:
                        return Decimal(
                            match.group().replace("$", "").replace(",", "")
                        )
                    except InvalidOperation:
                        return None
    return None


def _has_credit(reports: object, provider: str) -> bool | None:
    if not isinstance(reports, list):
        return None
    report = next(
        (
            value
            for value in reports
            if isinstance(value, dict) and value.get("provider") == provider
        ),
        None,
    )
    if not isinstance(report, dict) or "error" in report:
        return None
    usage = report.get("usage")
    if not isinstance(usage, dict):
        return None
    known_limit = False
    for name in ("primary", "secondary", "tertiary"):
        window = usage.get(name)
        used = window.get("usedPercent") if isinstance(window, dict) else None
        if _number(used):
            known_limit = True
            if used >= 100:
                return False
    cost = usage.get("providerCost")
    if isinstance(cost, dict) and "balance" in cost:
        balance = cost["balance"]
        if _number(balance):
            return balance > 0
        return True if known_limit else None
    balance = _detail_balance(usage.get("details"))
    if balance is not None:
        return balance > 0
    return True if known_limit else None


def check_credit(provider: str, credential: str, key: str) -> bool | None:
    """Return whether credit is available, or ``None`` when unknown."""
    env = {
        name: os.environ[name]
        for name in ("PATH", "HOME")
        if name in os.environ
    }
    env[credential] = key
    try:
        result = subprocess.run(
            ["codexbar", "usage", "--provider", provider, "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return None
    if result.returncode:
        return None
    try:
        reports = json.loads(result.stdout)
    except (TypeError, ValueError):
        return None
    return _has_credit(reports, provider)
