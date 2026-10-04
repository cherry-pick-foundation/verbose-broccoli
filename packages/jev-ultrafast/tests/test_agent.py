"""Offline contracts for a dynamic operation/target policy. No paid APIs."""

import json
import socket
import time
from copy import deepcopy
from unittest.mock import Mock

import pytest
from mcp.types import CallToolResult, ImageContent, TextContent

from jev_ultrafast import agent as loop
from jev_ultrafast import model
from jev_ultrafast.browser import StalePage, browser_operation, fingerprint
from jev_ultrafast.questions import NEXT_ACTION, TARGET


def page():
    state = {
        "url": "https://example.test/",
        "title": "Search",
        "text": "Search",
        "scroll": {"y": 0},
        "actions": [
            {"id": "e1", "kind": "fill", "label": "Search", "role": "textbox", "value": "", "node": 10},
            {"id": "e2", "kind": "click", "label": "Open Search", "role": "textbox", "value": "", "node": 10},
            {"id": "e3", "kind": "click", "label": "Go", "role": "button", "value": "", "node": 20},
            {"id": "wait", "kind": "wait", "label": "Wait"},
        ],
    }
    state["fingerprint"] = fingerprint(state)
    return state


def choice(ids, selected):
    return {"choice": selected, "confidence": 1.0, "probabilities": {i: float(i == selected) for i in ids}}


def decision(action="e1"):
    return {
        "choice": action,
        "operation": "TYPE_TEXT",
        "target": "1",
        "confidence": 1.0,
        "probabilities": {action: 1.0},
        "latency_ms": 10,
        "usage": {},
    }


def gate_result(head, selected, ids, usage=None, text=None, is_error=False):
    """What the gated jev_classify tool returns for one head."""
    row = {
        "id": head,
        "classification": selected,
        "probabilities": {i: float(i == selected) for i in ids},
        "confidence": 1.0,
        "margin": 1.0,
        "top_probability": 1.0,
        "decision": "auto",
    }
    payload = {"tool": "jev_classify", "model": "test", "provider": "openrouter", "results": [row]}
    if usage is not None:
        payload["usage"] = usage
    body = text if text is not None else json.dumps(payload)
    return CallToolResult(content=[TextContent(type="text", text=body)], is_error=is_error)


def install_gate(monkeypatch, picks, **overrides):
    """Replace the gated session with canned results; the real follow-up still decides the second request."""
    requests = []

    def respond(arguments):
        head = arguments["items"][0]["id"]
        ids = [c["id"] for c in arguments["classes"]]
        if head in overrides:
            return overrides[head](head, ids)
        return gate_result(head, picks[head], ids, usage={"input_tokens": 5, "output_tokens": 2})

    async def ask(first, followup):
        requests.append(first)
        results = [respond(first)]
        if (second := followup(results[0])) is not None:
            requests.append(second)
            results.append(respond(second))
        return results

    monkeypatch.setattr(model, "ask_gate", ask)
    return requests


@pytest.mark.parametrize("mutation", ["unknown", "nan", "missing", "negative", "non_max"])
def test_invalid_choice_is_rejected(mutation):
    a = choice(["a", "b"], "a")
    if mutation == "unknown":
        a["choice"] = "invented"
    elif mutation == "nan":
        a["probabilities"]["a"] = float("nan")
    elif mutation == "missing":
        del a["probabilities"]["b"]
    elif mutation == "negative":
        a["probabilities"]["b"] = -1
    elif mutation == "non_max":
        a["choice"] = "b"
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.validate_choice(a, {"a", "b"})


def test_one_index_per_node_with_operation_specific_targets():
    elements, targets, controls = model.action_space(page()["actions"])
    assert len(elements) == 2
    assert elements[0]["operations"] == ["TYPE_TEXT", "CLICK"]
    assert targets["TYPE_TEXT"]["1"]["id"] == "e1"
    assert targets["CLICK"]["1"]["id"] == "e2"
    assert targets["CLICK"]["2"]["id"] == "e3"
    assert "WAIT" in controls


