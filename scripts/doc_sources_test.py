from doc_sources import skill_table
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
