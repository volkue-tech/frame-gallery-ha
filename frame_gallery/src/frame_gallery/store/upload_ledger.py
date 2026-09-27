"""The TV-upload exclusion ledger (§13.6, D-137).

``upload_ledger.json`` records works that may already be on the television
although history does not hold them::

    {"format": "frame-gallery-upload-ledger", "version": 1,
     "entries": [{"id": "cma:…", "state": "uploaded" | "uncertain", "at": "…"}]}

- ``uncertain`` is the write-ahead intent committed at PRE-STAGE. It excludes
  the work for the 30-day quarantine period after ``at`` (Q-23), unless the
  run removes it because no ``upload_started`` marker was seen or the upload
  was explicitly refused.
- ``uploaded`` is written when the ``uploaded`` marker arrives. It excludes
  the work until the work reaches history; the entry is then pruned on the
  next ledger write.

The ledger holds at most 20 000 entries and 5 MiB. The oldest ``uploaded``
entries are dropped first, then the oldest ``uncertain`` ones; the entry
being written is always kept. An ``uploaded`` entry is never turned back into
an ``uncertain`` one.
"""

from __future__ import annotations

import enum
import json
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Final

from frame_gallery.store.atomic import DocumentSpec
from frame_gallery.store.fields import parse_qualified_id, parse_timestamp, timestamp_text

LEDGER_FILE: Final = "upload_ledger.json"
LEDGER_FORMAT: Final = "frame-gallery-upload-ledger"
LEDGER_VERSION: Final = 1
MAX_ENTRIES: Final = 20_000
MAX_BYTES: Final = 5 * 1024 * 1024
QUARANTINE_PERIOD: Final = timedelta(days=30)
"""The uncertainty quarantine (Q-23, accepted)."""


class LedgerState(enum.StrEnum):
    UPLOADED = "uploaded"
    UNCERTAIN = "uncertain"


_STATES: Final = frozenset(state.value for state in LedgerState)


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    qualified_id: str
    state: LedgerState
    at: datetime
    """When the intent was committed (``uncertain``) or promoted (``uploaded``)."""

    def excludes(self, now: datetime, period: timedelta = QUARANTINE_PERIOD) -> bool:
        """``uploaded`` always excludes; ``uncertain`` until its quarantine ends."""
        return self.state is LedgerState.UPLOADED or now < self.at + period

    def strength(self) -> tuple[bool, datetime]:
        """``uploaded`` beats ``uncertain``; then the later entry wins."""
        return (self.state is LedgerState.UPLOADED, self.at)


def parse_ledger(document: Mapping[str, object]) -> tuple[LedgerEntry, ...]:
    """The entries of a ledger document. Raises ``ValueError``.

    A repeated identifier keeps its strongest entry (``uploaded`` over
    ``uncertain``, then the later time) at its last position.
    """
    raw = document.get("entries")
    if not isinstance(raw, list):
        msg = "entries is not a list"
        raise ValueError(msg)
    if len(raw) > MAX_ENTRIES:
        msg = f"more than {MAX_ENTRIES} entries"
        raise ValueError(msg)
    entries: dict[str, LedgerEntry] = {}
    for item in raw:
        if not isinstance(item, dict):
            msg = "an entry is not an object"
            raise ValueError(msg)
        state = item.get("state")
        if not isinstance(state, str) or state not in _STATES:
            msg = "invalid state"
            raise ValueError(msg)
        entry = LedgerEntry(
            parse_qualified_id(item.get("id")), LedgerState(state), parse_timestamp(item.get("at"))
        )
        previous = entries.pop(entry.qualified_id, None)
        if previous is not None and previous.strength() > entry.strength():
            entry = previous
        entries[entry.qualified_id] = entry
    return tuple(entries.values())


LEDGER_SPEC: Final = DocumentSpec(LEDGER_FORMAT, LEDGER_VERSION, MAX_BYTES, parse_ledger)


def _entry_object(entry: LedgerEntry) -> dict[str, object]:
    return {"id": entry.qualified_id, "state": entry.state.value, "at": timestamp_text(entry.at)}


def ledger_document(entries: Sequence[LedgerEntry]) -> dict[str, object]:
    return {
        "format": LEDGER_FORMAT,
        "version": LEDGER_VERSION,
        "entries": [_entry_object(entry) for entry in entries],
    }


# --- transitions -----------------------------------------------------------------


def excluded_ids(
    entries: Sequence[LedgerEntry], now: datetime
) -> tuple[frozenset[str], frozenset[str]]:
    """The ``uploaded`` identifiers and the unexpired ``uncertain`` ones."""
    uploaded = frozenset(e.qualified_id for e in entries if e.state is LedgerState.UPLOADED)
    uncertain = frozenset(
        e.qualified_id for e in entries if e.state is LedgerState.UNCERTAIN and e.excludes(now)
    )
    return uploaded, uncertain


def pruned(
    entries: Sequence[LedgerEntry], *, history: Collection[str], now: datetime
) -> tuple[LedgerEntry, ...]:
    """Without works that reached history and without expired intents."""
    return tuple(e for e in entries if e.qualified_id not in history and e.excludes(now))


def with_intent(
    entries: Sequence[LedgerEntry], qualified_id: str, now: datetime
) -> tuple[LedgerEntry, ...]:
    """An ``uncertain`` intent for ``qualified_id`` at the end; an existing
    ``uploaded`` entry is kept as it is."""
    for entry in entries:
        if entry.qualified_id == qualified_id and entry.state is LedgerState.UPLOADED:
            return tuple(entries)
    others = [e for e in entries if e.qualified_id != qualified_id]
    return (*others, LedgerEntry(qualified_id, LedgerState.UNCERTAIN, now))


def promoted(
    entries: Sequence[LedgerEntry], qualified_id: str, now: datetime
) -> tuple[LedgerEntry, ...]:
    """``qualified_id`` as ``uploaded`` at the end, whatever it was before."""
    others = [e for e in entries if e.qualified_id != qualified_id]
    return (*others, LedgerEntry(qualified_id, LedgerState.UPLOADED, now))


def without_intent(entries: Sequence[LedgerEntry], qualified_id: str) -> tuple[LedgerEntry, ...]:
    """Without the ``uncertain`` intent for ``qualified_id``; never removes an
    ``uploaded`` entry."""
    return tuple(
        e
        for e in entries
        if not (e.qualified_id == qualified_id and e.state is LedgerState.UNCERTAIN)
    )


def _encoded_size(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=True, separators=(",", ":")))


def bounded(
    entries: Sequence[LedgerEntry],
    *,
    keep: str,
    max_entries: int = MAX_ENTRIES,
    max_bytes: int = MAX_BYTES,
) -> tuple[LedgerEntry, ...]:
    """``entries`` within both bounds: the oldest ``uploaded`` entries go
    first, then the oldest ``uncertain`` ones. ``keep`` is never dropped."""
    sizes = {e.qualified_id: _encoded_size(_entry_object(e)) for e in entries}
    count = len(entries)
    # The empty document, then each entry and the comma before all but the first.
    total = _encoded_size(ledger_document(())) + sum(sizes.values()) + max(0, count - 1)
    victims = sorted(
        (e for e in entries if e.qualified_id != keep),
        key=lambda e: (e.state is LedgerState.UNCERTAIN, e.at),
    )
    dropped: set[str] = set()
    for victim in victims:
        if count <= max_entries and total <= max_bytes:
            break
        dropped.add(victim.qualified_id)
        count -= 1
        total -= sizes[victim.qualified_id] + 1
    return tuple(e for e in entries if e.qualified_id not in dropped)
