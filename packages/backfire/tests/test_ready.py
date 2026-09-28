"""Offline checks for the readiness command."""

import asyncio
import json
import platform
import subprocess

import pytest

from backfire import ready
from fake_provider import FakeProvider, completion


def configure(tmp_path, monkeypatch):
    directory = tmp_path / "config" / "verbose-broccoli" / "backfire"
    directory.mkdir(parents=True)
    (directory / "config.toml").write_text(
        """
provider = "readiness-test"
[providers.readiness-test]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "ready-model"
credential = "READY_KEY"
request = {max_tokens = 64, response_format = {type = "json_object"}}
thinking = {requested = "on", content_path = "reasoning_content", token_path = "reasoning_tokens"}
""",
        encoding="utf-8",
    )
    credential = directory / "readiness-test.env"
    credential.write_text("READY_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("BACKFIRE_TEST_PROVIDER_BASE_URL", raising=False)


@pytest.mark.parametrize("education", [False, True])
def test_installation_check_matches_project_extra(
    tmp_path, monkeypatch, education
):
    root = tmp_path / "component"
    (root / "src/backfire").mkdir(parents=True)
    if education:
        (root / "src/backfire_education").mkdir()
    (root / ".python-version").write_text(
        platform.python_version(), encoding="utf-8"
    )
    monkeypatch.setattr(ready, "_ROOT", root)
    monkeypatch.setattr(ready.sys, "prefix", str(root / ".venv"))
    monkeypatch.setattr(
        ready.backfire, "__file__", str(root / "src/backfire/__init__.py")
    )
    commands = []

    def sync(command, **kwargs):
        commands.append(command)
        installed_extra = "--extra" in command
        passed = "--no-dev" in command and installed_extra is education
        return subprocess.CompletedProcess(command, int(not passed), "", "")

    monkeypatch.setattr(ready.subprocess, "run", sync)
    versions = {
        key: "synthetic"
        for key in (
            "jev_mcp_port",
            "mcp",
            "rfc8785",
            "system_one_adapter",
            "typesafe_sdk",
            "openai",
            "python",
            "uv",
            "prompt_sha256",
        )
    }

    assert ready._installation_problem(versions) is None
    assert len(commands) == 2
    assert all(("--extra" in command) is education for command in commands)


@pytest.mark.parametrize("education", [False, True])
def test_installation_failure_prints_matching_sync_command(
    tmp_path, monkeypatch, capsys, education
):
    root = tmp_path / "component"
    (root / "src/backfire").mkdir(parents=True)
    if education:
        (root / "src/backfire_education").mkdir()
    (root / ".python-version").write_text(
        platform.python_version(), encoding="utf-8"
    )
    monkeypatch.setattr(ready, "_ROOT", root)
    monkeypatch.setattr(ready.sys, "prefix", str(root / ".venv"))
    monkeypatch.setattr(
        ready.backfire, "__file__", str(root / "src/backfire/__init__.py")
    )
    monkeypatch.setattr(
        ready,
        "_versions",
        lambda: {
            key: "synthetic"
            for key in (
                "jev_mcp_port",
                "mcp",
                "rfc8785",
                "system_one_adapter",
                "typesafe_sdk",
                "openai",
                "python",
                "uv",
                "prompt_sha256",
            )
        },
    )
    monkeypatch.setattr(
        ready.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, "", ""
        ),
    )

    assert ready.main() == 1
    install = (
        "uv sync --frozen --no-dev --extra education"
        if education
        else "uv sync --frozen --no-dev"
    )
    assert (
        capsys.readouterr().err
        == f"Readiness failed: run `{install}` in this component, then retry.\n"
    )


def test_direct_noul_uses_118_second_deadline_without_records(monkeypatch):
    observed = {}

    async def scripted(state, questions, *, deadline, record_file):
        observed.update(
            state=state,
            questions=questions,
            remaining=deadline - asyncio.get_running_loop().time(),
            record_file=record_file,
        )
        return {
            "model": "ready-model",
            "answers": {"ready": {"noul": 1.0}},
            "usage": {},
            "metadata": {"thinking_evidence": True, "latency_ms": 1.0},
        }

    monkeypatch.setattr(ready, "judge", scripted)
    asyncio.run(ready._direct_judgment())
    assert 117.9 < observed["remaining"] <= 118
    assert observed["record_file"] is None
    assert observed["questions"]["ready"]["type"] == "noul"


def test_ready_confirms_direct_and_server_tool_paths_with_fake_provider(
    tmp_path, monkeypatch, capsys
):
    configure(tmp_path, monkeypatch)
    script = [
        completion({"ready": 0.99}, model="ready-model"),
        completion({"p_proposition0": 0.99}, model="ready-model"),
        completion({"f0": {"c0": 1, "none_of_them": 0}}, model="ready-model"),
    ]
    with FakeProvider(script) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        code = ready.main()

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert captured.err == "Readiness passed.\n"
    assert report["requested"] == {
        "provider": "readiness-test",
        "api": "openai",
        "endpoint": fake.base_url,
        "model": "ready-model",
        "thinking": "on",
    }
    assert report["confirmed"] == {
        "provider": "readiness-test",
        "model": "ready-model",
        "thinking": "on",
    }
    assert report["unconfirmed"] == []
    assert report["BACKFIRE_TEST_PROVIDER_BASE_URL"] == fake.base_url
    assert (
        report["sample"]["answer"] == 0.99
        and report["sample"]["latency_ms"] > 0
    )
    assert [check["passed"] for check in report["tool_checks"]] == [
        True,
        True,
        True,
    ]
    assert report["tool_checks"][0]["detail"] == "11 tools"
    assert (
        report["tool_checks"][1]["detail"]
        == "expected verdict, record digest matches"
    )
    assert (
        report["tool_checks"][2]["detail"]
        == "verbatim value, record digest matches"
    )
    assert len(fake.requests) == 3
    assert "synthetic-key" not in captured.out + captured.err
    assert len(report["versions"]["prompt_sha256"]) == 64
    assert report["versions"]["jev_mcp_port"].endswith(
        "a1fcc1e47fc696614f081e23a66ff48a890f22fd"
    )


def test_missing_credential_fails_before_any_provider_request(
    tmp_path, monkeypatch, capsys
):
    configure(tmp_path, monkeypatch)
    (
        tmp_path
        / "config"
        / "verbose-broccoli"
        / "backfire"
        / "readiness-test.env"
    ).unlink()
    with FakeProvider([]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        code = ready.main()

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 1
    assert fake.requests == []
    assert "mode-0600 credential" in captured.err
    assert [check["passed"] for check in report["tool_checks"]] == [
        False,
        False,
        False,
    ]
    assert {item["item"] for item in report["unconfirmed"]} >= {
        "configuration",
        "provider",
        "model",
        "thinking",
    }
