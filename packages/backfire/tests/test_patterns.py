import asyncio
import json
import signal
import sys
import time

import pytest

from backfire import patterns


@pytest.mark.parametrize(
    "document, pattern, flags, candidates",
    [
        ("price $10, again $10, now $12", r"\$\d+", "", ["$10", "$12"]),
        ("abc", "z*", "", []),
        ("a1 b2", r"([ab])(\d)", "", ["a1", "b2"]),
        ("ONE\ntwo", "^one|^two", "im", ["ONE", "two"]),
        ("a\nb", "a.b", "s", ["a\nb"]),
        ("한글 １２3", r"\w+", "", ["한글", "１２3"]),
        ("１２3", r"\d+", "a", ["3"]),
        ("name", r"(?P<label>\w+)", "", ["name"]),
        ("ab", "a b # comment", "x", ["ab"]),
        ("A a", "a", "gi!gii", ["A", "a"]),
        ("A a", "a", "I", ["a"]),
    ],
)
def test_patterns_keep_full_verbatim_matches(
    document, pattern, flags, candidates
):
    assert asyncio.run(patterns.run_regex(document, pattern, flags)) == {
        "candidates": candidates,
        "truncated": False,
        "tooLong": 0,
    }


def test_candidate_limits_skip_overlong_and_duplicate_values_before_cap():
    async def exercise():
        allowed = [f"x{index}" for index in range(20)]
        overlong = "a" * 2001
        document = " ".join([overlong, overlong, *allowed, "x0"])
        assert await patterns.run_regex(document, r"\w+") == {
            "candidates": allowed,
            "truncated": False,
            "tooLong": 1,
        }
        assert await patterns.run_regex(document + " extra", r"\w+") == {
            "candidates": allowed,
            "truncated": True,
            "tooLong": 1,
        }
        assert await patterns.run_regex("b" * 2000, "b+") == {
            "candidates": ["b" * 2000],
            "truncated": False,
            "tooLong": 0,
        }
        assert await patterns.run_regex("😀" * 1001 + " ok", r"\S+") == {
            "candidates": ["ok"],
            "truncated": False,
            "tooLong": 1,
        }

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "pattern, flags, error_text",
    [
        ("[", "", "unterminated character set"),
        ("(?<label>a)", "", "unknown extension"),
        ("a", "y", "unsupported regex flag: y"),
        ("a", "au", "ASCII and UNICODE flags are incompatible"),
    ],
)
def test_invalid_patterns_are_results(pattern, flags, error_text):
    result = asyncio.run(patterns.run_regex("a", pattern, flags))
    assert result["candidates"] == []
    assert result["truncated"] is False
    assert result["tooLong"] == 0
    assert error_text in result["error"]


def test_pattern_timeout_keeps_event_loop_responsive_and_reaps_child(
    monkeypatch,
):
    async def exercise():
        spawned = []
        original_spawn = asyncio.create_subprocess_exec

        async def observe_spawn(*args, **kwargs):
            child = await original_spawn(*args, **kwargs)
            spawned.append(child)
            return child

        monkeypatch.setattr(
            patterns.asyncio, "create_subprocess_exec", observe_spawn
        )
        gaps = []

        async def ticker():
            previous = time.monotonic()
            while True:
                await asyncio.sleep(0.02)
                current = time.monotonic()
                gaps.append(current - previous)
                previous = current

        ticker_task = asyncio.create_task(ticker())
        started = time.monotonic()
        try:
            result = await patterns.run_regex("a" * 50_000 + "!", "(a+)+$")
        finally:
            ticker_task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await ticker_task
        elapsed = time.monotonic() - started
        assert result == {
            "candidates": [],
            "truncated": False,
            "tooLong": 0,
            "error": "regex timed out after 1000ms; simplify the pattern",
        }
        assert 0.8 <= elapsed < 2
        assert len(gaps) >= 10 and max(gaps) < 0.2
        assert len(spawned) == 1 and spawned[0].returncode is not None
        assert await patterns.run_regex("ok", "ok") == {
            "candidates": ["ok"],
            "truncated": False,
            "tooLong": 0,
        }

    asyncio.run(exercise())


def test_child_timer_alone_ends_stuck_regex():
    async def exercise():
        child = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "backfire.patterns",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        started = time.monotonic()
        try:
            output, error = await asyncio.wait_for(
                child.communicate(
                    json.dumps(
                        {
                            "document": "a" * 50_000 + "!",
                            "pattern": "(a+)+$",
                            "flags": "",
                        }
                    ).encode()
                ),
                2,
            )
            assert child.returncode == -signal.SIGALRM
            assert output == error == b""
            assert 0.8 <= time.monotonic() - started < 2
        finally:
            if child.returncode is None:
                child.kill()
            await child.wait()

    asyncio.run(exercise())


def test_cancellation_kills_and_reaps_pattern_child(monkeypatch):
    async def exercise():
        spawned = asyncio.Event()
        children = []
        original_spawn = asyncio.create_subprocess_exec

        async def observe_spawn(*args, **kwargs):
            child = await original_spawn(*args, **kwargs)
            children.append(child)
            spawned.set()
            return child

        monkeypatch.setattr(
            patterns.asyncio, "create_subprocess_exec", observe_spawn
        )
        call = asyncio.create_task(
            patterns.run_regex("a" * 50_000 + "!", "(a+)+$")
        )
        await asyncio.wait_for(spawned.wait(), 1)
        await asyncio.sleep(0.1)
        started = time.monotonic()
        call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(call, 0.5)
        assert time.monotonic() - started < 0.5
        assert len(children) == 1 and children[0].returncode == -signal.SIGKILL

    asyncio.run(exercise())


def test_awaited_fields_finish_in_order_with_no_child_left(monkeypatch):
    async def exercise():
        children = []
        original_spawn = asyncio.create_subprocess_exec

        async def observe_spawn(*args, **kwargs):
            assert all(child.returncode is not None for child in children)
            child = await original_spawn(*args, **kwargs)
            children.append(child)
            return child

        monkeypatch.setattr(
            patterns.asyncio, "create_subprocess_exec", observe_spawn
        )
        results = []
        for pattern in ("a", "[", "b"):
            results.append(await patterns.run_regex("a b", pattern))
        assert [result["candidates"] for result in results] == [
            ["a"],
            [],
            ["b"],
        ]
        assert "error" in results[1]
        assert len(children) == 3 and all(
            child.returncode is not None for child in children
        )

    asyncio.run(exercise())
