"""Stop requests (SIGTERM) and their deferral after ``selected`` (§7.6).

The handler raises :class:`Cancelled` in the main thread, so blocking calls
are interrupted (PEP 475) and the run unwinds through its ``finally`` blocks.
Once ``selected`` has been seen, the runner defers stop requests until
RECORD's rename is ``fsync``ed; a request that arrives meanwhile is only
recorded, and the runner decides what to do when the deferral ends.

The controller uses no locks: the handler runs between bytecodes of the main
thread, which may itself be inside a controller method, so a lock could
deadlock. Each method reads or writes single attributes only.
"""

from __future__ import annotations

import contextlib
import signal
from collections.abc import Callable, Iterator
from types import FrameType

from frame_gallery.errors import Cancelled


class CancellationController:
    """Turns a stop request into ``Cancelled``, unless deferred.

    One controller serves exactly one run (:meth:`claim`). The entry point
    creates it with ``start_deferred=True`` *before* installing the SIGTERM
    handler, so a stop request that arrives before the runner's classified
    region is only recorded; the runner ends that initial deferral inside the
    region (:meth:`end_start_deferral`) and then honours the request.
    """

    def __init__(self, *, start_deferred: bool = False) -> None:
        self._stop_requested = False
        self._deferrals = 1 if start_deferred else 0
        self._start_deferral_pending = start_deferred
        self._raised = False
        self._claimed = False

    def claim(self) -> None:
        """Mark the controller as used by a run; a second claim is a bug."""
        if self._claimed:
            msg = "a CancellationController serves exactly one run"
            raise RuntimeError(msg)
        self._claimed = True

    def end_start_deferral(self) -> None:
        """End the deferral that ``start_deferred=True`` began (once; else a no-op)."""
        if self._start_deferral_pending:
            self._start_deferral_pending = False
            self._deferrals -= 1

    def request_stop(self) -> None:
        """Record a stop request; raise :class:`Cancelled` unless deferred.

        Only the first undeferred request raises. A repeated request while the
        run already unwinds from ``Cancelled`` is only recorded, so it cannot
        interrupt the cleanup in ``finally`` blocks (§14).
        """
        self._stop_requested = True
        if self._deferrals == 0 and not self._raised:
            self._raised = True
            msg = "stop requested"
            raise Cancelled(msg)

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested

    @property
    def deferred(self) -> bool:
        return self._deferrals > 0

    def check(self) -> None:
        """Raise :class:`Cancelled` if a stop is pending and not deferred."""
        if self._stop_requested and self._deferrals == 0:
            self._raised = True
            msg = "stop requested"
            raise Cancelled(msg)

    def begin_deferral(self) -> None:
        """Defer stop requests until the matching :meth:`end_deferral` (nestable).

        A request that arrives before this call has raised already; the runner
        handles that ``Cancelled`` according to the markers it has seen.
        """
        self._deferrals += 1

    def end_deferral(self) -> bool:
        """End one deferral and report whether a stop is pending.

        Never raises ``Cancelled``: the runner decides. Once no deferral is
        active, a later :meth:`check` raises.
        """
        if self._deferrals == 0:
            msg = "end_deferral() without begin_deferral()"
            raise RuntimeError(msg)
        self._deferrals -= 1
        return self._stop_requested


@contextlib.contextmanager
def deferring(controller: CancellationController) -> Iterator[None]:
    """Defer stop requests for the block, then honour one that arrived meanwhile.

    The entry point wraps the start of each worker in it (D-163): a SIGTERM
    can then never land between the fork and the executor's record of the
    worker. When the block ends normally and no other deferral is active, a
    pending request raises :class:`Cancelled`; when the block raises, its
    exception propagates and the request stays pending.
    """
    controller.begin_deferral()
    try:
        yield
    finally:
        controller.end_deferral()
    controller.check()


def install_sigterm_handler(controller: CancellationController) -> Callable[[], None]:
    """Route SIGTERM to ``controller`` and return a function that restores the
    previous handler. Must be called from the main thread (a ``signal`` rule).
    """

    def handle_sigterm(_signum: int, _frame: FrameType | None) -> None:
        controller.request_stop()

    previous = signal.signal(signal.SIGTERM, handle_sigterm)
    # ``None`` means the previous handler was not installed from Python.
    restored = signal.SIG_DFL if previous is None else previous

    def restore() -> None:
        signal.signal(signal.SIGTERM, restored)

    return restore
