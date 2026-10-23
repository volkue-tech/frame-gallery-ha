"""Settled cached-HA edge, NOT physical Art Mode proof or a no-wake guarantee."""

from __future__ import annotations

import math
from collections.abc import Callable

from frame_gallery.observer.model import Observation, Status, StatusReason
from frame_gallery.observer.wake import HA_POLL_S, MAX_SAMPLE_GAP_S, WakeEvent, WakeSample

OFF_S = 30.0
SETTLE_S = 10.0
EDGE_FRESH_S = 30.0


class StandbyResumeMonitor:
    def __init__(
        self,
        read: Callable[[], WakeSample | None],
        monotonic: Callable[[], float],
        wall: Callable[[], float],
        *,
        reserve: Callable[[float], StatusReason | None],
        block_auth: Callable[[], None],
        clear_auth: Callable[[], bool],
        configured: bool,
    ) -> None:
        self._read, self._monotonic, self._wall = read, monotonic, wall
        self._reserve, self._block_auth, self._clear_auth = reserve, block_auth, clear_auth
        self._configured = configured
        self._blocked_reason: StatusReason | None = None
        self._next = 0.0
        self._last: float | None = None
        self._last_wall: float | None = None
        self._sample: WakeSample | None = None
        self._off_at: float | None = None
        self._off_ready = False
        self._on_at: float | None = None
        self._reason: StatusReason | None = None
        self._pending: StatusReason | None = None
        self._grant: float | None = None
        self._status(
            StatusReason.WAITING_FOR_STANDBY if configured else StatusReason.CONFIGURATION_REQUIRED
        )

    def _status(self, reason: StatusReason) -> None:
        if reason is not self._reason:
            self._reason = self._pending = reason

    def take_status(self) -> StatusReason | None:
        reason, self._pending = self._pending, None
        return reason

    def supersede(self) -> None:
        self._sample = None
        self._off_at = self._on_at = None
        self._off_ready = False
        self._pending = None
        self._grant = None

    def claim(self) -> bool:
        """Second barrier: one same-poll reservation, never a saved resume flag."""
        grant, self._grant = self._grant, None
        now = self._monotonic()
        return grant is not None and math.isfinite(now) and 0 <= now - grant <= HA_POLL_S

    def observe(self, observation: Observation) -> None:
        if observation.status is Status.NOT_AUTHORIZED:
            self._blocked_reason = StatusReason.TV_AUTHORIZATION
            self._block_auth()
            self.supersede()
            self._status(StatusReason.TV_AUTHORIZATION)

    def delivered(self) -> None:
        self._blocked_reason = None if self._clear_auth() else StatusReason.BUDGET_UNAVAILABLE
        self.supersede()
        self._reason = None

    def poll(self) -> WakeEvent:
        if not self._configured:
            return WakeEvent.NONE
        now, wall = self._monotonic(), self._wall()
        if (
            not math.isfinite(now)
            or now < 0
            or not math.isfinite(wall)
            or wall < 0
            or (self._last is not None and now < self._last)
            or (self._last_wall is not None and wall < self._last_wall)
        ):
            return self._invalid()
        if now < self._next:
            return WakeEvent.NONE
        self._grant = None
        gap = self._last is not None and now - self._last > MAX_SAMPLE_GAP_S
        jump = (
            self._last_wall is not None
            and self._last is not None
            and abs((wall - self._last_wall) - (now - self._last)) > 2
        )
        self._last, self._last_wall, self._next = now, wall, now + HA_POLL_S
        sample = self._read()
        if (
            gap
            or jump
            or sample is None
            or sample.state not in {"on", "off"}
            or not math.isfinite(sample.changed)
            or not 0 <= sample.changed <= wall
            or (
                self._sample is not None
                and (
                    sample.changed < self._sample.changed
                    or (
                        sample.changed == self._sample.changed
                        and sample.state != self._sample.state
                    )
                )
            )
        ):
            return self._invalid()
        return self._advance(sample, now, wall)

    def _advance(self, sample: WakeSample, now: float, wall: float) -> WakeEvent:
        prior, self._sample = self._sample, sample
        if sample.state == "off":
            self._on_at = None
            if prior is None or prior.state != "off" or prior.changed != sample.changed:
                self._off_at, self._off_ready = now, False
            self._off_ready = self._off_at is not None and now - self._off_at >= OFF_S
            self._status(StatusReason.STANDBY)
            return WakeEvent.SLEEP
        if prior is not None and prior.state == "off":
            ready, self._off_ready = self._off_ready, False  # consume edge even on denial
            self._off_at = None
            if ready and 0 <= wall - sample.changed <= EDGE_FRESH_S:
                self._on_at = now
                self._status(StatusReason.WAKE_SETTLING)
            else:
                self._on_at = None
                self._status(StatusReason.WAITING_FOR_STANDBY)
        if self._on_at is None:
            return WakeEvent.NONE
        if prior is not None and prior.state == "on" and prior.changed != sample.changed:
            return self._invalid()  # a hidden transition cannot complete the old grant
        if wall - sample.changed > EDGE_FRESH_S:
            return self._invalid()
        if now - self._on_at < SETTLE_S:
            return WakeEvent.NONE
        self._on_at = None  # no retries, even if preparation/reservation later fails
        denial = self._blocked_reason or self._reserve(wall)
        self._status(denial or StatusReason.WAKE_REVALIDATION)
        if denial is None:
            self._grant = now
        return WakeEvent.NONE if denial is not None else WakeEvent.RESUME

    def _invalid(self) -> WakeEvent:
        self.supersede()
        self._status(StatusReason.HA_STATE_UNAVAILABLE)
        return WakeEvent.SLEEP
