"""Jev makes choices through the gated jev-mcp proxy; the text helper is held."""

import asyncio
import json
import os
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client

from .questions import NEXT_ACTION, TARGET

# The only route to a model: the gated jev-mcp proxy, which loads its own key.
GATE = StdioServerParameters(
    command="uv",
    args=[
        "--directory",
        str(Path(__file__).resolve().parents[3] / "education-privacy-gate"),
        "run",
        "--frozen",
        "--offline",
        "--no-sync",
        "jev-mcp",
    ],
    env={"XDG_CONFIG_HOME": config}
    if (config := os.environ.get("XDG_CONFIG_HOME")) and Path(config).is_absolute()
    else None,
)
# Seconds per request; the proxy's own upstream deadline is 60.
TIMEOUT = 90


def classify(head, text, classes, purpose, context):
    """One jev_classify request: a single question over a catalog of options."""
    return {
        "items": [{"id": head, "text": text}],
        "classes": [{"id": key, "description": description} for key, description in classes.items()],
        "purpose": purpose,
        "context": context,
    }


async def ask_gate(first, followup):
    """Send `first`, then the request `followup` builds from its result, in one gated session."""
    try:
        async with (
            stdio_client(GATE) as (read, write),
            ClientSession(read, write, read_timeout_seconds=TIMEOUT) as session,
        ):
            await session.initialize()
            results = [await session.call_tool("jev_classify", first)]
            if (second := followup(results[0])) is not None:
                results.append(await session.call_tool("jev_classify", second))
    except ExceptionGroup as group:
        error = group
        while isinstance(error, ExceptionGroup):
            error = error.exceptions[0]
        raise RuntimeError(f"Jev gate failed: {error}; no action executed.") from None
    return results


def parse(result):
    """The JSON in one jev_classify result; a refusal or error stops the step."""
    if result.is_error:
        text = " ".join(getattr(block, "text", "") for block in result.content)
        raise RuntimeError(f"Jev gate refused or failed: {text}; no action executed.")
    try:
        [block] = result.content
        return json.loads(block.text)
    except (AttributeError, ValueError):
        raise ValueError("Invalid Jev gate result; no action executed.") from None


def answer(parsed, head):
    """The one classification row of a jev_classify result, shaped as validate_choice reads an answer."""
    try:
        [row] = parsed["results"]
        if row["id"] != head or row.get("status") == "invalid_response":
            raise ValueError("Invalid TypeSafe response; no action executed.")
        return {
            "choice": row["classification"],
            "probabilities": row["probabilities"],
            "confidence": row.get("confidence"),
        }
    except (KeyError, IndexError, TypeError, ValueError):
        raise ValueError("Invalid TypeSafe response; no action executed.") from None


def total_usage(results):
    """Sum the numeric counts of every call; upstream does not validate usage values."""
    usage = {}
    for parsed in results:
        counts = parsed.get("usage")
        for key, value in counts.items() if isinstance(counts, dict) else ():
            if type(value) in (int, float):
                usage[key] = usage.get(key, 0) + value
    return usage


def validate_choice(answer, ids):
    # jev_judge_mcp/validation/choice.py:12-57: sum/argmax tolerances;
    # numbers.py:33-35: malformed confidence is unknown; no margin condition.
    try:
        probabilities = answer["probabilities"]
        valid = (
            isinstance(answer["choice"], str)
            and answer["choice"] in ids
            and isinstance(probabilities, dict)
            and set(probabilities) == set(ids)
            and all(type(n) in (int, float) and 0 <= n <= 1 for n in probabilities.values())
        )
        if not valid:
            raise ValueError
        # JS array-index keys first, then insertion order; left-to-right float64 sum.
        indices = {k for k in probabilities if k.isascii() and k.isdigit() and str(int(k)) == k and int(k) < 2**32 - 1}
        total = 0.0
        for key in sorted(indices, key=int) + [k for k in probabilities if k not in indices]:
            total += float(probabilities[key])
        valid = (
            abs(total - 1) <= 0.01 + 1e-12
            and probabilities[answer["choice"]] >= max(probabilities.values()) - 1e-9
        )
    except (KeyError, TypeError, ValueError, AttributeError):
        valid = False
    if not valid:
        raise ValueError("Invalid TypeSafe response; no action executed.")
    confidence = answer.get("confidence")
    return {
        **answer,
        "confidence": float(confidence) if type(confidence) in (int, float) and 0 <= confidence <= 1 else None,
    }


