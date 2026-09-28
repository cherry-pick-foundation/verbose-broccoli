from pathlib import Path


def skill_table(pattern: str) -> str:
    root = Path.cwd()
    matches = sorted(path for path in root.glob(pattern) if path.is_file())
    if not matches:
        raise ValueError(f"Pattern matches no files: {pattern}")

    packages: dict[str, set[str]] = {}
    for path in matches:
        package = path.parent.parent.relative_to(root).as_posix()
        packages.setdefault(package, set()).add(path.parent.name)

    rows = ["| Package | Owned skills |", "| --- | --- |"]
    rows.extend(
        f"| `{package}` | {', '.join(f'`{skill}`' for skill in sorted(skills))} |"
        for package, skills in sorted(packages.items())
    )
    return "\n".join(rows) + "\n"
