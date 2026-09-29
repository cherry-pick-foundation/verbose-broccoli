"""JSON text shared by the ported tools; see ../UPSTREAM.md."""

import json
import math

import rfc8785


def text(payload) -> str:
    """Match JSON.stringify(payload, null, 2), including ECMAScript numbers."""

    def encode(value, depth=0):
        if isinstance(value, dict):
            # ECMAScript enumerates array-index keys before other string keys.
            keys = sorted(
                value,
                key=lambda key: (
                    int(key)
                    if len(key) <= 10
                    and key.isascii()
                    and key.isdecimal()
                    and str(int(key)) == key
                    and int(key) < 2**32 - 1
                    else math.inf
                ),
            )
            parts = [
                f"{encode(key)}: {encode(value[key], depth + 1)}"
                for key in keys
            ]
            opening, closing = "{", "}"
        elif isinstance(value, list):
            parts = [encode(item, depth + 1) for item in value]
            opening, closing = "[", "]"
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            return (
                rfc8785.dumps(float(value)).decode()
                if math.isfinite(value)
                else "null"
            )
        else:
            return (
                json.dumps(value, ensure_ascii=False)
                .encode("utf-8", "backslashreplace")
                .decode()
            )
        if not parts:
            return opening + closing
        indent = "  " * (depth + 1)
        return (
            opening
            + "\n"
            + indent
            + (",\n" + indent).join(parts)
            + "\n"
            + "  " * depth
            + closing
        )

    return encode(payload)
