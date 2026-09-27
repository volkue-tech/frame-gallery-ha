"""The confirmed sent history (§13.3).

``history.json`` lists the works whose selection the television confirmed,
oldest first::

    {"format": "frame-gallery-history", "version": 1,
     "entries": [{"id": "aic:…", "at": "2026-09-27T12:00:00+00:00"}]}

It holds at most 20 000 entries and 5 MiB; the oldest entries go first. It
changes only after ``selected`` (E10). A repeated identifier keeps its last
position. Unknown fields are ignored and are not written back.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from frame_gallery.store.atomic import DocumentSpec
from frame_gallery.store.fields import parse_qualified_id, parse_timestamp, timestamp_text

HISTORY_FILE: Final = "history.json"
HISTORY_FORMAT: Final = "frame-gallery-history"
HISTORY_VERSION: Final = 1
MAX_ENTRIES: Final = 20_000
MAX_BYTES: Final = 5 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    qualified_id: str
    at: datetime
    """When the television confirmed the selection."""


def parse_history(document: Mapping[str, object]) -> tuple[HistoryEntry, ...]:
    """The entries of a history document, oldest first. Raises ``ValueError``."""
    raw = document.get("entries")
    if not isinstance(raw, list):
        msg = "entries is not a list"
        raise ValueError(msg)
    if len(raw) > MAX_ENTRIES:
        msg = f"more than {MAX_ENTRIES} entries"
        raise ValueError(msg)
    entries: dict[str, HistoryEntry] = {}
    for item in raw:
        if not isinstance(item, dict):
            msg = "an entry is not an object"
            raise ValueError(msg)
        entry = HistoryEntry(parse_qualified_id(item.get("id")), parse_timestamp(item.get("at")))
        entries.pop(entry.qualified_id, None)
        entries[entry.qualified_id] = entry
    return tuple(entries.values())


HISTORY_SPEC: Final = DocumentSpec(HISTORY_FORMAT, HISTORY_VERSION, MAX_BYTES, parse_history)


def _entry_object(entry: HistoryEntry) -> dict[str, object]:
    return {"id": entry.qualified_id, "at": timestamp_text(entry.at)}


def history_document(entries: Sequence[HistoryEntry]) -> dict[str, object]:
    return {
        "format": HISTORY_FORMAT,
        "version": HISTORY_VERSION,
        "entries": [_entry_object(entry) for entry in entries],
    }


def _encoded_size(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=True, separators=(",", ":")))


def append_bounded(
    entries: Sequence[HistoryEntry],
    new: HistoryEntry,
    *,
    max_entries: int = MAX_ENTRIES,
    max_bytes: int = MAX_BYTES,
) -> tuple[HistoryEntry, ...]:
    """``entries`` with ``new`` appended (moved to the end if present), the
    oldest dropped until both bounds hold. ``new`` itself is always kept."""
    kept = [entry for entry in entries if entry.qualified_id != new.qualified_id]
    kept = [*kept[max(0, len(kept) - (max_entries - 1)) :], new]
    sizes = [_encoded_size(_entry_object(entry)) for entry in kept]
    # The empty document, then each entry and the comma before all but the first.
    total = _encoded_size(history_document(())) + sum(sizes) + len(kept) - 1
    start = 0
    while total > max_bytes and start < len(kept) - 1:
        total -= sizes[start] + 1
        start += 1
    return tuple(kept[start:])
