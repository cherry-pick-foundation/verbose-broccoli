"""Offline-safe preflight and on-demand readiness checks for this copy."""

import asyncio
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile

import backfire
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from backfire.config import load_credential, load_profile, xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge
from backfire.records import RecordFile, RecordWriteError, digest, read_records

_ROOT = Path(__file__).resolve().parents[2]
_PORT = re.compile(r"release 0\.9\.0,\s+revision\s+`([0-9a-f]{40})`")
_TOOLS = (
    ("backfire_noul", {"propositions": ["2 + 2 = 4."], "auto_accept": 0.85}),
    (
        "backfire_extract",
        {
            "document": "Readiness token: READY-0051",
            "fields": [
                {
                    "id": "token",
                    "pattern": "READY-0051",
                    "description": "readiness token",
                }
            ],
        },
    ),
)
_RESPONSE_ERRORS = {
    "credential_rejected",
    "balance_exhausted",
    "request_rejected",
    "rate_limited",
    "truncated_output",
    "malformed_output",
    "refused",
    "invalid_distribution",
    "thinking_not_confirmed",
    "model_not_confirmed",
}


def _versions() -> dict[str, str | None]:
    distributions = {
        "mcp": "mcp",
        "rfc8785": "rfc8785",
        "system_one_adapter": "system-one-adapter",
        "typesafe_sdk": "typesafe-sdk",
        "openai": "openai",
    }
    versions = {}
    for key, package in distributions.items():
        try:
            versions[key] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[key] = None
    try:
        from system_one_adapter._client import _PROBABILITY_SYSTEM_PROMPT

        versions["prompt_sha256"] = hashlib.sha256(
            _PROBABILITY_SYSTEM_PROMPT.encode()
        ).hexdigest()
    except (ImportError, AttributeError):
        versions["prompt_sha256"] = None
    source = _ROOT / "src" / "backfire" / "UPSTREAM.md"
    try:
        match = _PORT.search(source.read_text(encoding="utf-8"))
    except OSError:
        match = None
    versions["jev_mcp_port"] = (
        f"0.9.0 ported from {match[1]}" if match else None
    )
    versions["python"] = platform.python_version()
    try:
        output = subprocess.run(
            ["uv", "--version"], capture_output=True, text=True, timeout=5
        )
        match = re.match(r"uv (\S+)", output.stdout)
        versions["uv"] = match[1] if output.returncode == 0 and match else None
    except (OSError, subprocess.TimeoutExpired):
        versions["uv"] = None
    return versions


