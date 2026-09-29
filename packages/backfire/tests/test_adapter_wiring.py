"""Gate 9: adapter prompts, concurrent metadata, and private diagnostics."""

import asyncio
import json
import logging
import traceback

from fake_provider import FakeProvider
from fake_provider import Reply
from fake_provider import completion
from jsonschema import Draft202012Validator
import pytest
from system_one_adapter import AsyncSystemOneAdapterClient
from typesafe_sdk import TypeSafeError

from backfire.config import xdg_path
from backfire.failures import JudgmentError
from backfire.judge import judge
from backfire.records import RecordFile
from backfire.records import digest
from backfire.records import read_records

PRIVATE = "adapter-wiring-private-document"
RAW = "adapter-wiring-private-provider-output"
QUESTIONS = {
    "q": {"type": "noul", "instructions": "adapter-wiring-private-question"}
}


@pytest.fixture(autouse=True)
def configuration(monkeypatch):
    for name in (
        "BACKFIRE_TEST_PROVIDER_BASE_URL",
        "BACKFIRE_TEST_REQUEST_LIMITS",
    ):
        monkeypatch.delenv(name, raising=False)
    directory = xdg_path("config") / "backfire"
    directory.mkdir(parents=True)
    (directory / "config.toml").write_text(
        """
provider = "wiring-test"
[providers.wiring-test]
api = "openai"
base_url = "https://provider.invalid/v1"
model = "requested-model"
credential = "SYNTHETIC_KEY"
request = {max_tokens = 64, response_format = {type = "json_object"}}
thinking = {requested = "on", token_path = "reasoning_tokens"}
""",
        encoding="utf-8",
    )
    credential = directory / "wiring-test.env"
    credential.write_text("SYNTHETIC_KEY=synthetic-key\n", encoding="utf-8")
    credential.chmod(0o600)


async def evaluate(*, state=PRIVATE, questions=QUESTIONS, record_file=None):
    return await judge(
        state,
        questions,
        deadline=asyncio.get_running_loop().time() + 10,
        record_file=record_file,
    )


def test_prompted_messages_carry_every_question_and_the_answer_schema(
    monkeypatch,
):
    questions = {
        "noul-id": {
            "type": "noul",
            "instructions": "Is the claim supported?",
            "criteria": {
                "true": "Evidence supports it",
                "false": "Evidence contradicts it",
            },
        },
        "choice-id": {
            "type": "choice",
            "instructions": "Select the department",
            "criteria": {
                "billing": "Invoice question",
                "shipping": "Delivery question",
            },
        },
        "score-id": {
            "type": "score",
            "instructions": "완성도를 평가하세요",
            "criteria": ["미완성", "일부 완성", "완성"],
        },
    }
    answers = {
        "noul-id": 0.5,
        "choice-id": {"billing": 0.8, "shipping": 0.2},
        "score-id": {"0": 0.1, "1": 0.2, "2": 0.7},
    }
    state = {"document": "A synthetic invoice. 한글 문서."}
    with FakeProvider([completion(answers)]) as fake:
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        result = asyncio.run(evaluate(state=state, questions=questions))
        (request,) = fake.requests
        sent = request["body"]
        assert sent["response_format"] == {"type": "json_object"}
        system, user = sent["messages"]
        assert system["role"] == "system" and user["role"] == "user"
        schema, _ = json.JSONDecoder().raw_decode(
            system["content"][system["content"].index("{") :]
        )
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        validator.validate({"answers": answers})
        assert not validator.is_valid({"answers": {"noul-id": 0.5}})
        assert not validator.is_valid(
            {"answers": {**answers, "choice-id": {"unknown": 1}}}
        )
        schema_text = json.dumps(schema, ensure_ascii=False)
        for identifier, question in questions.items():
            assert identifier in schema_text
            assert question["instructions"] in schema_text
            criteria = question["criteria"]
            for description in (
                criteria.values() if isinstance(criteria, dict) else criteria
            ):
                assert description in schema_text
        opening, document, closing = user["content"].splitlines()
        assert opening == "<document>" and closing == "</document>"
        assert json.loads(document) == state
        assert set(result["answers"]) == set(questions)


