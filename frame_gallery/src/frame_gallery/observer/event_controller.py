"""One explicitly armed event session. No cadence, retry or freshening heartbeat."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Protocol

from frame_gallery.observer.model import Action, Command, Observation, Status, StatusReason
from frame_gallery.observer.wake import WakeEvent


class EventSource(Protocol):
    def start(self) -> Observation: ...
    def update(self) -> Observation | None: ...
    def stop(self) -> None: ...


class EventController:
    def __init__(
        self,
        *,
        send: Callable[[], int],
        source: EventSource,
        publish: Callable[[Observation], None],
        claim: Callable[[Command], bool],
        stopped: Callable[[], bool],
        prepare_resume: Callable[[], bool] = lambda: False,
        monitor_wake: Callable[[], WakeEvent] = lambda: WakeEvent.NONE,
        supersede_wake: Callable[[], None] = lambda: None,
        keep_tv_session: bool = False,
        idle_status: Callable[[], StatusReason | None] = lambda: None,
        observe_result: Callable[[Observation], None] = lambda _seen: None,
        delivered: Callable[[], None] = lambda: None,
        report_reasons: bool = False,
    ) -> None:
        self._send, self._source, self._publish = send, source, publish
        self._claim, self._stopped = claim, stopped
        self._prepare_resume, self._monitor_wake = prepare_resume, monitor_wake
        self._supersede_wake = supersede_wake
        self._active = False
        self._resume_auth_refused = False
        self._keep_tv_session = keep_tv_session
        self._idle_status, self._observe_result, self._delivered = (
            idle_status,
            observe_result,
            delivered,
        )
        self._report_reasons = report_reasons
        self._last_idle: StatusReason | None = None

    def _report(self, seen: Observation) -> None:
        if self._report_reasons and seen.reason is None:
            reason = {
                Status.NOT_AUTHORIZED: StatusReason.TV_AUTHORIZATION,
                Status.VALIDATION_REQUIRED: StatusReason.ASSOCIATION_REQUIRED,
                Status.UNAVAILABLE: StatusReason.CONNECTION_FAILED,
            }.get(seen.status)
            if reason is not None:
                seen = replace(seen, reason=reason)
        self._observe_result(seen)
        self._last_idle = seen.reason if seen.status is Status.PAUSED else None
        self._publish(seen)

    def start(self) -> None:
        # Startup only publishes status; a later separately bounded grant may read.
        reason = self._idle_status() if self._report_reasons else None
        self._report(Observation(Status.VALIDATION_REQUIRED, reason=reason))

    def command(self, command: Command) -> bool:
        if self._stopped() or not self._claim(command):
            return False
        if command.action is Action.NEW_ARTWORK:
            # Spend the automatic startup opportunity BEFORE any send/reap/
            # publication failure. Only the successful delivery may arm a read.
            self._supersede_wake()
            self._active = False
            self._source.stop()  # must reap the old worker before delivery
            self._report(Observation(Status.CHECKING))
            if self._stopped():
                return False
            result = self._send()
            if result == 0 and not self._stopped():
                self._resume_auth_refused = False
                self._delivered()
                seen = self._source.start()
                self._active = seen.status is Status.CHECKING
                self._report(seen)
            else:
                self.start()
        # REFRESH_CURRENT only drains already received data; never queries.
        self.tick()
        return True

    def tick(self) -> None:
        if self._stopped():
            return
        edge = self._monitor_wake()
        idle = self._idle_status()
        if self._stopped():
            return
        if edge is WakeEvent.SLEEP:
            self.sleep(idle)
        elif edge is WakeEvent.RESUME:
            self.resume()
        if self._stopped():
            return
        if not self._active:
            if (
                self._report_reasons
                and edge is not WakeEvent.RESUME
                and idle is not None
                and idle is not self._last_idle
            ):
                self._report(Observation(Status.PAUSED, reason=idle))
            return
        seen = self._source.update()
        if seen is None:
            return
        self._report(seen)
        if seen.status is Status.NOT_AUTHORIZED:
            self._resume_auth_refused = True
        if seen.status not in {Status.ARTWORK, Status.UNIDENTIFIED, Status.CHECKING} and not (
            self._keep_tv_session and seen.status is Status.TV_IN_USE
        ):
            self._active = False
            self._source.stop()

    def sleep(self, reason: StatusReason | None = None) -> None:
        """A cached HA off is sufficient to stop, never to confirm an image."""
        if self._active:
            self._active = False
            self._source.stop()
            self._report(
                Observation(
                    Status.PAUSED,
                    reason=(reason or StatusReason.STANDBY) if self._report_reasons else None,
                )
            )

    def resume(self) -> bool:
        """One consumed opted-in startup/edge grant; never invokes the sender."""
        if self._stopped() or self._active or self._resume_auth_refused:
            return False
        if not self._prepare_resume():
            if self._report_reasons:
                self._report(
                    Observation(
                        Status.VALIDATION_REQUIRED, reason=StatusReason.ASSOCIATION_REQUIRED
                    )
                )
            return False
        if self._stopped():
            return False
        self._report(
            Observation(
                Status.CHECKING,
                reason=StatusReason.WAKE_REVALIDATION if self._report_reasons else None,
            )
        )
        if self._stopped():
            return False
        seen = self._source.start()
        self._active = seen.status is Status.CHECKING
        if seen.status is Status.NOT_AUTHORIZED:
            self._resume_auth_refused = True
        self._report(seen)
        return self._active

    def stop(self) -> None:
        self._active = False
        self._source.stop()
        self._report(
            Observation(
                Status.PAUSED, reason=StatusReason.SERVICE_STOPPED if self._report_reasons else None
            )
        )
