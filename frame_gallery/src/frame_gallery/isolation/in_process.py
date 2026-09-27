"""The Phase 2 in-process executor (§11.3, D-139).

It runs tasks in the calling thread but keeps the seam's contract: requests
and results pass through the bytes channel (encode, then decode), and task
failures surface only as :class:`WorkerError` kinds, never as the task's own
exception. The in-process seam cannot pre-empt a task: a task that outlives
its timeout finishes, and its result is then discarded as ``timeout``. The
process executor (Phase 5) enforces the timeout with a kill timer instead.
"""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.errors import Cancelled
from frame_gallery.isolation.channel import (
    MAX_MESSAGE_BYTES,
    ChannelError,
    decode_message,
    encode_message,
)
from frame_gallery.isolation.executor import (
    EventSink,
    EventTaskFunction,
    JsonObject,
    StopCheck,
    TaskFunction,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.logs.summary import sanitize_for_log

PREPARE_TASK: Final = "prepare"
INSPECT_TASK: Final = "inspect"

_WORKER_TASKS_MODULE: Final = "frame_gallery.imaging.worker_tasks"
"""Imported only when a task runs: the parent never imports Pillow (D-107)."""


class _Stopped(BaseException):
    """Ends an event task at the event after which a stop was requested, as
    the process executor's kill would. Task code cannot catch it."""


class InProcessExecutor:
    """Runs tasks from ``tasks`` in the calling thread (Phase 2 seam).

    Tasks in ``event_tasks`` also receive an event sink. Each event crosses
    the same encoding as a result and goes to ``on_event`` at once. A stop
    request is checked before the task starts and after each event; the task
    then ends there, as if its worker had been killed, and the run fails with
    ``stopped``.
    """

    def __init__(
        self,
        tasks: Mapping[str, TaskFunction],
        clock: Clock,
        *,
        event_tasks: Mapping[str, EventTaskFunction] | None = None,
        max_message_bytes: int = MAX_MESSAGE_BYTES,
    ) -> None:
        self._tasks: dict[str, EventTaskFunction] = {
            name: _without_events(function) for name, function in tasks.items()
        }
        self._tasks.update(event_tasks or {})
        self._clock = clock
        self._max_bytes = max_message_bytes

    def _round_trip(self, message: JsonObject, direction: str) -> JsonObject:
        try:
            return decode_message(
                encode_message(message, max_bytes=self._max_bytes), max_bytes=self._max_bytes
            )
        except ChannelError as error:
            raise WorkerError(WorkerErrorKind.PROTOCOL, f"{direction}: {error}") from None

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
    ) -> JsonObject:
        """Run ``task`` and return its result, as the process executor would.

        Raises :class:`WorkerError`; :class:`Cancelled` propagates unchanged.
        """
        if not timeout > 0:
            msg = f"timeout must be positive, got {timeout!r}"
            raise ValueError(msg)
        function = self._tasks.get(task)
        if function is None:
            raise WorkerError(WorkerErrorKind.UNKNOWN_TASK, sanitize_for_log(task, max_length=40))
        started = self._clock.monotonic()
        request = self._round_trip(payload, "request")
        stop = should_stop or _never

        def emit(event: JsonObject) -> None:
            decoded = self._round_trip(event, "event")
            if on_event is not None:
                try:
                    on_event(decoded)
                except ValueError as error:
                    raise WorkerError(WorkerErrorKind.PROTOCOL, f"event: {error}") from None
            if stop():
                raise _Stopped

        if stop():
            raise WorkerError(WorkerErrorKind.STOPPED)
        try:
            result = function(request, emit)
        except Cancelled:
            raise
        except _Stopped:
            raise WorkerError(WorkerErrorKind.STOPPED) from None
        except WorkerError:
            raise
        except MemoryError:
            raise WorkerError(WorkerErrorKind.MEMORY) from None
        except Exception as error:  # noqa: BLE001 - every task failure is a crash
            # Only the type name crosses the seam; a child's traceback cannot.
            raise WorkerError(WorkerErrorKind.CRASH, type(error).__name__) from None
        elapsed = self._clock.monotonic() - started
        if elapsed > timeout:
            raise WorkerError(WorkerErrorKind.TIMEOUT, f"{elapsed:.1f} s > {timeout:.1f} s")
        return self._round_trip(result, "result")

    def terminate_all(self) -> None:
        """Nothing runs outside the calling thread, so there is nothing to kill."""


def _prepare(payload: JsonObject) -> JsonObject:
    module = importlib.import_module(_WORKER_TASKS_MODULE)
    prepare_task: TaskFunction = module.prepare_task
    return prepare_task(payload)


def _inspect(payload: JsonObject) -> JsonObject:
    module = importlib.import_module(_WORKER_TASKS_MODULE)
    inspect_task: TaskFunction = module.inspect_task
    return inspect_task(payload)


def default_tasks() -> dict[str, TaskFunction]:
    """The prepare and inspect tasks for the in-process executor, which runs
    only in tests (R-27); worker modules are imported lazily. Production
    workers use ``launch.PRODUCTION_TASKS``."""
    return {PREPARE_TASK: _prepare, INSPECT_TASK: _inspect}


def _never() -> bool:
    return False


def _without_events(function: TaskFunction) -> EventTaskFunction:
    def call(payload: JsonObject, _emit: EventSink) -> JsonObject:
        return function(payload)

    return call
