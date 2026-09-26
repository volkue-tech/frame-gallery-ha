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
    JsonObject,
    TaskFunction,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.logs.summary import sanitize_for_log

PREPARE_TASK: Final = "prepare"

_WORKER_TASKS_MODULE: Final = "frame_gallery.imaging.worker_tasks"
"""Imported only when a task runs: the parent never imports Pillow (D-107)."""


class InProcessExecutor:
    """Runs tasks from ``tasks`` in the calling thread (Phase 2 seam)."""

    def __init__(
        self,
        tasks: Mapping[str, TaskFunction],
        clock: Clock,
        *,
        max_message_bytes: int = MAX_MESSAGE_BYTES,
    ) -> None:
        self._tasks = dict(tasks)
        self._clock = clock
        self._max_bytes = max_message_bytes

    def _round_trip(self, message: JsonObject, direction: str) -> JsonObject:
        try:
            return decode_message(
                encode_message(message, max_bytes=self._max_bytes), max_bytes=self._max_bytes
            )
        except ChannelError as error:
            raise WorkerError(WorkerErrorKind.PROTOCOL, f"{direction}: {error}") from None

    def run(self, task: str, payload: JsonObject, *, timeout: float) -> JsonObject:
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
        try:
            result = function(request)
        except Cancelled:
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


def default_tasks() -> dict[str, TaskFunction]:
    """The production task table; imports worker modules lazily."""
    return {PREPARE_TASK: _prepare}
