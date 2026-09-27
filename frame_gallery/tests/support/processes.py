"""Process executors for tests (D-163).

Every worker a test starts runs a task from ``tests/support/worker_tasks.py``,
each of which installs the H2 network guard first; the production entries
are wrapped the same way (``guarded_prepare`` and so on). The launch is
:meth:`Launch.production` for this host, plus the project root as the one
extra path, so the workers get exactly the bootstrap production gets here.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from frame_gallery.budget.clock import SystemClock
from frame_gallery.isolation.launch import IMAGE_LIMITS, TELEVISION_LIMITS, Limit, TaskEntry
from frame_gallery.isolation.process import Launch, ProcessExecutor

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
MODULE: Final = "tests.support.worker_tasks"


def entry(
    function: str, *, events: bool = False, limits: Mapping[Limit, int] = IMAGE_LIMITS
) -> TaskEntry:
    return TaskEntry(MODULE, function, events=events, limits=limits)


TEST_TASKS: Final[Mapping[str, TaskEntry]] = {
    "echo": entry("echo"),
    "events": entry("events", events=True),
    "sleep": entry("sleep"),
    "crash": entry("crash"),
    "memory": entry("memory"),
    "exit_now": entry("exit_now"),
    "not_json": entry("not_json"),
    "logs": entry("logs"),
    "raw": entry("raw"),
    "frame": entry("frame", events=True),
    "frame_plain": entry("frame"),
    "stderr_flood": entry("stderr_flood"),
    "close_stderr": entry("close_stderr"),
    "report": entry("report"),
    "report_tv": entry("report", limits=TELEVISION_LIMITS),
    "spawn": entry("spawn"),
    "orphan": entry("orphan"),
    "prepare": entry("guarded_prepare"),
    "inspect": entry("guarded_inspect"),
    "deliver": entry("fake_deliver", events=True, limits=TELEVISION_LIMITS),
    "deliver_real": entry("guarded_deliver", events=True, limits=TELEVISION_LIMITS),
}


def worker_launch(**changes: object) -> Launch:
    """This host's production launch, with the test tasks and the project root."""
    launch = dataclasses.replace(
        Launch.production(), tasks=TEST_TASKS, extra_paths=(str(PROJECT_ROOT),)
    )
    return dataclasses.replace(launch, **changes)  # type: ignore[arg-type]


def worker_executor(**changes: object) -> ProcessExecutor:
    return ProcessExecutor(worker_launch(**changes), SystemClock())
