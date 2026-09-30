"""Generate source-derived Markdown for repository reference documents."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def _escape(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"([\\`*_{}\[\]()!|<>])", r"\\\1", value).replace(
        "\n", "<br>"
    )


def _table(rows: list[list[str]]) -> str:
    widths = [
        max(len(row[index]) for row in rows) for index in range(len(rows[0]))
    ]

    def format_row(row: list[str]) -> str:
        return (
            "| "
            + " | ".join(
                value.ljust(width) for value, width in zip(row, widths)
            )
            + " |"
        )

    return (
        "\n".join(
            [format_row(rows[0]), format_row(["-" * width for width in widths])]
            + [format_row(row) for row in rows[1:]]
        )
        + "\n"
    )


def task_table(package_path: str, turbo_path: str) -> str:
    """Return the root npm task table and declared Turbo descriptions."""
    root = Path.cwd()
    scripts = json.loads((root / package_path).read_text(encoding="utf-8"))[
        "scripts"
    ]
    tasks = json.loads((root / turbo_path).read_text(encoding="utf-8"))["tasks"]
    rows = [["Task", "Invocation", "Declared description"]]
    for name in sorted(scripts):
        task = tasks.get(f"//#{name}")
        description = (
            task.get("description", "") if isinstance(task, dict) else ""
        )
        rows.append(
            [_escape(name), _escape(f"npm run {name}"), _escape(description)]
        )
    return _table(rows)


def command_help(*sources: str) -> str:
    """Return normalized --help text for the selected repository commands."""
    node = shutil.which("node")
    if node is None:
        raise FileNotFoundError("node")
    sections = []
    for source in sources:
        environment = {
            key: os.environ[key]
            for key in ("HOME", "SYSTEMROOT")
            if key in os.environ
        }
        environment.update(
            NO_COLOR="1", TERM="dumb", COLUMNS="80", LC_ALL="C", TZ="UTC"
        )
        result = subprocess.run(
            [
                node,
                "--disable-warning=MODULE_TYPELESS_PACKAGE_JSON",
                source,
                "--help",
            ],
            cwd=Path.cwd(),
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode or result.stderr:
            raise RuntimeError(f"Unable to collect help: {source}")
        help_text = "\n".join(
            line.rstrip(" \t")
            for line in result.stdout.replace("\r\n", "\n").split("\n")
        ).strip()
        if "Usage:" not in help_text or "--help" not in help_text:
            raise ValueError(f"Required help output is missing: {source}")
        name = Path(source).stem.replace("_", "-")
        sections.append((name, help_text))
    return (
        "\n\n".join(
            f"## {name}\n\n```text\n{help_text}\n```"
            for name, help_text in sorted(sections)
        )
        + "\n"
    )


def _link(label: str, path: str) -> str:
    return f"[{_escape(label)}](../../{path})"


def plugin_table(*sources: str) -> str:
    """Return plugin declarations and MCP server names from their manifests."""
    root = Path.cwd()
    plugins = {}
    servers = {}
    for source in sources:
        path = Path(source)
        value = json.loads((root / path).read_text(encoding="utf-8"))
        if path.name == "plugin.json":
            plugins[path.parent.as_posix()] = value
        elif path.name == "mcp.json":
            servers[path.parent.as_posix()] = value["mcpServers"]
        else:
            raise ValueError(f"Unsupported manifest: {source}")

    sections = []
    ordered = sorted(plugins.items(), key=lambda entry: entry[1]["name"])
    for package, plugin in ordered:
        names = sorted(servers.get(package, {}))
        rows = [
            ["Field", "Declared value"],
            ["Description", _escape(plugin.get("description") or "")],
            ["Version", _escape(plugin.get("version") or "")],
            ["Package", _link(package, f"{package}/")],
            ["Manifest", _link("plugin.json", f"{package}/plugin.json")],
            [
                "MCP declaration",
                _link("mcp.json", f"{package}/mcp.json")
                if package in servers
                else "Not declared",
            ],
            [
                "MCP server names",
                _escape(", ".join(names) if names else "None declared"),
            ],
        ]
        sections.append(
            f"## {_escape(plugin['name'])}\n\n{_table(rows).rstrip()}"
        )
    return "\n\n".join(sections) + "\n"


def skill_table(pattern: str) -> str:
    """Return a Markdown table of skills grouped by plugin package."""
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
        f"| `{package}` | "
        f"{', '.join(f'`{skill}`' for skill in sorted(skills))} |"
        for package, skills in sorted(packages.items())
    )
    return "\n".join(rows) + "\n"
