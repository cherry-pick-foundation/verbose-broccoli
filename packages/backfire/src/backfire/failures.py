"""Public judgment failures and the adapter's single SDK retry policy."""

from collections.abc import Mapping
from typing import Any

import httpx2
from typesafe_sdk import (
    RetryPolicy,
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeAPIResponseValidationError,
    TypeSafeAuthenticationError,
    TypeSafeBadRequestError,
    TypeSafeRateLimitError,
)

MESSAGES = {
    "invalid_request": "The questions do not match the request schema; correct the questions.",
    "request_limit_exceeded": "The request exceeds the option or answer-cell limit; split the request.",
    "backend_not_configured": "The configuration, profile or credential file is missing or invalid; correct the named configuration.",
    "pseudonym_conflict": "Two keys or labels become the same after pseudonymization; make them differ by more than a name.",
    "credential_rejected": "The provider rejected the credential; replace the selected profile's credential.",
    "balance_exhausted": "The provider balance is exhausted; restore the account balance.",
    "request_rejected": "The provider rejected the request; check the profile's model and request settings.",
    "rate_limited": "The provider rate limit prevented completion within the retry budget; wait before trying again.",
    "provider_unavailable": "The provider could not be reached or its response could not be read; check connectivity and provider availability.",
    "provider_error": "The provider returned an unexpected failure; check provider availability and the selected profile.",
    "truncated_output": "The provider did not complete its output; reduce the request size or review the profile's output limit.",
    "malformed_output": "The provider response is missing required data or has invalid answers; check the profile and model compatibility.",
    "refused": "The provider refused the judgment; review the request against the provider's usage rules.",
    "invalid_distribution": "The answer probabilities are all zero or do not sum to one; check the model's probability-output support.",
    "thinking_not_confirmed": "The response did not confirm requested thinking; check the profile's thinking settings and evidence paths.",
    "model_not_confirmed": "The response did not name its model; check that the provider reports the answering model.",
}


class JudgmentError(Exception):
    """Only fixed text and an optional safe configuration location may escape."""

    def __init__(self, error_type: str, detail: str | None = None) -> None:
        if detail is not None and error_type != "backend_not_configured":
            raise ValueError(
                "Only configuration failures may include a location."
            )
        self.error_type = error_type
        self.message = MESSAGES[error_type]
        self.detail = detail
        text = f"{error_type}: {self.message}"
        super().__init__(f"{text} ({detail})" if detail is not None else text)


def map_error(error: Exception, profile: Mapping[str, Any]) -> JudgmentError:
    """Discard SDK diagnostics; callers raise the returned error from None."""
    if isinstance(error, JudgmentError):
        return JudgmentError(error.error_type, error.detail)
    if isinstance(error, TypeSafeAPIResponseValidationError):
        return JudgmentError("malformed_output")
    if isinstance(error, TypeSafeAPIError) and 400 <= error.status <= 599:
        override = profile.get("statuses", {}).get(str(error.status))
        if override is not None:
            return JudgmentError(override)
    for error_class, error_type in (
        (TypeSafeAuthenticationError, "credential_rejected"),
        (TypeSafeBadRequestError, "request_rejected"),
        (TypeSafeRateLimitError, "rate_limited"),
        (TypeSafeAPIConnectionError, "provider_unavailable"),
        (ValueError, "invalid_request"),
    ):
        if isinstance(error, error_class):
            return JudgmentError(error_type)
    return JudgmentError("provider_error")


def _connect_failure(error: BaseException) -> bool:
    # The SDK's connection class also covers reads; only a known connect cause is safe.
    if not isinstance(error, TypeSafeAPIConnectionError):
        return False
    cause = error.__cause__
    while cause is not None:
        if isinstance(cause, httpx2.TransportError):
            return isinstance(
                cause, (httpx2.ConnectError, httpx2.ConnectTimeout)
            )
        cause = cause.__cause__
    return False


def retry_policy(
    profile: Mapping[str, Any], *, remaining_seconds: float
) -> RetryPolicy:
    """Use the caller's remaining budget; its outer deadline cancels in-flight work."""
    statuses = {429}
    for status, error_type in profile.get("statuses", {}).items():
        if not 400 <= int(status) <= 599:
            continue
        if error_type == "rate_limited":
            statuses.add(int(status))
        else:
            statuses.discard(int(status))
    return RetryPolicy(
        max_retries=3,
        backoff_initial=1.0,
        http_statuses=statuses,
        respect_retry_after=True,
        api_connection_error=False,
        api_timeout_error=False,
        predicate=_connect_failure,
        timeout=remaining_seconds,
    )
