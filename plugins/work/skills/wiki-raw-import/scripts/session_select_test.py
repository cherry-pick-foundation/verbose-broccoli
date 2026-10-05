"""Synthetic coverage for wiki-raw-import session selection."""

import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import random
import re
import sys
import textwrap
import time

from mcp.types import CallToolResult
from mcp.types import TextContent
import pytest

from education_privacy_gate.roster import Registry

sys.path.insert(0, str(Path(__file__).parent))
import session_select as selector  # noqa: E402


def roster_fixture(unused_path, monkeypatch):
    registry = Registry.from_data(
        {
            "version": 1,
            "entries": [
                {"kind": "person", "full": "SYNTHETIC_STUDENT"},
                {"kind": "person", "full": "SYNTHETIC_GUARDIAN"},
                {"kind": "school", "spellings": ["SYNTHETIC_SCHOOL"]},
            ],
        }
    )
    monkeypatch.setattr(selector, "load_registry", lambda: registry)
    monkeypatch.setattr(
        selector,
        "load_domain_roster",
        lambda: {
            "1234567890": ("student", "SYNTHETIC_STUDENT"),
        },
    )


def add_rendered(
    stage,
    provider,
    session_id,
    markdown,
    project="/synthetic/project",
    status="rendered",
    thread_source=None,
):
    path = stage / "rendered" / provider / f"{session_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    source = stage / "sources" / f"{session_id}.jsonl"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("synthetic source\n", encoding="utf-8")
    records = []
    sessions = stage / "sessions.jsonl"
    if sessions.exists():
        records = selector.read_jsonl(sessions)
    records.append(
        {
            "id": session_id,
            "provider": provider,
            "project": project,
            "source_path": str(source),
            "output_path": str(path),
            "mtime": source.stat().st_mtime,
            "status": status,
            "thread_source": thread_source,
        }
    )
    selector.write_jsonl(sessions, records)
    return path


def add_codex_session(
    home, filename, session_id, project, mtime, thread_source=None
):
    """Write one synthetic Codex rollout file."""
    path = home / ".codex/sessions/2026/09/30" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"id": session_id, "cwd": project}
    if thread_source is not None:
        payload["thread_source"] = thread_source
    path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": payload,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(path, (mtime, mtime))
    return path


def markdown(user=None, agent=None):
    chunks = []
    if user is not None:
        chunks.append(f"_**User**_\n\n{user}")
    if agent is not None:
        chunks.append(f"_**Agent**_\n\n{agent}")
    return "\n\n---\n\n".join(chunks) + "\n"


def empty_scan(stage):
    (stage / "scan.json").write_text("[]\n", encoding="utf-8")


def test_stage_dir_rejects_vault_raw_path(tmp_path):
    with pytest.raises(ValueError, match="outside repositories"):
        selector.stage_dir(tmp_path / "vaults" / "work" / "raw" / "stage")


def synthetic_catalog(tmp_path):
    catalog = {
        "purpose": "Synthetic classification purpose",
        "classes": [
            {"id": label, "description": f"Synthetic {label}"}
            for label in ("code", "work", "default", "chat", "none")
        ],
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog), encoding="utf-8")
    return path


def fake_mcp(calls, *, input_tokens=11, output_tokens=7):
    async def invoke(batches, purpose):
        calls.append((batches, purpose))
        return [
            {
                "results": [
                    {
                        "id": item["id"],
                        "classification": batch["classes"][0]["id"],
                        "confidence": 0.9,
                        "margin": 0.8,
                        "decision": "auto",
                    }
                    for item in batch["items"]
                ],
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
            }
            for batch in batches
        ]

    return invoke


