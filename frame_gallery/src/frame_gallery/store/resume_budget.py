"""D-250 durable reservations; a corrupt primary must NEVER reset the budget."""

from __future__ import annotations

import math
from itertools import pairwise
from pathlib import Path
from typing import Final

from frame_gallery.errors import StateError
from frame_gallery.observer.model import StatusReason
from frame_gallery.store.atomic import ReadFailure, decode_json, encode_json, open_directory

FILE: Final = "standby-resume-budget.json"
MAX_BYTES: Final = 2048
FORMAT: Final = "frame-gallery-standby-budget"
MAX_ATTEMPTS: Final = 6
MIN_INTERVAL: Final = 60.0
PERIOD: Final = 3600.0


def _stamp(value: object) -> bool:
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0 <= value <= 253402300799
    )


def _parse(raw: bytes) -> tuple[list[float], bool]:
    value = decode_json(raw)
    if (
        not isinstance(value, dict)
        or set(value) != {"format", "version", "attempts", "auth_blocked"}
        or value["format"] != FORMAT
        or type(value["version"]) is not int
        or value["version"] != 1
        or type(value["auth_blocked"]) is not bool
    ):
        raise ValueError("invalid standby budget")
    attempts = value["attempts"]
    if (
        not isinstance(attempts, list)
        or len(attempts) > MAX_ATTEMPTS
        or not all(_stamp(at) for at in attempts)
        or any(a >= b for a, b in pairwise(attempts))
    ):
        raise ValueError("invalid standby attempts")
    return [float(at) for at in attempts], value["auth_blocked"]


class ResumeBudget:
    """Called under the existing exclusive observer lease. No backup fallback."""

    def __init__(self, data: Path) -> None:
        self._data = data

    def _read(self) -> tuple[list[float], bool]:
        with open_directory(self._data, ("state",), create=True) as directory:
            raw = directory.read_bytes(FILE, MAX_BYTES)
        if raw is ReadFailure.MISSING:
            return [], False
        if not isinstance(raw, bytes):
            raise StateError("standby budget unreadable")
        return _parse(raw)

    def _write(self, attempts: list[float], *, blocked: bool) -> None:
        raw = encode_json(
            {"format": FORMAT, "version": 1, "attempts": attempts, "auth_blocked": blocked},
            MAX_BYTES,
        )
        _parse(raw)
        with open_directory(self._data, ("state",), create=True) as directory:
            directory.write(FILE, raw)
            if directory.read_bytes(FILE, MAX_BYTES) != raw:
                raise StateError("standby reservation readback mismatch")

    def reserve(self, now: float) -> StatusReason | None:
        try:
            if not _stamp(now):
                raise ValueError("invalid standby clock")
            attempts, blocked = self._read()
            if attempts and now < attempts[-1]:
                raise ValueError("standby clock moved backwards")
            if blocked:
                return StatusReason.TV_AUTHORIZATION
            attempts = [at for at in attempts if now - at < PERIOD]
            if len(attempts) >= MAX_ATTEMPTS or (attempts and now - attempts[-1] < MIN_INTERVAL):
                return StatusReason.RATE_LIMITED
            self._write([*attempts, now], blocked=False)  # durable BEFORE any TV preparation
        except (StateError, OSError, ValueError):
            return StatusReason.BUDGET_UNAVAILABLE
        return None

    def block_auth(self) -> None:
        try:
            attempts, _blocked = self._read()
            self._write(attempts, blocked=True)
        except (StateError, OSError, ValueError):
            pass  # caller also latches in memory; damaged/write-failed budget denies I/O

    def clear_auth(self) -> bool:
        try:
            attempts, blocked = self._read()
            if blocked:
                self._write(attempts, blocked=False)  # a successful send never clears limits
        except (StateError, OSError, ValueError):
            return False
        return True
