"""Select local Claude Code and Codex sessions for Wiki review."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import random
import re
import shlex
import shutil
import subprocess
import time

from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from education_privacy_gate.roster import load_registry
from wiki_consistency.roster import load_roster as load_domain_roster

SPECSTORY_FLAGS = (
    "--print",
    "--no-usage-analytics",
    "--no-version-check",
    "--no-cloud-sync",
    "--no-stats",
)
SPECSTORY_CONFIG = """[version_check]
enabled = false

[cloud_sync]
enabled = false

[analytics]
enabled = false

[redaction]
enabled = true
"""
CLAUDE_PROJECT_CHARS = re.compile(r"[^a-zA-Z0-9-]")
AUTO_REVIEW_PROMPT = (
    "The following is the Codex agent history whose request "
    "action you are assessing"
)
BATCH_SIZE = 64
DIGEST_LIMIT = 2000
MESSAGE_HEADER = re.compile(
    r"(?m)^_\*\*(User|Agent)(?: - sidechain)?(?: \([^)]*\))?\*\*_\r?$"
)
ROOT = Path(__file__).resolve().parents[5]


def stage_dir(value):
    """Create a private stage outside repositories and vault raw folders."""
    stage = Path(value).expanduser().resolve()
    if any(
        (parent / ".git").exists()
        or (parent.name == "raw" and parent.parent.parent.name == "vaults")
        for parent in (stage, *stage.parents)
    ):
        raise ValueError(
            "stage must be outside repositories and vault raw folders"
        )
    stage.mkdir(mode=0o700, parents=True, exist_ok=True)
    stage.chmod(0o700)
    return stage


def write_jsonl(path, records):
    """Write records as UTF-8 JSON Lines."""
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False) + "\n" for record in records
        ),
        encoding="utf-8",
    )


def read_jsonl(path):
    """Read a UTF-8 JSON Lines file."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def claude_project(path):
    """Return the first cwd field in a Claude session file."""
    with path.open(encoding="utf-8") as source:
        for line in source:
            try:
                cwd = json.loads(line).get("cwd")
            except (json.JSONDecodeError, AttributeError):
                continue
            if isinstance(cwd, str) and cwd:
                return cwd
    return ""


def discover(home):
    """List local Claude Code and Codex session files."""
    sessions = []
    for path in sorted((home / ".claude/projects").glob("*/*.jsonl")):
        try:
            project = claude_project(path)
        except OSError:
            project = ""
        sessions.append(
            (path, "claude", path.stem, project, bool(project), None)
        )
    for path in sorted((home / ".codex/sessions").rglob("rollout-*.jsonl")):
        try:
            with path.open(encoding="utf-8") as source:
                meta = json.loads(source.readline())
            payload = meta["payload"]
            session_id, project = payload["id"], payload["cwd"]
            if not isinstance(session_id, str) or not session_id:
                session_id = path.stem
            thread_source = payload.get("thread_source")
            valid = (
                meta.get("type") == "session_meta"
                and isinstance(session_id, str)
                and isinstance(project, str)
                and bool(session_id and project)
            )
        except (OSError, KeyError, TypeError, json.JSONDecodeError):
            session_id, project, valid, thread_source = (
                path.stem,
                "",
                False,
                None,
            )
        safe_id = bool(
            isinstance(session_id, str)
            and session_id
            and Path(session_id).name == session_id
            and "\\" not in session_id
        )
        sessions.append(
            (
                path,
                "codex",
                session_id,
                project,
                valid and safe_id,
                thread_source,
            )
        )
    return sessions


