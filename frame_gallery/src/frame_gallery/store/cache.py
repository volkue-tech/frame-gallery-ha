"""The bounded metadata cache (§13.4).

One JSON file per provider, ``/data/cache/<provider>.json``::

    {"format": "frame-gallery-cache", "version": 1, "provider": "aic",
     "entries": [
       {"key": "aic:count:any", "expires": "…", "used": "…", "count": 123},
       {"key": "aic:exhausted:any", "expires": "…", "used": "…",
        "total": 123, "pages": [3, 17]}]}

- It holds result counts per filter signature and exhausted-page hints:
  identifiers and numbers only, never images and never whole pages.
- At most 1 000 entries and 2 MiB. An entry is at most 8 KiB and lives at
  most 7 days. Expired entries go first, then the least recently used.
- It is read once, lazily, and written at most once per run (:meth:`flush`).
  Damage of any kind means the file is discarded; it is never quarantined,
  and a later write replaces it.
- A hint entry keeps the expiry it was created with when pages are added,
  so no hint is ever older than its time to live.
- An entry read with an expiry more than 7 days ahead (the clock went back)
  is cut to 7 days from now, so it never lives longer than that.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import StateError
from frame_gallery.store.atomic import (
    DocumentFile,
    DocumentSpec,
    open_directory,
    read_document,
)
from frame_gallery.store.fields import parse_timestamp, timestamp_text

CACHE_DIRECTORY: Final = "cache"
CACHE_FORMAT: Final = "frame-gallery-cache"
CACHE_VERSION: Final = 1
MAX_ENTRIES: Final = 1000
MAX_BYTES: Final = 2 * 1024 * 1024
MAX_ENTRY_BYTES: Final = 8 * 1024
MAX_TTL: Final = timedelta(days=7)
MAX_PAGES: Final = 800
"""Pages per hint entry; 800 page numbers below 10**6 fit an 8 KiB entry."""

MAX_NUMBER: Final = 10**12
KEY: Final = re.compile(r"([a-z]{2,16}):[A-Za-z0-9_.:-]{1,180}")

_log = logging.getLogger("frame_gallery.store")


@dataclass(frozen=True, slots=True)
class ExhaustedPages:
    """Pages known to offer nothing new, for one result count."""

    total: int
    """The result count the page numbers refer to. Hints for another count
    are stale: the pages may have shifted."""

    pages: frozenset[int]


def merge_exhausted(
    existing: ExhaustedPages | None, total: int, pages: Collection[int]
) -> ExhaustedPages:
    """``pages`` added to ``existing`` if it is for the same ``total``, else
    replacing it; at most :data:`MAX_PAGES` page numbers, the lowest kept."""
    known = existing.pages if existing is not None and existing.total == total else frozenset()
    merged = sorted(known | frozenset(pages))[:MAX_PAGES]
    return ExhaustedPages(total, frozenset(merged))


type _Value = int | ExhaustedPages


@dataclass(slots=True)
class _Entry:
    key: str
    value: _Value
    expires: datetime
    used: datetime

    def to_object(self) -> dict[str, object]:
        record: dict[str, object] = {
            "key": self.key,
            "expires": timestamp_text(self.expires),
            "used": timestamp_text(self.used),
        }
        if isinstance(self.value, ExhaustedPages):
            record["total"] = self.value.total
            record["pages"] = sorted(self.value.pages)
        else:
            record["count"] = self.value
        return record

    def size(self) -> int:
        return len(json.dumps(self.to_object(), ensure_ascii=True, separators=(",", ":")))


def _number(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_NUMBER:
        msg = "invalid number"
        raise ValueError(msg)
    return value


def _parse_entry(item: object, provider: str) -> _Entry:
    if not isinstance(item, dict):
        msg = "an entry is not an object"
        raise ValueError(msg)
    key = item.get("key")
    if not isinstance(key, str) or not _key_belongs(key, provider):
        msg = "invalid key"
        raise ValueError(msg)
    value: _Value
    if "count" in item:
        value = _number(item["count"])
    else:
        pages = item.get("pages")
        if not isinstance(pages, list) or len(pages) > MAX_PAGES:
            msg = "invalid pages"
            raise ValueError(msg)
        value = ExhaustedPages(_number(item.get("total")), frozenset(_number(p) for p in pages))
    entry = _Entry(
        key, value, parse_timestamp(item.get("expires")), parse_timestamp(item.get("used"))
    )
    if entry.size() > MAX_ENTRY_BYTES:
        msg = "an entry exceeds its size bound"
        raise ValueError(msg)
    return entry


def _key_belongs(key: str, provider: str) -> bool:
    match = KEY.fullmatch(key)
    return match is not None and match.group(1) == provider


def _spec(provider: str) -> DocumentSpec[dict[str, _Entry]]:
    def parse(document: Mapping[str, object]) -> dict[str, _Entry]:
        if document.get("provider") != provider:
            msg = "the cache belongs to another provider"
            raise ValueError(msg)
        raw = document.get("entries")
        if not isinstance(raw, list) or len(raw) > MAX_ENTRIES:
            msg = "invalid entries"
            raise ValueError(msg)
        entries = [_parse_entry(item, provider) for item in raw]
        return {entry.key: entry for entry in entries}

    return DocumentSpec(CACHE_FORMAT, CACHE_VERSION, MAX_BYTES, parse)


class FileMetadataCache:
    """The ``MetadataCache`` port over ``<data>/cache/<provider>.json``.

    One instance serves one run. Nothing it does raises for a damaged or
    unwritable cache: the adapters then simply ask the API again.
    """

    def __init__(self, data_root: Path, provider: str, *, clock: Clock) -> None:
        if KEY.fullmatch(f"{provider}:x") is None:
            msg = f"invalid provider key {provider!r}"
            raise ValueError(msg)
        self._data_root = data_root
        self._provider = provider
        self._name = f"{provider}.json"
        self._spec = _spec(provider)
        self._clock = clock
        self._entries: dict[str, _Entry] | None = None
        self._dirty = False
        self._flushed = False

    # --------------------------------------------------------------- the port

    def get_count(self, key: str) -> int | None:
        entry = self._live(key)
        if entry is None or not isinstance(entry.value, int):
            return None
        return entry.value

    def put_count(self, key: str, count: int, ttl: timedelta) -> None:
        now = self._clock.utc_now()
        self._put(_Entry(key, _number(count), now + _clamp(ttl), now))

    def get_exhausted(self, key: str) -> ExhaustedPages | None:
        entry = self._live(key)
        if entry is None or not isinstance(entry.value, ExhaustedPages):
            return None
        return entry.value

    def add_exhausted(self, key: str, total: int, pages: Collection[int], ttl: timedelta) -> None:
        """Remember ``pages`` as exhausted for ``total``. Hints for another
        total are replaced; the entry keeps its first expiry."""
        now = self._clock.utc_now()
        entry = self._live(key)
        current: ExhaustedPages | None = None
        expires = now + _clamp(ttl)
        if (
            entry is not None
            and isinstance(entry.value, ExhaustedPages)
            and entry.value.total == total
        ):
            current, expires = entry.value, entry.expires
        merged = merge_exhausted(current, _number(total), [_number(page) for page in pages])
        if merged.pages:
            self._put(_Entry(key, merged, expires, now))

    # ------------------------------------------------------------------ flush

    def flush(self, deadline: Deadline) -> None:
        """Write this run's changes, at most once per run. Never raises."""
        if self._flushed or not self._dirty or self._entries is None:
            return
        self._flushed = True
        if deadline.expired():
            _log.info("the metadata cache was not written: no time left")
            return
        entries = _bounded(self._entries, self._provider, self._clock.utc_now())
        document = _document(self._provider, entries)
        try:
            with open_directory(
                self._data_root, (CACHE_DIRECTORY,), create=True, mode=0o700
            ) as directory:
                DocumentFile(directory, self._name, self._spec).write(document)
        except StateError as exc:
            _log.warning("the metadata cache was not written: %s", exc)

    # -------------------------------------------------------------- internals

    def _loaded(self) -> dict[str, _Entry]:
        if self._entries is None:
            self._entries = self._read()
        return self._entries

    def _read(self) -> dict[str, _Entry]:
        try:
            directory = open_directory(self._data_root, (CACHE_DIRECTORY,))
        except StateError as exc:
            _log.debug("no metadata cache: %s", exc)
            return {}
        with directory:
            result = read_document(directory, self._name, self._spec, backup=False, quarantine=None)
        if not result.usable:
            _log.warning("%s/%s is not usable and is discarded", directory.label, self._name)
        now = self._clock.utc_now()
        entries = dict(result.value or {})
        stale = [key for key, entry in entries.items() if not _fresh(entry, now)]
        for key in stale:
            del entries[key]
        stretched = [entry for entry in entries.values() if entry.expires > now + MAX_TTL]
        for entry in stretched:
            # A clock that went back never stretches an entry's life.
            entry.expires = now + MAX_TTL
        self._dirty = bool(stale or stretched)
        return entries

    def _live(self, key: str) -> _Entry | None:
        entries = self._loaded()
        entry = entries.get(key)
        if entry is None:
            return None
        now = self._clock.utc_now()
        if not _fresh(entry, now):
            del entries[key]
            self._dirty = True
            return None
        entry.used = now
        self._dirty = True
        return entry

    def _put(self, entry: _Entry) -> None:
        if not _key_belongs(entry.key, self._provider):
            msg = f"invalid cache key {entry.key!r}"
            raise ValueError(msg)
        if entry.size() > MAX_ENTRY_BYTES:
            _log.debug("cache entry %s exceeds its size bound and is not kept", entry.key)
            return
        entries = self._loaded()
        entries.pop(entry.key, None)
        if len(entries) >= MAX_ENTRIES:
            now = self._clock.utc_now()
            for key in [key for key, other in entries.items() if not _fresh(other, now)]:
                del entries[key]  # expired entries go first
        while len(entries) >= MAX_ENTRIES:
            del entries[_least_recently_used(entries.values())]
        entries[entry.key] = entry
        self._dirty = True


