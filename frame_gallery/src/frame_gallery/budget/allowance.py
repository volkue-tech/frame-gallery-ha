"""Allowance counters that bound every loop (§7.1, §7.2)."""

from __future__ import annotations

from frame_gallery.errors import FrameGalleryError


class AllowanceExhausted(FrameGalleryError):
    """An allowance had no units left."""

    def __init__(self, allowance_name: str) -> None:
        super().__init__(f"allowance '{allowance_name}' exhausted")
        self.allowance_name = allowance_name


class Allowance:
    """A counter of units that may be used at most ``limit`` times per run."""

    __slots__ = ("_used", "limit", "name")

    def __init__(self, name: str, limit: int) -> None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            msg = f"limit must be a non-negative integer, got {limit!r}"
            raise ValueError(msg)
        self.name = name
        self.limit = limit
        self._used = 0

    @property
    def used(self) -> int:
        return self._used

    @property
    def remaining(self) -> int:
        return self.limit - self._used

    @property
    def exhausted(self) -> bool:
        return self._used >= self.limit

    def try_take(self, units: int = 1) -> bool:
        """Use ``units`` if they are all available; report whether it did."""
        if isinstance(units, bool) or not isinstance(units, int) or units <= 0:
            msg = f"units must be a positive integer, got {units!r}"
            raise ValueError(msg)
        if self._used + units > self.limit:
            return False
        self._used += units
        return True

    def take(self, units: int = 1) -> None:
        """Use ``units`` or raise :class:`AllowanceExhausted`."""
        if not self.try_take(units):
            raise AllowanceExhausted(self.name)

    def __repr__(self) -> str:
        return f"Allowance({self.name!r}, used={self._used}, limit={self.limit})"
