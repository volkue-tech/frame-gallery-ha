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


class WorkerError(FrameGalleryError):
    def __init__(self, kind: WorkerErrorKind, detail: str = "") -> None:
        super().__init__(f"{kind.value}: {detail}" if detail else kind.value)
        self.kind = kind
        self.detail = detail


class Executor(Protocol):
    def run(self, task: str, payload: JsonObject, *, timeout: float) -> JsonObject:
        """Run ``task`` with ``payload`` and return its JSON result.

        ``timeout`` must already be clamped to the phase deadline. Raises
        :class:`WorkerError`; ``Cancelled`` may propagate.
        """
        ...

    def terminate_all(self) -> None:
        """Kill every running worker (cleanup; idempotent)."""
        ...
