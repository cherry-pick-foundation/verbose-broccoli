"""Scripted judge and request capture for offline tool and stdio tests.

A file script is {"requests_file": "requests.jsonl", "script": [...]}.
Steps are raw results, {"result": <any JSON>}, {"error": "<type>: <message>"},
or {"stall": true}, which waits until cancelled. No answer is validated.
"""

import asyncio
from collections import deque
from collections.abc import Iterable
from copy import deepcopy
import json
from pathlib import Path

from backfire.judge import JSONContent, JudgmentRequest, JudgmentResult, Questions


class ScriptedJudge:
    def __init__(self, script: Iterable[object], *, requests_file: Path | None = None) -> None:
        self.script = deque(deepcopy(list(script)))
        self.requests: list[JudgmentRequest] = []
        self.requests_file = requests_file
        if requests_file is not None:
            requests_file.touch(exist_ok=True)

    @classmethod
    def from_file(cls, path: str | Path) -> "ScriptedJudge":
        path = Path(path).resolve()
        data = json.loads(path.read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or set(data) != {"script", "requests_file"}
                or not isinstance(data["script"], list)
                or not isinstance(data["requests_file"], str) or not data["requests_file"]):
            raise ValueError("Scripted judge requires a script array and a non-empty requests_file path.")
        requests_file = path.parent / data["requests_file"]
        if requests_file.resolve() == path:
            raise ValueError("Scripted judge script and requests_file must be different files.")
        return cls(data["script"], requests_file=requests_file)

    async def __call__(
        self,
        state: JSONContent,
        questions: Questions,
        *,
        deadline: float,
        record_file: Path | None = None,
    ) -> JudgmentResult:
        self.requests.append(deepcopy({
            "state": state, "questions": questions,
            "deadline": deadline, "record_file": record_file,
        }))
        if self.requests_file is not None:
            with self.requests_file.open("a", encoding="utf-8") as output:
                output.write(json.dumps({"state": state, "questions": questions}) + "\n")
        if not self.script:
            raise AssertionError("Scripted judge has no answer left.")
        step = self.script.popleft()
        if isinstance(step, dict):
            if set(step) == {"stall"} and step["stall"] is True:
                await asyncio.Future()
            if set(step) == {"error"}:
                raise RuntimeError(step["error"])
            if set(step) == {"result"}:
                return step["result"]
        return step
