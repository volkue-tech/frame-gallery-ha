"""Pure cached-HA edge gate. An accepted edge is not proof of physical Art Mode."""

from __future__ import annotations

import enum
import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final

FRESH_ON_S: Final = 30.0
MAX_SAMPLE_GAP_S: Final = 15.0
MAX_WAKES_PER_HOUR: Final = 6
HA_POLL_S: Final = 5.0


class WakeEvent(enum.Enum):
    NONE = 0
    SLEEP = 1
    RESUME = 2


@dataclass(frozen=True, slots=True)
class WakeSample:
    state: str
    changed: float

    @classmethod
    def from_json(cls, value: object, entity_id: str) -> WakeSample:
        if not isinstance(value, Mapping) or value.get("entity_id") != entity_id:
            raise ValueError("wake entity mismatch")
        state, changed = value.get("state"), value.get("last_changed")
        if not isinstance(state, str) or state not in {"on", "off", "unknown", "unavailable"}:
            raise ValueError("invalid wake state")
        if not isinstance(changed, str) or not 1 <= len(changed) <= 64:
            raise ValueError("invalid wake timestamp")
        date = datetime.fromisoformat(changed)
        if date.tzinfo is None:
            raise ValueError("wake timestamp needs timezone")
        stamp = date.timestamp()
        if not math.isfinite(stamp) or stamp < 0:
            raise ValueError("invalid wake timestamp")
        return cls(state, stamp)


class WakeGate:
    """Consume an edge before any connection; failure never retries that edge."""

    def __init__(self, started: float, *, initial_on: bool = False) -> None:
        self._started = started
        self._initial_on = initial_on
        self._last_poll: float | None = None
        self._changed = -1.0
        self._state: str | None = None
        self._off: float | None = None
        self._attempts: list[float] = []

    def feed(self, sample: WakeSample | None, now: float) -> WakeEvent:
        initial, self._initial_on = self._initial_on, False
        gap = self._last_poll is not None and not 0 <= now - self._last_poll <= MAX_SAMPLE_GAP_S
        self._last_poll = now
        if gap:
            self._off = None
        if sample is None or sample.state in {"unknown", "unavailable"}:
            self._off = None
            return WakeEvent.NONE
        if (
            not math.isfinite(now)
            or now < self._started
            or not math.isfinite(sample.changed)
            or sample.changed < 0
            or sample.state not in {"on", "off"}
            or sample.changed > now
            or sample.changed < self._changed
            or (sample.changed == self._changed and sample.state != self._state)
        ):
            self._off = None
            return WakeEvent.NONE
        prior_off = self._off
        self._changed, self._state = sample.changed, sample.state
        if sample.state == "off":
            self._off = sample.changed
            return WakeEvent.SLEEP
        self._off = None
        if not initial and (
            prior_off is None
            or sample.changed <= prior_off
            or sample.changed < self._started
            or now - sample.changed > FRESH_ON_S
        ):
            return WakeEvent.NONE
        self._attempts = [at for at in self._attempts if now - at < 3600]
        if len(self._attempts) >= MAX_WAKES_PER_HOUR:
            return WakeEvent.NONE
        self._attempts.append(now)
        return WakeEvent.RESUME


class WakeMonitor:
    """Poll one cached Core state at most every five seconds, not the TV."""

    def __init__(
        self,
        read: Callable[[], WakeSample | None],
        monotonic: Callable[[], float],
        wall: Callable[[], float],
        *,
        initial_on: bool = False,
    ) -> None:
        self._read, self._monotonic, self._wall = read, monotonic, wall
        self._gate = WakeGate(wall(), initial_on=initial_on)
        self._next = 0.0

    def poll(self) -> WakeEvent:
        now = self._monotonic()
        if now < self._next:
            return WakeEvent.NONE
        self._next = now + HA_POLL_S
        return self._gate.feed(self._read(), self._wall())
