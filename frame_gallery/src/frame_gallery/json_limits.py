"""Platform-independent nesting bound before decoding size-capped JSON bytes."""

from __future__ import annotations

from typing import Final

MAX_JSON_NESTING_DEPTH: Final = 32


def check_json_nesting(data: bytes) -> None:
    """Bound containers outside strings; syntax remains the JSON parser's job.

    Byte scanning avoids constructing an excessive tree and does not depend on
    the interpreter's recursion limit. Callers enforce their own byte caps first.
    Escaped quotes/backslashes and braces inside UTF-8 strings are not containers.
    """
    depth = 0
    quoted = False
    escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > MAX_JSON_NESTING_DEPTH:
                raise ValueError("nested too deeply")
        elif byte in (93, 125):
            depth -= 1