def _clamp(ttl: timedelta) -> timedelta:
    return min(ttl, MAX_TTL) if ttl > timedelta(0) else timedelta(0)


def _fresh(entry: _Entry, now: datetime) -> bool:
    return now < entry.expires


def _least_recently_used(entries: Collection[_Entry]) -> str:
    return min(entries, key=lambda entry: (entry.used, entry.key)).key


def _document(provider: str, entries: Collection[_Entry]) -> dict[str, object]:
    return {
        "format": CACHE_FORMAT,
        "version": CACHE_VERSION,
        "provider": provider,
        "entries": [entry.to_object() for entry in entries],
    }


def _bounded(entries: Mapping[str, _Entry], provider: str, now: datetime) -> list[_Entry]:
    """Fresh entries within both bounds, the least recently used dropped first."""
    kept = sorted(
        (entry for entry in entries.values() if _fresh(entry, now)),
        key=lambda entry: (entry.used, entry.key),
    )
    kept = kept[max(0, len(kept) - MAX_ENTRIES) :]
    sizes = [entry.size() for entry in kept]
    # The empty document, then each entry and the comma before all but the first.
    total = len(json.dumps(_document(provider, ()), separators=(",", ":")))
    total += sum(sizes) + max(0, len(kept) - 1)
    start = 0
    while total > MAX_BYTES and start < len(kept):
        total -= sizes[start] + 1
        start += 1
    return kept[start:]
