import asyncio
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import tomllib

import anyio
from fake_provider import FakeProvider
from fake_provider import completion
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest

from backfire import config
from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge
from backfire.tools import find
from backfire_education.pseudonymize import pseudonymize
from backfire_education.table import assign
from backfire_tools.build import ROOT
from backfire_tools.build import build

TOOL_NAMES = {
    "backfire_gate",
    "backfire_review",
    "backfire_verify",
    "backfire_noul",
    "backfire_classify",
    "backfire_find",
    "backfire_rerank",
    "backfire_compare",
    "backfire_screen",
    "backfire_extract",
    "backfire_decide",
}
STUDENT_A, STUDENT_B, STUDENT_C = "가라온", "나새봄", "다초록"
GIVEN_A, GIVEN_B = "라온", "새봄"
GUARDIANS = ("다누리", "마루나")
SCHOOLS = ("가상별학교", "바람숲학교")
PHONE, EMAIL = "+1 202-555-0123", "synthetic.one@example.test"


def write_roster(path: Path, names=(STUDENT_A, STUDENT_B)):
    rows = [
        (names[0], SCHOOLS[0], GUARDIANS[0], "3"),
        (names[1], SCHOOLS[1], GUARDIANS[1], "2"),
    ]
    if len(names) == 3:
        rows.append((names[2], "초록별학교", "", "1"))
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("name", "school", "guardians", "grade"))
        writer.writerows(rows)


def find_args(candidates):
    return {
        "query": "Find the synthetic progress note.",
        "candidates": candidates,
    }


