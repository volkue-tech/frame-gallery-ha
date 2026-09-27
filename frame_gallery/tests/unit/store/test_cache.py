"""The bounded, persistent metadata cache (store/cache.py, §13.4, F6)."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.providers.cache import COUNT_TTL, HINT_TTL, MetadataCache
from frame_gallery.store import cache as cache_module
from frame_gallery.store.cache import (
    MAX_BYTES,
    MAX_ENTRIES,
    MAX_ENTRY_BYTES,
    MAX_PAGES,
    MAX_TTL,
    ExhaustedPages,
    FileMetadataCache,
    merge_exhausted,
)
from tests.support.clock import FakeClock

DAY = timedelta(days=1).total_seconds()


class Caches:
    """Successive runs over one data root, each with its own cache instance."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.clock = FakeClock()

    def open(self, provider: str = "aic") -> FileMetadataCache:
        return FileMetadataCache(self.root, provider, clock=self.clock)

    def deadline(self, seconds: float = 5) -> Deadline:
        return Deadline.after(self.clock, seconds, "finish")

    @property
    def file(self) -> Path:
        return self.root / "cache" / "aic.json"

    def document(self) -> dict[str, object]:
        loaded = json.loads(self.file.read_text())
        assert isinstance(loaded, dict)
        return loaded

    def keys(self) -> list[str]:
        entries = self.document()["entries"]
        assert isinstance(entries, list)
        return [entry["key"] for entry in entries]


@pytest.fixture
def caches(tmp_path: Path) -> Caches:
    return Caches(tmp_path)


def test_the_bounds_are_the_documented_ones() -> None:
    assert MAX_ENTRIES == 1000
    assert MAX_BYTES == 2 * 1024 * 1024
    assert MAX_ENTRY_BYTES == 8 * 1024
    assert timedelta(days=7) == MAX_TTL
    assert timedelta(days=1) == COUNT_TTL
    assert timedelta(days=7) == HINT_TTL


def test_the_file_cache_implements_the_port(caches: Caches) -> None:
    cache: MetadataCache = caches.open()
    assert cache.get_count("aic:count:any") is None


class TestPersistence:
    def test_counts_and_hints_survive_to_the_next_run(self, caches: Caches) -> None:
        first = caches.open()
        first.put_count("aic:count:any", 1234, COUNT_TTL)
        first.add_exhausted("aic:exhausted:any", 1234, [3, 1], HINT_TTL)
        first.flush(caches.deadline())
        assert caches.document()["provider"] == "aic"
        assert oct(caches.file.stat().st_mode & 0o777) == "0o600"
        second = caches.open()
        assert second.get_count("aic:count:any") == 1234
        assert second.get_exhausted("aic:exhausted:any") == ExhaustedPages(1234, frozenset({1, 3}))

    def test_nothing_is_written_without_a_change(self, caches: Caches) -> None:
        cache = caches.open()
        assert cache.get_count("aic:count:any") is None
        cache.flush(caches.deadline())
        assert not caches.file.exists()

    def test_at_most_one_write_per_run(self, caches: Caches) -> None:
        cache = caches.open()
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        cache.flush(caches.deadline())
        cache.put_count("aic:count:any", 2, COUNT_TTL)
        cache.flush(caches.deadline())
        assert caches.open().get_count("aic:count:any") == 1

    def test_no_write_when_no_time_is_left(
        self, caches: Caches, caplog: pytest.LogCaptureFixture
    ) -> None:
        cache = caches.open()
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        with caplog.at_level(logging.INFO, "frame_gallery.store"):
            cache.flush(caches.deadline(0))
        assert "no time left" in caplog.text
        assert not caches.file.exists()

    def test_a_write_failure_only_warns(
        self, caches: Caches, caplog: pytest.LogCaptureFixture
    ) -> None:
        (caches.root / "cache").write_text("not a directory")
        cache = caches.open()
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            cache.flush(caches.deadline())
        assert "the metadata cache was not written" in caplog.text

    def test_a_linked_cache_directory_is_never_used(self, caches: Caches, tmp_path: Path) -> None:
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (caches.root / "cache").symlink_to(elsewhere)
        cache = caches.open()
        assert cache.get_count("aic:count:any") is None
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        cache.flush(caches.deadline())
        assert list(elsewhere.iterdir()) == []


