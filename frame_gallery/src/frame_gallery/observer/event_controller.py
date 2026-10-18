"""One explicitly armed event session. No cadence, retry or freshening heartbeat."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from frame_gallery.observer.model import Action, Command, Observation, Status


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
    ) -> None:
        self._send, self._source, self._publish = send, source, publish
        self._claim, self._stopped = claim, stopped
        self._active = False

    def start(self) -> None:
        # Restart/idle/refresh never opens the TV, even with background=true.
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
                seen = self._source.start()
                self._active = seen.status is Status.CHECKING
                self._publish(seen)
            else:
                self.start()
        # REFRESH_CURRENT only drains already received data; never queries.
        self.tick()
        return True

    def tick(self) -> None:
        if self._stopped() or not self._active:
            return
        seen = self._source.update()
        if seen is None:
            return
        self._publish(seen)
        if seen.status not in {Status.ARTWORK, Status.UNIDENTIFIED, Status.CHECKING}:
            self._active = False
            self._source.stop()

    def stop(self) -> None:
        self._active = False
        self._source.stop()
        self._publish(Observation(Status.PAUSED))