async def capture_find(arguments):
    captured = {}

    async def capture(state, questions, *, deadline, record_file):
        del deadline, record_file  # Unused.
        captured["state"] = state
        captured["questions"] = questions
        labels = list(questions["best"]["criteria"])
        return {
            "model": "synthetic-model",
            "answers": {
                "best": {
                    "type": "choice",
                    "choice": labels[0],
                    "confidence": 0.9,
                    "probabilities": {labels[0]: 0.9, labels[1]: 0.1},
                },
                "exists": {"type": "noul", "noul": 0.9},
            },
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    await find.call(
        arguments,
        capture,
        deadline=asyncio.get_running_loop().time() + 10,
        record_file=None,
    )
    return captured


def answer_questions(masked_questions):
    question = masked_questions["best"]
    criteria = (
        question.criteria
        if hasattr(question, "criteria")
        else question["criteria"]
    )
    labels = list(criteria)
    return {"best": {labels[0]: 0.8, labels[1]: 0.2}, "exists": 0.9}


def process_messages(
    plugin: Path,
    config_home: Path,
    data_home: Path,
    state_home: Path,
    uv: str,
    base_url: str,
    callback,
):
    async def run():
        parameters = StdioServerParameters(
            command=shutil.which("env"),
            args=[
                "-i",
                f"XDG_CONFIG_HOME={config_home}",
                f"XDG_DATA_HOME={data_home}",
                f"XDG_STATE_HOME={state_home}",
                f"BACKFIRE_TEST_PROVIDER_BASE_URL={base_url}",
                uv,
                "--directory",
                str(plugin / "backfire"),
                "run",
                "--frozen",
                "--offline",
                "--no-sync",
                "backfire",
                "serve-mcp",
            ],
            cwd=plugin.parent,
        )
        with anyio.fail_after(45):
            async with stdio_client(parameters) as streams:
                async with ClientSession(*streams) as client:
                    initialized = await client.initialize()
                    assert initialized.server_info.name == "backfire"
                    tools = (await client.list_tools()).tools
                    assert len(tools) == 11
                    assert {tool.name for tool in tools} == TOOL_NAMES
                    await callback(client)

    asyncio.run(run())


async def successful_call(client, name, arguments):
    result = await client.call_tool(name, arguments)
    assert not result.is_error, result.content[0].text
    return json.loads(result.content[0].text)


async def failed_call(
    client, provider, name, arguments, error_type, detail=None
):
    before = len(provider.requests)
    result = await client.call_tool(name, arguments)
    assert result.is_error
    message = result.content[0].text
    assert message.startswith(f"{error_type}:")
    if detail is not None:
        assert detail in message
    assert all(
        value not in message
        for value in (
            STUDENT_A,
            STUDENT_B,
            STUDENT_C,
            GIVEN_A,
            GIVEN_B,
            *GUARDIANS,
            *SCHOOLS,
            PHONE,
            EMAIL,
        )
    )
    assert len(provider.requests) == before


def test_built_work_server_pseudonymizes_restores_and_fails_closed(monkeypatch):
    uv = shutil.which("uv")
    assert uv is not None, (
        "Run npm run backfire:install to prepare uv and its caches."
    )
    uv = str(Path(uv).resolve())
    with TemporaryDirectory(prefix="backfire-education-") as temporary:
        parent = Path(temporary).resolve()
        assert not parent.is_relative_to(ROOT)
        plugin = build(parent / "work", plugin="work")
        install = subprocess.run(
            [uv, "sync", "--frozen", "--no-dev", "--extra", "education"],
            cwd=plugin / "backfire",
            env={**os.environ, "UV_OFFLINE": "1"},
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert install.returncode == 0, install.stderr

        config_home, data_home, state_home = (
            parent / name for name in ("config", "data", "state")
        )
        monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
        monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
        monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
        operator = config_home / "verbose-broccoli" / "backfire"
        operator.mkdir(parents=True)
        roster_path = parent / "synthetic-roster.csv"
        write_roster(roster_path)
        config_path = operator / "education.toml"
        config_path.write_text(
            f"roster = {json.dumps(str(roster_path))}\n", encoding="utf-8"
        )
        profile_path = plugin / "backfire" / "src" / "backfire" / "config.toml"
        profile = tomllib.loads(profile_path.read_text(encoding="utf-8"))
        credential_name = profile["providers"][profile["provider"]][
            "credential"
        ]
        credential = operator / "education.env"
        credential.write_text(
            f"{credential_name}=synthetic-test-key\n", encoding="utf-8"
        )
        credential.chmod(0o600)
        table_path = (
            data_home / "verbose-broccoli" / "backfire" / "pseudonyms.json"
        )
        try:
            seeded = assign([("student", STUDENT_A), ("student", STUDENT_B)])
            assert seeded == {
                ("student", STUDENT_A): "학생01",
                ("student", STUDENT_B): "학생02",
            }

            first_find = find_args(
                [
                    {
                        "id": "synthetic-a",
                        "text": (
                            f"{STUDENT_A}은 2026-09-28 91점을 받았다. "
                            f"{GIVEN_A}이는 {GUARDIANS[0]}와 "
                            f"{SCHOOLS[0]}에서 연습했다. "
                            f"연락처 {PHONE}, 이메일 {EMAIL}."
                        ),
                    },
                    {
                        "id": "synthetic-b",
                        "text": (
                            f"{STUDENT_B}은 2026-09-27 84점을 받았다. "
                            f"{GIVEN_B}이는 {GUARDIANS[1]}와 "
                            f"{SCHOOLS[1]}에서 복습했다."
                        ),
                    },
                ]
            )
            captured = asyncio.run(capture_find(first_find))
            _, expected_questions, _ = pseudonymize(
                captured["state"],
                captured["questions"],
            )
            best = expected_questions["best"]
            first_labels = list(
                best.criteria if hasattr(best, "criteria") else best["criteria"]
            )
            assert first_labels == ["synthetic-a", "synthetic-b"]
            assert len(set(seeded.values())) == 2
            assert "학생03" not in seeded.values()

            baseline_answers = {
                "best": {"synthetic-a": 0.8, "synthetic-b": 0.2},
                "exists": 0.9,
            }
            with FakeProvider([completion(baseline_answers)]) as baseline:
                monkeypatch.setenv(
                    "BACKFIRE_TEST_PROVIDER_BASE_URL", baseline.base_url
                )
                monkeypatch.setattr(config, "SHIPPED_CONFIG", profile_path)

                async def baseline_call():
                    return await judge(
                        captured["state"],
                        captured["questions"],
                        deadline=asyncio.get_running_loop().time() + 10,
                        pseudonymize=False,
                    )

                asyncio.run(baseline_call())
                baseline_body = baseline.requests[0]["body"]
                transformed_messages, _, _ = pseudonymize(
                    baseline_body["messages"], {}
                )

            with FakeProvider([]) as conflict_provider:
                monkeypatch.setenv(
                    "BACKFIRE_TEST_PROVIDER_BASE_URL",
                    conflict_provider.base_url,
                )

                async def conflict_call():
                    return await judge(
                        {"record": "synthetic"},
                        {
                            "q": {
                                "type": "choice",
                                "criteria": {
                                    STUDENT_A: None,
                                    GIVEN_A: None,
                                },
                            }
                        },
                        deadline=asyncio.get_running_loop().time() + 10,
                    )

                with pytest.raises(JudgmentError) as caught:
                    asyncio.run(conflict_call())
                assert caught.value.error_type == "pseudonym_conflict"
                assert STUDENT_A not in str(
                    caught.value
                ) and GIVEN_A not in str(caught.value)
                assert conflict_provider.requests == []

            def classify_reply():
                return completion({"i0": {"c0": 0.9, "c1": 0.1}})

            def verify_reply():
                return completion(
                    {
                        "relation_claim0": {
                            "supports": 0.9,
                            "contradicts": 0.05,
                            "says_nothing": 0.05,
                        }
                    }
                )

            next_student = "학생03"
            with FakeProvider(
                [
                    classify_reply(),
                    verify_reply(),
                    completion(answer_questions(expected_questions)),
                    completion(
                        {
                            "best": {
                                "synthetic-a": 0.7,
                                "synthetic-b": 0.2,
                                "synthetic-c": 0.1,
                            },
                            "exists": 0.9,
                        }
                    ),
                ]
            ) as provider:

                async def first_session(client):
                    classification = await successful_call(
                        client,
                        "backfire_classify",
                        {
                            "items": [
                                {
                                    "id": "synthetic-item",
                                    "text": (
                                        f"{STUDENT_A}은 {GIVEN_A}이가 "
                                        f"{SCHOOLS[0]}에서 연습했다."
                                    ),
                                }
                            ],
                            "classes": [
                                {
                                    "id": STUDENT_A,
                                    "description": f"{STUDENT_A}의 진전 기록",
                                },
                                {
                                    "id": STUDENT_B,
                                    "description": f"{STUDENT_B}의 진전 기록",
                                },
                            ],
                        },
                    )
                    assert (
                        classification["results"][0]["classification"]
                        == STUDENT_A
                    )
                    assert (
                        classification["results"][0]["id"] == "synthetic-item"
                    )

                    claim = (
                        f"{STUDENT_A}은 91점을 받았고 "
                        f"{GIVEN_A}이는 꾸준히 연습했다."
                    )
                    verified = await successful_call(
                        client,
                        "backfire_verify",
                        {
                            "claims": [claim],
                            "evidence": (
                                f"{STUDENT_A}의 {SCHOOLS[0]} 기록은 "
                                f"{GUARDIANS[0]}가 확인했다. "
                                f"연락처 {PHONE}, 이메일 {EMAIL}."
                            ),
                        },
                    )
                    assert verified["results"][0]["claim"] == claim

                    found = await successful_call(
                        client, "backfire_find", first_find
                    )
                    assert found["top"][0]["id"] == "synthetic-a"
                    assert (
                        found["top"][0]["text"]
                        == first_find["candidates"][0]["text"]
                    )
                    assert "학생" not in json.dumps(
                        [classification, verified, found], ensure_ascii=False
                    )

                process_messages(
                    plugin,
                    config_home,
                    data_home,
                    state_home,
                    uv,
                    provider.base_url,
                    first_session,
                )
                assert len(provider.requests) == 3

                second_names = (STUDENT_A, STUDENT_B, STUDENT_C)
                write_roster(roster_path, second_names)
                second_find = find_args(
                    [
                        {"id": "synthetic-a", "text": f"{STUDENT_A} 91점 기록"},
                        {"id": "synthetic-b", "text": f"{STUDENT_B} 84점 기록"},
                        {"id": "synthetic-c", "text": f"{STUDENT_C} 77점 기록"},
                    ]
                )

                async def second_session(client):
                    result = await successful_call(
                        client, "backfire_find", second_find
                    )
                    assert result["top"][0]["id"] == "synthetic-a"
                    assert result["top"][-1]["id"] == "synthetic-c"
                    assert "학생" not in json.dumps(result, ensure_ascii=False)

                    valid_config = config_path.read_bytes()
                    valid_roster = roster_path.read_bytes()
                    data_dir = xdg_path("data") / "backfire"
                    table_path = data_dir / "pseudonyms.json"
                    lock_path = data_dir / "pseudonyms.lock"
                    valid_table = table_path.read_bytes()
                    valid_lock = lock_path.read_bytes()

                    for contents in (
                        b"roster = [\n",
                        b'roster = "relative.csv"\n',
                        (
                            f"roster = {json.dumps(str(roster_path))}\n"
                            "extra = true\n"
                        ).encode(),
                    ):
                        config_path.write_bytes(contents)
                        await failed_call(
                            client,
                            provider,
                            "backfire_find",
                            second_find,
                            "backend_not_configured",
                            str(config_path),
                        )
                    config_path.unlink()
                    await failed_call(
                        client,
                        provider,
                        "backfire_find",
                        second_find,
                        "backend_not_configured",
                        str(config_path),
                    )
                    config_path.write_bytes(valid_config)

                    missing_roster = parent / "missing-roster.csv"
                    config_path.write_text(
                        f"roster = {json.dumps(str(missing_roster))}\n",
                        encoding="utf-8",
                    )
                    await failed_call(
                        client,
                        provider,
                        "backfire_find",
                        second_find,
                        "backend_not_configured",
                        str(missing_roster),
                    )
                    directory_roster = parent / "roster-directory"
                    directory_roster.mkdir()
                    config_path.write_text(
                        f"roster = {json.dumps(str(directory_roster))}\n",
                        encoding="utf-8",
                    )
                    await failed_call(
                        client,
                        provider,
                        "backfire_find",
                        second_find,
                        "backend_not_configured",
                        str(directory_roster),
                    )
                    for contents in (
                        b"name\n\xff\n",
                        b"school\nsynthetic\n",
                        b"name,school\n,synthetic\n",
                    ):
                        roster_path.write_bytes(contents)
                        config_path.write_text(
                            f"roster = {json.dumps(str(roster_path))}\n",
                            encoding="utf-8",
                        )
                        await failed_call(
                            client,
                            provider,
                            "backfire_find",
                            second_find,
                            "backend_not_configured",
                            str(roster_path),
                        )
                    roster_path.write_bytes(valid_roster)
                    config_path.write_bytes(valid_config)

                    for contents in (b"{", b"x" * (1024 * 1024 + 1)):
                        table_path.write_bytes(contents)
                        table_path.chmod(0o600)
                        await failed_call(
                            client,
                            provider,
                            "backfire_find",
                            second_find,
                            "backend_not_configured",
                            str(table_path),
                        )
                        table_path.write_bytes(valid_table)
                    table_path.chmod(0o640)
                    await failed_call(
                        client,
                        provider,
                        "backfire_find",
                        second_find,
                        "backend_not_configured",
                        str(table_path),
                    )
                    table_path.chmod(0o600)
                    lock_path.write_bytes(b"occupied")
                    await failed_call(
                        client,
                        provider,
                        "backfire_find",
                        second_find,
                        "backend_not_configured",
                        str(lock_path),
                    )
                    lock_path.write_bytes(valid_lock)
                    lock_path.chmod(0o640)
                    await failed_call(
                        client,
                        provider,
                        "backfire_find",
                        second_find,
                        "backend_not_configured",
                        str(lock_path),
                    )
                    lock_path.chmod(0o600)

                process_messages(
                    plugin,
                    config_home,
                    data_home,
                    state_home,
                    uv,
                    provider.base_url,
                    second_session,
                )

                assert len(provider.requests) == 4
                identifiers = (
                    STUDENT_A,
                    STUDENT_B,
                    STUDENT_C,
                    GIVEN_A,
                    GIVEN_B,
                    *GUARDIANS,
                    *SCHOOLS,
                    PHONE,
                    "+12025550123",
                    EMAIL,
                    "synthetic.one@example.test",
                )
                for request in provider.requests:
                    wire = json.dumps(request, ensure_ascii=False)
                    assert all(
                        identifier not in wire for identifier in identifiers
                    )
                first_request = json.dumps(
                    provider.requests[2], ensure_ascii=False
                )
                second_request = json.dumps(
                    provider.requests[3], ensure_ascii=False
                )
                for pseudonym in seeded.values():
                    assert (
                        pseudonym in first_request
                        and pseudonym in second_request
                    )
                assert (
                    next_student in second_request
                    and next_student not in first_request
                )
                assert "2026-09-28" in json.dumps(
                    provider.requests[2], ensure_ascii=False
                )
                assert "91점" in json.dumps(
                    provider.requests[2], ensure_ascii=False
                )

                expected_body = dict(baseline_body)
                expected_body["messages"] = transformed_messages
                assert provider.requests[2]["body"] == expected_body
                assert all(
                    identifier.encode() not in table_path.read_bytes()
                    for identifier in identifiers
                )
                assert not table_path.is_relative_to(ROOT)
        finally:
            monkeypatch.undo()
