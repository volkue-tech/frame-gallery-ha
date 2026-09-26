"""The watchdog: the hard cap on a run's duration (§4.3, D-106).

One daemon thread waits until ``T + 10 s`` (:attr:`RunBudget.watchdog_at`).
If the run has not disarmed it by then, it kills the active worker group and
removes the workspace (best-effort ``on_fire`` callbacks), emits exactly one
summary line, and ends the process with exit code 71 (D-133). No last-run
record is written for a watchdog termination (§4.1).
"""

from __future__ import annotations

import contextlib
import os
import threading
from collections.abc import Callable, Sequence
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.logs.summary import format_summary

WATCHDOG_EXIT_CODE: Final = 71
WATCHDOG_OUTCOME: Final = "watchdog_termination"


class Watchdog:
    """Ends the process at ``fire_at`` on the clock's monotonic scale, unless disarmed.

    ``on_fire`` callbacks must not block; each is best-effort, so one that
    raises does not stop the next. ``wait(seconds)`` blocks for at most
    ``seconds`` and may return early; the default returns early on
    :meth:`disarm`. ``started_at`` (default: construction time) is the run's
    start, for the elapsed time in the summary line. A firing claimed before
    :meth:`disarm` still completes; callers check :attr:`fired` after
    disarming.
    """

    def __init__(
        self,
        *,
        clock: Clock,
        fire_at: float,
        on_fire: Sequence[Callable[[], None]],
        emit_line: Callable[[str], None],
        exit_process: Callable[[int], object] = os._exit,
        wait: Callable[[float], bool] | None = None,
        started_at: float | None = None,
    ) -> None:
        self._clock = clock
        self._fire_at = fire_at
        self._on_fire = tuple(on_fire)
        self._emit_line = emit_line
        self._exit_process = exit_process
        self._started_at = clock.monotonic() if started_at is None else started_at
        self._wake = threading.Event()
        self._wait = self._wake.wait if wait is None else wait
        self._lock = threading.Lock()
        self._disarmed = False
        self._fired = False
        self._thread: threading.Thread | None = None

    @property
    def thread(self) -> threading.Thread | None:
        """The watchdog thread, once armed."""
        return self._thread

    @property
    def fired(self) -> bool:
        """True once a firing is claimed, by the thread or by :meth:`fire`.

        A claimed firing always completes: the callbacks run, the watchdog
        line is emitted, and the process exits with 71 (D-133). Read after
        :meth:`disarm`, ``False`` is final for the thread. ``True`` means the
        run's own summary line must not be emitted, since exactly one line
        ends a run (§19): the Phase 6 entry point then waits for the exit
        (for example by joining :attr:`thread`) instead of printing a summary
        and returning its own exit code.
        """
        return self._fired

    def arm(self) -> None:
        """Start the watchdog thread. Arming again, or after disarming, does nothing."""
        with self._lock:
            if self._thread is not None or self._disarmed:
                return
            self._thread = threading.Thread(
                target=self._watch, name="frame-gallery-watchdog", daemon=True
            )
            self._thread.start()

    def disarm(self) -> bool:
        """Stop the watchdog (idempotent) and report whether it was stopped in time.

        Once this returns, the thread never claims a firing. A firing it
        claimed earlier is not stopped and may still be running when this
        returns: then this returns ``False`` (as :attr:`fired` would report),
        and the caller must not emit its own summary line (§19).
        """
        with self._lock:
            self._disarmed = True
            stopped_in_time = not self._fired
        self._wake.set()
        return stopped_in_time

    def fire(self) -> None:
        """Terminate now: run ``on_fire``, emit one line, exit 71.

        Runs at most once. An explicit call is unconditional; :meth:`disarm`
        only stops the thread from calling it.
        """
        with self._lock:
            if self._fired:
                return
            self._fired = True
        self._terminate()

    def _watch(self) -> None:
        while True:
            with self._lock:
                if self._disarmed or self._fired:
                    return
                remaining = self._fire_at - self._clock.monotonic()
                if remaining <= 0:
                    # Claimed under the lock, so a concurrent disarm either
                    # happened before (no fire) or cannot stop it any more.
                    self._fired = True
                    break
            self._wait(remaining)
        self._terminate()

    def _terminate(self) -> None:
        # Every step is best-effort; the exit in ``finally`` always happens.
        try:
            for callback in self._on_fire:
                with contextlib.suppress(Exception):
                    callback()
            line = format_summary(
                outcome=WATCHDOG_OUTCOME,
                exit_code=WATCHDOG_EXIT_CODE,
                elapsed_s=self._clock.monotonic() - self._started_at,
            )
            with contextlib.suppress(Exception):
                self._emit_line(line)
        finally:
            self._exit_process(WATCHDOG_EXIT_CODE)
