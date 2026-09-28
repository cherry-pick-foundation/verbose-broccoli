"""Profile options and response checks around the pinned adapter's provider."""

import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field

from system_one_adapter.providers.base import record_request, render_messages, translating
from system_one_adapter.providers.openai import (
    AsyncOpenAIProvider, _response_format, _responses_request_kwargs,
    _responses_result, _result,
)
from typesafe_sdk import TypeSafeAPIError, TypeSafeError

from backfire.failures import JudgmentError


@dataclass
class ProviderCall:
    """The judge installs one per judgment and fills latency_ms at its end.

    Model and usage belong to the result; metadata contains only the four
    record fields, including on failure. Never keep response or reasoning text.
    """

    deadline: float
    model: str | None = None
    usage: dict[str, int] | None = None
    metadata: dict = field(default_factory=lambda: {
        "attempts": 0, "latency_ms": None,
        "thinking_evidence": None, "reasoning_tokens": None,
    })


provider_call: ContextVar[ProviderCall] = ContextVar("backfire_provider_call")


def _value_at_path(value, path):
    if not path:
        return None
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


class ProfileProvider(AsyncOpenAIProvider):
    """One SDK attempt; the adapter owns prompting, decoding and retries."""

    def __init__(self, profile: dict, api_key: str):
        super().__init__(profile["model"], base_url=profile["base_url"], api_key=api_key)
        self.profile = profile

    async def request(self, messages, *, schema, structured):
        call = provider_call.get()
        remaining = call.deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise TimeoutError
        if self.api == "responses":
            kwargs = _responses_request_kwargs(self.model_name, messages, schema, structured=structured)
            create, read = self._client.responses.with_raw_response.create, _responses_result
        else:
            kwargs = {
                "model": self.model_name, "messages": render_messages(messages),
                "response_format": _response_format(schema, structured=structured),
            }
            create, read = self._client.chat.completions.with_raw_response.create, _result
        # extra_body also carries profile fields the SDK does not know yet.
        kwargs.update(extra_body=self.profile["request"], timeout=remaining)
        record_request(kwargs, api=self.api)
        call.metadata["attempts"] += 1
        call.model = call.usage = None
        call.metadata.update(thinking_evidence=None, reasoning_tokens=None)
        try:
            with translating(self.translate_error):
                raw = await create(**kwargs)
        except TypeSafeAPIError:
            call.metadata["thinking_evidence"] = False
            raise

        call.metadata["thinking_evidence"] = False
        # Check the JSON before SDK coercion (for example, true -> one token).
        try:
            response = raw.http_response.json()
        except ValueError:
            raise JudgmentError("provider_error") from None
        if not isinstance(response, dict):
            raise JudgmentError("provider_error")
        model = response.get("model")
        if isinstance(model, str) and model.strip():
            call.model = model
        usage = response.get("usage")
        input_key, output_key = (("input_tokens", "output_tokens") if self.api == "responses"
                                 else ("prompt_tokens", "completion_tokens"))
        counts = [_value_at_path(usage, key) for key in (input_key, output_key)]
        if all(type(count) is int and count >= 0 for count in counts):
            call.usage = dict(zip(("input_tokens", "output_tokens"), counts))

        if self.api == "responses":
            output = response.get("output")
            messages = [item for item in output
                        if isinstance(item, dict) and item.get("type") == "message"] if isinstance(output, list) else []
            message = messages[0] if messages else None
            refusal = any(isinstance(part, dict) and part.get("type") == "refusal"
                          for item in messages for part in (item.get("content") or []))
        else:
            choices = response.get("choices")
            choice = choices[0] if isinstance(choices, list) and choices else None
            message = choice.get("message") if isinstance(choice, dict) else None
            refusal = message.get("refusal") if isinstance(message, dict) else None

        thinking = self.profile["thinking"]
        reasoning = _value_at_path(message, thinking.get("content_path", ""))
        tokens = _value_at_path(usage, thinking.get("token_path", ""))
        if type(tokens) is int and tokens >= 0:
            call.metadata["reasoning_tokens"] = tokens
        evidence = ((isinstance(reasoning, str) and bool(reasoning.strip()))
                    or (type(tokens) is int and tokens > 0))
        call.metadata["thinking_evidence"] = evidence
        if self.api == "responses":
            if not isinstance(output, list):
                raise JudgmentError("provider_error")
        elif not isinstance(choices, list) or not choices:
            raise JudgmentError("provider_error")
        if (self.api != "responses" and not isinstance(message, dict)) or call.usage is None:
            raise JudgmentError("malformed_output")
        if refusal:
            raise JudgmentError("refused")
        maximum = self.profile["request"].get("max_tokens")
        if maximum is not None and call.usage["output_tokens"] >= maximum:
            raise JudgmentError("truncated_output")
        if call.model is None:
            raise JudgmentError("model_not_confirmed")
        if thinking["requested"] == "on" and not evidence:
            raise JudgmentError("thinking_not_confirmed")
        try:
            result = read(raw.parse())
        except TypeSafeError:
            # The pinned adapter owns the finish-reason/status acceptance rule.
            raise JudgmentError("truncated_output") from None
        except (AttributeError, IndexError, TypeError, ValueError):
            raise JudgmentError("malformed_output") from None
        if not isinstance(result.text, str) or not result.text.strip():
            raise JudgmentError("malformed_output")
        return result
