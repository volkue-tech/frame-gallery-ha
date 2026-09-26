"""The injected clock (§7.1, §20.2)."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Time as the core sees it. Tests substitute a fake that never waits."""

    def monotonic(self) -> float:
        """Seconds on a monotonic scale; only differences are meaningful."""
        ...

    def utc_now(self) -> datetime:
        """The current wall-clock time, timezone-aware, in UTC."""
        ...

    def sleep(self, seconds: float) -> None:
        """Block for ``seconds`` (used for provider pacing)."""
        ...


class SystemClock:
    """The production clock."""

    def monotonic(self) -> float:
        return time.monotonic()

    def utc_now(self) -> datetime:
        return datetime.now(UTC)

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)
