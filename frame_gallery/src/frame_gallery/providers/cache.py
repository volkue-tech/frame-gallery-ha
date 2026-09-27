"""The adapters' metadata cache port (§9.5, §9.6, §13.4).

Adapters cache small, non-personal metadata only: the number of results per
filter signature (1 day). The bounded, persistent cache in
``/data/cache/<provider>.json`` arrives in Phase 4 (§13.4); until then the
in-memory implementation serves one run.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final, Protocol

from frame_gallery.budget.clock import Clock

COUNT_TTL: Final = timedelta(days=1)
MEMORY_MAX_ENTRIES: Final = 1000


class MetadataCache(Protocol):
    def get_count(self, key: str) -> int | None:
        """A cached, unexpired count, or ``None``."""
        ...

    def put_count(self, key: str, count: int, ttl: timedelta) -> None: ...


class MemoryMetadataCache:
    """A bounded, per-process cache (the oldest entry goes first)."""

    def __init__(self, clock: Clock, max_entries: int = MEMORY_MAX_ENTRIES) -> None:
        self._clock = clock
        self._max_entries = max_entries
        self._counts: dict[str, tuple[int, datetime]] = {}

    def get_count(self, key: str) -> int | None:
        entry = self._counts.get(key)
        if entry is None:
            return None
        count, expires = entry
        if self._clock.utc_now() >= expires:
            del self._counts[key]
            return None
        return count

    def put_count(self, key: str, count: int, ttl: timedelta) -> None:
        self._counts.pop(key, None)
        while len(self._counts) >= self._max_entries:
            del self._counts[next(iter(self._counts))]
        self._counts[key] = (count, self._clock.utc_now() + ttl)