def action_space(actions):
    """One index per observed element; each operation has its own valid target choices."""
    elements, indices, targets, controls = [], {}, {}, {}
    operations = {"click": "CLICK", "fill": "TYPE_TEXT", "select": "SELECT"}
    for action in actions:
        kind = action["kind"]
        if kind not in operations:
            controls[action["id"].upper()] = action
            continue
        node = action["node"]
        if node not in indices:
            index = str(len(elements) + 1)
            indices[node] = index
            element = {k: action[k] for k in ("role", "value", "checked", "selected", "expanded") if k in action}
            element.update(index=index, label=action["label"].split(" → ")[0], operations=[])
            if kind == "select":
                element["value"] = action.get("current_value", "")
                element["options"] = []
            elements.append(element)
        index = indices[node]
        operation = operations[kind]
        group = targets.setdefault(operation, {})
        element = elements[int(index) - 1]
        if operation not in element["operations"]:
            element["operations"].append(operation)
        target = index
        if kind == "select":
            target = f"{index}:{len(element['options']) + 1}"
            element["options"].append({"index": target, "label": action["label"], "value": action["value"]})
        group[target] = action
    return elements, targets, controls


def choose(state, goal, history):
    elements, targets, controls = action_space(state["actions"])
    labels = {
        "CLICK": "Click an element, button, menu option, autocomplete suggestion, or calendar day.",
        "TYPE_TEXT": "Enter or replace text in an editable field. A small LLM will supply the value from the goal.",
        "SELECT": "Select an observed dropdown value.",
    }
    operations = {key: labels[key] for key in targets}
    operations.update({key: value["label"] for key, value in controls.items()})
    operations.update(DONE="Every requirement is visibly satisfied.", BLOCKED="No supported operation can progress.")
    context = {
        "goal": goal,
        "page": {k: state[k] for k in ("url", "title", "text")},
        "elements": elements,
        "recent_actions": [{k: h.get(k) for k in ("action", "kind", "text", "page_changed")} for h in history[-10:]],
    }

    def target_request(operation):
        classes = {
            index: json.dumps(
                {
                    "element": f"[{index}] {a['label']}",
                    "current_value": a.get("current_value", a.get("value", "")),
                    **{k: a[k] for k in ("role", "checked", "selected", "expanded") if k in a},
                },
                ensure_ascii=False,
            )
            for index, a in targets[operation].items()
        }
        return classify(
            operation.lower() + "_target",
            f"Which element should the {operation} operation use?",
            classes,
            f"{NEXT_ACTION}\n\n{TARGET}",
            {**context, "operation": operation},
        )

    def followup(result):
        # Only the chosen operation's target is requested, and only when it has options to choose between
        # (jev_classify needs two). A bad answer gets no second request; it is rejected below.
        try:
            operation = validate_choice(answer(parse(result), "operation"), operations)["choice"]
        except (RuntimeError, ValueError):
            return None
        return target_request(operation) if len(targets.get(operation, ())) > 1 else None

    first = classify("operation", "Which operation should run next?", operations, NEXT_ACTION, context)
    started = time.perf_counter()
    parsed = [parse(result) for result in asyncio.run(ask_gate(first, followup))]
    operation_answer = validate_choice(answer(parsed[0], "operation"), operations)
    operation = operation_answer["choice"]
    target = None
    target_answer = None
    probabilities = {}
    if operation in targets:
        # Only the head selected by the operation is requested and validated; no other head can cause an action.
        if len(targets[operation]) > 1:
            target_answer = validate_choice(answer(parsed[1], operation.lower() + "_target"), targets[operation])
        else:
            # A lone option is no judgment: it is chosen without a model call.
            (only,) = targets[operation]
            target_answer = {"choice": only, "probabilities": {only: 1.0}, "confidence": 1.0}
        target = target_answer["choice"]
        choice = targets[operation][target]["id"]
        probabilities = {a["id"]: target_answer["probabilities"][index] for index, a in targets[operation].items()}
    else:
        choice = controls[operation]["id"] if operation in controls else operation
        probabilities[choice] = operation_answer["probabilities"][operation]
    return {
        "choice": choice,
        "operation": operation,
        "target": target,
        "confidence": operation_answer["confidence"],
        "probabilities": probabilities,
        "operation_probabilities": operation_answer["probabilities"],
        "target_probabilities": target_answer["probabilities"] if target_answer else {},
        "target_confidence": target_answer["confidence"] if target_answer else None,
        "raw_answers": {"operation": operation_answer, **({operation.lower() + "_target": target_answer} if target_answer else {})},
        "model": parsed[0].get("model"),
        "usage": total_usage(parsed),
        "latency_ms": round((time.perf_counter() - started) * 1000),
        "request": [first, target_request(operation)] if len(parsed) > 1 else [first],
    }


def field_context(goal, action, page, history):
    return {
        "goal": goal,
        "field": {k: action.get(k) for k in ("label", "role", "value")},
        "page": {"title": page["title"], "text": page["text"][:6000]},
        "recent_actions": [{k: h.get(k) for k in ("action", "text")} for h in history[-6:]],
    }


def field_text(context):
    # Held: page and goal text has no gated route, so no text model is called and nothing is typed.
    raise ValueError("TYPE_TEXT is held until the text helper has a gated route; nothing typed.")
