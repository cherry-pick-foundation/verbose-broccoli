"""Offline tests for offer discovery, judgment, and notification."""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

import credit_offers

END = "2026-09-27T12:00:00+09:00"


def offer(slug, status="active", expiry_date=None):
    return {
        "slug": slug,
        "title": f"Title {slug}",
        "provider": "Example Provider",
        "category": "api_provider",
        "amount": "Free credits",
        "expiry_date": expiry_date,
        "source_url": f"https://example.test/{slug}",
        "status": status,
    }


def install_tracker(monkeypatch, old=(), new=(), same_commit=False):
    start, _ = credit_offers._block(6, END)
    start_sha, end_sha = "old-commit", "new-commit"
    if same_commit:
        end_sha = start_sha
    requests = []
    config = credit_offers.TRACKER

    def respond(request):
        requests.append(request)
        if request.url.path.endswith("/commits"):
            sha = (
                start_sha
                if request.url.params["until"] == start.isoformat()
                else end_sha
            )
            return httpx.Response(200, json=[{"sha": sha}])
        if request.url.path.endswith(f"/{start_sha}/{config['index_path']}"):
            return httpx.Response(200, json={"offers": list(old)})
        if request.url.path.endswith(f"/{end_sha}/{config['index_path']}"):
            return httpx.Response(200, json={"offers": list(new)})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(credit_offers.httpx, "Client", lambda **_: client)
    return requests


def answers_for(offers, choices):
    return {
        offer["slug"]: {
            "choice": choice,
            "probabilities": {
                "qualifies": 0.9 if choice == "qualifies" else 0.1,
                "excluded": 0.1 if choice == "qualifies" else 0.9,
            },
            "confidence": 0.9,
        }
        for offer, choice in zip(offers, choices, strict=True)
    }


def test_default_end_is_latest_local_boundary():
    now = datetime.fromisoformat("2026-09-30T13:59:00+09:00")
    local = now.astimezone()
    start, end = credit_offers._block(6, now=now)
    expected = local.replace(hour=12, minute=0, second=0, microsecond=0)
    assert end == expected
    assert start == expected.replace(hour=6)


def test_explicit_end_and_non_dividing_hours():
    start, end = credit_offers._block(6, END)
    expected = datetime.fromisoformat(END).astimezone()
    assert end == expected
    assert start == expected.replace(hour=expected.hour - 6)
    with pytest.raises(ValueError, match="divide 24"):
        credit_offers._block(5, END)


def test_same_commit_exits_without_fetching_index_or_calling_jev(
    monkeypatch, capsys
):
    requests = install_tracker(monkeypatch, same_commit=True)
    request_jev = Mock()
    monkeypatch.setattr(credit_offers.model, "request_jev", request_jev)

    status = credit_offers.main(["--end", END])

    assert status == 1
    assert len(requests) == 2
    assert all(
        not request.url.path.endswith("/index.json") for request in requests
    )
    request_jev.assert_not_called()
    assert "jev_calls=0" in capsys.readouterr().out


def test_filters_new_offers_and_judges_each_candidate_once(monkeypatch, capsys):
    existing = offer("existing")
    strong = offer("strong")
    excluded = offer("excluded")
    expired = offer("expired", expiry_date="2026-09-30")
    inactive = offer("inactive", status="expired")
    install_tracker(
        monkeypatch,
        old=[existing],
        new=[existing, strong, excluded, expired, inactive],
    )
    calls = []
    monkeypatch.setattr(
        credit_offers.model,
        "request_jev",
        lambda body: (
            calls.append(body),
            {
                "answers": answers_for(
                    [strong, excluded], ["qualifies", "excluded"]
                )
            },
        )[1],
    )

    status = credit_offers.main(["--end", END])

    output = capsys.readouterr().out
    assert status == 0
    assert len(calls) == 1
    assert set(calls[0]["questions"]) == {"strong", "excluded"}
    assert calls[0]["questions"]["strong"]["type"] == "choice"
    assert {
        slug: question["instructions"]
        for slug, question in calls[0]["questions"].items()
    } == {
        slug: {
            "offer": slug,
            "task": "Judge this.",
        }
        for slug in ("strong", "excluded")
    }
    assert "strong\tqualifies\t0.9" in output
    assert "excluded\texcluded\t0.9" in output


def test_filtered_offers_make_no_jev_call(monkeypatch, capsys):
    install_tracker(
        monkeypatch,
        new=[
            offer("expired", expiry_date="2026-09-30"),
            offer("inactive", status="removed"),
        ],
    )
    request_jev = Mock()
    monkeypatch.setattr(credit_offers.model, "request_jev", request_jev)

    status = credit_offers.main(["--end", END])

    assert status == 1
    request_jev.assert_not_called()
    assert "jev_calls=0" in capsys.readouterr().out


