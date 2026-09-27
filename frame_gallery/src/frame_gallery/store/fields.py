"""Field rules shared by the state documents (§13.3, §13.6).

Timestamps are timezone-aware ISO 8601 text in UTC with whole seconds, for
example ``2026-09-27T12:00:00+00:00``. Identifiers are the persistent
``<provider key>:<native id>`` form.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from frame_gallery.domain import is_qualified_id

MAX_TIMESTAMP_LENGTH: Final = 40


def timestamp_text(moment: datetime) -> str:
    """``moment`` in UTC, whole seconds. Raises ``ValueError`` for a naive time."""
    if moment.tzinfo is None:
        msg = "a timestamp must be timezone-aware"
        raise ValueError(msg)
    return moment.astimezone(UTC).isoformat(timespec="seconds")


def parse_timestamp(value: object) -> datetime:
    """A timezone-aware timestamp, in UTC. Raises ``ValueError``."""
    if not isinstance(value, str) or len(value) > MAX_TIMESTAMP_LENGTH:
        msg = "invalid timestamp"
        raise ValueError(msg)
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        msg = "invalid timestamp"
        raise ValueError(msg) from None
    if moment.tzinfo is None:
        msg = "a timestamp without a time zone"
        raise ValueError(msg)
    return moment.astimezone(UTC)


def parse_qualified_id(value: object) -> str:
    """A persistent identifier. Raises ``ValueError``."""
    if not isinstance(value, str) or not is_qualified_id(value):
        msg = "invalid identifier"
        raise ValueError(msg)
    return value