def test_only_the_chosen_operations_head_is_requested(monkeypatch):
    requests = install_gate(monkeypatch, {"operation": "CLICK", "click_target": "2"})
    d = model.choose(page(), "Find a book", [])
    assert [r["items"][0]["id"] for r in requests] == ["operation", "click_target"]
    assert [c["id"] for c in requests[0]["classes"]] == ["TYPE_TEXT", "CLICK", "WAIT", "DONE", "BLOCKED"]
    assert [c["id"] for c in requests[1]["classes"]] == ["1", "2"]
    assert d["operation"] == "CLICK" and d["target"] == "2" and d["choice"] == "e3"
    assert d["probabilities"] == {"e2": 0.0, "e3": 1.0}
    assert d["operation_probabilities"]["CLICK"] == 1.0 and d["target_probabilities"] == {"1": 0.0, "2": 1.0}
    assert d["confidence"] == 1.0 and d["target_confidence"] == 1.0
    assert d["model"] == "test" and d["usage"] == {"input_tokens": 10, "output_tokens": 4}
    assert isinstance(d["latency_ms"], int) and d["request"] == requests
    assert set(d["raw_answers"]) == {"operation", "click_target"}


def test_lone_option_is_chosen_without_a_model_call(monkeypatch):
    # jev_classify needs two options; the text field is the only TYPE_TEXT target.
    requests = install_gate(monkeypatch, {"operation": "TYPE_TEXT"})
    d = model.choose(page(), "Find a book", [])
    assert [r["items"][0]["id"] for r in requests] == ["operation"] and d["request"] == requests
    assert d["operation"] == "TYPE_TEXT" and d["target"] == "1" and d["choice"] == "e1"
    assert d["probabilities"] == {"e1": 1.0} and d["target_probabilities"] == {"1": 1.0}
    assert d["target_confidence"] == 1.0 and d["usage"] == {"input_tokens": 5, "output_tokens": 2}
    assert d["raw_answers"]["type_text_target"]["choice"] == "1"


def test_control_operation_needs_no_target_request(monkeypatch):
    requests = install_gate(monkeypatch, {"operation": "WAIT"})
    d = model.choose(page(), "Find a book", [])
    assert len(requests) == 1 and d["request"] == requests
    assert d["choice"] == "wait" and d["operation"] == "WAIT" and d["target"] is None
    assert d["probabilities"] == {"wait": 1.0} and d["target_probabilities"] == {} and d["target_confidence"] is None
    assert d["usage"] == {"input_tokens": 5, "output_tokens": 2}


@pytest.mark.parametrize("operation", ["DONE", "BLOCKED"])
def test_terminal_operation_keeps_its_name_as_the_choice(monkeypatch, operation):
    install_gate(monkeypatch, {"operation": operation})
    d = model.choose(page(), "Find a book", [])
    assert d["choice"] == operation and d["probabilities"] == {operation: 1.0}


def test_click_cannot_consume_a_text_target(monkeypatch):
    requests = install_gate(
        monkeypatch,
        {"operation": "CLICK"},
        click_target=lambda head, ids: gate_result(head, "999", [*ids, "999"]),
    )
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.choose(page(), "Find a book", [])
    # Only the click head is requested; the text head is never asked.
    assert [r["items"][0]["id"] for r in requests] == ["operation", "click_target"]
    assert [c["id"] for c in requests[1]["classes"]] == ["1", "2"]


def test_target_head_receives_control_state_and_full_next_step_rules(monkeypatch):
    p = page()
    p["actions"].insert(0, {
        "id": "toggle", "kind": "click", "label": "Free cancellation", "node": 30,
        "role": "checkbox", "checked": "true", "selected": False,
    })
    requests = install_gate(monkeypatch, {"operation": "CLICK", "click_target": "3"})
    d = model.choose(p, "Search with free cancellation", [])
    first, second = requests
    target = {c["id"]: json.loads(c["description"]) for c in second["classes"]}
    assert target["1"]["checked"] == "true" and target["1"]["selected"] is False
    assert target["1"]["element"] == "[1] Free cancellation"
    assert first["purpose"] in second["purpose"] and second["purpose"].endswith(TARGET)
    assert second["context"]["goal"] == "Search with free cancellation" and second["context"]["operation"] == "CLICK"
    assert d["choice"] == "e3"


def test_request_carries_goal_page_elements_and_recent_actions_within_bounds(monkeypatch):
    history = [{"action": f"a{n}", "kind": "click", "text": None, "page_changed": True, "secret": "x"} for n in range(15)]
    requests = install_gate(monkeypatch, {"operation": "DONE"})
    model.choose(page(), "Find a book", history)
    (first,) = requests
    assert set(first) == {"items", "classes", "purpose", "context"}
    assert len(first["items"]) == 1 and first["purpose"] == NEXT_ACTION
    assert set(first["context"]) == {"goal", "page", "elements", "recent_actions"}
    assert set(first["context"]["page"]) == {"url", "title", "text"}
    assert [h["action"] for h in first["context"]["recent_actions"]] == [f"a{n}" for n in range(5, 15)]
    assert all(set(h) == {"action", "kind", "text", "page_changed"} for h in first["context"]["recent_actions"])


