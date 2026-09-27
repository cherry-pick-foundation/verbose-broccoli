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
@pytest.mark.parametrize("subcommand", ["ready"])
def test_subcommands_are_not_implemented(
    entry_point: list[str], subcommand: str
) -> None:
    result = subprocess.run(
        [*entry_point, subcommand],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode != 0
    assert f"{subcommand}: not implemented yet" in result.stderr
    assert result.stdout == ""
