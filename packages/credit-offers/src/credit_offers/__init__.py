"""Search the tracker for newly listed API credit offers."""

from argparse import ArgumentParser
import asyncio
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import httpx
from mcp import ClientSession
from mcp import StdioServerParameters
from mcp import stdio_client

TRACKER = tomllib.loads(Path(__file__).with_name("tracker.toml").read_text())
FIELDS = ("slug", "title", "provider", "category", "amount", "source_url")
CRITERIA = {
    "qualifies": "Claiming it costs nothing, and it states no time limit, "
    "trial period, expiry or end date",
    "excluded": "Claiming it needs a payment, deposit, top-up or paid plan, "
    "or it states a time limit, trial period, expiry or end date",
}
ERRORS = (
    httpx.HTTPError,
    KeyError,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
    subprocess.CalledProcessError,
)
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
)
# Seconds per request; the proxy's own upstream deadline is 60.
TIMEOUT = 90
# The most items one jev_classify call accepts.
MAX_OFFERS = 64


def _block(hours, end=None, now=None):
    if hours <= 0 or 24 % hours:
        raise ValueError("--hours must divide 24")
    local = (now or dt.datetime.now().astimezone()).astimezone()
    finish = (
        dt.datetime.fromisoformat(end).astimezone()
        if end is not None
        else local.replace(
            hour=local.hour // hours * hours, minute=0, second=0, microsecond=0
        )
    )
    if finish.hour % hours or any(
        (finish.minute, finish.second, finish.microsecond)
    ):
        raise ValueError("--end must be a local block boundary")
    return finish - dt.timedelta(hours=hours), finish


def _get_json(client, url, **kwargs):
    return client.get(url, **kwargs).raise_for_status().json()


def notify(offers):
    """Show one desktop notification for the supplied strong offers."""
    text = "\n".join(
        f"{o['title']} — {o['provider']} — {o['amount']}\n{o['source_url']}"
        for o in offers
    )
    subprocess.run(
        ["notify-send", "--", "New API credit offers", text], check=True
    )


async def judge(offers):
    """Classify the offers in one call to the gated jev-mcp proxy."""
    if len(offers) > MAX_OFFERS:
        raise ValueError(
            f"{len(offers)} offers exceed the {MAX_OFFERS} one call can judge"
        )
    arguments = {
        "items": [
            {
                "id": offer["slug"],
                "text": json.dumps(
                    {field: offer.get(field) for field in FIELDS},
                    ensure_ascii=False,
                ),
            }
            for offer in offers
        ],
        "classes": [
            {"id": choice, "description": description}
            for choice, description in CRITERIA.items()
        ],
        "purpose": "Judge each API credit offer.",
    }
    try:
        async with (
            stdio_client(GATE) as (read, write),
            ClientSession(read, write, read_timeout_seconds=TIMEOUT) as session,
        ):
            await session.initialize()
            result = await session.call_tool("jev_classify", arguments)
    except ExceptionGroup as group:
        error = group
        while isinstance(error, ExceptionGroup):
            error = error.exceptions[0]
        raise RuntimeError(f"jev-mcp: {error}") from None
    if result.is_error:
        text = " ".join(getattr(block, "text", "") for block in result.content)
        raise RuntimeError(f"jev-mcp: {text}")
    return result


def _answer(row):
    """The (choice, probability) of one classification row, if it is valid."""
    choice, probabilities = row["classification"], row["probabilities"]
    if (
        row.get("status") == "invalid_response"
        or choice not in CRITERIA
        or set(probabilities) != set(CRITERIA)
        or not all(
            type(value) in (int, float) and 0 <= value <= 1
            for value in probabilities.values()
        )
    ):
        raise ValueError("Invalid choice answer")
    return choice, float(probabilities[choice])


def _answers(result, offers):
    """Map a jev_classify result to each offer's (choice, probability)."""
    try:
        [block] = result.content
        rows = {row["id"]: row for row in json.loads(block.text)["results"]}
        return {offer["slug"]: _answer(rows[offer["slug"]]) for offer in offers}
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid choice answer") from error


def main(argv=None):
    """Run one block of the tracker search and return its exit status."""
    parser = ArgumentParser(prog="credit-offers")
    parser.add_argument("--hours", type=int, default=6)
    parser.add_argument("--end")
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args(argv)
    try:
        start, end = _block(args.hours, args.end)
    except ValueError as error:
        parser.error(str(error))

    jev_calls = 0
    token = os.environ.get(TRACKER["token_env"], "").strip()
    try:
        api = f"{TRACKER['api_root']}/repos/{TRACKER['repository']}/commits"
        query = {"path": TRACKER["index_path"], "per_page": 1}
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        with httpx.Client(timeout=25) as client:
            commits = [
                _get_json(
                    client,
                    api,
                    headers=headers,
                    params={**query, "until": t.isoformat()},
                )
                for t in (start, end)
            ]
            if not all(commits):
                raise RuntimeError("No index commit for a boundary")
            before, after = (rows[0]["sha"] for rows in commits)
            offers = []
            if before != after:
                root = f"{TRACKER['raw_root']}/{TRACKER['repository']}"
                path = TRACKER["index_path"].lstrip("/")
                old = _get_json(client, f"{root}/{before}/{path}")["offers"]
                new = _get_json(client, f"{root}/{after}/{path}")["offers"]
                seen = {offer["slug"] for offer in old}
                offers = [
                    offer
                    for offer in new
                    if offer["slug"] not in seen
                    if offer.get("status") == "active"
                    if not offer.get("expiry_date")
                ]
        if not offers:
            print("No active offer is new in this block.\njev_calls=0")
            return 1

        result = asyncio.run(judge(offers))
        jev_calls = 1
        answers = _answers(result, offers)
        strong = [o for o in offers if answers[o["slug"]][0] == "qualifies"]
        for offer in offers:
            choice, probability = answers[offer["slug"]]
            print(f"{offer['slug']}\t{choice}\t{probability}")
        if args.notify and strong:
            notify(strong)
        print(f"jev_calls={jev_calls}")
        return 0 if strong else 1
    except ERRORS as error:
        message = str(error).replace(token, "[redacted]") if token else error
        print(f"credit-offers: {message}", file=sys.stderr)
        print(f"jev_calls={jev_calls}")
        return 3
