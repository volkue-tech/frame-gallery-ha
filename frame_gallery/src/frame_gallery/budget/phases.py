"""The normative 120 s phase table and the phase calculator (§7.1-§7.3, D-114).

Each phase receives ``child(min(budget, remaining - sum of later reserves))``.
An early phase can therefore never use a later phase's reserve, and unused
time is never added to a later phase's cap; it only ends the run earlier.
Inside the content window, unused discovery time passes to the attempts.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline


class Phase(enum.StrEnum):
    CONFIGURE = "configure"
    """CONFIGURE + RESOLVE_FILTERS."""

    CONTENT = "content"
    """The content window: SELECT + ATTEMPT + PRE-STAGE."""

    DELIVER = "deliver"
    FINISH = "finish"
    """Reserved: RECORD, PUBLISH, run records, cleanup."""


TOTAL_S: Final = 120.0
PHASE_BUDGETS_S: Final = {
    Phase.CONFIGURE: 10.0,
    Phase.CONTENT: 60.0,
    Phase.DELIVER: 40.0,
    Phase.FINISH: 10.0,
}
PHASE_ORDER: Final = (Phase.CONFIGURE, Phase.CONTENT, Phase.DELIVER, Phase.FINISH)

SHUTDOWN_ALLOWANCE_S: Final = 10.0
"""The watchdog fires this long after the total deadline (130 s)."""

DISCOVERY_S: Final = 30.0
"""Discovery ends at most this long into the content window."""

DOWNLOAD_S: Final = 20.0
PREPARE_S: Final = 15.0
PRESTAGE_RESERVE_S: Final = 2.0
"""The last seconds of the content window, reserved for PRE-STAGE, or for
the FINISH of a run with nothing to deliver."""

LAST_RUN_RESERVE_S: Final = 2.0
"""The end of FINISH, kept for the last-run record: PUBLISH may not use it."""

NO_DELIVERY_BOUND_S: Final = PHASE_BUDGETS_S[Phase.CONFIGURE] + PHASE_BUDGETS_S[Phase.CONTENT]
"""``no_match``, ``source_failed``, and ``image_failed`` end by 70 s (C11)."""

TELEVISION_RESERVE_S: Final = PHASE_BUDGETS_S[Phase.DELIVER] + PHASE_BUDGETS_S[Phase.FINISH]
"""Re-checked at PRE-STAGE before any upload intent is committed (§7.3)."""

DASHBOARD_TIMER_S: Final = TOTAL_S + 30.0
"""The dashboard's loading indicator (§16.3): 150 s."""


class RunBudget:
    """The deadlines of one run, derived from its start time."""

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        self.started_at = clock.monotonic()
        self.total = Deadline(clock, self.started_at + TOTAL_S, "total")

    @property
    def watchdog_at(self) -> float:
        """Monotonic time at which the watchdog fires: ``T`` + 10 s."""
        return self.started_at + TOTAL_S + SHUTDOWN_ALLOWANCE_S

    @property
    def no_delivery_end(self) -> float:
        """Latest monotonic time at which a run without delivery ends (70 s)."""
        return self.started_at + NO_DELIVERY_BOUND_S

    def elapsed(self) -> float:
        return self._clock.monotonic() - self.started_at

    def phase(self, phase: Phase) -> Deadline:
        """The deadline for ``phase``, starting now."""
        later = PHASE_ORDER[PHASE_ORDER.index(phase) + 1 :]
        reserve = sum(PHASE_BUDGETS_S[p] for p in later)
        # One clock reading: time passing between two readings must never let
        # a phase reach into a later phase's reserve.
        now = self._clock.monotonic()
        latest = max(now, self.total.expires_at - reserve)
        return self.total.cap_at(min(now + PHASE_BUDGETS_S[phase], latest), phase.value)

    def television_reserve_available(self) -> bool:
        """Whether DELIVER's and FINISH's reserve is still intact (§7.3)."""
        return self.total.remaining() >= TELEVISION_RESERVE_S

    def content_window(self) -> ContentWindow:
        """Open the content window, starting now."""
        return ContentWindow.open(self.phase(Phase.CONTENT))


@dataclass(frozen=True, slots=True)
class ContentWindow:
    """The content window and its internal deadlines (§7.2)."""

    window: Deadline
    """The whole window. PRE-STAGE, or a no-delivery FINISH, ends by it."""

    attempts: Deadline
    """The window minus the PRE-STAGE reserve."""

    discovery: Deadline
    """At most 30 s into the window, and never into the PRE-STAGE reserve."""

    @classmethod
    def open(cls, window: Deadline) -> ContentWindow:
        attempts = window.cap_at(window.expires_at - PRESTAGE_RESERVE_S, "attempts")
        discovery = attempts.child(DISCOVERY_S, "discovery")
        return cls(window=window, attempts=attempts, discovery=discovery)

    def download(self) -> Deadline:
        """The deadline for one download, starting now."""
        return self.attempts.child(DOWNLOAD_S, "download")

    def prepare(self) -> Deadline:
        """The deadline for one preparation, starting now."""
        return self.attempts.child(PREPARE_S, "prepare")
