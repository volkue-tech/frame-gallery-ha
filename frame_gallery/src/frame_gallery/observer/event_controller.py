"""One explicitly armed event session. No cadence, retry or freshening heartbeat."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from frame_gallery.observer.model import Action, Command, Observation, Status
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
    ) -> None:
        self._send, self._source, self._publish = send, source, publish
        self._claim, self._stopped = claim, stopped
        self._prepare_resume, self._monitor_wake = prepare_resume, monitor_wake
        self._active = False
        self._resume_auth_refused = False

    def start(self) -> None:
        # Only tick's separately opted-in initial-on/fresh-edge gate may read.
        self._publish(Observation(Status.VALIDATION_REQUIRED))

    def command(self, command: Command) -> bool:
        if self._stopped() or not self._claim(command):
            return False
        if command.action is Action.NEW_ARTWORK:
            self._active = False
            self._source.stop()  # must reap the old worker before delivery
            self._publish(Observation(Status.CHECKING))
            if self._stopped():
                return False
            result = self._send()
            if result == 0 and not self._stopped():
                self._resume_auth_refused = False
                seen = self._source.start()
                self._active = seen.status is Status.CHECKING
                self._publish(seen)
            else:
                self.start()
        # REFRESH_CURRENT only drains already received data; never queries.
        self.tick()
        return True

    def tick(self) -> None:
        if self._stopped():
            return
        edge = self._monitor_wake()
        if self._stopped():
            return
        if edge is WakeEvent.SLEEP:
            self.sleep()
        elif edge is WakeEvent.RESUME:
            self.resume()
        if self._stopped() or not self._active:
            return
        seen = self._source.update()
        if seen is None:
            return
        self._publish(seen)
        if seen.status is Status.NOT_AUTHORIZED:
            self._resume_auth_refused = True
        if seen.status not in {Status.ARTWORK, Status.UNIDENTIFIED, Status.CHECKING}:
            self._active = False
            self._source.stop()

    def sleep(self) -> None:
        """A cached HA off is sufficient to stop, never to confirm an image."""
        if self._active:
            self._active = False
            self._source.stop()
            self._publish(Observation(Status.PAUSED))

    def resume(self) -> bool:
        """One consumed opted-in startup/edge grant; never invokes the sender."""
        if (
            self._stopped()
            or self._active
            or self._resume_auth_refused
            or not self._prepare_resume()
        ):
            return False
        if self._stopped():
            return False
        self._publish(Observation(Status.CHECKING))
        if self._stopped():
            return False
        seen = self._source.start()
        self._active = seen.status is Status.CHECKING
        if seen.status is Status.NOT_AUTHORIZED:
            self._resume_auth_refused = True
        self._publish(seen)
        return self._active

    def stop(self) -> None:
        self._active = False
        self._source.stop()
        self._publish(Observation(Status.PAUSED))