def _installation_problem(versions: dict[str, str | None]) -> str | None:
    if Path(sys.prefix).resolve() != (_ROOT / ".venv").resolve():
        return "Python is not running from this component's .venv."
    try:
        expected_python = (
            (_ROOT / ".python-version").read_text(encoding="utf-8").strip()
        )
    except OSError:
        return "This component's .python-version is missing or unreadable."
    if platform.python_version() != expected_python:
        return f"Python {expected_python} is required; found {platform.python_version()}."
    if (
        Path(backfire.__file__).resolve().parent
        != (_ROOT / "src" / "backfire").resolve()
    ):
        return "backfire does not import from this component's src/backfire directory."
    required = (
        "jev_mcp_port",
        "mcp",
        "rfc8785",
        "system_one_adapter",
        "typesafe_sdk",
        "openai",
        "python",
        "uv",
        "prompt_sha256",
    )
    if any(versions[key] is None for key in required):
        return "A required package version, uv version, or port revision is unavailable."

    education_extra = (
        ["--extra", "education"]
        if (_ROOT / "src" / "backfire_education").is_dir()
        else []
    )
    base = [
        "uv",
        "sync",
        "--project",
        str(_ROOT),
        "--check",
        "--frozen",
        "--offline",
        *education_extra,
    ]
    for extra in ([], ["--no-dev"]):
        try:
            result = subprocess.run(
                [*base, *extra],
                cwd=_ROOT,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode == 0:
            return None
    return "This component's .venv does not match uv.lock."


async def _direct_judgment():
    loop = asyncio.get_running_loop()
    return await judge(
        {"proposition": "2 + 2 = 4."},
        {
            "ready": {
                "type": "noul",
                "instructions": "Judge the truth of the proposition: 2 + 2 = 4.",
                "criteria": {
                    "true": "The proposition is true.",
                    "false": "The proposition is false.",
                },
            }
        },
        deadline=loop.time() + 118,
        record_file=None,
    )


def _requested(profile: dict) -> dict[str, str]:
    return {
        "provider": profile["name"],
        "api": profile["api"],
        "endpoint": profile["base_url"],
        "model": profile["model"],
        "thinking": profile["thinking"]["requested"],
    }


def _unconfirmed(report: dict, item: str, reason: str) -> None:
    report["unconfirmed"] = [
        entry for entry in report["unconfirmed"] if entry["item"] != item
    ]
    report["unconfirmed"].append({"item": item, "reason": reason})


def _confirm(report: dict, item: str, value) -> None:
    report["confirmed"][item] = value
    report["unconfirmed"] = [
        entry for entry in report["unconfirmed"] if entry["item"] != item
    ]


def _apply_observation(
    report: dict, profile: dict, model, thinking_evidence
) -> None:
    _confirm(report, "provider", profile["name"])
    if model == profile["model"]:
        _confirm(report, "model", model)
    else:
        _unconfirmed(
            report, "model", "The response did not name the requested model."
        )
    if profile["thinking"]["requested"] == "on":
        if thinking_evidence is True:
            _confirm(report, "thinking", "on")
        else:
            _unconfirmed(
                report,
                "thinking",
                "The response did not show the configured thinking evidence.",
            )


def _apply_judgment_error(
    report: dict, profile: dict, error: JudgmentError
) -> None:
    if error.error_type in _RESPONSE_ERRORS:
        _confirm(report, "provider", profile["name"])
    else:
        _unconfirmed(
            report,
            "provider",
            "The request ended without evidence that the selected endpoint answered.",
        )
    if error.error_type == "model_not_confirmed":
        reason = "The response did not name a model."
    else:
        reason = f"No model was confirmed because the judgment ended with {error.error_type}."
    _unconfirmed(report, "model", reason)
    if profile["thinking"]["requested"] == "on":
        reason = (
            "The response did not show the configured thinking evidence."
            if error.error_type == "thinking_not_confirmed"
            else f"Thinking was not confirmed because the judgment ended with {error.error_type}."
        )
        _unconfirmed(report, "thinking", reason)


def _tool_environment(state_home: str) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "XDG_CONFIG_HOME": os.environ.get(
            "XDG_CONFIG_HOME", str(Path.home() / ".config")
        ),
        "XDG_STATE_HOME": state_home,
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for key in (
        "BACKFIRE_TEST_PROVIDER_BASE_URL",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "all_proxy",
        "no_proxy",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
    ):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def _tool_json(result) -> dict | None:
    if (
        getattr(result, "is_error", getattr(result, "isError", True))
        or len(result.content) != 1
    ):
        return None
    block = result.content[0]
    if getattr(block, "type", None) != "text":
        return None
    try:
        value = json.loads(block.text)
    except (AttributeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _read_session_records(directory: Path) -> list[dict]:
    try:
        return [
            record
            for path in sorted(directory.glob("*.jsonl"))
            for record in read_records(path)
        ]
    except (OSError, json.JSONDecodeError):
        return []


def _matching_tool_record(
    records: list[dict], tool: str, arguments: dict
) -> bool:
    matches = [
        record
        for record in records
        if record.get("kind") == "tool_call" and record.get("tool") == tool
    ]
    return (
        len(matches) == 1
        and matches[0].get("outcome") == "ok"
        and matches[0].get("input_digest")
        == digest({"tool": tool, "arguments": arguments})
    )


async def _tool_path() -> tuple[list[dict], dict | None]:
    with tempfile.TemporaryDirectory(prefix="backfire-ready-") as state_home:
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "backfire", "serve-mcp"],
            cwd=str(_ROOT),
            env=_tool_environment(state_home),
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                list_ok = len(listed.tools) == 11
                noul_result = await session.call_tool(
                    _TOOLS[0][0], _TOOLS[0][1]
                )
                noul = _tool_json(noul_result)
                noul_ok = bool(
                    noul
                    and noul.get("results")
                    and noul["results"][0].get("label") == "likely"
                    and noul["results"][0].get("probability", 0) >= 0.85
                )
                extract_result = await session.call_tool(
                    _TOOLS[1][0], _TOOLS[1][1]
                )
                extracted = _tool_json(extract_result)
                extract_ok = bool(
                    extracted
                    and extracted.get("results")
                    and extracted["results"][0].get("value") == "READY-0051"
                    and extracted["results"][0].get("status") == "auto"
                )

        directory = (
            Path(state_home) / "verbose-broccoli" / "backfire" / "records"
        )
        records = _read_session_records(directory)
        tool_records = [
            record for record in records if record.get("kind") == "tool_call"
        ]
        judgments = [
            record for record in records if record.get("kind") == "judgment"
        ]
        expected_judgments = {
            tuple(record.get("calls_in_flight", [])): record
            for record in judgments
        }
        calls_recorded = (
            len(judgments) == 2
            and expected_judgments.get((1,), {}).get("outcome") == "ok"
            and expected_judgments.get((2,), {}).get("outcome") == "ok"
        )
        noul_ok = (
            noul_ok
            and calls_recorded
            and _matching_tool_record(tool_records, *_TOOLS[0])
        )
        extract_ok = (
            extract_ok
            and calls_recorded
            and _matching_tool_record(tool_records, *_TOOLS[1])
        )
        checks = [
            {
                "tool": "tools/list",
                "passed": list_ok,
                "detail": "11 tools"
                if list_ok
                else f"{len(listed.tools)} tools",
            },
            {
                "tool": _TOOLS[0][0],
                "passed": noul_ok,
                "detail": "expected verdict, record digest matches"
                if noul_ok
                else "expected verdict or record digest did not match",
            },
            {
                "tool": _TOOLS[1][0],
                "passed": extract_ok,
                "detail": "verbatim value, record digest matches"
                if extract_ok
                else "verbatim value or record digest did not match",
            },
        ]
        return checks, expected_judgments.get((1,))


def _skipped_tool_checks(reason: str) -> list[dict]:
    return [
        {"tool": tool, "passed": False, "detail": reason}
        for tool in ("tools/list", _TOOLS[0][0], _TOOLS[1][0])
    ]


def main() -> int:
    report = {
        "requested": {},
        "confirmed": {},
        "unconfirmed": [],
        "tool_checks": [],
        "sample": None,
        "versions": _versions(),
    }
    if "BACKFIRE_TEST_PROVIDER_BASE_URL" in os.environ:
        report["BACKFIRE_TEST_PROVIDER_BASE_URL"] = os.environ[
            "BACKFIRE_TEST_PROVIDER_BASE_URL"
        ]

    problem = _installation_problem(report["versions"])
    if problem:
        _unconfirmed(report, "installation", problem)
        report["tool_checks"] = _skipped_tool_checks(
            "not run: installation check failed"
        )
        print(json.dumps(report, ensure_ascii=False))
        education_extra = (
            " --extra education"
            if (_ROOT / "src" / "backfire_education").is_dir()
            else ""
        )
        print(
            f"Readiness failed: run `uv sync --frozen --no-dev{education_extra}` in this component, then retry.",
            file=sys.stderr,
        )
        return 1

    profile = None
    try:
        profile = load_profile()
        report["requested"] = _requested(profile)
        load_credential(profile)
    except JudgmentError as error:
        reason = f"Configuration check failed ({error.error_type})."
        if profile is None:
            _unconfirmed(report, "configuration", reason)
        else:
            _unconfirmed(
                report,
                "configuration",
                "The selected credential could not be validated.",
            )
            for item in ("provider", "model"):
                _unconfirmed(
                    report,
                    item,
                    "No request was sent because the credential could not be validated.",
                )
            if profile["thinking"]["requested"] == "on":
                _unconfirmed(
                    report,
                    "thinking",
                    "No request was sent because the credential could not be validated.",
                )
        report["tool_checks"] = _skipped_tool_checks(
            "not run: configuration check failed"
        )
        print(json.dumps(report, ensure_ascii=False))
        print(
            "Readiness failed: correct the selected profile and its mode-0600 credential, then retry.",
            file=sys.stderr,
        )
        return 1

    try:
        with RecordFile(xdg_path("state") / "backfire" / "records"):
            pass
    except (JudgmentError, RecordWriteError):
        _unconfirmed(
            report,
            "records",
            "The record directory could not be created, locked, and opened for writing.",
        )
        for item in ("provider", "model"):
            _unconfirmed(
                report,
                item,
                "No request was sent because the record directory check failed.",
            )
        if profile["thinking"]["requested"] == "on":
            _unconfirmed(
                report,
                "thinking",
                "No request was sent because the record directory check failed.",
            )
        report["tool_checks"] = _skipped_tool_checks(
            "not run: record directory check failed"
        )
        print(json.dumps(report, ensure_ascii=False))
        print(
            "Readiness failed: check record-directory permissions and available space, then retry.",
            file=sys.stderr,
        )
        return 1

    try:
        result = asyncio.run(_direct_judgment())
    except JudgmentError as error:
        _apply_judgment_error(report, profile, error)
        _unconfirmed(
            report,
            "sample",
            f"The known-answer judgment ended with {error.error_type}.",
        )
    except Exception:
        _unconfirmed(
            report, "provider", "The direct judgment did not complete."
        )
        _unconfirmed(
            report, "model", "No model was confirmed by the direct judgment."
        )
        if profile["thinking"]["requested"] == "on":
            _unconfirmed(
                report,
                "thinking",
                "No thinking evidence was confirmed by the direct judgment.",
            )
        _unconfirmed(
            report,
            "sample",
            "The direct known-answer judgment did not complete.",
        )
    else:
        _apply_observation(
            report,
            profile,
            result["model"],
            result["metadata"].get("thinking_evidence"),
        )
        answer = result["answers"]["ready"]["noul"]
        report["sample"] = {
            "question": "noul",
            "answer": answer,
            "latency_ms": round(result["metadata"]["latency_ms"], 1),
        }
        if answer < 0.85:
            _unconfirmed(
                report,
                "sample",
                "The known true proposition did not receive the likely verdict.",
            )

    try:
        checks, tool_judgment = asyncio.run(_tool_path())
    except Exception:
        checks, tool_judgment = (
            _skipped_tool_checks("MCP readiness session did not complete"),
            None,
        )
    report["tool_checks"] = checks
    if tool_judgment and tool_judgment.get("outcome") == "ok":
        _apply_observation(
            report,
            profile,
            tool_judgment.get("model"),
            tool_judgment.get("thinking_evidence"),
        )

    passed = not report["unconfirmed"] and all(
        check["passed"] for check in checks
    )
    print(json.dumps(report, ensure_ascii=False))
    print(
        "Readiness passed."
        if passed
        else "Readiness failed: see unconfirmed items and tool checks in the JSON report.",
        file=sys.stderr,
    )
    return 0 if passed else 1
