"""The serial background controller, with fail-closed TV access and bounded replay state."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from frame_gallery.observer.model import POLL_S, Action, Command, Observation, Status


@dataclass(frozen=True, slots=True)
class SafetyPermit:
    """Validated hardware policy or explicitly accepted experimental risk.

    Neither an experimental opt-in nor a token is proof of no-wake safety.
    """

    validated: bool = False
    experimental: bool = False

    @property
    def enabled(self) -> bool:
        return self.validated or self.experimental


UNVALIDATED = SafetyPermit()


class Controller:
    def __init__(
        self,
        *,
        send: Callable[[], int],
        observe: Callable[[], Observation],
        publish: Callable[[Observation], None],
        now: Callable[[], float],
        claim: Callable[[Command], bool],
        permit: SafetyPermit = UNVALIDATED,
        stopped: Callable[[], bool] = lambda: False,
    ) -> None:
        self._send, self._observe, self._publish, self._now = send, observe, publish, now
        self._permit = permit
        self._claim = claim
        self._stopped = stopped
        self._armed = False
        self._next_read = 0.0
        self._next_publish = 0.0
        self._last = Observation(Status.VALIDATION_REQUIRED)

    def _report(self, observation: Observation) -> None:
        self._last = observation
        self._next_publish = self._now() + POLL_S
        self._publish(observation)

    def start(self) -> None:
        # Boot/restart only publishes status; never connects to or sends to the TV.
        self._report(
            Observation(Status.PAUSED if self._permit.enabled else Status.VALIDATION_REQUIRED)
        )

    def command(self, command: Command) -> bool:
        if self._stopped() or not self._claim(command):
            return False
        if command.action is Action.NEW_ARTWORK:
            self._armed = False
            self._report(Observation(Status.CHECKING))
            if self._stopped():
                return False
            if self._send() == 0:
                self._armed = self._permit.enabled
                self._next_read = self._now()
            if not self._armed:
                self.start()
            self.tick()
        elif self._armed:
            self._next_read = self._now()
            self.tick()
        else:
            self.start()
        return True

    def tick(self) -> None:
        if self._stopped():
            return
        if not self._permit.enabled or not self._armed:
            if self._now() >= self._next_publish:
                # Only non-current statuses can be heartbeated without observing TV.
                self._report(self._last)
            return
        if self._now() < self._next_read:
            return
        observation = self._observe()
        self._next_read = self._now() + POLL_S
        # No reconnection loop after standby, loss, revocation or unconfirmed mode.
        if observation.status not in {Status.ARTWORK, Status.UNIDENTIFIED}:
            self._armed = False
        self._report(observation)

    def stop(self) -> None:
        self._armed = False
        self._report(Observation(Status.PAUSED))