def specstory_config(stage):
    """Write isolated SpecStory configs and return its staging paths."""
    root = stage / "specstory"
    home = root / "home"
    cache = root / "cache"
    claude = root / "claude"
    for path in (home / ".specstory/cli/config.toml", root / "config.toml"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(SPECSTORY_CONFIG, encoding="utf-8")
    cache.mkdir(parents=True, exist_ok=True)
    return root, home, cache, claude


def claude_mirror(stage, source):
    """Hard-link one Claude session tree under a staged project mirror."""
    mirror = stage / "specstory/mirror" / source.parent.name
    mirror.mkdir(parents=True)
    encoded = CLAUDE_PROJECT_CHARS.sub("-", str(mirror.resolve()))
    project_store = stage / "specstory/claude/projects" / encoded
    project_store.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(
            source.parent, project_store, copy_function=os.link, symlinks=True
        )
    except OSError:
        shutil.rmtree(project_store, ignore_errors=True)
        shutil.rmtree(mirror, ignore_errors=True)
        raise
    return mirror, project_store


def remove_specstory_database(home):
    """Remove SpecStory's temporary session index and sidecar files."""
    for path in (home / ".specstory").glob("sessions.db*"):
        path.unlink(missing_ok=True)


def render(stage, specstory="specstory", now=None):
    """Render quiet sessions and write their status manifest."""
    real_home = Path(os.environ.get("HOME", str(Path.home()))).resolve()
    output_root = stage / "rendered"
    for path in (
        stage / "specstory/mirror",
        stage / "specstory/claude/projects",
    ):
        shutil.rmtree(path, ignore_errors=True)
    config_root, spec_home, cache, claude_config = specstory_config(stage)
    command = shlex.split(specstory)
    now = time.time() if now is None else now
    records, counts = [], {"rendered": 0, "running": 0, "failed": 0}
    sessions = {}
    for source, provider, session_id, project, valid, thread_source in discover(
        real_home
    ):
        sessions.setdefault((provider, session_id), []).append(
            (source, project, valid, thread_source)
        )
    for (provider, session_id), sources in sorted(sessions.items()):
        timed = []
        for source, project, valid, thread_source in sources:
            try:
                timed.append(
                    (
                        source.stat().st_mtime,
                        source,
                        project,
                        valid,
                        thread_source,
                    )
                )
            except OSError:
                continue
        latest = max(timed, key=lambda item: item[0], default=None)
        selected = max(timed, key=lambda item: (item[3], item[0]), default=None)
        source, project, valid, thread_source = (
            selected[1:] if selected else (*sources[0][:2], False, None)
        )
        mtime = latest[0] if latest else None
        output = output_root / provider / f"{session_id}.md"
        record = {
            "id": session_id,
            "provider": provider,
            "project": project,
            "source_path": str(source.resolve()),
            "output_path": str(output),
            "mtime": mtime,
            "status": "failed",
            "thread_source": thread_source,
        }
        if not valid or mtime is None:
            pass
        elif now - mtime < 60 * 60:
            record["status"] = "running"
        elif output.is_file() and output.stat().st_mtime > mtime:
            record["status"] = "rendered"
        else:
            mirror = project_store = None
            try:
                project_path = project
                if provider == "claude":
                    mirror, project_store = claude_mirror(stage, source)
                    project_path = str(mirror)
                env = os.environ.copy()
                for key in tuple(env):
                    if key.startswith("OTEL_"):
                        env.pop(key)
                env.update(
                    {
                        "HOME": str(spec_home),
                        "XDG_CACHE_HOME": str(cache),
                        "OTEL_SDK_DISABLED": "true",
                        "CLAUDE_CONFIG_DIR": str(claude_config),
                        "CODEX_HOME": str(real_home / ".codex"),
                    }
                )
                result = subprocess.run(
                    [
                        *command,
                        "sync",
                        provider,
                        "-s",
                        session_id,
                        *SPECSTORY_FLAGS,
                        "--project-path",
                        project_path,
                        "--config-dir",
                        str(config_root),
                    ],
                    cwd=stage,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=300,
                )
            except (OSError, UnicodeError, subprocess.SubprocessError):
                result = None
            finally:
                try:
                    if project_store and project_store.exists():
                        shutil.rmtree(project_store)
                    if mirror and mirror.exists():
                        shutil.rmtree(mirror)
                    remove_specstory_database(spec_home)
                except OSError:
                    result = None
            if result and result.returncode == 0 and result.stdout.strip():
                try:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(result.stdout, encoding="utf-8")
                    record["status"] = "rendered"
                except (OSError, UnicodeError):
                    pass
        counts[record["status"]] += 1
        records.append(record)
    write_jsonl(stage / "sessions.jsonl", records)
    return counts


def messages(markdown):
    """Parse SpecStory's role headers into visible message bodies."""
    headers = list(MESSAGE_HEADER.finditer(markdown))
    found = []
    for index, header in enumerate(headers):
        end = (
            headers[index + 1].start()
            if index + 1 < len(headers)
            else len(markdown)
        )
        body = re.sub(
            r"(?:^|\n)\s*---\s*$", "", markdown[header.end() : end]
        ).strip()
        if body:
            found.append((header.group(1), body))
    return found


def roster_match(text, pattern):
    """Match roster terms without Hangul or ASCII word prefixes."""
    for match in pattern.finditer(text):
        before = text[match.start() - 1 : match.start()]
        after = text[match.end() : match.end() + 1]
        ending = match.group()[-1:]
        if (
            before.isascii()
            and before.isalnum()
            or "\uac00" <= before <= "\ud7a3"
            or ending.isascii()
            and ending.isalnum()
            and after.isascii()
            and after.isalnum()
        ):
            continue
        return True
    return False


def bounded_digest(user, agent, project, orca_worker=False):
    """Join header and message parts within the 2,000-character limit."""
    prefix = f"Project: {project}\n"
    if orca_worker:
        prefix += "Orca worker session. Task:\n"
    separator = "\n\n" if user and agent else ""
    available = max(0, DIGEST_LIMIT - len(prefix) - len(separator))
    user_size = min(len(user), available // 2)
    agent_size = min(len(agent), available - user_size)
    user_size = min(len(user), available - agent_size)
    parts = ([user[:user_size]] if user else []) + (
        [agent[-agent_size:]] if agent else []
    )
    return prefix + separator.join(parts)


def digest(stage, scan=None):
    """Hold unsafe sessions and write roster-tagged bounded digests."""
    report_path = scan or stage / "scan.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    findings = {str(Path(item["File"]).resolve()) for item in report}
    sessions = sorted(
        (
            item
            for item in read_jsonl(stage / "sessions.jsonl")
            if item["status"] == "rendered"
        ),
        key=lambda item: (item["provider"], item["id"]),
    )
    scan_mtime = report_path.stat().st_mtime
    if any(
        scan_mtime < Path(item["output_path"]).stat().st_mtime
        for item in sessions
    ):
        raise ValueError("scan report is stale")
    registry = load_registry()
    if not registry.matches:
        raise ValueError("registry is empty")
    student_numbers = {
        spelling
        for spelling, (kind, unused_name) in load_domain_roster().items()
        if kind == "student" and spelling.isdecimal()
    }
    number_pattern = (
        re.compile(
            "|".join(
                map(re.escape, sorted(student_numbers, key=len, reverse=True))
            )
        )
        if student_numbers
        else None
    )
    digests, held = [], []
    for info in sessions:
        path = Path(info["output_path"])
        provider, session_id = info["provider"], info["id"]
        if str(path.resolve()) in findings:
            held.append({"id": session_id, "reason": "secret_finding"})
            continue
        text = path.read_text(encoding="utf-8")
        turns = messages(text)
        user = next((body for role, body in turns if role == "User"), "")
        if info.get("thread_source") == "guardian_review" or user.startswith(
            AUTO_REVIEW_PROMPT
        ):
            held.append({"id": session_id, "reason": "auto_review"})
            continue
        if not user:
            held.append({"id": session_id, "reason": "no_user_message"})
            continue
        agent = next(
            (body for role, body in reversed(turns) if role == "Agent"), ""
        )
        tags = []
        orca_worker = "You are working inside Orca, a multi-agent IDE." in user
        if orca_worker:
            user = user.rsplit("=== TASK ===", 1)[-1].strip()
            tags.append("orca_worker")
        if (
            any(roster_match(text, match.pattern) for match in registry.matches)
            or number_pattern is not None
            and roster_match(text, number_pattern)
        ):
            tags.append("student_data")
        digests.append(
            {
                "id": session_id,
                "provider": provider,
                "project": info.get("project", ""),
                "tags": tags,
                "text": bounded_digest(
                    user, agent, info.get("project", ""), orca_worker
                ),
            }
        )
    write_jsonl(stage / "digests.jsonl", digests)
    write_jsonl(stage / "held.jsonl", held)
    return {"digests": len(digests), "held": len(held)}


async def mcp_classify(batches, purpose, server_command=None):
    """Send classification batches through the always-gated jev-mcp proxy."""
    server_command = server_command or [
        "uv",
        "--directory",
        str(ROOT / "packages/education-privacy-gate"),
        "run",
        "--frozen",
        "--offline",
        "--no-sync",
        "jev-mcp",
    ]
    server = StdioServerParameters(
        command=server_command[0],
        args=server_command[1:],
        cwd=str(ROOT),
    )
    responses = []
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            for batch in batches:
                result = await client.call_tool(
                    "jev_classify",
                    {
                        "items": batch["items"],
                        "classes": batch["classes"],
                        "purpose": purpose,
                    },
                )
                if (
                    result.is_error
                    or len(result.content) != 1
                    or result.content[0].type != "text"
                ):
                    raise RuntimeError("jev-mcp classification failed")
                try:
                    payload = json.loads(result.content[0].text)
                except json.JSONDecodeError:
                    raise RuntimeError(
                        "jev-mcp classification failed"
                    ) from None
                if not isinstance(payload, dict) or not isinstance(
                    payload.get("results"), list
                ):
                    raise RuntimeError("jev-mcp classification failed")
                responses.append(payload)
    return responses


def classify(stage, catalog_path, limit=None, call=None):
    """Sample digests, classify batches and write their labels."""
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    digests = read_jsonl(stage / "digests.jsonl")
    if limit is not None:
        digests = random.Random(0).sample(digests, min(limit, len(digests)))
    groups = (
        [item for item in digests if "student_data" not in item["tags"]],
        [item for item in digests if "student_data" in item["tags"]],
    )
    batches = []
    for group in groups:
        for start in range(0, len(group), BATCH_SIZE):
            items = group[start : start + BATCH_SIZE]
            classes = catalog["classes"]
            if items and "student_data" in items[0]["tags"]:
                classes = [
                    item for item in classes if item["id"] in {"work", "none"}
                ]
            offset = len(batches) * BATCH_SIZE
            batches.append(
                {
                    "digests": items,
                    "classes": classes,
                    "items": [
                        {"id": str(offset + index), "text": item["text"]}
                        for index, item in enumerate(items)
                    ],
                }
            )
    responses = (
        asyncio.run((call or mcp_classify)(batches, catalog["purpose"]))
        if batches
        else []
    )
    labels, usage = [], {"input_tokens": 0, "output_tokens": 0}
    for batch, response in zip(batches, responses, strict=True):
        for digest_item, result in zip(
            batch["digests"], response["results"], strict=True
        ):
            if (
                result.get("classification")
                not in {item["id"] for item in batch["classes"]}
                and result.get("classification") is not None
            ):
                raise ValueError("jev-mcp returned an unexpected class")
            labels.append(
                {
                    "id": digest_item["id"],
                    "label": result.get("classification"),
                    "confidence": result.get("confidence"),
                    "margin": result.get("margin"),
                    "decision": result["decision"],
                    "tags": digest_item["tags"],
                }
            )
        reported_usage = response.get("usage")
        for key in usage:
            value = (
                reported_usage.get(key)
                if isinstance(reported_usage, dict)
                else None
            )
            if type(value) in (int, float):
                usage[key] += value
    write_jsonl(stage / "labels.jsonl", labels)
    return {
        "jev_calls": len(batches),
        **usage,
    }


def main():
    """Run one session-selection subcommand."""
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    render_parser = commands.add_parser("render")
    digest_parser = commands.add_parser("digest")
    classify_parser = commands.add_parser("classify")
    for command in (render_parser, digest_parser, classify_parser):
        command.add_argument("--stage", required=True, type=Path)
    render_parser.add_argument("--specstory", default="specstory")
    digest_parser.add_argument("--scan", type=Path)
    classify_parser.add_argument("--catalog", required=True, type=Path)
    classify_parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    try:
        stage = stage_dir(args.stage)
        if args.command == "render":
            counts = render(stage, args.specstory)
        elif args.command == "digest":
            counts = digest(stage, args.scan)
        else:
            counts = classify(stage, args.catalog, args.limit)
    except Exception as error:  # noqa: BLE001 - never include session data in errors.
        parser.exit(1, f"session selection failed: {type(error).__name__}\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
