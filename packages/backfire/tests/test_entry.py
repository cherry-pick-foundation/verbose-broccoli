import json
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINTS = [
    ["uv", "run", "--frozen", "--offline", "--no-sync", "backfire"],
    [sys.executable, "-m", "backfire"],
]


@pytest.mark.parametrize("entry_point", ENTRY_POINTS, ids=["console", "module"])
def test_help_lists_subcommands(entry_point: list[str]) -> None:
    result = subprocess.run(
        [*entry_point, "--help"],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert "serve-mcp" in result.stdout
    assert "ready" in result.stdout
    assert result.stderr == ""


@pytest.mark.parametrize("entry_point", ENTRY_POINTS, ids=["console", "module"])
def test_ready_runs_configuration_check(
    entry_point: list[str], monkeypatch
) -> None:
    monkeypatch.delenv("BACKFIRE_TEST_PROVIDER_BASE_URL", raising=False)
    result = subprocess.run(
        [*entry_point, "ready"],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "not implemented yet" not in result.stderr
    assert "mode-0600 credential" in result.stderr
    report = json.loads(result.stdout)
    assert report["requested"]["provider"] == "hive"
    assert any(
        item["item"] == "configuration" for item in report["unconfirmed"]
    )
