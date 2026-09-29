import asyncio
import json
import sys
from types import ModuleType

from fake_provider import FakeProvider
from fake_provider import completion
import pytest

from backfire import config
from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge
from backfire.records import RecordFile
from backfire.records import digest
from backfire.records import read_records

SHIPPED = """
pseudonymize = true
provider = "hook-test"
[providers.hook-test]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "hook-model"
credential = "HOOK_KEY"
thinking = { requested = "off" }
"""
STATE = {"record": "synthetic original state"}
QUESTIONS = {"q": {"type": "noul", "instructions": "synthetic question"}}


@pytest.fixture
def environment(tmp_path, monkeypatch):
    shipped = tmp_path / "shipped.toml"
    shipped.write_text(SHIPPED, encoding="utf-8")
    monkeypatch.setattr(config, "SHIPPED_CONFIG", shipped)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("BACKFIRE_TEST_PROVIDER_BASE_URL", raising=False)
    directory = xdg_path("config") / "backfire"
    directory.mkdir(parents=True)
    credential = directory / "hook-test.env"
    credential.write_text("HOOK_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)
    return directory / "config.toml"


def install_stand_in(monkeypatch, replace):
    module = ModuleType("backfire_education.pseudonymize")
    module.pseudonymize = replace
    monkeypatch.setitem(sys.modules, module.__name__, module)


def run_judge(
    state=STATE, questions=QUESTIONS, *, pseudonymize=None, record_file=None
):
    async def run():
        return await judge(
            state,
            questions,
            deadline=asyncio.get_running_loop().time() + 5,
            record_file=record_file,
            pseudonymize=pseudonymize,
        )

    return asyncio.run(run())


def test_hook_sends_stand_in_output_restores_answers_and_records_originals(
    environment,
    monkeypatch,
):
    del environment  # Unused.
    restored = []

    def replace(state, questions):
        assert state == STATE
        assert list(questions) == ["q"]

        def restore(answers):
            restored.append(answers)
            return {"q": answers["masked-q"]}

        return (
            {"record": "synthetic masked state"},
            {"masked-q": questions["q"]},
            restore,
        )

    install_stand_in(monkeypatch, replace)
    with FakeProvider([completion({"masked-q": 0.5})]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with RecordFile(xdg_path("state") / "backfire/records") as records:
            result = run_judge(record_file=records)
            (entry,) = read_records(records.path)

    request = json.dumps(
        fake.requests[0]["body"]["messages"], ensure_ascii=False
    )
    assert "synthetic masked state" in request
    assert "masked-q" in request
    assert "synthetic original state" not in request
    assert restored == [{"masked-q": {"type": "noul", "noul": 0.5}}]
    assert result["answers"] == {"q": {"type": "noul", "noul": 0.5}}
    assert entry["payload_digest"] == digest(
        {
            "model": "hook-model",
            "state": STATE,
            "questions": QUESTIONS,
        }
    )


def test_stand_in_failure_sends_no_provider_request(environment, monkeypatch):
    del environment  # Unused.

    def fail(state, questions):
        del state, questions  # Unused.
        raise JudgmentError("pseudonym_conflict")

    install_stand_in(monkeypatch, fail)
    with (
        FakeProvider([]) as fake,
        RecordFile(xdg_path("state") / "backfire/records") as records,
    ):
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        with pytest.raises(JudgmentError, match="^pseudonym_conflict:"):
            run_judge(record_file=records)
        assert fake.requests == []


def test_explicit_false_skips_the_shipped_hook(environment, monkeypatch):
    del environment  # Unused.

    def fail(state, questions):
        del state, questions  # Unused.
        raise AssertionError("pseudonymizer was called")

    install_stand_in(monkeypatch, fail)
    with FakeProvider([completion()]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        result = run_judge(pseudonymize=False)

    request = json.dumps(
        fake.requests[0]["body"]["messages"], ensure_ascii=False
    )
    assert "synthetic original state" in request
    assert "masked-q" not in request
    assert result["answers"] == {"q": {"type": "noul", "noul": 0.5}}


def test_operator_cannot_set_pseudonymize(environment):
    environment.write_text("pseudonymize = false\n", encoding="utf-8")

    with pytest.raises(JudgmentError) as caught:
        config.load_profile()

    assert caught.value.error_type == "backend_not_configured"
    assert caught.value.detail == str(environment)
