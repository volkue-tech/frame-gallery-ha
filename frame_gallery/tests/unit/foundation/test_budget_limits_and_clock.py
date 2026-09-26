"""Allowance and per-request limits (§7.2, D-114), and the system clock (§7.1)."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import pytest

from frame_gallery.budget import limits
from frame_gallery.budget.clock import Clock, SystemClock


class TestLimits:
    def test_count_allowances_match_the_table(self) -> None:
        assert limits.SHORTLIST_SIZE == 2
        assert limits.CANDIDATE_ALLOWANCE == 150
        assert limits.METADATA_REQUEST_ALLOWANCE == 15
        assert limits.REMOTE_PROBE_ALLOWANCE == 30
        assert limits.LOCAL_DIRECTORY_ENTRY_ALLOWANCE == 20_000
        assert limits.LOCAL_DIRECTORY_DEPTH == 4
        assert limits.LOCAL_INSPECTION_ALLOWANCE == 300

    def test_per_request_times_match_the_table(self) -> None:
        assert limits.METADATA_REQUEST_S == 10.0
        assert limits.PROBE_REQUEST_S == 5.0
        assert limits.DOWNLOAD_REQUEST_S == 20.0
        assert limits.HELPER_REQUEST_S == 3.0
        assert limits.CONNECT_S == 5.0
        assert limits.READ_S == 10.0
        assert limits.DNS_S == 3.0

    def test_count_allowances_are_non_negative_integers(self) -> None:
        for value in (
            limits.SHORTLIST_SIZE,
            limits.CANDIDATE_ALLOWANCE,
            limits.METADATA_REQUEST_ALLOWANCE,
            limits.REMOTE_PROBE_ALLOWANCE,
            limits.LOCAL_DIRECTORY_ENTRY_ALLOWANCE,
            limits.LOCAL_DIRECTORY_DEPTH,
            limits.LOCAL_INSPECTION_ALLOWANCE,
        ):
            assert type(value) is int
            assert value >= 0


class TestSystemClock:
    def test_satisfies_the_clock_protocol(self) -> None:
        clock: Clock = SystemClock()
        assert isinstance(clock.monotonic(), float)

    def test_monotonic_never_goes_backwards(self) -> None:
        clock = SystemClock()
        before = time.monotonic()
        readings = [clock.monotonic() for _ in range(100)]
        after = time.monotonic()
        assert readings == sorted(readings)
        assert before <= readings[0]
        assert readings[-1] <= after

    def test_utc_now_is_timezone_aware_utc(self) -> None:
        clock = SystemClock()
        before = datetime.now(UTC)
        now = clock.utc_now()
        after = datetime.now(UTC)
        assert now.tzinfo is UTC
        assert now.utcoffset() == timedelta(0)
        assert before <= now <= after

    @pytest.mark.parametrize("seconds", [0.0, -1.0, -0.001])
    def test_sleep_without_positive_time_returns_immediately(
        self, seconds: float, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls: list[float] = []
        monkeypatch.setattr(time, "sleep", calls.append)
        SystemClock().sleep(seconds)
        assert calls == []

    def test_sleep_with_positive_time_delegates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The real sleep is replaced: the test never waits.
        calls: list[float] = []
        monkeypatch.setattr(time, "sleep", calls.append)
        SystemClock().sleep(1.25)
        assert calls == [1.25]
