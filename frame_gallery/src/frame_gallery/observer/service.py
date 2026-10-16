"""The optional service loop over injected I/O. No TV or process transport imports."""

from __future__ import annotations

from collections.abc import Callable

from frame_gallery.observer.controller import Controller
from frame_gallery.observer.model import Command


def serve(
    controller: Controller,
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
