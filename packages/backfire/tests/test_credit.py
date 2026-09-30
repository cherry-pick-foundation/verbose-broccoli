"""CodexBar parsing and process setup use synthetic reports only."""

import json
import os
import shlex
import subprocess

import pytest

from backfire import credit

REPORTS = {
    "openrouter_zero": [
        {
            "provider": "other",
            "usage": {"providerCost": {"balance": 0}},
        },
        {
            "provider": "openrouter",
            "usage": {"providerCost": {"balance": 0}},
        },
    ],
    "openrouter_positive": [
        {
            "provider": "openrouter",
            "usage": {"providerCost": {"balance": 7.25}},
        }
    ],
    "openrouter_limit_almost_used": [
        {
            "provider": "openrouter",
            "usage": {"primary": {"usedPercent": 99.9}},
        }
    ],
    "openrouter_used_up": [
        {
            "provider": "openrouter",
            "usage": {
                "primary": {"usedPercent": 100},
                "providerCost": {"balance": 7.25},
            },
        }
    ],
    "openrouter_tertiary_used_up": [
        {
            "provider": "openrouter",
            "usage": {
                "tertiary": {"usedPercent": 100},
                "providerCost": {"balance": 7.25},
            },
        }
    ],
    "available_balance_zero": [
        {
            "provider": "openrouter",
            "usage": {
                "details": [
                    {
                        "title": "Team credits",
                        "rows": [
                            {"label": "Available balance", "value": "$0.00"}
                        ],
                    }
                ]
            },
        }
    ],
    "available_balance_positive": [
        {
            "provider": "openrouter",
            "usage": {
                "details": [
                    {
                        "title": "Team credits",
                        "rows": [
                            {
                                "label": "Available balance",
                                "value": "$12.50",
                            }
                        ],
                    }
                ]
            },
        }
    ],
    "openrouter_details_zero": [
        {
            "provider": "openrouter",
            "usage": {
                "details": [
                    {
                        "title": "Credits",
                        "rows": [{"label": "Remaining", "value": "$0.00"}],
                    }
                ]
            },
        }
    ],
    "openrouter_comma_balance": [
        {
            "provider": "openrouter",
            "usage": {
                "details": [
                    {
                        "title": "Credits",
                        "rows": [{"label": "Remaining", "value": "$1,234.56"}],
                    }
                ]
            },
        }
    ],
    "provider_balance_fallback": [
        {
            "provider": "openrouter",
            "usage": {
                "providerCost": {"balance": None},
                "details": [
                    {
                        "title": "Credits",
                        "rows": [{"label": "Remaining", "value": "$0.00"}],
                    }
                ],
            },
        }
    ],
    "provider_balance_invalid_fallback": [
        {
            "provider": "openrouter",
            "usage": {
                "providerCost": {"balance": "unknown"},
                "details": [
                    {
                        "title": "Credits",
                        "rows": [{"label": "Remaining", "value": "$0.00"}],
                    }
                ],
            },
        },
    ],
    "openrouter_malformed_balance": [
        {
            "provider": "openrouter",
            "usage": {
                "details": [
                    {
                        "title": "Credits",
                        "rows": [{"label": "Remaining", "value": "$,"}],
                    }
                ]
            },
        }
    ],
    "error": [
        {
            "provider": "openrouter",
            "error": "synthetic provider error",
            "usage": {"providerCost": {"balance": 7.25}},
        }
    ],
    "null_error": [
        {
            "provider": "openrouter",
            "error": None,
            "usage": {"providerCost": {"balance": 7.25}},
        }
    ],
}


