"""Shared adapter helpers: defensive JSON readers, period ranges, and the
metadata cache (§9.5, §9.6, §13.4, §15.2)."""

from __future__ import annotations

from datetime import timedelta
from itertools import pairwise

import pytest

from frame_gallery.providers.cache import (
    COUNT_TTL,
    HINT_TTL,
    MemoryMetadataCache,
    MetadataCache,
)
from frame_gallery.providers.contract import SourceError, SourceErrorKind
from frame_gallery.providers.jsonread import (
    as_count,
    as_list,
    as_object,
    positive_int,
    text,
    year,
)
from frame_gallery.providers.periods import PERIOD_RANGES, YearRange, period_range
from frame_gallery.store.cache import ExhaustedPages
from tests.support.clock import FakeClock


class TestJsonReaders:
    def test_structure(self) -> None:
        assert as_object({"a": 1}, "x") == {"a": 1}
        assert as_list([1], "x") == [1]
        assert as_count(0, "x") == 0
        for call in (
            lambda: as_object([], "the thing"),
            lambda: as_list({}, "the thing"),
            lambda: as_count(-1, "the thing"),
            lambda: as_count(True, "the thing"),
            lambda: as_count(10**13, "the thing"),
            lambda: as_count("3", "the thing"),
        ):
            with pytest.raises(SourceError, match="the thing") as excinfo:
                call()
            assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (5, 5),
            ("3400", 3400),
            ("0", None),
            (0, None),
            (-3, None),
            (True, None),
            ("3.5", None),
            ("", None),
            ("\u0661\u0662", None),  # non-ASCII digits
            ("9" * 13, None),
            (2.0, None),
            (None, None),
            (101, None),
        ],
    )
    def test_positive_int(self, value: object, expected: int | None) -> None:
        assert positive_int(value, maximum=100 if value == 101 else 10**12) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (1880, 1880),
            (-500, -500),
            (0, 0),
            (True, None),
            ("1880", None),
            (1880.0, None),
            (20_000, None),
        ],
    )
    def test_year(self, value: object, expected: int | None) -> None:
        assert year(value) == expected

    def test_text(self) -> None:
        assert text("  a \t b\n c ") == "a b c"
        assert text("a\u0000b\u202ec\u2028d") == "a b c d"
        assert text("   ") is None
        assert text(5) is None
        assert text(None) is None
        assert text("y" * 1000) == "y" * 300
        assert text("z" * 50, max_length=10) == "z" * 10


class TestPeriods:
    def test_ranges_are_contiguous_and_cover_every_year(self) -> None:
        ranges = list(PERIOD_RANGES.values())
        assert ranges[0].first is None
        assert ranges[-1].last is None
        for before, after in pairwise(ranges):
            assert before.last is not None
            assert after.first == before.last + 1
        for value in (-3000, 0, 1399, 1400, 1599, 1600, 1799, 1800, 1899, 1900, 2026):
            assert sum(r.contains(value) for r in ranges) == 1

    def test_keys(self) -> None:
        assert list(PERIOD_RANGES) == [
            "period_before_1400",
            "period_1400_1599",
            "period_1600_1799",
            "period_1800_1899",
            "period_1900_and_later",
        ]
        assert period_range("period_1600_1799") == YearRange(1600, 1799)
        with pytest.raises(ValueError, match="unknown period"):
            period_range("period_1990s")

    def test_invalid_ranges(self) -> None:
        with pytest.raises(ValueError, match="at least one bound"):
            YearRange(None, None)
        with pytest.raises(ValueError, match="must not follow"):
            YearRange(1900, 1800)
        assert YearRange(1800, 1800).contains(1800)


class TestCache:
    def test_counts_expire(self) -> None:
        clock = FakeClock()
        cache: MetadataCache = MemoryMetadataCache(clock)
        assert cache.get_count("a") is None
        cache.put_count("a", 7, COUNT_TTL)
        assert cache.get_count("a") == 7
        clock.advance(COUNT_TTL.total_seconds() - 1)
        assert cache.get_count("a") == 7
        clock.advance(1)
        assert cache.get_count("a") is None
        assert cache.get_count("a") is None

    def test_the_cache_is_bounded(self) -> None:
        clock = FakeClock()
        cache = MemoryMetadataCache(clock, max_entries=2)
        for key, value in (("a", 1), ("b", 2), ("c", 3)):
            cache.put_count(key, value, timedelta(hours=1))
        assert cache.get_count("a") is None
        assert (cache.get_count("b"), cache.get_count("c")) == (2, 3)
        cache.put_count("b", 20, timedelta(hours=1))  # a refresh moves it to the end
        cache.put_count("d", 4, timedelta(hours=1))
        assert cache.get_count("c") is None
        assert (cache.get_count("b"), cache.get_count("d")) == (20, 4)

    def test_exhausted_pages_merge_for_the_same_total_and_keep_their_expiry(self) -> None:
        clock = FakeClock()
        cache: MetadataCache = MemoryMetadataCache(clock)
        assert cache.get_exhausted("h") is None
        cache.add_exhausted("h", 100, [], HINT_TTL)
        assert cache.get_exhausted("h") is None  # nothing to remember
        cache.add_exhausted("h", 100, [3], HINT_TTL)
        clock.advance(HINT_TTL.total_seconds() - 10)
        cache.add_exhausted("h", 100, [5], HINT_TTL)
        assert cache.get_exhausted("h") == ExhaustedPages(100, frozenset({3, 5}))
        clock.advance(10)
        assert cache.get_exhausted("h") is None  # the first expiry still applies

    def test_exhausted_pages_for_another_total_replace_the_old_ones(self) -> None:
        cache = MemoryMetadataCache(FakeClock())
        cache.add_exhausted("h", 100, [3], HINT_TTL)
        cache.add_exhausted("h", 101, [4], HINT_TTL)
        assert cache.get_exhausted("h") == ExhaustedPages(101, frozenset({4}))

    def test_a_count_is_not_a_hint_and_back(self) -> None:
        cache = MemoryMetadataCache(FakeClock())
        cache.put_count("c", 5, COUNT_TTL)
        cache.add_exhausted("h", 5, [1], HINT_TTL)
        assert cache.get_exhausted("c") is None
        assert cache.get_count("h") is None
