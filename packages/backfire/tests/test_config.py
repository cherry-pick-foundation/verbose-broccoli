import os
from pathlib import Path
import tomllib
import traceback

import pytest

from backfire import config
from backfire.failures import JudgmentError


@pytest.fixture
def operator(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for kind in ("config", "state", "cache", "data"):
        monkeypatch.setenv(f"XDG_{kind.upper()}_HOME", str(tmp_path / kind))
    monkeypatch.delenv("BACKFIRE_TEST_PROVIDER_BASE_URL", raising=False)
    path = tmp_path / "config" / "verbose-broccoli" / "backfire" / "config.toml"
    path.parent.mkdir(parents=True)
    return path


def write_profile(path, name="second-test", **changes):
    fields = {
        "api": '"openai"',
        "base_url": '"https://example.test/v2"',
        "model": '"second-model"',
        "credential": '"TEST_KEY"',
        "thinking": (
            '{ requested = "on", token_path = "completion_tokens_details.'
            'reasoning_tokens" }'
        ),
        "request": "{ max_tokens = 64, temperature = 0.1 }",
        "statuses": '{ 409 = "rate_limited" }',
    }
    fields.update(changes)
    path.write_text(
        f'provider = "{name}"\n[providers.{name}]\n'
        + "".join(
            f"{key} = {value}\n"
            for key, value in fields.items()
            if value is not None
        ),
        encoding="utf-8",
    )


def assert_unconfigured(call, path, profile=None):
    with pytest.raises(JudgmentError) as caught:
        call()
    message = str(caught.value)
    assert message.startswith("backend_not_configured: ")
    assert str(path) in message
    if profile is not None:
        assert f"providers.{profile}" in message
    return caught.value


def test_absent_operator_keeps_the_shipped_selection(operator):
    with config.SHIPPED_CONFIG.open("rb") as file:
        shipped = tomllib.load(file)
    name = shipped["provider"]
    assert config.load_profile() == {"name": name, **shipped["providers"][name]}
    assert not operator.exists()


def test_operator_addition_selection_and_fresh_reads(operator):
    write_profile(operator)
    profile = config.load_profile()
    assert profile["name"] == "second-test"
    assert profile["model"] == "second-model"
    assert profile["request"] == {"max_tokens": 64, "temperature": 0.1}
    assert profile["thinking"] == {
        "requested": "on",
        "token_path": "completion_tokens_details.reasoning_tokens",
    }
    assert profile["statuses"] == {"409": "rate_limited"}
    assert "rate_limit_per_second" not in profile
    operator.write_text('provider = "hive"\n', encoding="utf-8")
    assert config.load_profile()["name"] == "hive"


def test_operator_table_replaces_whole_table_without_reselecting(operator):
    write_profile(
        operator,
        name="hive",
        request=None,
        statuses=None,
        thinking='{ requested = "off" }',
    )
    operator.write_text(
        operator.read_text().split("\n", 1)[1], encoding="utf-8"
    )
    profile = config.load_profile()
    assert profile["name"] == "hive"
    assert profile["model"] == "second-model"
    assert profile["request"] == profile["statuses"] == {}
    assert profile["thinking"] == {"requested": "off"}
    assert "rate_limit_per_second" not in profile


def test_partial_replacement_cannot_inherit_required_fields(operator):
    operator.write_text(
        '[providers.hive]\nmodel = "second-model"\n', encoding="utf-8"
    )
    assert_unconfigured(config.load_profile, operator, "hive")


def test_unselected_profile_is_not_validated_or_selected(operator):
    operator.write_text(
        '[providers.future]\napi = "anthropic"\n', encoding="utf-8"
    )
    assert config.load_profile()["name"] == "hive"


@pytest.mark.parametrize(
    "source",
    [
        b"broken = [",
        b"\xff",
        b'provider = "hive"\nprovider = "hive"',
        b"unexpected = true",
        b"provider = false",
        b'provider = ""',
        b'provider = "../escape"',
        b'provider = "HIVE"',
        b'provider = "hive\\n"',
        b'provider = "missing"',
        b"providers = []",
        b"providers = false",
        b'[providers."../escape"]',
        b'[providers."Bad"]',
        b"[providers]\nsecond = 3",
    ],
)
@pytest.mark.parametrize("shipped", [False, True])
def test_invalid_files_name_their_source(
    operator, monkeypatch, source, shipped
):
    path = operator.with_name("shipped.toml") if shipped else operator
    if shipped:
        monkeypatch.setattr(config, "SHIPPED_CONFIG", path)
    path.write_bytes(source)
    assert_unconfigured(config.load_profile, path)


def test_missing_shipped_selection_and_file_fail(operator, monkeypatch):
    path = operator.with_name("shipped.toml")
    monkeypatch.setattr(config, "SHIPPED_CONFIG", path)
    assert_unconfigured(config.load_profile, path)
    path.write_text("", encoding="utf-8")
    assert_unconfigured(config.load_profile, path)


def test_unreadable_operator_file_is_not_treated_as_absent(
    operator, monkeypatch
):
    original = os.open

    def deny(path, *args, **kwargs):
        if path == operator:
            raise PermissionError("private-error-marker")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(config.os, "open", deny)
    error = assert_unconfigured(config.load_profile, operator)
    assert "private-error-marker" not in "".join(
        traceback.format_exception(error)
    )


@pytest.mark.parametrize("kind", ["directory", "fifo", "broken-link"])
def test_invalid_operator_file_type_does_not_fall_back_or_block(operator, kind):
    if kind == "directory":
        operator.mkdir()
    elif kind == "fifo":
        os.mkfifo(operator)
    else:
        operator.symlink_to(operator.with_name("absent.toml"))
    assert_unconfigured(config.load_profile, operator)


@pytest.mark.parametrize(
    "changes",
    [
        *(
            {key: None}
            for key in ("api", "base_url", "model", "credential", "thinking")
        ),
        {"extra": "true"},
        {"api": '"unknown"'},
        {"api": "42"},
        {"base_url": '""'},
        {"base_url": '"/relative"'},
        {"base_url": '"https://"'},
        {"base_url": '"https://example.test:bad"'},
        {"base_url": '"https://[broken"'},
        {"model": '" "'},
        {"model": "42"},
        {"credential": '"BAD-NAME"'},
        {"credential": '"9KEY"'},
        {"credential": '"TEST_KEY\\n"'},
        {"thinking": "[]"},
        {"thinking": "{}"},
        {"thinking": '{ requested = "maybe" }'},
        {"thinking": '{ requested = "on" }'},
        {"thinking": '{ requested = "off", token_path = "tokens" }'},
        {"thinking": '{ requested = "off", content_path = "content" }'},
        {"thinking": '{ requested = "on", token_path = "a..b" }'},
        {"thinking": '{ requested = "on", content_path = "" }'},
        {"thinking": '{ requested = "on", token_path = true }'},
        {
            "thinking": (
                '{ requested = "on", token_path = "tokens", extra = true }'
            )
        },
        {"request": "[]"},
        *(
            {"request": "{ " + key + " = true }"}
            for key in ("model", "messages", "stream", "n")
        ),
        {"request": "{ max_tokens = 0 }"},
        {"request": "{ max_tokens = true }"},
        {"request": "{ max_tokens = 1.5 }"},
        {"request": "{ temperature = nan }"},
        {"request": "{ date = 2026-09-27 }"},
        *(
            {"rate_limit_per_second": value}
            for value in ("true", "-1", "inf", "nan", '"5"')
        ),
        {"statuses": "[]"},
        {"statuses": '{ 99 = "rate_limited" }'},
        {"statuses": '{ 600 = "rate_limited" }'},
        {"statuses": '{ bad = "rate_limited" }'},
        {"statuses": '{ 429 = "unknown" }'},
        {"statuses": "{ 429 = true }"},
    ],
)
def test_invalid_selected_profile_rules(operator, changes):
    write_profile(operator, **changes)
    assert_unconfigured(config.load_profile, operator, "second-test")


def test_reserved_api_reports_not_supported_yet(operator):
    write_profile(operator, api='"anthropic"')
    error = assert_unconfigured(config.load_profile, operator, "second-test")
    assert "not supported yet" in str(error)


@pytest.mark.parametrize("status", [100, 200, 399, 600])
def test_status_overrides_only_accept_errors_and_name_the_key(operator, status):
    write_profile(operator, statuses=f'{{ {status} = "rate_limited" }}')
    error = assert_unconfigured(config.load_profile, operator, "second-test")
    assert f"statuses.{status}" in str(error)


def test_optional_values_and_both_thinking_paths(operator):
    write_profile(
        operator,
        request=None,
        statuses=None,
        credential='"lowercase_key"',
        rate_limit_per_second="1.5",
        thinking=(
            '{ requested = "on", content_path = "reasoning", '
            'token_path = "usage.tokens" }'
        ),
    )
    profile = config.load_profile()
    assert profile["credential"] == "lowercase_key"
    assert profile["rate_limit_per_second"] == 1.5
    assert profile["request"] == profile["statuses"] == {}
    assert profile["thinking"]["content_path"] == "reasoning"


def test_test_endpoint_override_is_reloaded(operator, monkeypatch):
    write_profile(operator)
    monkeypatch.setenv(
        "BACKFIRE_TEST_PROVIDER_BASE_URL", "http://127.0.0.1:54321/v1"
    )
    assert config.load_profile()["base_url"] == "http://127.0.0.1:54321/v1"
    monkeypatch.delenv("BACKFIRE_TEST_PROVIDER_BASE_URL")
    assert config.load_profile()["base_url"] == "https://example.test/v2"


@pytest.mark.parametrize(
    "endpoint", ["", "relative", "https://", "http://localhost:bad"]
)
def test_invalid_test_endpoint_fails_configuration(
    operator, monkeypatch, endpoint
):
    write_profile(operator)
    monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", endpoint)
    error = assert_unconfigured(config.load_profile, operator, "second-test")
    assert "BACKFIRE_TEST_PROVIDER_BASE_URL" in str(error)


@pytest.mark.parametrize(
    "kind, default",
    [
        ("config", ".config"),
        ("state", ".local/state"),
        ("cache", ".cache"),
        ("data", ".local/share"),
    ],
)
def test_xdg_paths_without_reading_or_creating_them(
    operator, monkeypatch, kind, default
):
    del operator  # Unused.
    variable = f"XDG_{kind.upper()}_HOME"
    assert (
        config.xdg_path(kind) == Path(os.environ[variable]) / "verbose-broccoli"
    )
    monkeypatch.delenv(variable)
    expected = Path(os.environ["HOME"]) / default / "verbose-broccoli"
    assert config.xdg_path(kind) == expected
    monkeypatch.setenv(variable, "")
    assert config.xdg_path(kind) == expected
    assert not expected.exists()
    monkeypatch.setenv(variable, "relative")
    assert_unconfigured(lambda: config.xdg_path(kind), variable)


def test_credentials_are_private_selected_and_reloaded(
    operator, monkeypatch, capsys
):
    write_profile(operator)
    profile = config.load_profile()
    path = operator.with_name("second-test.env")
    path.write_bytes(b"OTHER_KEY=ignored\r\nTEST_KEY=  synthetic-first  \r\n")
    path.chmod(0o600)
    monkeypatch.setenv("TEST_KEY", "inherited-is-ignored")
    before = dict(os.environ)
    assert config.load_credential(profile) == "synthetic-first"
    path.write_text("TEST_KEY=synthetic-second\n", encoding="utf-8")
    assert config.load_credential(profile) == "synthetic-second"
    assert dict(os.environ) == before
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b" \n",
        b"OTHER_KEY=synthetic-secret",
        b"TEST_KEY= \n",
        b"TEST_KEY=\xff",
    ],
)
def test_missing_or_invalid_credentials_fail_privately(operator, content):
    write_profile(operator)
    profile = config.load_profile()
    path = operator.with_name("second-test.env")
    assert_unconfigured(lambda: config.load_credential(profile), path)
    path.write_bytes(content)
    path.chmod(0o600)
    error = assert_unconfigured(lambda: config.load_credential(profile), path)
    assert "synthetic-secret" not in "".join(traceback.format_exception(error))