def install_codexbar(tmp_path, monkeypatch, output, *, exit_code=0):
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    seen = tmp_path / "environment.txt"
    arguments = tmp_path / "arguments.txt"
    key_present = tmp_path / "key-present.txt"
    output_text = output if isinstance(output, str) else json.dumps(output)
    script = binary_dir / "codexbar"
    script.write_text(
        "#!/bin/sh\n"
        "unset PWD\n"
        f"/usr/bin/env | /usr/bin/cut -d= -f1 | /usr/bin/sort > "
        f"{shlex.quote(str(seen))}\n"
        f"printf '%s\\n' \"$@\" > {shlex.quote(str(arguments))}\n"
        f'if [ -n "$SYNTHETIC_API_KEY" ]; then '
        f"printf true > {shlex.quote(str(key_present))}; else "
        f"printf false > {shlex.quote(str(key_present))}; fi\n"
        f"printf '%s\\n' {shlex.quote(output_text)}\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    script.chmod(0o700)
    monkeypatch.setenv("PATH", f"{binary_dir}{os.pathsep}{os.environ['PATH']}")
    return seen, arguments, key_present


@pytest.mark.parametrize(
    ("provider", "reports", "expected"),
    [
        ("openrouter", REPORTS["openrouter_zero"], False),
        ("openrouter", REPORTS["openrouter_positive"], True),
        ("openrouter", REPORTS["openrouter_limit_almost_used"], True),
        ("openrouter", REPORTS["openrouter_used_up"], False),
        ("openrouter", REPORTS["openrouter_tertiary_used_up"], False),
        ("openrouter", REPORTS["openrouter_details_zero"], False),
        ("openrouter", REPORTS["openrouter_comma_balance"], True),
        ("openrouter", REPORTS["openrouter_malformed_balance"], None),
        ("openrouter", REPORTS["provider_balance_fallback"], False),
        ("openrouter", REPORTS["provider_balance_invalid_fallback"], False),
        ("openrouter", REPORTS["available_balance_zero"], False),
        ("openrouter", REPORTS["available_balance_positive"], True),
        ("openrouter", REPORTS["error"], None),
        ("openrouter", REPORTS["null_error"], True),
    ],
)
def test_reads_credit_balance_and_rate_windows(
    tmp_path, monkeypatch, provider, reports, expected
):
    install_codexbar(tmp_path, monkeypatch, reports)

    assert (
        credit.check_credit(provider, "SYNTHETIC_API_KEY", "test-key")
        is expected
    )


def test_codexbar_gets_only_the_allowed_environment(
    tmp_path, monkeypatch, caplog
):
    for name in (
        "OPENROUTER_API_KEY",
        "OPENROUTER_API_URL",
        "OPENROUTER_MANAGEMENT_API_KEY",
        "CODEXBAR_CONFIG",
        "CLAUDE_CLI_PATH",
        "CODEX_CLI_PATH",
        "ANTHROPIC_ADMIN_KEY",
        "ANTHROPIC_ADMIN_API_KEY",
        "CODEXBAR_CLAUDE_OAUTH_TOKEN",
    ):
        monkeypatch.setenv(name, "synthetic-parent-value")
    seen, arguments, key_present = install_codexbar(
        tmp_path, monkeypatch, REPORTS["openrouter_positive"]
    )

    assert (
        credit.check_credit("openrouter", "SYNTHETIC_API_KEY", "test-key")
        is True
    )
    assert arguments.read_text(encoding="utf-8").splitlines() == [
        "usage",
        "--provider",
        "openrouter",
        "--format",
        "json",
    ]
    assert seen.read_text(encoding="utf-8").splitlines() == sorted(
        ("PATH", "HOME", "SYNTHETIC_API_KEY")
    )
    assert key_present.read_text(encoding="utf-8") == "true"
    assert "test-key" not in arguments.read_text(encoding="utf-8")
    assert "test-key" not in caplog.text


@pytest.mark.parametrize(
    "output,exit_code",
    [("not JSON", 0), (REPORTS["openrouter_zero"], 1)],
)
def test_bad_output_or_exit_is_unknown(
    tmp_path, monkeypatch, output, exit_code
):
    install_codexbar(tmp_path, monkeypatch, output, exit_code=exit_code)

    assert (
        credit.check_credit("openrouter", "SYNTHETIC_API_KEY", "test-key")
        is None
    )


def test_timeout_is_unknown(monkeypatch):
    def timeout(command, **kwargs):
        assert command == [
            "codexbar",
            "usage",
            "--provider",
            "openrouter",
            "--format",
            "json",
        ]
        assert kwargs["timeout"] == 30
        assert kwargs["env"]["SYNTHETIC_API_KEY"] == "test-key"
        raise subprocess.TimeoutExpired(command, 30)

    monkeypatch.setattr(credit.subprocess, "run", timeout)

    assert (
        credit.check_credit("openrouter", "SYNTHETIC_API_KEY", "test-key")
        is None
    )


def test_missing_codexbar_is_unknown(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))

    assert (
        credit.check_credit("openrouter", "SYNTHETIC_API_KEY", "test-key")
        is None
    )
