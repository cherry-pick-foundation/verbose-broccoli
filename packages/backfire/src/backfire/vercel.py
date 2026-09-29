"""Ported from @jkudish/jev-agent-tools 0.1.2.

MIT; Copyright (c) 2026 Joey Kudish.

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import ClassVar, cast

from jev_judge_mcp.domain import JsonValue
from jev_judge_mcp.domain import Usage
from jev_judge_mcp.errors import Redactor
from jev_judge_mcp.providers.base import Evaluation
from jev_judge_mcp.providers.base import HttpProvider
from jev_judge_mcp.providers.base import ProviderError
from jev_judge_mcp.providers.base import ProviderName
from jev_judge_mcp.providers.base import decode_body


class VercelProvider(HttpProvider):
    """Call the Vercel AI Gateway using PyModel's HTTP provider base."""

    name: ClassVar[ProviderName] = cast(ProviderName, "vercel")
    label = "Vercel AI Gateway"

    def __init__(self, profile: dict, api_key: str) -> None:
        super().__init__(Redactor([api_key]))
        self._base_url, self._api_key = profile["base_url"], api_key

    async def _send(
        self,
        state: JsonValue,
        questions: dict[str, JsonValue],
        model: str,
        timeout: float | None,
    ) -> Evaluation:
        del timeout
        model = model if model.startswith("typesafe-ai/") else "typesafe-ai/jev"
        questions = {
            key: {
                **question,
                "type": "boolean"
                if question.get("type") == "noul"
                else question.get("type"),
            }
            for key, question in questions.items()
        }
        response = await self._post(
            self._base_url,
            {
                "Authorization": f"Bearer {self._api_key}",
                "ai-gateway-protocol-version": "0.0.1",
                "ai-gateway-auth-method": "api-key",
                "ai-evaluation-model-specification-version": "4",
                "ai-model-id": model,
            },
            {"state": state, "questions": questions},
        )
        if not response.is_success:
            raise self._error(response)
        result = decode_body(response.content)
        if not isinstance(result, dict):
            raise ProviderError(
                "Vercel AI Gateway invalid response (response omitted)"
            )
        usage = result.get("usage")
        if usage is not None and not isinstance(usage, dict):
            raise ProviderError(
                "Vercel AI Gateway invalid usage (response omitted)"
            )
        answers = result.get("answers")
        metadata = result.get("providerMetadata")
        typesafe = (
            metadata.get("typesafe") if isinstance(metadata, dict) else None
        )
        confidence = (
            typesafe.get("confidence", {}) if isinstance(typesafe, dict) else {}
        )
        mapped = {}
        for key, answer in answers.items() if isinstance(answers, dict) else ():
            if isinstance(answer, dict) and answer.get("type") == "boolean":
                mapped[key] = {
                    "type": "noul",
                    "noul": answer.get("probability"),
                }
            elif isinstance(answer, dict) and answer.get("type") in (
                "choice",
                "score",
            ):
                mapped[key] = {
                    **answer,
                    "confidence": confidence.get(key)
                    if isinstance(confidence, dict)
                    else None,
                }
            else:
                mapped[key] = answer
        usage = usage or {}
        return Evaluation(
            mapped,
            Usage(usage.get("inputTokens", 0), usage.get("outputTokens", 0)),
            self.name,
            model,
        )
