import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx2
import pytest

from backfire_tools.acceptance import probe_provider as probe


def config():
    return {
        "provider": "alpha",
        "providers": {
            "alpha": {
                "api": "openai",
                "base_url": "https://example.test/v1",
                "model": "model-for-test",
                "credential": "API_KEY",
                "request": {},
                "thinking": {
                    "requested": "on",
                    "content_path": "reasoning_content",
                },
            },
        },
    }


def use_transport(monkeypatch, handler):
    client = httpx2.AsyncClient
    monkeypatch.setattr(
        probe.httpx2,
        "AsyncClient",
        lambda **kwargs: client(
            transport=httpx2.MockTransport(handler), **kwargs
        ),
    )


def test_summary_prints_only_approved_fields():
    summary = probe.summarize(
        "settings",
        200,
        {
            "model": "model-for-probe",
            "choices": [
                {
                    "message": {
                        "reasoning_content": "private thinking marker",
                        "content": "private response marker",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "completion_tokens_details": {"reasoning_tokens": 4},
                "prompt_tokens": 8,
                "completion_tokens": 10,
                "total_tokens": 18,
            },
            "error": "private error marker",
            "request": "private request marker",
        },
        17.6,
        {
            "content_path": "reasoning_content",
            "token_path": "completion_tokens_details.reasoning_tokens",
        },
    )
    output = json.dumps(summary, separators=(",", ":"))
    assert output == (
        '{"label":"settings","status":200,"elapsed_ms":18,"model":"model-for-probe",'
        '"thinking_content_non_empty":true,"thinking_tokens":4,"prompt_tokens":8,'
        '"completion_tokens":10,"total_tokens":18,"finish_reason":"stop"}'
    )
    assert "private" not in output


@pytest.mark.parametrize(
    "body",
    [
        None,
        [],
        {"choices": []},
        {
            "model": 1,
            "choices": [
                {
                    "message": {"reasoning_content": " \n "},
                    "finish_reason": False,
                }
            ],
            "usage": {
                "reasoning_tokens": True,
                "prompt_tokens": True,
                "total_tokens": "3",
            },
        },
    ],
)
def test_summary_handles_missing_and_wrongly_typed_evidence(body):
    assert probe.summarize(
        "settings",
        200,
        body,
        2.5,
        {
            "content_path": "reasoning_content",
            "token_path": "reasoning_tokens",
        },
    ) == {
        "label": "settings",
        "status": 200,
        "elapsed_ms": 3,
        "thinking_content_non_empty": False,
        "thinking_tokens": None,
    }


def test_selection_and_optional_burst():
    profile = probe.select_profile(config())
    assert "rate_limit_per_second" not in profile
    assert probe.burst_size(profile.get("rate_limit_per_second")) is None
    assert (
        probe.select_profile({**config(), "provider": "missing"}, "alpha")[
            "name"
        ]
        == "alpha"
    )
    assert (
        probe.select_profile({"providers": config()["providers"]}, "alpha")
        == profile
    )
    assert json.dumps(probe.burst_not_applicable(), separators=(",", ":")) == (
        '{"label":"burst","status":null,"not_applicable":"profile has no rate_limit_per_second"}'
    )
    assert probe.burst_size(5) == 6
    assert probe.burst_size(0) == 1
    assert probe.burst_size(1.5) == 2
    selected = config()["providers"]["alpha"]
    selected.pop("request")
    selected["thinking"] = {"requested": "off"}
    selected["statuses"] = {"405": "balance_exhausted"}
    profile = probe.select_profile(
        {"provider": "alpha", "providers": {"alpha": selected}}
    )
    assert profile["request"] == profile["thinking"] == {}


@pytest.mark.parametrize(
    "value, override",
    [
        ({"provider": "alpha", "providers": {}}, None),
        ({**config(), "unexpected": True}, None),
        ({**config(), "provider": "../alpha"}, "alpha"),
        (config(), "../alpha"),
        ({"providers": config()["providers"]}, None),
    ],
)
def test_selection_rejects_bad_config(value, override):
    with pytest.raises(ValueError):
        probe.select_profile(value, override)


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "alpha"},
        {"api": "unsupported"},
        {"base_url": ""},
        {"model": ""},
        {"credential": "BAD-NAME"},
        {"request": []},
        *(
            {"request": {key: True}}
            for key in ("model", "messages", "stream", "n")
        ),
        {"thinking": {}},
        {"thinking": {"requested": "on"}},
        {"thinking": {"requested": "off", "content_path": "content"}},
        {"thinking": {"requested": "on", "content_path": "a..b"}},
        {
            "thinking": {
                "requested": "on",
                "token_path": "tokens",
                "extra": True,
            }
        },
        *(
            {"rate_limit_per_second": rate}
            for rate in (True, -1, float("inf"), float("nan"), None)
        ),
        {"statuses": []},
        {"statuses": {"99": "rate_limited"}},
        {"statuses": {"600": "rate_limited"}},
        {"statuses": {"429": "unknown"}},
        {"statuses": {"200": "rate_limited"}},
        {"statuses": {"399": "request_rejected"}},
    ],
)
def test_selection_rejects_invalid_profile_fields(changes):
    value = config()
    value["providers"]["alpha"].update(changes)
    with pytest.raises(ValueError):
        probe.select_profile(value)


