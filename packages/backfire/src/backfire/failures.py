"""Public education and configuration failures."""

MESSAGES = {
    "backend_not_configured": (
        "The configuration, profile or credential file is missing or invalid; "
        "correct the named configuration."
    ),
    "pseudonym_conflict": (
        "Two keys or labels become the same after pseudonymization; "
        "make them differ by more than a name."
    ),
    "no_credit": "No profile in the order has credit.",
    "hangul_remaining": (
        "The request contains Hangul, so nothing was sent; translate it into "
        "English first."
    ),
    "identifier_remaining": (
        "An identifier survived replacement, so nothing was sent; report "
        "this to the operator."
    ),
}


class JudgmentError(Exception):
    """Carry the two safe failures shared by education and wiki consistency."""

    def __init__(self, error_type: str, detail: str | None = None) -> None:
        self.error_type = error_type
        self.message = MESSAGES[error_type]
        self.detail = detail
        text = f"{error_type}: {self.message}"
        super().__init__(f"{text} ({detail})" if detail is not None else text)
