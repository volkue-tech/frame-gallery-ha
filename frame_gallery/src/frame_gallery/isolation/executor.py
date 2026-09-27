"""The executor seam (§11.3, D-109, D-139).

Tasks exchange JSON objects only. The process executor (Phase 5) carries
them as bytes over a size-capped channel and never unpickles child output;
the in-process executor (Phase 2) applies the same encoding so both behave
the same at this seam.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from typing import Protocol

from frame_gallery.errors import FrameGalleryError

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None
type JsonObject = dict[str, JsonValue]

TaskFunction = Callable[[JsonObject], JsonObject]

EventSink = Callable[[JsonObject], None]
"""Receives each intermediate event a task sends (the television markers), in
order, before :meth:`Executor.run` returns or raises. It may raise
``ValueError`` for an event it refuses; the task is then killed and the run
fails with ``protocol``. After a kill by the timer or a stop request, a
refusal of an event still found in the pipe only ends the relay: the run
keeps ``timeout`` or ``stopped``."""

StopCheck = Callable[[], bool]

EventTaskFunction = Callable[[JsonObject, EventSink], JsonObject]
"""A task that sends intermediate events: it calls the sink for each one,
and the sink returns once the event is on its way to the parent."""


class WorkerErrorKind(enum.StrEnum):
    TIMEOUT = "timeout"
    """The task outlived its (clamped) timeout."""

    CRASH = "crash"
    """The task raised, or the worker died."""

    MEMORY = "memory"
    """The task exceeded its memory limit."""

    PROTOCOL = "protocol"
    """The request or result was not a valid, size-capped JSON object."""

    UNKNOWN_TASK = "unknown_task"

    STOPPED = "stopped"
    """A stop request ended the task: the worker was killed after the events
    it had already sent were delivered (D-141)."""


class WorkerError(FrameGalleryError):
    def __init__(self, kind: WorkerErrorKind, detail: str = "") -> None:
        super().__init__(f"{kind.value}: {detail}" if detail else kind.value)
        self.kind = kind
        self.detail = detail


class IsolationFailure(FrameGalleryError):
    """The isolation itself failed: a worker could not be started, or refused
    to run because its bootstrap did not complete (§11.3: "If dropping
    privileges fails, the worker refuses to run (``internal_error``)").

    Deliberately not a :class:`WorkerError`: no caller treats it as a failure
    of one task, so it ends the run as ``internal_error`` (D-163)."""


class Executor(Protocol):
    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
    ) -> JsonObject:
        """Run ``task`` with ``payload`` and return its JSON result.

        ``timeout`` must already be clamped to the phase deadline. Events the
        task sends go to ``on_event`` as they arrive. ``should_stop`` is polled
        while the task runs; once it returns true, the task is killed and the
        run fails with ``stopped``, after every event already sent was
        delivered. Returns or raises only after the task was killed or ended
        and its channel closed, so nothing it sends can arrive later. Raises
        :class:`WorkerError`; the process executor also raises
        ``IsolationFailure``; ``Cancelled`` may propagate.
        """
        ...

    def terminate_all(self) -> None:
        """Kill every running worker (cleanup; idempotent)."""
        ...