class TestAge:
    def test_entries_expire(self, caches: Caches) -> None:
        cache = caches.open()
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        caches.clock.advance(DAY - 1)
        assert cache.get_count("aic:count:any") == 1
        caches.clock.advance(1)
        assert cache.get_count("aic:count:any") is None

    def test_no_entry_lives_longer_than_seven_days(self, caches: Caches) -> None:
        cache = caches.open()
        cache.put_count("aic:count:any", 1, timedelta(days=30))
        caches.clock.advance(7 * DAY)
        assert cache.get_count("aic:count:any") is None

    def test_a_non_positive_lifetime_stores_nothing_usable(self, caches: Caches) -> None:
        cache = caches.open()
        cache.put_count("aic:count:any", 1, timedelta(seconds=-5))
        assert cache.get_count("aic:count:any") is None

    def test_expired_entries_are_dropped_when_read_and_rewritten(self, caches: Caches) -> None:
        first = caches.open()
        first.put_count("aic:count:any", 1, COUNT_TTL)
        first.put_count("aic:count:period_1800_1899", 2, timedelta(days=3))
        first.flush(caches.deadline())
        caches.clock.advance(2 * DAY)
        second = caches.open()
        assert second.get_count("aic:count:period_1800_1899") == 2
        second.flush(caches.deadline())
        assert caches.keys() == ["aic:count:period_1800_1899"]

    def test_expired_entries_alone_make_a_write(self, caches: Caches) -> None:
        first = caches.open()
        first.put_count("aic:count:any", 1, COUNT_TTL)
        first.flush(caches.deadline())
        caches.clock.advance(2 * DAY)
        second = caches.open()
        assert second.get_exhausted("aic:exhausted:any") is None
        second.flush(caches.deadline())
        assert caches.keys() == []

    def test_a_clock_that_went_back_never_stretches_an_entry(self, caches: Caches) -> None:
        """An expiry more than 7 days ahead is cut to 7 days from now."""
        first = caches.open()
        first.put_count("aic:count:any", 1, COUNT_TTL)
        first.flush(caches.deadline())
        document = caches.document()
        entries = document["entries"]
        assert isinstance(entries, list)
        entries[0]["expires"] = "2099-01-01T00:00:00+00:00"
        caches.file.write_text(json.dumps(document))
        second = caches.open()
        assert second.get_count("aic:count:any") == 1
        second.flush(caches.deadline())
        entries = caches.document()["entries"]
        assert isinstance(entries, list)
        assert entries[0]["expires"] == "2026-01-08T12:00:00+00:00"
        caches.clock.advance(7 * DAY)
        assert caches.open().get_count("aic:count:any") is None

    def test_a_small_step_back_keeps_a_full_length_hint(self, caches: Caches) -> None:
        first = caches.open()
        caches.clock.advance(60)
        first.add_exhausted("aic:exhausted:any", 10, [1], HINT_TTL)
        first.flush(caches.deadline())
        back = Caches(caches.root)  # a new process whose clock is a minute behind
        assert back.open().get_exhausted("aic:exhausted:any") == ExhaustedPages(10, frozenset({1}))

    def test_a_hint_keeps_its_first_expiry(self, caches: Caches) -> None:
        cache = caches.open()
        cache.add_exhausted("aic:exhausted:any", 100, [1], HINT_TTL)
        caches.clock.advance(6 * DAY)
        cache.add_exhausted("aic:exhausted:any", 100, [2], HINT_TTL)
        assert cache.get_exhausted("aic:exhausted:any") == ExhaustedPages(100, frozenset({1, 2}))
        caches.clock.advance(DAY)
        assert cache.get_exhausted("aic:exhausted:any") is None

    def test_hints_for_another_total_start_over(self, caches: Caches) -> None:
        cache = caches.open()
        cache.add_exhausted("aic:exhausted:any", 100, [1], HINT_TTL)
        caches.clock.advance(6 * DAY)
        cache.add_exhausted("aic:exhausted:any", 101, [2], HINT_TTL)
        caches.clock.advance(DAY)
        assert cache.get_exhausted("aic:exhausted:any") == ExhaustedPages(101, frozenset({2}))

    def test_no_pages_store_nothing(self, caches: Caches) -> None:
        cache = caches.open()
        cache.add_exhausted("aic:exhausted:any", 100, [], HINT_TTL)
        cache.flush(caches.deadline())
        assert not caches.file.exists()

    def test_a_count_key_is_not_a_hint(self, caches: Caches) -> None:
        cache = caches.open()
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        cache.add_exhausted("aic:count:any", 1, [1], HINT_TTL)  # replaces the count
        assert cache.get_count("aic:count:any") is None
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        assert cache.get_exhausted("aic:count:any") is None


