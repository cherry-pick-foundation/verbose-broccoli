"""In-memory scripted judge for testing tool requests and results."""

from collections import deque
from collections.abc import Iterable
from copy import deepcopy
from pathlib import Path

from backfire.judge import JSONContent, JudgmentRequest, JudgmentResult, Questions


class ScriptedJudge:
    def __init__(self, script: Iterable[JudgmentResult]) -> None:
        self.script = deque(deepcopy(list(script)))
        self.requests: list[JudgmentRequest] = []

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
        if not self.script:
            raise AssertionError("Scripted judge has no answer left.")
        return self.script.popleft()
