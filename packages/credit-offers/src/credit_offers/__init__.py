"""Search the tracker for newly listed API credit offers."""

from argparse import ArgumentParser
import datetime as dt
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import httpx

from jev_ultrafast import model

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
    try:
        api = f"{TRACKER['api_root']}/repos/{TRACKER['repository']}/commits"
        query = {"path": TRACKER["index_path"], "per_page": 1}
        token = os.environ.get(TRACKER["token_env"])
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

        questions = {
            o["slug"]: {
                "type": "choice",
                "criteria": CRITERIA,
                "instructions": {"offer": o["slug"], "task": "Judge this."},
            }
            for o in offers
        }
        result = model.request_jev(
            {
                "model": os.environ.get("TYPESAFE_MODEL", "jev-latest"),
                "state": {
                    "offers": [{f: o.get(f) for f in FIELDS} for o in offers]
                },
                "questions": questions,
            }
        )
        jev_calls = 1
        answers = {
            o["slug"]: model.validate_choice(
                result["answers"][o["slug"]], ("qualifies", "excluded")
            )
            for o in offers
        }
        strong = [
            o for o in offers if answers[o["slug"]]["choice"] == "qualifies"
        ]
        for offer in offers:
            answer = answers[offer["slug"]]
            print(
                f"{offer['slug']}\t{answer['choice']}\t{answer['probabilities'][answer['choice']]}"
            )
        if args.notify and strong:
            notify(strong)
        print(f"jev_calls={jev_calls}")
        return 0 if strong else 1
    except ERRORS as error:
        print(f"credit-offers: {error}", file=sys.stderr)
        print(f"jev_calls={jev_calls}")
        return 3