def test_operation_is_validated_before_a_target_is_requested(monkeypatch):
    short = {"results": [{"classification": "CLICK", "probabilities": {"CLICK": 1.0}, "confidence": 1.0}]}
    requests = install_gate(
        monkeypatch, {}, operation=lambda head, ids: gate_result(head, None, [], text=json.dumps(short))
    )
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.choose(page(), "Find a book", [])
    assert len(requests) == 1


@pytest.mark.parametrize(
    "result",
    [
        gate_result("operation", None, [], text="not json"),
        gate_result("operation", None, [], text="[]"),
        gate_result("operation", None, [], text=json.dumps({"results": []})),
        gate_result("operation", None, [], text=json.dumps({"results": [{"status": "invalid_response", "probabilities": None}]})),
        CallToolResult(content=[]),
        CallToolResult(content=[TextContent(type="text", text="{}"), TextContent(type="text", text="{}")]),
        CallToolResult(content=[ImageContent(type="image", data="AA==", mime_type="image/png")]),
    ],
    ids=["text", "list", "no-rows", "invalid-row", "no-blocks", "two-blocks", "image"],
)
def test_malformed_result_is_rejected_without_a_second_request(monkeypatch, result):
    requests = install_gate(monkeypatch, {}, operation=lambda head, ids: result)
    with pytest.raises(ValueError, match="Invalid"):
        model.choose(page(), "Find a book", [])
    assert len(requests) == 1


@pytest.mark.parametrize("head", ["operation", "click_target"])
def test_gate_refusal_stops_the_step_and_requests_nothing_more(monkeypatch, head):
    refusal = lambda head, ids: gate_result(head, None, [], text="Privacy gate rejected the call.", is_error=True)
    requests = install_gate(monkeypatch, {"operation": "CLICK", "click_target": "1"}, **{head: refusal})
    with pytest.raises(RuntimeError, match="Jev gate refused or failed: Privacy gate rejected the call.*no action executed"):
        model.choose(page(), "Find a book", [])
    assert len(requests) == (1 if head == "operation" else 2)


def test_usage_sums_numbers_and_ignores_unvalidated_values():
    assert model.total_usage([{"usage": {"input_tokens": 3, "output_tokens": 1.5, "x": {"a": 1}, "y": "2", "z": True}}]) == {
        "input_tokens": 3,
        "output_tokens": 1.5,
    }
    assert model.total_usage([{"usage": None}, {"usage": "text"}, {}]) == {}
    assert model.total_usage([{"usage": {"input_tokens": 3}}, {"usage": {"input_tokens": 4}}]) == {"input_tokens": 7}


def test_text_helper_is_held_and_makes_no_connection(monkeypatch):
    monkeypatch.setenv("TEXT_MODEL_API_KEY", "synthetic-test-key")
    monkeypatch.setattr(socket, "create_connection", Mock(side_effect=AssertionError("network used")))
    monkeypatch.setattr(socket.socket, "connect", Mock(side_effect=AssertionError("network used")))
    context = model.field_context('Fly from "Zurich" to London', page()["actions"][0], page(), [])
    assert context["goal"] == 'Fly from "Zurich" to London'
    with pytest.raises(ValueError, match="held.*nothing typed"):
        model.field_text(context)


def test_no_direct_provider_route_remains():
    assert not any(hasattr(model, name) for name in ("request_jev", "post_json", "CLIENT", "httpx"))


@pytest.fixture
def runner():
    a = loop.Agent.__new__(loop.Agent)
    a.screenshots = False
    a.pending_text = None
    p = page()
    a.state = {
        "browser": Mock(fresh=Mock(return_value=True), observe=Mock(return_value=p)),
        "page": p,
        "decision": decision(),
        "goal": "Find a book",
        "history": [],
        "decisions": [],
        "status": "predicted",
        "started_at": time.perf_counter(),
        "record": False,
        "text_calls": [],
    }
    return a


def test_stale_decision_is_consumed_before_any_mutation(runner):
    runner.state["browser"].fresh.return_value = False
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["browser"].act.assert_not_called()
    assert runner.state["decision"] is None


