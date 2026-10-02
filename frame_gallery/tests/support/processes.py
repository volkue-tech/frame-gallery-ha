"""Process executors for tests (D-163, D-165).

A worker started through :func:`worker_executor` runs a task from
``tests/support/worker_tasks.py``, each of which installs the H2 network
guard first; the production entries are wrapped the same way
(``guarded_prepare`` and so on). The launch is :meth:`Launch.production` for
this host, plus the project root as the one extra path, so for a non-root
parent the workers get exactly the bootstrap production gets here.

A root parent drops every worker to 65534, and such a worker refuses test
paths (D-163), so these tests need a non-root parent. :func:`require` says
which host a test needs; the root-only tests run production tasks only,
without the test paths and so without the H2 guard, and only tasks that
fail before any I/O (``tests/unit/isolation/test_root_isolation.py``).

``FRAME_GALLERY_REQUIRE_ISOLATION`` names the run mode of a container run:
``user`` (a non-root Linux run: the Linux-only checks must run) or ``root``
(a root run: the root-only checks must run). Then a skip of what the mode
promises is a failure; tests the mode cannot run are skipped.
"""

from __future__ import annotations

import dataclasses
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pytest

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
    "raw_events": entry("raw", events=True),
    "big_frame": entry("big_frame", events=True),
    "frame": entry("frame", events=True),
    "frame_plain": entry("frame"),
    "stderr_flood": entry("stderr_flood"),
    "close_stderr": entry("close_stderr"),
    "fork_and_sleep": entry("fork_and_sleep", events=True),
    "tick": entry("tick", events=True),
    "big_event": entry("big_event", events=True),
    "big_result": entry("big_result"),
    "stderr_line": entry("stderr_line"),
    "report": entry("report"),
    "report_tv": entry("report", limits=TELEVISION_LIMITS),
    "spawn": entry("spawn"),
    "orphan": entry("orphan"),
    "prepare": entry("guarded_prepare"),
    "inspect": entry("guarded_inspect", events=True),
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


REQUIREMENTS: Final = {
    "unprivileged": "the test tasks need a non-root parent: a root parent drops its workers, "
    "which refuse test paths (D-163)",
    "linux": "a Linux-only check (RLIMIT_AS, threads, prctl), run by a non-root Linux parent",
    "root": "a root-only check (the drop to 65534), run by a root parent on Linux",
}


def able(kind: str) -> bool:
    linux, root = sys.platform.startswith("linux"), os.geteuid() == 0
    return {"unprivileged": not root, "linux": linux and not root, "root": linux and root}[kind]


def require(kind: str) -> None:
    """Skip unless this host can run a test of ``kind``; in a container run
    whose mode promises it, fail instead (D-165)."""
    if able(kind):
        return
    promised = {"user": "linux", "root": "root"}.get(
        os.environ.get("FRAME_GALLERY_REQUIRE_ISOLATION", "")
    )
    if promised == kind:
        pytest.fail(f"this run promises it, but this host cannot: {REQUIREMENTS[kind]}")
    pytest.skip(REQUIREMENTS[kind])