def test_excluded_only_answer_returns_one(monkeypatch, capsys):
    candidate = offer("excluded")
    install_tracker(monkeypatch, new=[candidate])
    monkeypatch.setattr(
        credit_offers.model,
        "request_jev",
        lambda _: {"answers": answers_for([candidate], ["excluded"])},
    )

    status = credit_offers.main(["--end", END])

    output = capsys.readouterr().out
    assert status == 1
    assert "excluded\texcluded\t0.9" in output
    assert "jev_calls=1" in output


def test_notification_only_contains_strong_offers(monkeypatch):
    strong, excluded = offer("strong"), offer("excluded")
    strong["title"] = "--version"
    install_tracker(monkeypatch, new=[strong, excluded])
    monkeypatch.setattr(
        credit_offers.model,
        "request_jev",
        lambda _: {
            "answers": answers_for(
                [strong, excluded], ["qualifies", "excluded"]
            )
        },
    )
    sent = []

    def record(command, check):
        sent.append(command)
        assert check is True

    monkeypatch.setattr(credit_offers.subprocess, "run", record)

    status = credit_offers.main(["--end", END, "--notify"])

    assert status == 0
    assert len(sent) == 1
    assert sent[0][0] == "notify-send"
    assert sent[0][1:3] == ["--", "New API credit offers"]
    assert sent[0][3].startswith("--version — Example Provider")
    assert "Title excluded" not in sent[0][3]
    assert "Example Provider" in sent[0][3]
    assert "Free credits" in sent[0][3]
    assert "https://example.test/strong" in sent[0][3]


@pytest.mark.parametrize(
    "error",
    [
        credit_offers.subprocess.CalledProcessError(1, ["notify-send"]),
        OSError("notify-send unavailable"),
    ],
)
def test_notification_failure_exits_three_after_printing_judgment(
    monkeypatch, capsys, error
):
    candidate = offer("candidate")
    install_tracker(monkeypatch, new=[candidate])
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(
        credit_offers.model,
        "request_jev",
        lambda _: {"answers": answers_for([candidate], ["qualifies"])},
    )

    monkeypatch.setattr(
        credit_offers.subprocess, "run", Mock(side_effect=error)
    )

    status = credit_offers.main(["--end", END, "--notify"])

    captured = capsys.readouterr()
    assert status == 3
    assert "candidate\tqualifies\t0.9" in captured.out
    assert "jev_calls=1" in captured.out
    assert str(error) in captured.err
    assert "synthetic-test-key" not in captured.out + captured.err


def test_tracker_http_error_exits_three_without_key(monkeypatch, capsys):
    monkeypatch.setenv("AI_GATEWAY_API_KEY", "synthetic-test-key")

    def forbidden(request):
        return httpx.Response(403, request=request)

    client = httpx.Client(transport=httpx.MockTransport(forbidden))
    monkeypatch.setattr(credit_offers.httpx, "Client", lambda **_: client)
    request_jev = Mock()
    monkeypatch.setattr(credit_offers.model, "request_jev", request_jev)

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    request_jev.assert_not_called()
    assert "403" in captured.err
    assert "jev_calls=0" in captured.out
    assert "synthetic-test-key" not in captured.out + captured.err


def test_invalid_answer_fails_with_status_three(monkeypatch, capsys):
    candidate = offer("bad-answer")
    install_tracker(monkeypatch, new=[candidate])
    monkeypatch.setattr(
        credit_offers.model,
        "request_jev",
        lambda _: {
            "answers": {
                "bad-answer": {"choice": "qualifies", "probabilities": {}}
            }
        },
    )

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    assert "Invalid TypeSafe response" in captured.err
    assert "jev_calls=1" in captured.out


def test_missing_provider_key_names_only_the_variable(monkeypatch, capsys):
    candidate = offer("candidate")
    install_tracker(monkeypatch, new=[candidate])

    def missing_key(_):
        raise ValueError(
            "AI_GATEWAY_API_KEY is required for vercel; no request sent"
        )

    monkeypatch.setattr(credit_offers.model, "request_jev", missing_key)

    status = credit_offers.main(["--end", END])

    captured = capsys.readouterr()
    assert status == 3
    assert "AI_GATEWAY_API_KEY" in captured.err
    assert "jev_calls=0" in captured.out


def test_invalid_arguments_exit_two(capsys):
    with pytest.raises(SystemExit) as error:
        credit_offers.main(["--hours", "5"])
    assert error.value.code == 2
    assert "divide 24" in capsys.readouterr().err


def test_search_writes_no_files(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    install_tracker(monkeypatch, same_commit=True)
    before = set(Path(tmp_path).iterdir())
    monkeypatch.setattr(credit_offers.model, "request_jev", lambda _: None)

    assert credit_offers.main(["--end", END]) == 1
    assert set(Path(tmp_path).iterdir()) == before
