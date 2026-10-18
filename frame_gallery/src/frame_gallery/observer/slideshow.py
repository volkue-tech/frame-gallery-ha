"""Corroborate an ordered event triple; no I/O, clock freshening or ID guessing."""

from __future__ import annotations

from frame_gallery.observer.stream import QUERY_S, Change


class IncompleteSequence(ValueError):
    """Known notifications cannot confirm a work; discard, never guess an ID."""


class SlideshowSequence:
    def __init__(self, initial_id: str, at: float) -> None:
        self.pending_at: float | None = None
        self._selected: str | None = None
        self._rotation = False
        self._last_id, self._last_at = initial_id, at

    def expire(self, now: float) -> bool:
        if self.pending_at is not None and now - self.pending_at >= QUERY_S:
            self._clear()
            return True
        return False

    def _discard(self, reason: str) -> None:
        self._clear()
        raise IncompleteSequence(reason)

    def consume(self, change: Change, at: float, now: float) -> str | None:
        if not 0 <= now - at < QUERY_S or at < self._last_at:
            raise ValueError("stale or future slideshow event")
        self._last_at = at
        if self.expire(at):
            raise IncompleteSequence("slideshow sequence expired")
        if change.kind == "invalidate":
            self._clear()
        elif change.kind == "selected":
            if self.pending_at is not None:
                self._discard("overlapping slideshow selection")
            self.pending_at, self._selected = at, change.value
        elif change.kind == "rotation":
            if self._selected != change.value or self._rotation:
                self._discard("inconsistent slideshow rotation")
            self._rotation = True
        elif change == Change("mode", "on"):
            if self.pending_at is not None:
                if not self._rotation:
                    self._discard("slideshow rotation not confirmed")
                content_id = self._selected
                self._clear()
                if content_id != self._last_id:
                    self._last_id = str(content_id)
                    return content_id
        else:
            raise ValueError("unexpected slideshow sequence")
        return None

    def _clear(self) -> None:
        self.pending_at, self._selected, self._rotation = None, None, False
