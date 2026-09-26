"""Deadlines: every timeout is clamped to the time that remains (§7.1)."""

from __future__ import annotations

from frame_gallery.budget.clock import Clock
from frame_gallery.errors import FrameGalleryError


class DeadlineExceeded(FrameGalleryError):
    """A deadline expired before, or while, an operation ran."""

    def __init__(self, deadline_name: str) -> None:
        super().__init__(f"deadline '{deadline_name}' exceeded")
        self.deadline_name = deadline_name


class Deadline:
    """An absolute point on the clock's monotonic scale.

    Deadlines only ever shrink: :meth:`child` and :meth:`cap_at` never produce
    a deadline later than their parent, so a timeout clamped to a phase
    deadline is also clamped to the run's total deadline.
    """

    __slots__ = ("_clock", "expires_at", "name")

    def __init__(self, clock: Clock, expires_at: float, name: str) -> None:
        self._clock = clock
        self.expires_at = expires_at
        self.name = name

    @classmethod
    def after(cls, clock: Clock, seconds: float, name: str) -> Deadline:
        """A deadline ``seconds`` from now (negative values mean now)."""
        return cls(clock, clock.monotonic() + max(0.0, seconds), name)

    @property
    def clock(self) -> Clock:
        return self._clock

    def remaining(self) -> float:
        """Seconds left, never negative."""
        return max(0.0, self.expires_at - self._clock.monotonic())

    def expired(self) -> bool:
        return self._clock.monotonic() >= self.expires_at

    def check(self) -> None:
        """Raise :class:`DeadlineExceeded` if the deadline has passed."""
        if self.expired():
            raise DeadlineExceeded(self.name)

    def child(self, seconds: float, name: str) -> Deadline:
        """A deadline ``seconds`` from now, but never later than this one."""
        candidate = self._clock.monotonic() + max(0.0, seconds)
        return Deadline(self._clock, min(self.expires_at, candidate), name)

    def cap_at(self, expires_at: float, name: str) -> Deadline:
        """A deadline at ``expires_at``, but never later than this one."""
        return Deadline(self._clock, min(self.expires_at, expires_at), name)

    def clamp(self, timeout: float) -> float:
        """Return ``min(timeout, remaining)`` for a blocking call.

        Raises :class:`DeadlineExceeded` when no time remains, so that no
        blocking call ever starts with a zero or negative timeout.
        """
        if timeout <= 0:
            msg = f"timeout must be positive, got {timeout!r}"
            raise ValueError(msg)
        remaining = self.remaining()
        if remaining <= 0:
            raise DeadlineExceeded(self.name)
        return min(timeout, remaining)

    def __repr__(self) -> str:
        return f"Deadline({self.name!r}, expires_at={self.expires_at!r})"
