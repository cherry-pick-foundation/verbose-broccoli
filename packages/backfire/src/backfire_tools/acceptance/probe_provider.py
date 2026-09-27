"""Probe a selected profile without printing credentials or response content."""

import asyncio
import json
import math
import os
from pathlib import Path
import re
import sys
import time
import tomllib

import httpx2


def _object(value):
    return value if isinstance(value, dict) else {}


def _matches(pattern, value):
    return isinstance(value, str) and re.fullmatch(pattern, value) is not None


def _path(value):
    return isinstance(value, str) and all(value.split("."))


def _value_at_path(value, path):
    for key in path.split("."):
        value = _object(value).get(key)
    return value


def select_profile(value, provider_override=None):
    config = _object(value)
    if config.keys() - {"provider", "providers"} or (
        "provider" in config and not _matches(r"[a-z0-9-]+", config["provider"])
    ):
        raise ValueError
    name = provider_override if provider_override is not None else config.get("provider")
    providers = _object(config.get("providers"))
    if not _matches(r"[a-z0-9-]+", name) or name not in providers:
        raise ValueError

    profile = _object(providers[name])
    thinking = _object(profile.get("thinking"))
    request = profile.get("request", {})
    statuses = profile.get("statuses", {})
    rate = profile.get("rate_limit_per_second")
    if (
        profile.keys() - {
            "api", "base_url", "model", "credential", "rate_limit_per_second",
            "request", "thinking", "statuses",
        }
        or profile.get("api") != "openai"
        or not isinstance(profile.get("base_url"), str)
        or not profile["base_url"]
        or not isinstance(profile.get("model"), str)
        or not profile["model"]
        or not _matches(r"[A-Z_][A-Z0-9_]*", profile.get("credential"))
        or not isinstance(request, dict)
        or {"model", "messages", "stream", "n"} & request.keys()
        or thinking.keys() - {"requested", "content_path", "token_path"}
        or thinking.get("requested") not in ("on", "off")
        or any(key in thinking and not _path(thinking[key])
               for key in ("content_path", "token_path"))
        or (thinking["requested"] == "on"
            and not {"content_path", "token_path"} & thinking.keys())
        or (thinking["requested"] == "off"
            and {"content_path", "token_path"} & thinking.keys())
        or ("rate_limit_per_second" in profile
            and (type(rate) not in (int, float) or not math.isfinite(rate) or rate < 0))
        or not isinstance(statuses, dict)
        or any(not _matches(r"[0-9]+", status) or not 100 <= int(status) <= 599
               or meaning not in (
                   "credential_rejected", "balance_exhausted",
                   "request_rejected", "rate_limited",
               ) for status, meaning in statuses.items())
    ):
        raise ValueError

    return {
        "name": name,
        "base_url": profile["base_url"],
        "model": profile["model"],
        "credential": profile["credential"],
        **({"rate_limit_per_second": rate} if rate is not None else {}),
        "request": request,
        "thinking": {key: thinking[key] for key in ("content_path", "token_path")
                     if key in thinking},
    }


def summarize(label, status, body, elapsed_ms, thinking):
    response = _object(body)
    choices = response.get("choices")
    choice = _object(choices[0] if isinstance(choices, list) and choices else None)
    usage = _object(response.get("usage"))
    message = _object(choice.get("message"))
    summary = {"label": label, "status": status, "elapsed_ms": math.floor(elapsed_ms + 0.5)}
    if isinstance(response.get("model"), str):
        summary["model"] = response["model"]
    if thinking.get("content_path"):
        content = _value_at_path(message, thinking["content_path"])
        summary["thinking_content_non_empty"] = isinstance(content, str) and bool(content.strip())
    if thinking.get("token_path"):
        tokens = _value_at_path(usage, thinking["token_path"])
        summary["thinking_tokens"] = tokens if type(tokens) in (int, float) else None
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        if type(usage.get(key)) in (int, float):
            summary[key] = usage[key]
    if isinstance(choice.get("finish_reason"), str):
        summary["finish_reason"] = choice["finish_reason"]
    return summary


def burst_size(rate_limit=None):
    return None if rate_limit is None else math.floor(rate_limit) + 1


def burst_not_applicable():
    return {
        "label": "burst",
        "status": None,
        "not_applicable": "profile has no rate_limit_per_second",
    }


async def request(label, api_key, profile, model, fields, endpoint):
    started = time.perf_counter()
    status = None
    body = None
    try:
        async with asyncio.timeout(30), httpx2.AsyncClient(
            timeout=30, follow_redirects=True
        ) as client:
            async with client.stream(
                "POST", endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    **fields,
                    "model": model,
                    "messages": [{"role": "user", "content": "Return a small JSON object."}],
                },
            ) as response:
                status = response.status_code
                if status == 200:
                    await response.aread()
                    body = response.json()
    except Exception:
        # Transport errors and invalid response bodies must not reach the output.
        pass
    return summarize(label, status, body, (time.perf_counter() - started) * 1000, profile["thinking"])


async def main(args=None):
    source = Path(__file__).resolve().parents[2] / "backfire" / "config.toml"
    provider_override = None
    arguments = iter(sys.argv[1:] if args is None else args)
    for argument in arguments:
        if argument == "--config":
            source = Path(next(arguments))
        elif argument.startswith("--") or provider_override is not None:
            raise ValueError
        else:
            provider_override = argument
    with source.open("rb") as file:
        profile = select_profile(tomllib.load(file), provider_override)
    home = os.environ.get("HOME")
    config_home = os.environ.get("XDG_CONFIG_HOME", f"{home}/.config" if home else None)
    if not config_home:
        raise ValueError
    credentials = (Path(config_home) / "verbose-broccoli" / "backfire"
                   / f"{profile['name']}.env").read_text(encoding="utf-8")
    prefix = f"{profile['credential']}="
    api_key = next((line[len(prefix):].strip() for line in credentials.split("\n")
                    if line.startswith(prefix)), "")
    if not api_key:
        raise ValueError

    endpoint = f"{profile['base_url'].rstrip('/')}/chat/completions"
    results = [
        await request("settings", api_key, profile, profile["model"], profile["request"], endpoint),
        await request("invalid key", "not-a-valid-api-key-for-probe", profile,
                      profile["model"], profile["request"], endpoint),
        await request("unknown model", api_key, profile, "verbose-broccoli/unknown-model-for-probe",
                      profile["request"], endpoint),
    ]
    count = burst_size(profile.get("rate_limit_per_second"))
    if count is None:
        results.append(burst_not_applicable())
    else:
        results.extend(await asyncio.gather(*(
            request(f"burst-{index + 1}", api_key, profile, profile["model"],
                    {**profile["request"], "max_tokens": 1}, endpoint)
            for index in range(count)
        )))
    for result in results:
        print(json.dumps(result, separators=(",", ":"), ensure_ascii=False))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        print("Probe could not start.", file=sys.stderr)
        sys.exit(1)
