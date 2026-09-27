"""Defensive readers for untrusted provider JSON (§18.2, D-127).

A structural problem (a missing object, a list that is not a list, a total
that is not a count) is ``SourceError(UNEXPECTED_FORMAT)``: the provider's
response is not what its documentation describes. A bad *field* inside one
record is not an error; the readers return ``None`` and the adapter skips or
blanks that record.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Final, NoReturn

from frame_gallery.providers.contract import SourceError, SourceErrorKind

TEXT_MAX_LENGTH: Final = 300
"""Attribution text is cut to this many characters."""

_MAX_COUNT: Final = 10**12


def malformed(detail: str) -> NoReturn:
    raise SourceError(SourceErrorKind.UNEXPECTED_FORMAT, detail)


def as_object(value: object, what: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        malformed(f"{what} is not an object")
    return value


def as_list(value: object, what: str) -> Sequence[object]:
    if not isinstance(value, list):
        malformed(f"{what} is not a list")
    return value


def as_count(value: object, what: str) -> int:
    """A non-negative integer (not a boolean)."""
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= _MAX_COUNT:
        malformed(f"{what} is not a count")
    return value


def positive_int(value: object, maximum: int = _MAX_COUNT) -> int | None:
    """A positive integer, also from a string of digits (Cleveland's image
    sizes are strings), or ``None``."""
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value.isascii() and value.isdigit() and len(value) <= 12:
        value = int(value)
    if isinstance(value, int) and 0 < value <= maximum:
        return value
    return None


def year(value: object) -> int | None:
    """A year as an integer (negative for BCE), or ``None``."""
    if isinstance(value, bool) or not isinstance(value, int) or not -100_000 <= value <= 10_000:
        return None
    return value


def text(value: object, max_length: int = TEXT_MAX_LENGTH) -> str | None:
    """Display text: a non-blank string with control characters replaced by
    spaces and runs of whitespace collapsed, cut to ``max_length``; ``None``
    for anything else."""
    if not isinstance(value, str):
        return None
    cleaned = "".join(
        " " if unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp") else char
        for char in value[: max_length * 4]
    )
    collapsed = " ".join(cleaned.split())
    return collapsed[:max_length] or None
