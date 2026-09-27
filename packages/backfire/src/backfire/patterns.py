"""One bounded Python regex child per field; callers await fields in order."""

import asyncio
from contextlib import suppress
import json
import re
import signal
import sys
from typing import NotRequired, TypedDict

from backfire.lib import (
    MAX_EXTRACT_CANDIDATE_CHARS,
    MAX_EXTRACT_CANDIDATES,
    REGEX_TIMEOUT_MS,
)


class PatternResult(TypedDict):
    candidates: list[str]
    truncated: bool
    tooLong: int
    error: NotRequired[str]


def _failure(message: str) -> PatternResult:
    return {"candidates": [], "truncated": False, "tooLong": 0, "error": message}


def _match(document: str, pattern: str, flags: str) -> PatternResult:
    """Run only in the child: even compilation can consume the whole budget."""
    try:
        flag_values = {"a": re.A, "i": re.I, "m": re.M, "s": re.S, "u": re.U, "x": re.X}
        mask = 0
        for flag in flags:
            if flag == "g" or not "a" <= flag <= "z":
                continue
            if flag not in flag_values:
                raise ValueError(f"unsupported regex flag: {flag}")
            mask |= flag_values[flag]
        seen: set[str] = set()
        candidates = []
        truncated = False
        too_long = 0
        for match in re.finditer(pattern, document, mask):
            value = match[0]
            if not value or value in seen:
                continue
            seen.add(value)
            if len(value.encode("utf-16-le", errors="surrogatepass")) > MAX_EXTRACT_CANDIDATE_CHARS * 2:
                too_long += 1
                continue
            if len(candidates) >= MAX_EXTRACT_CANDIDATES:
                truncated = True
                break
            candidates.append(value)
        return {"candidates": candidates, "truncated": truncated, "tooLong": too_long}
    except (re.error, ValueError, OverflowError, RecursionError) as error:
        return _failure(str(error))


async def run_regex(document: str, pattern: str, flags: str = "") -> PatternResult:
    """Return upstream's worker shape; timeout and cancellation reap the child."""
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "backfire.patterns",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    timeout_error = f"regex timed out after {REGEX_TIMEOUT_MS}ms; simplify the pattern"
    try:
        payload = json.dumps({"document": document, "pattern": pattern, "flags": flags}).encode()
        try:
            output, _ = await asyncio.wait_for(process.communicate(payload), REGEX_TIMEOUT_MS / 1000)
        except TimeoutError:
            return _failure(timeout_error)
        if process.returncode == -signal.SIGALRM:
            return _failure(timeout_error)
        if process.returncode:
            return _failure(f"regex worker exited with code {process.returncode}")
        return json.loads(output)
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
        await process.wait()


def _main() -> None:
    # The OS default action ends a stuck C regex even if its parent has died.
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, REGEX_TIMEOUT_MS / 1000)
    request = json.load(sys.stdin)
    json.dump(_match(**request), sys.stdout)


if __name__ == "__main__":
    _main()
