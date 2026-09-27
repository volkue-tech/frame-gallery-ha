"""The adapters' metadata cache port (§9.5, §9.6, §13.4).

Adapters cache small, non-personal metadata only: the number of results per
filter signature (1 day) and the pages known to offer nothing new (7 days).
The bounded, persistent implementation is ``store.cache.FileMetadataCache``
(``/data/cache/<provider>.json``); the in-memory one serves tests and a
single run.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from datetime import datetime, timedelta
from typing import Final, Protocol

from frame_gallery.budget.clock import Clock
from frame_gallery.providers.contract import Candidate
from frame_gallery.store.cache import ExhaustedPages, merge_exhausted

COUNT_TTL: Final = timedelta(days=1)
HINT_TTL: Final = timedelta(days=7)
MEMORY_MAX_ENTRIES: Final = 1000


def known_exhausted(hints: ExhaustedPages | None, total: int) -> frozenset[int]:
    """The pages hinted as exhausted for exactly this result count."""
    return hints.pages if hints is not None and hints.total == total else frozenset()


def offers_nothing_new(
    candidates: Sequence[Candidate], is_excluded_for_good: Callable[[str], bool]
) -> bool:
    """Whether a result page is exhausted: it offered at least one candidate,
    and every candidate it offered is excluded for good.

    A page that offered nothing (an empty or failed page, or one whose records
    the adapter could not use) is never exhausted, because the reason may be
    passing; neither is a page with a work that was not sent yet, even one
    without dimensions. Records that the adapter refuses for good (rights,
    identifiers, the period, the rendition) do not count either way."""
    return bool(candidates) and all(
        is_excluded_for_good(candidate.qualified_id) for candidate in candidates
    )


class MetadataCache(Protocol):
    def get_count(self, key: str) -> int | None:
        """A cached, unexpired count, or ``None``."""
        ...

    def put_count(self, key: str, count: int, ttl: timedelta) -> None: ...

    def get_exhausted(self, key: str) -> ExhaustedPages | None:
        """The pages known to offer nothing new, or ``None``."""
        ...

    def add_exhausted(self, key: str, total: int, pages: Collection[int], ttl: timedelta) -> None:
        """Add ``pages`` to the hints for ``total``; hints for another total
        are replaced. The entry keeps the expiry it was created with."""
        ...


class MemoryMetadataCache:
    """A bounded, per-process cache (the oldest entry goes first)."""

    def __init__(self, clock: Clock, max_entries: int = MEMORY_MAX_ENTRIES) -> None:
        self._clock = clock
        self._max_entries = max_entries
        self._entries: dict[str, tuple[int | ExhaustedPages, datetime]] = {}

    def get_count(self, key: str) -> int | None:
        value = self._get(key)
        return value if isinstance(value, int) else None

    def put_count(self, key: str, count: int, ttl: timedelta) -> None:
        self._put(key, count, self._clock.utc_now() + ttl)

    def get_exhausted(self, key: str) -> ExhaustedPages | None:
        value = self._get(key)
        return value if isinstance(value, ExhaustedPages) else None

    def add_exhausted(self, key: str, total: int, pages: Collection[int], ttl: timedelta) -> None:
        current = self.get_exhausted(key)
        if current is not None and current.total == total:
            expires = self._entries[key][1]
        else:
            current, expires = None, self._clock.utc_now() + ttl
        merged = merge_exhausted(current, total, pages)
        if merged.pages:
            self._put(key, merged, expires)

    def _get(self, key: str) -> int | ExhaustedPages | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        value, expires = entry
        if self._clock.utc_now() >= expires:
            del self._entries[key]
            return None
        return value

    def _put(self, key: str, value: int | ExhaustedPages, expires: datetime) -> None:
        self._entries.pop(key, None)
        while len(self._entries) >= self._max_entries:
            del self._entries[next(iter(self._entries))]
        self._entries[key] = (value, expires)
