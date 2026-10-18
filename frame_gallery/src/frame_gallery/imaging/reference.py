"""Small fixed pixel reference; no decoder, file or network access."""

import base64
from typing import Final

REFERENCE_BYTES: Final = 64 * 36 * 3


def valid_reference(value: object) -> bool:
    if not isinstance(value, str) or len(value) != REFERENCE_BYTES * 4 // 3:
        return False
    try:
        return len(base64.b64decode(value, validate=True)) == REFERENCE_BYTES
    except ValueError:
        return False