def test_render_skips_running_and_renders_quiet_sessions(tmp_path, monkeypatch):
    home = tmp_path / "home"
    claude = home / ".claude/projects/escaped"
    codex = home / ".codex/sessions/2026/09/30"
    claude.mkdir(parents=True)
    codex.mkdir(parents=True)
    now = time.time()
    for name, mtime in (("running", now), ("finished", now - 7200)):
        path = claude / f"{name}.jsonl"
        path.write_text(
            json.dumps({"cwd": "/synthetic/workspace (gone)"}) + "\n"
        )
        os.utime(path, (mtime, mtime))
    nested = claude / "subagents/agent-synthetic.jsonl"
    nested.parent.mkdir()
    nested.write_text("synthetic nested record\n", encoding="utf-8")
    add_codex_session(
        home,
        "rollout-synthetic.jsonl",
        "codex-synthetic",
        "/synthetic/codex",
        now - 7200,
        thread_source="guardian_review",
    )
    newest_quiet = add_codex_session(
        home,
        "rollout-quiet-new.jsonl",
        "quiet-duplicate",
        "/synthetic/quiet",
        now - 4000,
        thread_source="subagent",
    )
    add_codex_session(
        home,
        "rollout-quiet-old.jsonl",
        "quiet-duplicate",
        "/synthetic/quiet",
        now - 7200,
    )
    add_codex_session(
        home,
        "rollout-running-new.jsonl",
        "running-duplicate",
        "/synthetic/running",
        now,
    )
    add_codex_session(
        home,
        "rollout-running-old.jsonl",
        "running-duplicate",
        "/synthetic/running",
        now - 7200,
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "https://synthetic.invalid"
    )
    monkeypatch.setenv("OTEL_SERVICE_NAME", "synthetic-test")
    stage = selector.stage_dir(tmp_path / "stage")
    (stage / "specstory/mirror/escaped").mkdir(parents=True)
    (stage / "specstory/claude/projects/stale").mkdir(parents=True)
    trace = stage / "trace.jsonl"
    fake = tmp_path / "specstory.py"
    fake.write_text(
        textwrap.dedent(
            r"""
            import json
            import os
            from pathlib import Path
            import re
            import sys

            args = sys.argv[1:]
            project = Path(args[args.index('--project-path') + 1])
            home = Path(os.environ['HOME'])
            config_dir = Path(args[args.index('--config-dir') + 1])
            config = Path(os.environ['CLAUDE_CONFIG_DIR'])
            store = config / 'projects' / re.sub(
                r'[^a-zA-Z0-9-]', '-', str(project.resolve())
            )
            source = Path(os.environ['SOURCE_TREE'])
            data = {
                'args': args,
                'cwd': os.getcwd(),
                'env': {
                    key: value
                    for key, value in os.environ.items()
                    if key in (
                        'HOME', 'XDG_CACHE_HOME', 'CLAUDE_CONFIG_DIR',
                        'CODEX_HOME'
                    ) or key.startswith('OTEL_')
                },
                'config': [
                    (home / '.specstory/cli/config.toml').read_text(),
                    (config_dir / 'config.toml').read_text(),
                ],
                'mirror': str(project),
                'mirror_exists': project.is_dir(),
                'store_exists': store.is_dir(),
                'nested_linked': False,
            }
            if args[1] == 'claude':
                source_file = source / 'subagents/agent-synthetic.jsonl'
                store_file = store / 'subagents/agent-synthetic.jsonl'
                data['nested_linked'] = (
                    source_file.stat().st_ino == store_file.stat().st_ino
                )
            with open(os.environ['TRACE'], 'a') as trace_file:
                trace_file.write(json.dumps(data) + '\n')
            database = Path(os.environ['HOME']) / '.specstory/sessions.db'
            database.parent.mkdir(parents=True, exist_ok=True)
            database.write_text('synthetic')
            print('_**User**_\n\nSYNTHETIC_REQUEST\n\n_**Agent**_\n\nSYNTHETIC_REPLY')
            """
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TRACE", str(trace))
    monkeypatch.setenv("SOURCE_TREE", str(claude))
    outside = {
        str(path.relative_to(tmp_path)): (
            path.stat().st_mtime_ns,
            path.stat().st_size,
        )
        for path in tmp_path.rglob("*")
        if not path.is_relative_to(stage)
    }
    counts = selector.render(stage, f"{sys.executable} {fake}", now=now)
    assert counts == {"rendered": 3, "running": 2, "failed": 0}
    runs = selector.read_jsonl(trace)
    assert len(runs) == 3
    assert {run["args"][3] for run in runs} == {
        "finished",
        "codex-synthetic",
        "quiet-duplicate",
    }
    claude_run = next(item for item in runs if item["args"][1] == "claude")
    assert claude_run["cwd"] == str(stage)
    assert claude_run["mirror_exists"] and claude_run["store_exists"]
    assert claude_run["nested_linked"]
    assert (
        claude_run["args"][claude_run["args"].index("--project-path") + 1]
        == claude_run["mirror"]
    )
    assert claude_run["args"][
        claude_run["args"].index("--config-dir") + 1
    ] == str(stage / "specstory")
    assert all(flag in claude_run["args"] for flag in selector.SPECSTORY_FLAGS)
    assert not {
        "--no-redact-secrets",
        "--log",
        "--debug",
        "--debug-raw",
        "--telemetry-endpoint",
        "--cloud-token",
    } & set(claude_run["args"])
    assert claude_run["env"]["HOME"] == str(stage / "specstory/home")
    assert claude_run["env"]["XDG_CACHE_HOME"] == str(stage / "specstory/cache")
    assert claude_run["env"]["CLAUDE_CONFIG_DIR"] == str(
        stage / "specstory/claude"
    )
    assert claude_run["env"]["CODEX_HOME"] == str(home / ".codex")
    assert claude_run["env"]["OTEL_SDK_DISABLED"] == "true"
    assert [key for key in claude_run["env"] if key.startswith("OTEL_")] == [
        "OTEL_SDK_DISABLED"
    ]
    assert claude_run["config"] == [
        selector.SPECSTORY_CONFIG,
        selector.SPECSTORY_CONFIG,
    ]
    assert not list((stage / "specstory/home/.specstory").glob("sessions.db*"))
    assert not (stage / "specstory/mirror/escaped").exists()
    assert not (stage / "specstory/claude/projects/stale").exists()
    assert not (
        stage
        / "specstory/claude/projects"
        / re.sub(
            r"[^a-zA-Z0-9-]",
            "-",
            str((stage / "specstory/mirror/escaped").resolve()),
        )
    ).exists()
    assert not (home / ".specstory").exists()
    assert outside == {
        str(path.relative_to(tmp_path)): (
            path.stat().st_mtime_ns,
            path.stat().st_size,
        )
        for path in tmp_path.rglob("*")
        if not path.is_relative_to(stage)
    }
    manifest = selector.read_jsonl(stage / "sessions.jsonl")
    statuses = {item["id"]: item["status"] for item in manifest}
    assert len(manifest) == 5
    quiet_record = next(
        item for item in manifest if item["id"] == "quiet-duplicate"
    )
    assert quiet_record["source_path"] == str(newest_quiet)
    assert quiet_record["mtime"] == newest_quiet.stat().st_mtime
    assert quiet_record["thread_source"] == "subagent"
    assert (
        next(item for item in manifest if item["id"] == "codex-synthetic")[
            "thread_source"
        ]
        == "guardian_review"
    )
    assert (
        next(item for item in manifest if item["id"] == "running")[
            "thread_source"
        ]
        is None
    )
    assert statuses == {
        "running": "running",
        "finished": "rendered",
        "codex-synthetic": "rendered",
        "quiet-duplicate": "rendered",
        "running-duplicate": "running",
    }


def test_digest_holds_scan_findings_before_classification(
    tmp_path, monkeypatch
):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    held_path = add_rendered(
        stage,
        "claude",
        "secret-synthetic",
        markdown("SYNTHETIC_PROMPT", "SYNTHETIC_REPLY"),
    )
    add_rendered(
        stage,
        "codex",
        "clear-synthetic",
        markdown("SYNTHETIC_OTHER", "SYNTHETIC_DONE"),
    )
    (stage / "scan.json").write_text(
        json.dumps([{"File": str(held_path)}]), encoding="utf-8"
    )
    assert selector.digest(stage) == {"digests": 1, "held": 1}
    assert selector.read_jsonl(stage / "held.jsonl") == [
        {"id": "secret-synthetic", "reason": "secret_finding"}
    ]
    calls = []
    counts = selector.classify(
        stage, synthetic_catalog(tmp_path), call=fake_mcp(calls)
    )
    sent_ids = [
        item["id"] for batch in calls[0][0] for item in batch["digests"]
    ]
    assert len(sent_ids) == 1
    assert (
        selector.read_jsonl(stage / "labels.jsonl")[0]["id"]
        == "clear-synthetic"
    )
    assert counts["jev_calls"] == 1


def test_digest_holds_no_user_and_tags_orca_roster_match(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(
        stage, "claude", "agent-only", markdown(agent="SYNTHETIC_REPLY")
    )
    add_rendered(
        stage,
        "codex",
        "orca-synthetic",
        markdown(
            "You are working inside Orca, a multi-agent IDE.\n\n"
            "=== TASK ===\nSYNTHETIC_STUDENT task",
            "SYNTHETIC_FINAL_REPORT",
        ),
    )
    empty_scan(stage)
    assert selector.digest(stage) == {"digests": 1, "held": 1}
    assert selector.read_jsonl(stage / "held.jsonl") == [
        {"id": "agent-only", "reason": "no_user_message"}
    ]
    result = selector.read_jsonl(stage / "digests.jsonl")[0]
    assert result["tags"] == ["orca_worker", "student_data"]
    assert result["text"] == (
        "Project: /synthetic/project\n"
        "Orca worker session. Task:\n"
        "SYNTHETIC_STUDENT task\n\nSYNTHETIC_FINAL_REPORT"
    )


def test_digest_bounds_excerpt_to_two_thousand_characters(
    tmp_path, monkeypatch
):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(
        stage, "claude", "long-synthetic", markdown("U" * 3000, "A" * 3000)
    )
    empty_scan(stage)
    selector.digest(stage)
    text = selector.read_jsonl(stage / "digests.jsonl")[0]["text"]
    assert len(text) <= 2000
    assert text.startswith("Project: /synthetic/project\nU") and text.endswith(
        "A"
    )


def test_digest_holds_auto_reviews_before_roster_matching(
    tmp_path, monkeypatch
):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(
        stage,
        "codex",
        "guardian-review",
        markdown("SYNTHETIC_STUDENT approval request"),
        thread_source="guardian_review",
    )
    add_rendered(
        stage,
        "codex",
        "subagent-review",
        markdown(
            selector.AUTO_REVIEW_PROMPT + "\nSYNTHETIC_STUDENT approval request"
        ),
        thread_source="subagent",
    )
    add_rendered(
        stage,
        "codex",
        "ordinary-session",
        markdown("SYNTHETIC_STUDENT ordinary request"),
    )
    empty_scan(stage)
    assert selector.digest(stage) == {"digests": 1, "held": 2}
    assert selector.read_jsonl(stage / "held.jsonl") == [
        {"id": "guardian-review", "reason": "auto_review"},
        {"id": "subagent-review", "reason": "auto_review"},
    ]
    digest = selector.read_jsonl(stage / "digests.jsonl")[0]
    assert digest["id"] == "ordinary-session"
    assert digest["tags"] == ["student_data"]
    calls = []
    selector.classify(stage, synthetic_catalog(tmp_path), call=fake_mcp(calls))
    sent_ids = [
        item["id"] for batch in calls[0][0] for item in batch["digests"]
    ]
    assert sent_ids == ["ordinary-session"]


def test_digest_uses_only_rendered_manifest_outputs(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(
        stage,
        "codex",
        "rendered-session",
        markdown("SYNTHETIC_RENDERED"),
    )
    add_rendered(
        stage,
        "codex",
        "running-session",
        markdown("SYNTHETIC_STALE"),
        status="running",
    )
    orphan = stage / "rendered/codex/orphan-session.md"
    orphan.write_text(markdown("SYNTHETIC_ORPHAN"), encoding="utf-8")
    empty_scan(stage)
    assert selector.digest(stage) == {"digests": 1, "held": 0}
    assert [
        item["id"] for item in selector.read_jsonl(stage / "digests.jsonl")
    ] == ["rendered-session"]


def test_main_error_names_exception_without_its_message(
    tmp_path, monkeypatch, capsys
):
    stage = selector.stage_dir(tmp_path / "stage")
    monkeypatch.setattr(
        sys, "argv", ["session_select.py", "digest", "--stage", str(stage)]
    )
    with pytest.raises(SystemExit) as error:
        selector.main()
    assert error.value.code == 1
    assert (
        capsys.readouterr().err
        == "session selection failed: FileNotFoundError\n"
    )


def test_student_data_uses_only_work_and_none_classes(tmp_path):
    stage = selector.stage_dir(tmp_path / "stage")
    selector.write_jsonl(
        stage / "digests.jsonl",
        [
            {
                "id": "ordinary",
                "provider": "claude",
                "project": "p",
                "tags": [],
                "text": "synthetic",
            },
            {
                "id": "student",
                "provider": "codex",
                "project": "p",
                "tags": ["student_data"],
                "text": "synthetic",
            },
        ],
    )
    calls = []
    counts = selector.classify(
        stage, synthetic_catalog(tmp_path), call=fake_mcp(calls)
    )
    batches = calls[0][0]
    by_id = {
        batch["digests"][0]["id"]: {item["id"] for item in batch["classes"]}
        for batch in batches
    }
    assert by_id["ordinary"] == {"code", "work", "default", "chat", "none"}
    assert by_id["student"] == {"work", "none"}
    assert counts["input_tokens"] == 22 and counts["output_tokens"] == 14


def test_classify_samples_and_batches_at_most_sixty_four(tmp_path):
    stage = selector.stage_dir(tmp_path / "stage")
    digests = [
        {
            "id": f"item-{index}",
            "provider": "claude",
            "project": "p",
            "tags": [],
            "text": "synthetic",
        }
        for index in range(130)
    ]
    selector.write_jsonl(stage / "digests.jsonl", digests)
    calls = []
    counts = selector.classify(
        stage,
        synthetic_catalog(tmp_path),
        limit=70,
        call=fake_mcp(calls, input_tokens=3, output_tokens=2),
    )
    batches = calls[0][0]
    labels = selector.read_jsonl(stage / "labels.jsonl")
    expected = [item["id"] for item in random.Random(0).sample(digests, 70)]
    assert [item["id"] for item in labels] == expected
    assert [len(batch["items"]) for batch in batches] == [64, 6]
    assert counts == {
        "jev_calls": 2,
        "input_tokens": 6,
        "output_tokens": 4,
    }


def test_messages_keep_pasted_separators_and_strip_message_separator():
    source = (
        "_**User**_\n\nfirst line\n---\npasted line\n---\n\n"
        "_**Agent**_\n\nreply\n---\n\n"
    )
    assert selector.messages(source) == [
        ("User", "first line\n---\npasted line"),
        ("Agent", "reply"),
    ]


def test_orca_detection_and_last_task_marker(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(
        stage,
        "claude",
        "orca-with-task",
        markdown(
            "typed preface\nYou are working inside Orca, a multi-agent IDE.\n"
            "=== TASK ===\nold task\n=== TASK ===\nlast task",
            "synthetic reply",
        ),
    )
    add_rendered(
        stage,
        "codex",
        "orca-without-task",
        markdown(
            "typed preface\nYou are working inside Orca, a multi-agent IDE.\n"
            "whole user message",
            "synthetic reply",
        ),
    )
    empty_scan(stage)

    assert selector.digest(stage) == {"digests": 2, "held": 0}
    digests = {
        item["id"]: item
        for item in selector.read_jsonl(stage / "digests.jsonl")
    }
    assert digests["orca-with-task"]["tags"] == ["orca_worker"]
    assert digests["orca-with-task"]["text"] == (
        "Project: /synthetic/project\n"
        "Orca worker session. Task:\n"
        "last task\n\nsynthetic reply"
    )
    assert digests["orca-without-task"]["tags"] == ["orca_worker"]
    assert digests["orca-without-task"]["text"] == (
        "Project: /synthetic/project\n"
        "Orca worker session. Task:\n"
        "typed preface\nYou are working inside Orca, a multi-agent IDE.\n"
        "whole user message\n\nsynthetic reply"
    )


def test_roster_match_uses_requested_boundaries():
    pattern = re.compile(r"가가|Student7")
    assert not selector.roster_match("이름가가", pattern)
    assert not selector.roster_match("x가가", pattern)
    assert not selector.roster_match("Student77", pattern)
    assert selector.roster_match("가가님", pattern)
    assert selector.roster_match("Student7!", pattern)
    assert selector.roster_match("Student7명", pattern)


def test_empty_specstory_output_is_failed(tmp_path, monkeypatch):
    home = tmp_path / "home"
    add_codex_session(
        home,
        "rollout-empty.jsonl",
        "empty-output",
        "/synthetic/project",
        time.time() - 7200,
    )
    monkeypatch.setenv("HOME", str(home))
    stage = selector.stage_dir(tmp_path / "stage")
    empty = tmp_path / "empty_specstory.py"
    empty.write_text("pass\n", encoding="utf-8")

    assert selector.render(stage, f"{sys.executable} {empty}") == {
        "rendered": 0,
        "running": 0,
        "failed": 1,
    }
    assert (
        selector.read_jsonl(stage / "sessions.jsonl")[0]["status"] == "failed"
    )


def test_mcp_classify_uses_stdio_client(tmp_path):
    server_script = tmp_path / "mcp_server.py"
    server_script.write_text(
        textwrap.dedent(
            """\
            from mcp.server.mcpserver import MCPServer

            server = MCPServer("synthetic")

            @server.tool()
            def jev_classify(
                items: list[dict], classes: list[dict], purpose: str
            ) -> dict:
                return {
                    "results": [
                        {
                            "id": item["id"],
                            "classification": "work",
                            "confidence": 0.9,
                            "margin": 0.7,
                            "decision": "auto",
                        }
                        for item in items
                    ],
                    "usage": {"input_tokens": 4, "output_tokens": 2},
                }

            server.run()
            """
        ),
        encoding="utf-8",
    )
    batch = {
        "items": [{"id": "synthetic-0", "text": "synthetic request"}],
        "classes": [{"id": "work", "description": "synthetic work"}],
    }

    result = asyncio.run(
        selector.mcp_classify(
            [batch], "synthetic purpose", [sys.executable, str(server_script)]
        )
    )

    assert result[0]["results"][0]["classification"] == "work"
    assert result[0]["usage"] == {"input_tokens": 4, "output_tokens": 2}


def test_digest_matches_finding_through_stage_symlink(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "actual")
    alias = tmp_path / "stage-link"
    alias.symlink_to(stage, target_is_directory=True)
    output = add_rendered(
        stage, "claude", "linked-session", markdown("SYNTHETIC_PROMPT")
    )
    empty_scan(stage)
    (stage / "scan.json").write_text(
        json.dumps([{"File": str(alias / output.relative_to(stage))}]),
        encoding="utf-8",
    )
    assert selector.digest(stage) == {"digests": 0, "held": 1}


def test_digest_rejects_missing_and_stale_scan(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    output = add_rendered(
        stage, "claude", "new-session", markdown("SYNTHETIC_PROMPT")
    )
    with pytest.raises(FileNotFoundError):
        selector.digest(stage)
    empty_scan(stage)
    os.utime(stage / "scan.json", (1, 1))
    os.utime(output, (10, 10))
    with pytest.raises(ValueError, match="stale"):
        selector.digest(stage)


def test_digest_rejects_empty_roster(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(stage, "claude", "empty-roster", markdown("SYNTHETIC"))
    empty_scan(stage)
    monkeypatch.setattr(
        selector,
        "load_registry",
        lambda: Registry.from_data({"version": 1, "entries": []}),
    )
    with pytest.raises(ValueError, match="registry is empty"):
        selector.digest(stage)


def test_render_invalid_codex_id_uses_file_stem(tmp_path, monkeypatch):
    home = tmp_path / "home"
    path = add_codex_session(
        home, "rollout-invalid-id.jsonl", None, "/synthetic/project", 1
    )
    monkeypatch.setenv("HOME", str(home))
    stage = selector.stage_dir(tmp_path / "stage")
    assert selector.render(stage, "unused", now=10000) == {
        "rendered": 0,
        "running": 0,
        "failed": 1,
    }
    assert selector.read_jsonl(stage / "sessions.jsonl")[0]["id"] == path.stem


def test_render_timeout_continues_after_failed_session(tmp_path, monkeypatch):
    home = tmp_path / "home"
    for session_id in ("timeout", "continues"):
        add_codex_session(
            home,
            f"rollout-{session_id}.jsonl",
            session_id,
            "/synthetic/project",
            1,
        )
    monkeypatch.setenv("HOME", str(home))
    stage = selector.stage_dir(tmp_path / "stage")
    calls = []

    def run(command, **kwargs):
        calls.append(kwargs["timeout"])
        if command[4] == "timeout":
            raise selector.subprocess.TimeoutExpired(command, kwargs["timeout"])
        return selector.subprocess.CompletedProcess(
            command, 0, "_**User**_\n\nrequest", ""
        )

    monkeypatch.setattr(selector.subprocess, "run", run)
    assert selector.render(stage, "specstory", now=10000) == {
        "rendered": 1,
        "running": 0,
        "failed": 1,
    }
    assert calls == [300, 300]


@pytest.mark.parametrize(
    ("text", "is_error", "succeeds"),
    [
        ('{"results": []}', False, True),
        ("SYNTHETIC_ERROR", True, False),
        ("not JSON", False, False),
        ("[]", False, False),
    ],
)
@pytest.mark.parametrize(
    "config", ["/synthetic/config", None, "relative/config", ""]
)
def test_proxy_launcher_and_classification_result_shape(
    monkeypatch, text, is_error, succeeds, config
):
    if config is None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", config)
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-marker")
    monkeypatch.setenv("JEV_PROVIDER", "synthetic-marker")
    monkeypatch.setenv("NODE_OPTIONS", "synthetic-marker")
    launches, calls = [], []

    @asynccontextmanager
    async def transport(server):
        launches.append(server)
        yield None, None

    class Client:
        def __init__(self, *unused):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *unused):
            pass

        async def initialize(self):
            pass

        async def call_tool(self, name, arguments):
            calls.append((name, arguments))
            return CallToolResult(
                content=[TextContent(type="text", text=text)],
                is_error=is_error,
            )

    monkeypatch.setattr(selector, "stdio_client", transport)
    monkeypatch.setattr(selector, "ClientSession", Client)
    batch = {"items": [], "classes": []}
    if succeeds:
        assert asyncio.run(selector.mcp_classify([batch], "synthetic")) == [
            {"results": []}
        ]
    else:
        with pytest.raises(RuntimeError, match="jev-mcp classification failed"):
            asyncio.run(selector.mcp_classify([batch], "synthetic"))
    assert launches[0].command == "uv"
    assert launches[0].args == [
        "--directory",
        str(selector.ROOT / "packages/education-privacy-gate"),
        "run",
        "--frozen",
        "--offline",
        "--no-sync",
        "jev-mcp",
    ]
    expected = (
        {"XDG_CONFIG_HOME": config}
        if config and config.startswith("/")
        else None
    )
    assert launches[0].env == expected
    assert calls == [("jev_classify", {**batch, "purpose": "synthetic"})]


def test_classify_rejects_out_of_scope_student_label(tmp_path):
    stage = selector.stage_dir(tmp_path / "stage")
    selector.write_jsonl(
        stage / "digests.jsonl",
        [
            {
                "id": "synthetic",
                "tags": ["student_data"],
                "text": "synthetic",
            }
        ],
    )

    async def wrong_label(*unused_args):
        return [{"results": [{"classification": "code", "decision": "auto"}]}]

    with pytest.raises(ValueError, match="unexpected class"):
        selector.classify(stage, synthetic_catalog(tmp_path), call=wrong_label)
    assert not (stage / "labels.jsonl").exists()


def test_student_number_only_session_stays_work_only(tmp_path, monkeypatch):
    roster_fixture(tmp_path, monkeypatch)
    stage = selector.stage_dir(tmp_path / "stage")
    add_rendered(stage, "codex", "number-only", markdown("s-1234567890"))
    empty_scan(stage)
    assert selector.digest(stage) == {"digests": 1, "held": 0}
    assert selector.read_jsonl(stage / "digests.jsonl")[0]["tags"] == [
        "student_data"
    ]


@pytest.mark.parametrize("status", ["invalid_response", None])
def test_classify_null_review_rejects_only_invalid_response(tmp_path, status):
    stage = selector.stage_dir(tmp_path / "stage")
    selector.write_jsonl(
        stage / "digests.jsonl",
        [{"id": "synthetic", "tags": [], "text": "synthetic"}],
    )

    async def invoke(*unused_args):
        row = {"classification": None, "decision": "review"}
        if status is not None:
            row["status"] = status
        return [{"results": [row]}]

    if status == "invalid_response":
        with pytest.raises(
            ValueError, match="^jev-mcp returned an invalid response$"
        ):
            selector.classify(stage, synthetic_catalog(tmp_path), call=invoke)
        assert not (stage / "labels.jsonl").exists()
    else:
        selector.classify(stage, synthetic_catalog(tmp_path), call=invoke)
        labels = selector.read_jsonl(stage / "labels.jsonl")
        assert len(labels) == 1
        assert labels[0]["label"] is None
        assert labels[0]["decision"] == "review"


@pytest.mark.parametrize(
    "usage",
    [
        "synthetic",
        {"input_tokens": {"nested": 1}, "output_tokens": "synthetic"},
    ],
)
def test_classify_does_not_treat_text_usage_as_token_counts(tmp_path, usage):
    stage = selector.stage_dir(tmp_path / "stage")
    selector.write_jsonl(
        stage / "digests.jsonl",
        [
            {
                "id": "synthetic",
                "tags": [],
                "text": "synthetic",
            }
        ],
    )

    async def invoke(*unused_args):
        return [
            {
                "results": [{"classification": "work", "decision": "review"}],
                "usage": usage,
            }
        ]

    counts = selector.classify(stage, synthetic_catalog(tmp_path), call=invoke)
    assert counts == {"jev_calls": 1, "input_tokens": 0, "output_tokens": 0}
