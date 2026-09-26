"""A fake clock: time moves only when a test (or a fake) advances it."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

FAKE_EPOCH = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class FakeClock:
    """Implements ``frame_gallery.budget.clock.Clock`` without real waiting."""

    def __init__(self, start: float = 1000.0, wall_start: datetime = FAKE_EPOCH) -> None:
        self._start = start
        self._now = start
        self._wall_start = wall_start
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self._now

    def utc_now(self) -> datetime:
        return self._wall_start + timedelta(seconds=self._now - self._start)

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.advance(max(0.0, seconds))

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            msg = "a fake clock never goes backwards"
            raise ValueError(msg)
        self._now += seconds

    def advance_to(self, monotonic: float) -> None:
        self.advance(max(0.0, monotonic - self._now))

    @property
    def elapsed(self) -> float:
        return self._now - self._start
