"""The optional service loop over injected I/O. No TV or process transport imports."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from frame_gallery.observer.model import Command, Observation


class PublicationGuard:
    """Fail closed once; a missing owned display forbids a continuing listener."""

    def __init__(self, publish: Callable[[Observation], bool], stop: Callable[[], None]) -> None:
        self._publish, self._stop = publish, stop
        self.failed = False

    def __call__(self, observation: Observation) -> None:
        if self.failed:
            return  # including final pause: never retry a refused state write
        if not self._publish(observation):
            self.failed = True
            self._stop()


class ServiceController(Protocol):
    def start(self) -> None: ...
    def command(self, command: Command) -> bool: ...
    def tick(self) -> None: ...
    def stop(self) -> None: ...


def serve(
    controller: ServiceController,
    receive: Callable[[float], Command | None],
    stopped: Callable[[], bool],
) -> None:
    controller.start()
    try:
        while not stopped():
            command = receive(0.5)
            if stopped():
                break
            if command is not None:
                controller.command(command)
            controller.tick()
    finally:
        controller.stop()
