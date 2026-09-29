"""Offline contracts for configured Jev providers."""

import json

import httpx
import pytest

from jev_ultrafast import model

TEST_KEY = "synthetic-test-key"


@pytest.fixture
def mock_provider(monkeypatch):
    requests = []
    clients = []

    def install(result):
        def respond(request):
            requests.append(request)
            return httpx.Response(200, json=result)

        client = httpx.Client(transport=httpx.MockTransport(respond))
        clients.append(client)
        monkeypatch.setattr(model, "CLIENT", client)

    yield requests, install
    for client in clients:
        client.close()


def body():
    return {
        "model": "jev-latest",
        "state": {"page": {"url": "https://example.test/"}},
        "questions": {
            "operation": {
                "type": "choice",
                "instructions": {},
                "criteria": {"DONE": "done"},
            }
        },
    }


def test_vercel_request_and_answer_conversion(monkeypatch, mock_provider):
    requests, install = mock_provider
    install(
        {
            "answers": {
                "operation": {
                    "type": "choice",
                    "choice": "DONE",
                    "probabilities": {"DONE": 1.0},
                },
                "other": {"type": "score", "score": 0.5},
            },
            "providerMetadata": {
                "typesafe": {"confidence": {"operation": 0.9}}
            },
            "usage": {"inputTokens": 12, "outputTokens": 3},
        }
    )
    monkeypatch.setenv("JEV_PROVIDER", "vercel")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", TEST_KEY)

    result = model.request_jev(body())

    request = requests[0]
    assert (
        str(request.url)
        == "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
    )
    assert request.headers["authorization"] == f"Bearer {TEST_KEY}"
    assert request.headers["ai-gateway-protocol-version"] == "0.0.1"
    assert request.headers["ai-gateway-auth-method"] == "api-key"
    assert request.headers["ai-evaluation-model-specification-version"] == "4"
    assert request.headers["ai-model-id"] == "typesafe-ai/jev"
    assert (
        request.read()
        == httpx.Request(
            "POST",
            str(request.url),
            json={"state": body()["state"], "questions": body()["questions"]},
        ).read()
    )
    assert result == {
        "answers": {
            "operation": {
                "type": "choice",
                "choice": "DONE",
                "probabilities": {"DONE": 1.0},
                "confidence": 0.9,
            },
            "other": {"type": "score", "score": 0.5},
        },
        "usage": {"input_tokens": 12, "output_tokens": 3},
        "model": "typesafe-ai/jev",
    }


def test_vercel_choice_without_confidence_is_preserved_as_missing(
    monkeypatch, mock_provider
):
    _, install = mock_provider
    install(
        {
            "answers": {
                "operation": {
                    "type": "choice",
                    "choice": "DONE",
                    "probabilities": {"DONE": 1.0},
                }
            }
        }
    )
    monkeypatch.setenv("JEV_PROVIDER", "vercel")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", TEST_KEY)

    assert (
        model.request_jev(body())["answers"]["operation"]["confidence"] is None
    )


def test_typesafe_request_matches_upstream(monkeypatch, mock_provider):
    requests, install = mock_provider
    install({"model": "jev-latest", "answers": {}})
    monkeypatch.delenv("JEV_PROVIDER", raising=False)
    monkeypatch.setenv("TYPESAFE_API_KEY", TEST_KEY)
    request_body = body()

    result = model.request_jev(request_body)

    request = requests[0]
    assert str(request.url) == "https://api.typesafe.ai/v1/systemone"
    assert request.headers["authorization"] == f"Bearer {TEST_KEY}"
    assert (
        request.read()
        == httpx.Request("POST", str(request.url), json=request_body).read()
    )
    assert result == {"model": "jev-latest", "answers": {}}


def test_choose_uses_vercel_stub_end_to_end(monkeypatch, mock_provider):
    requests, _ = mock_provider

    def response(request):
        payload = json.loads(request.read())
        operations = payload["questions"]["operation"]["criteria"]
        targets = payload["questions"]["click_target"]["criteria"]
        return httpx.Response(
            200,
            json={
                "answers": {
                    "operation": {
                        "type": "choice",
                        "choice": "CLICK",
                        "probabilities": {
                            key: float(key == "CLICK") for key in operations
                        },
                    },
                    "click_target": {
                        "type": "choice",
                        "choice": "1",
                        "probabilities": {
                            key: float(key == "1") for key in targets
                        },
                    },
                },
                "providerMetadata": {
                    "typesafe": {
                        "confidence": {"operation": 0.9, "click_target": 0.95}
                    }
                },
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: (requests.append(request), response(request))[1]
        )
    )
    monkeypatch.setattr(model, "CLIENT", client)
    monkeypatch.setenv("JEV_PROVIDER", "vercel")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", TEST_KEY)
    state = {
        "url": "https://example.test/",
        "title": "Example",
        "text": "Go",
        "actions": [
            {
                "id": "go",
                "kind": "click",
                "label": "Go",
                "node": 1,
                "role": "button",
                "value": "",
            }
        ],
    }

    decision = model.choose(state, "Click Go", [])

    assert (
        str(requests[0].url)
        == "https://ai-gateway.vercel.sh/v4/ai/evaluation-model"
    )
    assert decision["choice"] == "go"
    assert decision["confidence"] == 0.9
    client.close()


@pytest.mark.parametrize(
    "provider,variable",
    [("vercel", "AI_GATEWAY_API_KEY"), ("typesafe", "TYPESAFE_API_KEY")],
)
def test_missing_key_fails_before_request(
    monkeypatch, mock_provider, provider, variable
):
    requests, install = mock_provider
    install({})
    monkeypatch.setenv("JEV_PROVIDER", provider)
    monkeypatch.delenv(variable, raising=False)

    with pytest.raises(ValueError) as error:
        model.request_jev(body())

    assert variable in str(error.value)
    assert TEST_KEY not in str(error.value)
    assert requests == []


def test_unknown_provider_fails_before_request(monkeypatch, mock_provider):
    requests, install = mock_provider
    install({})
    monkeypatch.setenv("JEV_PROVIDER", "unknown-provider")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", TEST_KEY)

    with pytest.raises(ValueError, match="unknown-provider") as error:
        model.request_jev(body())

    assert TEST_KEY not in str(error.value)
    assert requests == []


def test_malformed_vercel_choice_is_rejected_before_action(monkeypatch):
    def response(request):
        operations = json.loads(request.read())["questions"]["operation"][
            "criteria"
        ]
        return httpx.Response(
            200,
            json={
                "answers": {
                    "operation": {
                        "type": "choice",
                        "choice": "CLICK",
                        "probabilities": {
                            key: float(key == "CLICK") for key in operations
                        },
                    }
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(response))
    monkeypatch.setattr(model, "CLIENT", client)
    monkeypatch.setenv("JEV_PROVIDER", "vercel")
    monkeypatch.setenv("AI_GATEWAY_API_KEY", TEST_KEY)
    state = {
        "url": "https://example.test/",
        "title": "Example",
        "text": "Go",
        "actions": [
            {
                "id": "go",
                "kind": "click",
                "label": "Go",
                "node": 1,
                "role": "button",
                "value": "",
            }
        ],
    }

    with pytest.raises(ValueError, match="Invalid TypeSafe response"):
        model.choose(state, "Click Go", [])
    client.close()