def test_generated_text_reused_only_for_identical_retry_context(runner, monkeypatch):
    helper = Mock(return_value=("book", {"model": "test", "latency_ms": 10}))
    monkeypatch.setattr(loop, "field_text", helper)
    runner.state["browser"].act.side_effect = [StalePage("Changed before input"), None]
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["decision"] = decision()
    runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert helper.call_count == 1
    assert runner.state["browser"].act.call_count == 2  # The first call rejects before any browser input.
    assert runner.pending_text is None


def test_changed_field_context_does_not_reuse_generated_text(runner, monkeypatch):
    helper = Mock(return_value=("book", {"model": "test", "latency_ms": 10}))
    monkeypatch.setattr(loop, "field_text", helper)
    runner.state["browser"].act.side_effect = [StalePage("Changed before input"), None]
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["page"]["text"] = "Different page context"
    runner.state["decision"] = decision()
    runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert helper.call_count == 2


def test_loading_waits_do_not_trigger_no_progress_stop(runner):
    for _ in range(5):
        runner.state["decision"] = decision("wait")
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert len(runner.state["history"]) == 5 and runner.state["status"] == "ready"


def test_stale_observation_preserves_executed_action(runner):
    runner.state["decision"] = decision("e3")
    runner.state["browser"].observe.side_effect = StalePage("changed")
    with pytest.raises(StalePage):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    assert runner.state["history"][-1]["action"] == "Go"
    runner.state["browser"].act.assert_called_once()


def test_observation_is_one_atomic_browser_read(monkeypatch):
    import jev_ultrafast.browser as browser

    p = page()
    cdp = Mock(return_value={"result": {"value": p}})
    monkeypatch.setattr(browser, "cdp", cdp)
    actual = browser_operation({"operation": "observe", "session": "test", "screenshot": False})
    assert actual["actions"] == p["actions"]
    assert cdp.call_count == 1
    assert cdp.call_args.args[0] == "Runtime.evaluate"


def test_executor_rejects_a_stale_page_before_browser_input(monkeypatch):
    import jev_ultrafast.browser as browser

    b = browser.Browser.__new__(browser.Browser)
    b.fresh = Mock(return_value=False)
    operation = Mock()
    monkeypatch.setattr(browser, "browser_operation", operation)
    with pytest.raises(StalePage):
        b.act(page()["actions"][0], page(), "book")
    operation.assert_not_called()


@pytest.mark.parametrize("response", [{"exceptionDetails": {}}, {"result": {}}])
def test_interrupted_dropdown_mutation_cannot_be_retried_as_stale(monkeypatch, response):
    import jev_ultrafast.browser as browser

    # A navigation can destroy the evaluation result after the change event already fired.
    if "exceptionDetails" in response:
        response["exceptionDetails"] = {"text": "Execution context destroyed"}
    cdp = Mock(return_value=response)
    monkeypatch.setattr(browser, "cdp", cdp)
    with pytest.raises(RuntimeError, match="Dropdown execution"):
        browser_operation({"operation": "act", "session": "test", "action": {
            "id": "e1", "kind": "select", "node": 1, "value": "Design",
        }})
    assert cdp.call_count == 1


def test_fingerprint_tracks_values_and_identity_not_screenshots():
    p = page()
    other = deepcopy(p)
    other["screenshot"] = "changed"
    assert fingerprint(p) == fingerprint(other)
    other["actions"][0]["node"] = 99
    assert fingerprint(p) != fingerprint(other)


@pytest.mark.parametrize("changed", ["Departure", "Where from?", "Where to?", "year"])
def test_flight_verification_rejects_wrong_trip(changed):
    from examples.flights import verify

    actual = {
        "url": "https://www.google.com/travel/flights/search?tfs=example",
        "text": "Track prices from Zürich to London departing 2026-09-20",
        "actions": [
            {"label": k, "value": v}
            for k, v in [
                ("Change ticket type. One way", "One way"),
                ("Where from?", "Zürich"),
                ("Where to?", "London"),
                ("Departure", "Sun, Sep 20"),
                ("Nonstop flight on Sunday, September 20. Select flight", ""),
            ]
        ],
    }
    assert verify(actual)["passed"]
    if changed == "year":
        actual["text"] = actual["text"].replace("2026", "2027")
    else:
        next(a for a in actual["actions"] if a["label"] == changed)["value"] = "wrong"
    assert not verify(actual)["passed"]


def test_navigation_during_prediction_reobserves_without_action(runner):
    runner.state["browser"].fresh.side_effect = StalePage("Document navigating")
    runner.command("tick")
    assert runner.state["status"] == "ready"
    assert runner.state["decision"] is None
    runner.state["browser"].act.assert_not_called()