@pytest.mark.parametrize("with_burst", [False, True])
def test_main_reads_toml_and_credentials_and_preserves_requests(
    tmp_path,
    monkeypatch,
    capsys,
    with_burst,
):
    source = tmp_path / "config.toml"
    source.write_text(
        'provider = "missing"\n' if with_burst else 'provider = "alpha"\n',
        encoding="utf-8",
    )
    with source.open("a", encoding="utf-8") as file:
        file.write("""
[providers.alpha]
api = "openai"
base_url = "https://example.test/v1///"
model = "model-for-test"
credential = "API_KEY"
request = {max_tokens = 32768, response_format = {type = "json_object"}, reasoning_effort = "medium"}
thinking = {requested = "on", content_path = "reasoning_content", token_path = "details.tokens"}
""")
        if with_burst:
            file.write("rate_limit_per_second = 5\n")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    config_home = tmp_path / ".config"
    if with_burst:
        config_home = tmp_path / "xdg"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    credential = config_home / "verbose-broccoli" / "backfire" / "alpha.env"
    credential.parent.mkdir(parents=True)
    credential.write_bytes(
        b"OTHER_KEY=ignored\r\nAPI_KEY=  private-key-marker  \r\nAPI_KEY=ignored\r\n"
    )
    monkeypatch.setenv("API_KEY", "inherited-key-is-ignored")
    received = []
    burst_started = asyncio.Event()
    active = 0

    async def respond(request):
        nonlocal active
        body = json.loads(request.content)
        received.append((request.headers["authorization"], body))
        assert request.method == "POST"
        assert str(request.url) == "https://example.test/v1/chat/completions"
        assert request.headers["content-type"] == "application/json"
        if body["max_tokens"] == 1:
            active += 1
            if active == 6:
                burst_started.set()
            await asyncio.wait_for(burst_started.wait(), timeout=2)
            status = 429
        elif request.headers["authorization"] != "Bearer private-key-marker":
            status = 401
        elif body["model"] != "model-for-test":
            status = 400
        else:
            status = 200
        return httpx2.Response(
            status,
            json={
                "model": "model-for-test",
                "choices": [
                    {
                        "message": {
                            "reasoning_content": "private thinking",
                            "content": "private response",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "details": {"tokens": 4},
                    "prompt_tokens": 8,
                    "completion_tokens": 10,
                    "total_tokens": 18,
                },
                "error": "private error",
            },
        )

    use_transport(monkeypatch, respond)
    asyncio.run(
        probe.main(
            ["--config", str(source)] + (["alpha"] if with_burst else [])
        )
    )
    output = capsys.readouterr()
    assert output.err == ""
    assert "private" not in output.out and "inherited" not in output.out
    rows = [json.loads(line) for line in output.out.splitlines()]
    assert [row["label"] for row in rows[:3]] == [
        "settings",
        "invalid key",
        "unknown model",
    ]
    assert [row["status"] for row in rows[:3]] == [200, 401, 400]
    assert rows[0]["thinking_tokens"] == 4
    assert rows[0]["thinking_content_non_empty"] is True
    assert all(row["elapsed_ms"] >= 0 for row in rows if "elapsed_ms" in row)
    assert "model" not in rows[1] and "model" not in rows[2]
    assert received[0][0] == received[2][0] == "Bearer private-key-marker"
    assert received[1][0] == "Bearer not-a-valid-api-key-for-probe"
    assert received[2][1]["model"] == "verbose-broccoli/unknown-model-for-probe"
    for index, (key, body) in enumerate(received):
        assert body == {
            "max_tokens": 32768 if index < 3 else 1,
            "response_format": {"type": "json_object"},
            "reasoning_effort": "medium",
            "model": "verbose-broccoli/unknown-model-for-probe"
            if index == 2
            else "model-for-test",
            "messages": [
                {"role": "user", "content": "Return a small JSON object."}
            ],
        }
    if with_burst:
        assert len(received) == 9 and active == 6
        assert [row["label"] for row in rows[3:]] == [
            f"burst-{index}" for index in range(1, 7)
        ]
        assert all(row["status"] == 429 for row in rows[3:])
    else:
        assert len(received) == 3 and rows[3] == probe.burst_not_applicable()


@pytest.mark.parametrize("failure", ["transport", "json", "body", "deadline"])
def test_request_keeps_failures_private(monkeypatch, capsys, failure):
    class BrokenBody(httpx2.AsyncByteStream):
        async def __aiter__(self):
            raise httpx2.ReadError("private response marker")
            yield b""

    async def respond(request):
        if failure == "transport":
            raise httpx2.ConnectError("private credential marker")
        if failure == "deadline":
            await asyncio.sleep(60)
        if failure == "body":
            return httpx2.Response(200, stream=BrokenBody())
        return httpx2.Response(200, content=b"private invalid json marker")

    if failure == "deadline":
        timeout = asyncio.timeout

        def short_timeout(seconds):
            assert seconds == 30
            return timeout(0.01)

        monkeypatch.setattr(probe.asyncio, "timeout", short_timeout)
    use_transport(monkeypatch, respond)
    profile = probe.select_profile(config())
    result = asyncio.run(
        probe.request(
            "settings",
            "private-key",
            profile,
            profile["model"],
            {},
            "https://example.test",
        )
    )
    assert result["status"] == (
        None if failure in ("transport", "deadline") else 200
    )
    assert result["thinking_content_non_empty"] is False
    assert "private" not in json.dumps(result)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "arguments", [["--config"], ["--private-argument"], ["alpha", "beta"]]
)
def test_cli_startup_failure_prints_only_fixed_message(tmp_path, arguments):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "backfire_tools.acceptance.probe_provider",
            *arguments,
        ],
        env={
            **os.environ,
            "HOME": str(tmp_path),
            "XDG_CONFIG_HOME": str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "Probe could not start.\n"


def test_default_config_and_missing_credential_fail_before_network(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    seen = []

    def reject_network(*args, **kwargs):
        pytest.fail("missing credential must not send a request")

    select = probe.select_profile

    def record_selection(value, override):
        seen.append(value)
        return select(value, override)

    monkeypatch.setattr(probe, "select_profile", record_selection)
    monkeypatch.setattr(probe.httpx2, "AsyncClient", reject_network)
    with pytest.raises(FileNotFoundError):
        asyncio.run(probe.main([]))
    shipped = (
        Path(probe.__file__).resolve().parents[2] / "backfire" / "config.toml"
    )
    with shipped.open("rb") as file:
        assert seen == [probe.tomllib.load(file)]
