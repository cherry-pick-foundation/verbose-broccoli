import os
from pathlib import Path
import subprocess


def test_workspace_layers_reject_higher_layer_import(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    for name in (
        "backfire",
        "backfire_tools",
        "backfire_education",
        "doc_regions",
        "wiki_consistency",
    ):
        package = tmp_path / name
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "wiki_consistency" / "__init__.py").write_text(
        "value = 1\n", encoding="utf-8"
    )
    (tmp_path / "backfire" / "__init__.py").write_text(
        "from wiki_consistency import value\n", encoding="utf-8"
    )
    (tmp_path / "backfire_education" / "pseudonymize.py").write_text(
        "def pseudonymize():\n    pass\n", encoding="utf-8"
    )
    (tmp_path / "backfire" / "judge.py").write_text(
        "from backfire_education.pseudonymize import pseudonymize\n",
        encoding="utf-8",
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
