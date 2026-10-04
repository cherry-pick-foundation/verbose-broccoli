import os
from pathlib import Path
import subprocess
import tomllib


def test_workspace_layers_reject_higher_layer_import(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    config = tomllib.loads((root / "pyproject.toml").read_text())
    for name in config["tool"]["importlinter"]["root_packages"]:
        package = tmp_path / name
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "wiki_consistency" / "__init__.py").write_text(
        "value = 1\n", encoding="utf-8"
    )
    (tmp_path / "doc_regions" / "__init__.py").write_text(
        "from wiki_consistency import value\n", encoding="utf-8"
    )

    result = subprocess.run(
        [
            "lint-imports",
            "--config",
            str(root / "pyproject.toml"),
            "--no-cache",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode != 0
    assert "Workspace package layers" in result.stdout + result.stderr