@pytest.mark.parametrize(
    "mode", [0o400, 0o640, 0o604, 0o700, 0o1600, 0o2600, 0o4600]
)
def test_credentials_require_exact_mode(operator, mode):
    write_profile(operator)
    path = operator.with_name("second-test.env")
    path.write_text("TEST_KEY=synthetic-secret\n", encoding="utf-8")
    path.chmod(mode)
    assert_unconfigured(
        lambda: config.load_credential(config.load_profile()), path
    )


def test_credentials_require_operator_ownership(operator, monkeypatch):
    write_profile(operator)
    path = operator.with_name("second-test.env")
    path.write_text("TEST_KEY=synthetic-secret\n", encoding="utf-8")
    path.chmod(0o600)
    monkeypatch.setattr(config.os, "getuid", lambda: path.stat().st_uid + 1)
    assert_unconfigured(
        lambda: config.load_credential(config.load_profile()), path
    )


@pytest.mark.parametrize("kind", ["directory", "fifo"])
def test_credential_nonfiles_fail_without_blocking(operator, kind):
    write_profile(operator)
    path = operator.with_name("second-test.env")
    if kind == "directory":
        path.mkdir(mode=0o600)
    else:
        os.mkfifo(path, mode=0o600)
    assert_unconfigured(
        lambda: config.load_credential(config.load_profile()), path
    )