def test_concurrent_judgments_keep_results_and_record_metadata_separate(
    monkeypatch,
):
    first_body = completion({"q": 0.2}, model="first-reported-model")
    second_body = completion({"q": 0.8}, model="second-reported-model")
    second_body["usage"].update(
        prompt_tokens=23, completion_tokens=13, reasoning_tokens=6
    )
    retry = Reply(
        {"error": "synthetic rate limit"}, 429, {"Retry-After": "0"}, stall=True
    )
    with (
        FakeProvider([retry, second_body, first_body]) as fake,
        RecordFile(xdg_path("state") / "backfire/records") as records,
    ):
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)

        async def run():
            first = asyncio.create_task(
                evaluate(state="first-state", record_file=records)
            )
            try:
                assert await asyncio.to_thread(fake.received.wait, 2)
                second = await evaluate(
                    state="second-state", record_file=records
                )
                assert not first.done()
            finally:
                fake.release.set()
            return await first, second

        first, second = asyncio.run(run())
        assert len(fake.requests) == 3
        assert first["metadata"] is not second["metadata"]
        entries = list(read_records(records.path))
        assert len(entries) == 2
        assert [entry["model"] for entry in entries] == [
            second["model"],
            first["model"],
        ]
        by_digest = {entry["payload_digest"]: entry for entry in entries}
        for (
            result,
            state,
            model,
            attempts,
            input_tokens,
            output_tokens,
            reasoning,
            probability,
        ) in (
            (first, "first-state", "first-reported-model", 2, 11, 7, 3, 0.2),
            (
                second,
                "second-state",
                "second-reported-model",
                1,
                23,
                13,
                6,
                0.8,
            ),
        ):
            metadata = result["metadata"]
            assert result["model"] == model
            assert result["usage"] == {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
            assert result["answers"]["q"]["noul"] == probability
            assert metadata == {
                "attempts": attempts,
                "latency_ms": metadata["latency_ms"],
                "thinking_evidence": True,
                "reasoning_tokens": reasoning,
            }
            assert metadata["latency_ms"] > 0
            entry = by_digest[
                digest(
                    {
                        "model": "requested-model",
                        "state": state,
                        "questions": QUESTIONS,
                    }
                )
            ]
            assert entry["model"] == model and entry["outcome"] == "ok"
            assert entry["results"] == [{"p": probability}]
            assert entry["usage"] == {
                **result["usage"],
                "reasoning_tokens": reasoning,
            }
            for field in ("attempts", "latency_ms", "thinking_evidence"):
                assert entry[field] == metadata[field]


@pytest.mark.parametrize(
    "outcome", ["ok", "malformed_output", "provider_error"]
)
def test_real_adapter_debug_never_reaches_results_logs_errors_or_records(
    monkeypatch, caplog, capsys, outcome
):
    caplog.set_level(logging.INFO)
    caplog.set_level(logging.DEBUG, logger="backfire")
    caplog.set_level(logging.DEBUG, logger="system_one_adapter")
    debug_objects = []
    system_one = AsyncSystemOneAdapterClient.system_one

    async def capture_debug(client, *args, **kwargs):
        try:
            response = await system_one(client, *args, **kwargs)
        except TypeSafeError as error:
            debug_objects.append(error.debug)
            raise
        debug_objects.append(response.debug)
        return response

    monkeypatch.setattr(
        AsyncSystemOneAdapterClient, "system_one", capture_debug
    )
    body = completion()
    body["choices"][0]["message"]["reasoning_content"] = RAW
    if outcome == "malformed_output":
        body["choices"][0]["message"]["content"] = RAW
    reply = Reply({"error": RAW}, 500) if outcome == "provider_error" else body
    with (
        FakeProvider([reply]) as fake,
        RecordFile(xdg_path("state") / "backfire/records") as records,
    ):
        monkeypatch.setenv("BACKFIRE_TEST_PROVIDER_BASE_URL", fake.base_url)
        if outcome == "ok":
            result = asyncio.run(evaluate(record_file=records))
            assert set(result) == {"model", "answers", "usage", "metadata"}
            public = json.dumps(result)
        else:
            with pytest.raises(JudgmentError) as caught:
                asyncio.run(evaluate(record_file=records))
            assert str(caught.value) == str(JudgmentError(outcome))
            assert not hasattr(caught.value, "debug")
            public = "".join(traceback.format_exception(caught.value))
        (debug,) = debug_objects
        (attempt,) = debug["llm_attempts"]
        (request,) = fake.requests
        assert attempt["messages"] == request["body"]["messages"]
        assert PRIVATE in json.dumps(debug) and RAW in json.dumps(debug)
        (entry,) = read_records(records.path)
        assert entry["outcome"] == outcome
        assert entry["results"] == ([{"p": 0.5}] if outcome == "ok" else None)
        output = capsys.readouterr()
        exposed = (
            public
            + records.path.read_text()
            + caplog.text
            + output.out
            + output.err
        )
        for private in (
            PRIVATE,
            RAW,
            QUESTIONS["q"]["instructions"],
            "synthetic-key",
            "llm_attempts",
            "model_request_parameters",
            "llm_response",
        ):
            assert private not in exposed