def test_prediction_through_the_gate_never_touches_the_page(runner, monkeypatch):
    requests = install_gate(monkeypatch, {"operation": "CLICK", "click_target": "2"})
    runner.state["decision"] = None
    runner.state["decisions"] = []
    runner.command("predict")
    assert runner.state["decision"]["choice"] == "e3" and runner.state["status"] == "predicted"
    assert len(requests) == 2 and len(runner.state["decisions"]) == 1
    runner.state["browser"].act.assert_not_called()
    runner.state["browser"].fresh.assert_called()


def test_gate_refusal_leaves_no_decision_to_execute(runner, monkeypatch):
    install_gate(
        monkeypatch,
        {},
        operation=lambda head, ids: gate_result(head, None, [], text="Privacy gate rejected the call.", is_error=True),
    )
    runner.state["decision"] = None
    with pytest.raises(RuntimeError, match="no action executed"):
        runner.command("predict")
    assert runner.state["decision"] is None and runner.state["decisions"] == []
    with pytest.raises(ValueError, match="Observe and choose before acting"):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["browser"].act.assert_not_called()


def test_held_text_helper_stops_a_typing_step_before_any_input(runner):
    runner.state["decision"] = decision("e1")
    with pytest.raises(ValueError, match="held"):
        runner.command("act", {"fingerprint": runner.state["page"]["fingerprint"]})
    runner.state["browser"].act.assert_not_called()
    assert runner.state["decision"] is None and runner.state["history"] == []


@pytest.mark.parametrize("head", ["operation", "click_target"])
@pytest.mark.parametrize("case", ["wrong-id", "missing-id", "extra-row", "no-row", "invalid-response", "sum-off", "near-non-max"])
def test_choice_head_trust_boundary(monkeypatch, head, case):
    def corrupt(request_head, ids):
        selected = "CLICK" if request_head == "operation" else "1"
        result = gate_result(request_head, selected, ids)
        payload = json.loads(result.content[0].text)
        row = payload["results"][0]
        if case == "wrong-id":
            row["id"] = "other-head"
        elif case == "missing-id":
            del row["id"]
        elif case == "extra-row":
            payload["results"].append(dict(row))
        elif case == "no-row":
            payload["results"] = []
        elif case == "invalid-response":
            row["status"] = "invalid_response"
        elif case == "sum-off":
            row["probabilities"][selected] = 0.985
        else:
            row["probabilities"] = dict.fromkeys(ids, 0.0)
            row["probabilities"][selected] = 0.5 - 2e-8
            row["probabilities"][next(i for i in ids if i != selected)] = 0.5 + 2e-8
        result.content[0].text = json.dumps(payload)
        return result

    requests = install_gate(monkeypatch, {"operation": "CLICK", "click_target": "1"}, **{head: corrupt})
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.choose(page(), "Synthetic goal", [])
    assert len(requests) == (1 if head == "operation" else 2)


@pytest.mark.parametrize("confidence", [None, "bad", True, 5, float("nan"), float("inf")])
def test_choice_old_confidence_normalizes(confidence):
    a = choice(["a", "b"], "a")
    a["confidence"] = confidence
    assert model.validate_choice(a, ["a", "b"])["confidence"] is None


@pytest.mark.parametrize("probabilities", [{"a": 0.9, "b": 0.09}, {"a": 0.5 - 2e-10, "b": 0.5 + 2e-10}])
def test_choice_old_tolerance_accepts(probabilities):
    a = {"choice": "a", "probabilities": probabilities, "confidence": 1.0, "margin": -5}
    assert model.validate_choice(a, ["a", "b"])["choice"] == "a"


@pytest.mark.parametrize("head", ["operation", "click_target"])
def test_choice_probability_object_required(monkeypatch, head):
    def corrupt(request_head, ids):
        selected = "CLICK" if request_head == "operation" else "1"
        result = gate_result(request_head, selected, ids)
        payload = json.loads(result.content[0].text)
        row = payload["results"][0]
        row["probabilities"] = list(row["probabilities"].items())
        result.content[0].text = json.dumps(payload)
        return result

    requests = install_gate(monkeypatch, {"operation": "CLICK", "click_target": "1"}, **{head: corrupt})
    with pytest.raises(ValueError, match="Invalid TypeSafe"):
        model.choose(page(), "Synthetic goal", [])
    assert len(requests) == (1 if head == "operation" else 2)


def test_choice_old_confidence_absent():
    a = choice(["a", "b"], "a")
    del a["confidence"]
    assert model.validate_choice(a, ["a", "b"])["confidence"] is None