class TestBounds:
    def test_merging_keeps_the_lowest_pages(self) -> None:
        merged = merge_exhausted(None, 10, range(MAX_PAGES + 50))
        assert merged.pages == frozenset(range(MAX_PAGES))
        assert merge_exhausted(ExhaustedPages(9, frozenset({1})), 10, [2]).pages == {2}

    def test_the_largest_hint_fits_its_entry_bound(self, caches: Caches) -> None:
        cache = caches.open()
        pages = range(10**6 - MAX_PAGES, 10**6)
        cache.add_exhausted("aic:exhausted:any", 10**8, pages, HINT_TTL)
        assert cache.get_exhausted("aic:exhausted:any") is not None

    def test_an_oversize_entry_is_not_kept(self, caches: Caches) -> None:
        cache = caches.open()
        cache.add_exhausted(
            "aic:exhausted:any", 10**12, range(10**12 - MAX_PAGES, 10**12), HINT_TTL
        )
        assert cache.get_exhausted("aic:exhausted:any") is None

    def test_the_least_recently_used_entries_go_first(
        self, caches: Caches, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cache_module, "MAX_ENTRIES", 3)
        cache = caches.open()
        for number in range(3):
            cache.put_count(f"aic:count:{number}", number, COUNT_TTL)
            caches.clock.advance(1)
        assert cache.get_count("aic:count:0") == 0  # now the most recently used
        caches.clock.advance(1)
        cache.put_count("aic:count:3", 3, COUNT_TTL)
        assert cache.get_count("aic:count:1") is None
        assert [cache.get_count(f"aic:count:{n}") for n in (0, 2, 3)] == [0, 2, 3]

    def test_the_file_bounds_hold_on_flush(
        self, caches: Caches, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cache = caches.open()
        for number in range(6):
            cache.put_count(f"aic:count:{number}", number, COUNT_TTL)
            caches.clock.advance(1)
        monkeypatch.setattr(cache_module, "MAX_ENTRIES", 4)
        entry_size = len('{"key":"aic:count:0","expires":"2026-01-02T12:00:00+00:00",') + len(
            '"used":"2026-01-01T12:00:00+00:00","count":0}'
        )
        empty = len('{"format":"frame-gallery-cache","version":1,"provider":"aic","entries":[]}')
        monkeypatch.setattr(cache_module, "MAX_BYTES", empty + 3 * entry_size + 2)
        cache.flush(caches.deadline())
        assert caches.keys() == ["aic:count:3", "aic:count:4", "aic:count:5"]
        assert len(caches.file.read_bytes()) <= empty + 3 * entry_size + 2

    @pytest.mark.parametrize(
        "key", ["cma:count:any", "aic", "aic:", "aic:bad key", "aic:" + "x" * 181]
    )
    def test_keys_must_belong_to_the_provider(self, caches: Caches, key: str) -> None:
        with pytest.raises(ValueError, match="invalid cache key"):
            caches.open().put_count(key, 1, COUNT_TTL)

    @pytest.mark.parametrize("value", [-1, True, 10**13])
    def test_numbers_are_bounded(self, caches: Caches, value: int) -> None:
        with pytest.raises(ValueError, match="invalid number"):
            caches.open().put_count("aic:count:any", value, COUNT_TTL)

    def test_the_provider_key_is_checked(self, caches: Caches) -> None:
        with pytest.raises(ValueError, match="invalid provider key"):
            FileMetadataCache(caches.root, "A", clock=caches.clock)


class TestDamage:
    def seed(self, caches: Caches, content: object) -> None:
        caches.file.parent.mkdir(parents=True, exist_ok=True)
        text = content if isinstance(content, str) else json.dumps(content)
        caches.file.write_text(text)

    def valid(self, **changes: object) -> dict[str, object]:
        entry: dict[str, object] = {
            "key": "aic:count:any",
            "expires": "2026-01-02T12:00:00+00:00",
            "used": "2026-01-01T12:00:00+00:00",
            "count": 5,
        }
        entry.update(changes)
        return {
            "format": "frame-gallery-cache",
            "version": 1,
            "provider": "aic",
            "entries": [entry],
        }

    def test_a_valid_file_is_read(self, caches: Caches) -> None:
        self.seed(caches, self.valid())
        assert caches.open().get_count("aic:count:any") == 5

    @pytest.mark.parametrize(
        "content",
        [
            "{not json",
            {"format": "frame-gallery-cache", "version": 1, "provider": "cma", "entries": []},
            {"format": "frame-gallery-cache", "version": 1, "provider": "aic", "entries": {}},
            {"format": "frame-gallery-cache", "version": 1, "provider": "aic", "entries": [1]},
            {"format": "frame-gallery-cache", "version": 9, "provider": "aic", "entries": []},
        ],
    )
    def test_a_damaged_or_foreign_file_is_discarded(
        self, caches: Caches, content: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        self.seed(caches, content)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            cache = caches.open()
            assert cache.get_count("aic:count:any") is None
        assert caplog.text != ""
        cache.put_count("aic:count:any", 1, COUNT_TTL)
        cache.flush(caches.deadline())
        assert caches.keys() == ["aic:count:any"]
        assert not (caches.root / "cache" / "quarantine").exists()

    @pytest.mark.parametrize(
        "changes",
        [
            {"key": "cma:count:any"},
            {"key": 5},
            {"count": -1},
            {"count": "5"},
            {"expires": "later"},
            {"count": None},
        ],
    )
    def test_an_invalid_entry_discards_the_file(
        self, caches: Caches, changes: dict[str, object]
    ) -> None:
        self.seed(caches, self.valid(**changes))
        assert caches.open().get_count("aic:count:any") is None

    @pytest.mark.parametrize(
        "hint",
        [
            {"total": 5, "pages": "1,2"},
            {"total": 5, "pages": list(range(MAX_PAGES + 1))},
            {"total": -5, "pages": [1]},
            {"pages": [1]},
            {"total": 5, "pages": [1.5]},
            {"total": 10**12, "pages": list(range(10**12 - MAX_PAGES, 10**12))},
        ],
    )
    def test_an_invalid_hint_discards_the_file(
        self, caches: Caches, hint: dict[str, object]
    ) -> None:
        document = self.valid()
        entries = document["entries"]
        assert isinstance(entries, list)
        del entries[0]["count"]
        entries[0].update(hint, key="aic:exhausted:any")
        self.seed(caches, document)
        assert caches.open().get_exhausted("aic:exhausted:any") is None

    def test_too_many_entries_discard_the_file(self, caches: Caches) -> None:
        document = self.valid()
        entries = document["entries"]
        assert isinstance(entries, list)
        document["entries"] = [dict(entries[0], key=f"aic:count:{n}") for n in range(1001)]
        self.seed(caches, document)
        assert caches.open().get_count("aic:count:1") is None
