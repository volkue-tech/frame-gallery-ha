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
EARLIEST: Final = datetime(2000, 1, 1, tzinfo=UTC)
LATEST: Final = datetime(9000, 1, 1, tzinfo=UTC)


def timestamp_text(moment: datetime) -> str:
    """``moment`` in UTC, whole seconds. Raises ``ValueError`` for a naive time."""
    if moment.tzinfo is None:
        msg = "a timestamp must be timezone-aware"
        raise ValueError(msg)
    return moment.astimezone(UTC).isoformat(timespec="seconds")


def parse_timestamp(value: object) -> datetime:
    """A timezone-aware timestamp from 2000 to 8999, in UTC. Raises ``ValueError``.

    The range keeps every later calculation (a quarantine period or a time to
    live added to it) far from the limits of ``datetime``."""
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
    try:
        moment = moment.astimezone(UTC)
    except OverflowError:
        moment = LATEST  # beyond the limits of datetime: out of range as well
    if not EARLIEST <= moment < LATEST:
        msg = "a timestamp out of range"
        raise ValueError(msg)
    return moment


def parse_qualified_id(value: object) -> str:
    """A persistent identifier. Raises ``ValueError``."""
    if not isinstance(value, str) or not is_qualified_id(value):
        msg = "invalid identifier"
        raise ValueError(msg)
    return value
