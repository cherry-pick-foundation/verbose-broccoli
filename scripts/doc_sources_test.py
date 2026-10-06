import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import doc_sources
from doc_sources import command_help
from doc_sources import skill_table
from doc_sources import task_table
import pytest


def test_skill_table_lists_full_names_by_package_and_skill(
    tmp_path, monkeypatch
):
    skills = {
        "plugins/work/skills": ["zebra", "alpha"],
        "plugins/code/skills": [
            "verification-before-completion",
            "ponytail-review",
            "clean-code",
            "speckit-plan",
        ],
    }
    for package, names in skills.items():
        for name in names:
            folder = tmp_path / package / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("# Skill\n")
    monkeypatch.chdir(tmp_path)

    assert skill_table("plugins/*/skills/*/SKILL.md") == (
        "| Package | Owned skills |\n"
        "| --- | --- |\n"
        "| `plugins/code/skills` | `clean-code`, `ponytail-review`, "
        "`speckit-plan`, "
        "`verification-before-completion` |\n"
        "| `plugins/work/skills` | `alpha`, `zebra` |\n"
    )


def test_skill_table_raises_when_pattern_matches_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="matches no files"):
        skill_table("plugins/*/skills/*/SKILL.md")


def test_task_table_uses_sorted_root_tasks_and_turbo_descriptions(
    tmp_path, monkeypatch
):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"zeta": "ignored", "alpha": "ignored"}}),
        encoding="utf-8",
    )
    (tmp_path / "turbo.json").write_text(
        json.dumps(
            {
                "tasks": {
                    "//#alpha": {"description": "A *value* | next\nline"},
                    "//#zeta": {"cache": False},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    table = task_table("package.json", "turbo.json")

    assert table.index("| alpha ") < table.index("| zeta ")
    assert "A \\*value\\* \\| next<br>line" in table
    assert "npm run alpha" in table


def test_command_help_uses_normalized_environment_and_sorted_sections(
    tmp_path, monkeypatch
):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("z_tool.ts", "alpha.ts"):
        (scripts / name).write_text("// synthetic command\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", "/synthetic/home")
    monkeypatch.delenv("SYSTEMROOT", raising=False)
    monkeypatch.setenv("NO_COLOR", "0")
    calls = []

    def fake_run(args, *, cwd, env, capture_output, text, encoding, check):
        calls.append((args, cwd, env, capture_output, text, encoding, check))
        name = Path(args[-2]).stem.replace("_", "-")
        return SimpleNamespace(
            returncode=0,
            stdout=f"\r\nUsage: {name} --help  \r\nOptions:\r\n  --help\r\n",
            stderr="",
        )

    monkeypatch.setattr(
        doc_sources.shutil, "which", lambda _: "/synthetic/node"
    )
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = command_help("scripts/z_tool.ts", "scripts/alpha.ts")

    assert output.index("## alpha") < output.index("## z-tool")
    assert "Usage: z-tool --help\nOptions:\n  --help" in output
    assert len(calls) == 2
    for args, cwd, env, capture_output, text, encoding, check in calls:
        assert args[0] == "/synthetic/node"
        assert args[-1] == "--help"
        assert cwd == tmp_path
        assert capture_output and text and encoding == "utf-8"
        assert check is False
        assert env == {
            "HOME": "/synthetic/home",
            "NO_COLOR": "1",
            "TERM": "dumb",
            "COLUMNS": "80",
            "LC_ALL": "C",
            "TZ": "UTC",
        }
