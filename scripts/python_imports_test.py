"""Exercise the installed import checker against the repository contracts."""

import os
from pathlib import Path
import subprocess

import pytest
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "pyproject.toml"
SETTINGS = tomllib.loads(CONFIG.read_text())["tool"]["importlinter"]


def run_checker(tmp_path, files, config=CONFIG):
    """Build an isolated source tree and return the real checker's result."""
    for name in SETTINGS["root_packages"]:
        package = tmp_path / name
        package.mkdir(exist_ok=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
    for name, source in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Every directory is a package so Grimp discovers nested fixtures.
        for parent in path.parents:
            if parent == tmp_path:
                break
            (parent / "__init__.py").touch()
        path.write_text(source, encoding="utf-8")
    result = subprocess.run(
        ["lint-imports", "--config", str(config), "--no-cache"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        check=False,
        text=True,
    )
    print(result.stdout + result.stderr)
    return result


@pytest.mark.parametrize(
    ("ring", "outer"),
    [
        ("domain", "application"),
        ("domain", "adapters"),
        ("domain", "entrypoints"),
        ("domain", "bootstrap"),
        ("application", "adapters"),
        ("application", "entrypoints"),
        ("application", "bootstrap"),
        ("adapters", "entrypoints"),
        ("adapters", "bootstrap"),
        ("bootstrap", "entrypoints"),
    ],
)
def test_d1_ring_direction(tmp_path, ring, outer):
    result = run_checker(
        tmp_path,
        {
            f"credit_offers/{ring}.py": f"import credit_offers.{outer}\n",
            f"credit_offers/{outer}.py": "",
        },
    )
    assert result.returncode == 1
    assert "Component ring layers BROKEN" in result.stdout


@pytest.mark.parametrize("ring", ["domain", "application"])
@pytest.mark.parametrize(
    "library",
    [
        "os",
        "sys",
        "subprocess",
        "socket",
        "shutil",
        "tempfile",
        "urllib",
        "http",
        "httpx",
        "mcp",
        "fastmcp",
    ],
)
def test_d2_d3_inner_io(tmp_path, ring, library):
    result = run_checker(
        tmp_path, {f"credit_offers/{ring}.py": f"import {library}\n"}
    )
    assert result.returncode == 1
    assert "Input and output only at the edge BROKEN" in result.stdout


@pytest.mark.parametrize(
    "module", ["credit_offers/__init__", "credit_offers/adapters/network"]
)
def test_io_flat_module_and_adapter_pass(tmp_path, module):
    result = run_checker(tmp_path, {f"{module}.py": "import socket\n"})
    assert result.returncode == 0


@pytest.mark.parametrize("package", SETTINGS["root_packages"])
def test_d4_unpublished_module(tmp_path, package):
    importer = "doc_regions" if package == "credit_offers" else "credit_offers"
    result = run_checker(
        tmp_path,
        {
            f"{importer}/__init__.py": f"import {package}.private\n",
            f"{package}/private.py": "",
        },
    )
    assert result.returncode == 1
    assert f"Published modules: {package} BROKEN" in result.stdout


def test_d4_published_module_passes(tmp_path):
    result = run_checker(
        tmp_path,
        {
            "wiki_consistency/__init__.py": "import doc_regions.config\n",
            "doc_regions/config.py": "",
        },
    )
    assert result.returncode == 0


def test_d5_sibling_cycle(tmp_path):
    result = run_checker(
        tmp_path,
        {
            "credit_offers/a.py": "import credit_offers.b\n",
            "credit_offers/b.py": "import credit_offers.a\n",
        },
    )
    assert result.returncode == 1
    assert "Python package sibling cycles BROKEN" in result.stdout


def test_d5_cross_root_cycle_needs_root_layers(tmp_path):
    files = {
        "wiki_consistency/evidence.py": "import doc_regions.config\n",
        "doc_regions/config.py": "import wiki_consistency.evidence\n",
    }
    probe = tmp_path / "probe.toml"
    probe.write_text(
        "[tool.importlinter]\n"
        f"root_packages = {SETTINGS['root_packages']!r}\n"
        "[[tool.importlinter.contracts]]\n"
        'name = "Root cycle probe"\n'
        'type = "acyclic_siblings"\n'
        f"ancestors = {SETTINGS['root_packages']!r}\n",
        encoding="utf-8",
    )
    blind = run_checker(tmp_path, files, probe)
    assert blind.returncode == 0
    checked = run_checker(tmp_path, files)
    assert checked.returncode == 1
    assert "Workspace package layers BROKEN" in checked.stdout


def test_d2_indirect_io(tmp_path):
    result = run_checker(
        tmp_path,
        {
            "credit_offers/domain.py": "import credit_offers.shared\n",
            "credit_offers/shared.py": "import socket\n",
        },
    )
    assert result.returncode == 1
    assert "Input and output only at the edge BROKEN" in result.stdout
