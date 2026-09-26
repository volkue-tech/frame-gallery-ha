"""The 120 s phase table and the phase calculator (§7.1-§7.3, D-114; C5, C11).

Every test uses the fake clock. The start time and all offsets on the 0.5 s
grid are exact in binary floating point, so boundaries are compared exactly.
"""

from __future__ import annotations

import pytest

from frame_gallery.budget.deadline import DeadlineExceeded
from frame_gallery.budget.limits import (
    CONNECT_S,
    DOWNLOAD_REQUEST_S,
    HELPER_REQUEST_S,
    METADATA_REQUEST_S,
)
from frame_gallery.budget.phases import (
    DASHBOARD_TIMER_S,
    DISCOVERY_S,
    DOWNLOAD_S,
    NO_DELIVERY_BOUND_S,
    PHASE_BUDGETS_S,
    PHASE_ORDER,
    PREPARE_S,
    PRESTAGE_RESERVE_S,
    SHUTDOWN_ALLOWANCE_S,
    TELEVISION_RESERVE_S,
    TOTAL_S,
    ContentWindow,
    Phase,
    RunBudget,
)
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock

START = 1000.0

LATER_RESERVE_S = {
    Phase.CONFIGURE: 110.0,
    Phase.CONTENT: 50.0,
    Phase.DELIVER: 10.0,
    Phase.FINISH: 0.0,
}
"""The sum of the budgets after each phase (§7.1), written out independently."""


def _budget() -> tuple[FakeClock, RunBudget]:
    clock = FakeClock(START)
    return clock, RunBudget(clock)


def _half_seconds(stop: float) -> list[float]:
    """``0, 0.5, ..., stop``: exact binary fractions."""
    return [step / 2 for step in range(int(stop * 2) + 1)]


def _configure_end_times() -> list[float]:
    """The 0.5 s grid from 0 to 40 s, plus seeded random end times."""
    rng = SeededRandomSource(20260926)
    return _half_seconds(40.0) + [rng.random() * 40.0 for _ in range(12)]


class TestPhaseTable:
    def test_phases_sum_to_the_120_second_total(self) -> None:
        # C5: the normative table sums to exactly T.
        assert TOTAL_S == 120.0
        assert sum(PHASE_BUDGETS_S.values()) == TOTAL_S

    def test_budgets_match_the_normative_table(self) -> None:
        assert PHASE_BUDGETS_S == {
            Phase.CONFIGURE: 10.0,
            Phase.CONTENT: 60.0,
            Phase.DELIVER: 40.0,
            Phase.FINISH: 10.0,
        }

    def test_order_covers_every_phase_once(self) -> None:
        assert PHASE_ORDER == (Phase.CONFIGURE, Phase.CONTENT, Phase.DELIVER, Phase.FINISH)
        assert tuple(PHASE_BUDGETS_S) == PHASE_ORDER
        assert set(PHASE_ORDER) == set(Phase)
        assert [phase.value for phase in PHASE_ORDER] == [
            "configure",
            "content",
            "deliver",
            "finish",
        ]

    def test_derived_bounds(self) -> None:
        assert SHUTDOWN_ALLOWANCE_S == 10.0
        assert NO_DELIVERY_BOUND_S == 70.0
        assert TELEVISION_RESERVE_S == 50.0
        assert DASHBOARD_TIMER_S == 150.0
        assert NO_DELIVERY_BOUND_S + TELEVISION_RESERVE_S == TOTAL_S
        assert LATER_RESERVE_S[Phase.CONTENT] == TELEVISION_RESERVE_S

    def test_content_window_constants(self) -> None:
        assert DISCOVERY_S == 30.0
        assert DOWNLOAD_S == 20.0
        assert DOWNLOAD_S == DOWNLOAD_REQUEST_S
        assert PREPARE_S == 15.0
        assert PRESTAGE_RESERVE_S == 2.0


class TestRunBudget:
    def test_deadlines_derive_from_the_start(self) -> None:
        clock, budget = _budget()
        assert budget.started_at == START
        assert budget.total.name == "total"
        assert budget.total.expires_at == START + 120.0
        assert budget.total.clock is clock
        assert budget.no_delivery_end == START + 70.0

    def test_watchdog_fires_ten_seconds_after_the_total(self) -> None:
        # C5: the hard cap is T + the shutdown allowance, 130 s.
        clock, budget = _budget()
        assert budget.watchdog_at == START + 130.0
        assert budget.watchdog_at == budget.total.expires_at + SHUTDOWN_ALLOWANCE_S
        clock.advance(100.0)
        assert budget.watchdog_at == START + 130.0

    def test_elapsed_follows_the_clock(self) -> None:
        clock, budget = _budget()
        assert budget.elapsed() == 0.0
        clock.advance(12.5)
        assert budget.elapsed() == 12.5
        assert budget.total.remaining() == 107.5

    def test_a_budget_started_later_is_relative_to_its_own_start(self) -> None:
        clock = FakeClock(START)
        clock.advance(300.0)
        budget = RunBudget(clock)
        assert budget.started_at == START + 300.0
        assert budget.total.expires_at == START + 420.0
        assert budget.watchdog_at == START + 430.0
        assert budget.no_delivery_end == START + 370.0


class TestPhaseCalculator:
    def test_phases_on_schedule_follow_the_table(self) -> None:
        clock, budget = _budget()
        ends = {
            Phase.CONFIGURE: 10.0,
            Phase.CONTENT: 70.0,
            Phase.DELIVER: 110.0,
            Phase.FINISH: 120.0,
        }
        for phase in PHASE_ORDER:
            deadline = budget.phase(phase)
            assert deadline.name == phase.value
            assert deadline.expires_at == START + ends[phase]
            assert deadline.remaining() == PHASE_BUDGETS_S[phase]
            clock.advance_to(deadline.expires_at)
        assert budget.total.expired()

    @pytest.mark.parametrize(
        ("phase", "starts_at", "ends_at"),
        [
            (Phase.CONTENT, 0.0, 60.0),
            (Phase.CONTENT, 2.0, 62.0),
            (Phase.DELIVER, 30.0, 70.0),
            (Phase.DELIVER, 62.0, 102.0),
            (Phase.FINISH, 50.0, 60.0),
            (Phase.FINISH, 80.0, 90.0),
        ],
    )
    def test_unused_time_is_not_added_to_a_later_cap(
        self, phase: Phase, starts_at: float, ends_at: float
    ) -> None:
        # §7.1: time an earlier phase did not use only ends the run earlier.
        clock, budget = _budget()
        clock.advance(starts_at)
        assert budget.phase(phase).expires_at == START + ends_at

    @pytest.mark.parametrize(
        ("phase", "starts_at", "ends_at"),
        [
            (Phase.CONFIGURE, 5.0, 10.0),
            (Phase.CONTENT, 10.5, 70.0),
            (Phase.CONTENT, 15.0, 70.0),
            (Phase.CONTENT, 40.0, 70.0),
            (Phase.CONTENT, 69.5, 70.0),
            (Phase.DELIVER, 75.0, 110.0),
            (Phase.DELIVER, 100.0, 110.0),
            (Phase.DELIVER, 109.5, 110.0),
            (Phase.FINISH, 115.0, 120.0),
            (Phase.FINISH, 119.5, 120.0),
        ],
    )
    def test_an_overrun_never_eats_a_later_reserve(
        self, phase: Phase, starts_at: float, ends_at: float
    ) -> None:
        # CONFIGURE ending at 15 s: the content window ends at 70 s, not 75 s.
        clock, budget = _budget()
        clock.advance(starts_at)
        assert budget.phase(phase).expires_at == START + ends_at

    @pytest.mark.parametrize(
        ("phase", "starts_at"),
        [
            (Phase.CONFIGURE, 10.0),
            (Phase.CONFIGURE, 60.0),
            (Phase.CONTENT, 70.0),
            (Phase.CONTENT, 75.0),
            (Phase.DELIVER, 110.0),
            (Phase.DELIVER, 112.0),
            (Phase.FINISH, 120.0),
        ],
    )
    def test_a_phase_whose_time_is_reserved_expires_now(
        self, phase: Phase, starts_at: float
    ) -> None:
        clock, budget = _budget()
        clock.advance(starts_at)
        deadline = budget.phase(phase)
        assert deadline.expires_at == clock.monotonic()
        assert deadline.expired()
        assert deadline.remaining() == 0.0
        with pytest.raises(DeadlineExceeded) as caught:
            deadline.clamp(1.0)
        assert caught.value.deadline_name == phase.value

    def test_a_phase_after_the_total_is_capped_at_the_total(self) -> None:
        clock, budget = _budget()
        clock.advance(125.0)
        for phase in Phase:
            deadline = budget.phase(phase)
            assert deadline.expires_at == budget.total.expires_at
            assert deadline.expired()

    @pytest.mark.parametrize("phase", list(Phase))
    def test_formula_holds_at_every_start_time(self, phase: Phase) -> None:
        # Each phase = child(min(budget, remaining - sum of later reserves)).
        reserve = LATER_RESERVE_S[phase]
        for offset in _half_seconds(130.0):
            clock, budget = _budget()
            clock.advance(offset)
            deadline = budget.phase(phase)
            now = clock.monotonic()
            total_end = budget.total.expires_at
            wanted = min(PHASE_BUDGETS_S[phase], max(0.0, total_end - now) - reserve)
            assert deadline.expires_at == min(total_end, now + max(0.0, wanted)), offset
            assert deadline.expires_at <= total_end
            assert deadline.expires_at <= max(now, total_end - reserve)
            assert deadline.expires_at <= now + PHASE_BUDGETS_S[phase]

    def test_time_passing_inside_phase_never_breaches_a_later_reserve(self) -> None:
        # §7.1: an early phase can never use a later phase's reserve. A real
        # clock moves between any two readings, so the calculator must derive
        # the phase from a single reading of "now".
        violations: list[str] = []
        for phase, starts_at in (
            (Phase.CONFIGURE, 5.0),
            (Phase.CONTENT, 15.0),
            (Phase.DELIVER, 75.0),
            (Phase.FINISH, 115.0),
        ):
            clock = _TickingClock(tick=0.001)
            budget = RunBudget(clock)
            clock.advance_to(budget.started_at + starts_at)
            deadline = budget.phase(phase)
            limit = budget.total.expires_at - LATER_RESERVE_S[phase]
            if deadline.expires_at > limit:
                overrun = deadline.expires_at - limit
                violations.append(f"{phase.value} ends {overrun:.6f} s into the later reserve")
        assert violations == []

    @pytest.mark.parametrize(
        ("starts_at", "ends_at"),
        [
            (20.0, 60.0),
            (70.0, 110.0),
            (75.0, 110.0),
            (100.0, 110.0),
            (109.0, 110.0),
            (110.0, 110.0),
            (111.0, 111.0),
        ],
    )
    def test_deliver_is_min_of_40_and_remaining_minus_finish(
        self, starts_at: float, ends_at: float
    ) -> None:
        clock, budget = _budget()
        clock.advance(starts_at)
        remaining = budget.total.remaining()
        deliver = budget.phase(Phase.DELIVER)
        assert deliver.expires_at == START + ends_at
        assert deliver.remaining() == max(0.0, min(40.0, remaining - 10.0))

    @pytest.mark.parametrize(
        ("starts_at", "ends_at"),
        [
            (50.0, 60.0),
            (110.0, 120.0),
            (115.0, 120.0),
            (119.5, 120.0),
            (120.0, 120.0),
        ],
    )
    def test_finish_gets_the_remaining_time_up_to_its_budget(
        self, starts_at: float, ends_at: float
    ) -> None:
        # FINISH has no later reserve: it receives what remains of the total,
        # and never more than its own 10 s (§7.1).
        clock, budget = _budget()
        clock.advance(starts_at)
        remaining = budget.total.remaining()
        finish = budget.phase(Phase.FINISH)
        assert finish.expires_at == START + ends_at
        assert finish.remaining() == min(10.0, remaining)


class TestTelevisionReserve:
    def test_available_at_exactly_50_seconds_remaining(self) -> None:
        clock, budget = _budget()
        assert budget.television_reserve_available()
        clock.advance_to(START + 69.5)
        assert budget.television_reserve_available()
        clock.advance_to(START + 70.0)
        assert budget.total.remaining() == TELEVISION_RESERVE_S
        assert budget.television_reserve_available()

    def test_unavailable_just_below_50_seconds(self) -> None:
        clock, budget = _budget()
        clock.advance_to(START + 70.000001)
        assert budget.total.remaining() < TELEVISION_RESERVE_S
        assert not budget.television_reserve_available()
        clock.advance_to(START + 125.0)
        assert not budget.television_reserve_available()


class TestContentWindow:
    @pytest.mark.parametrize("configure_end", _configure_end_times(), ids=lambda v: f"{v:.4f}s")
    def test_a_run_without_delivery_ends_by_70_seconds(self, configure_end: float) -> None:
        # C11: whenever CONFIGURE ends, the content window (and with it a
        # no-delivery FINISH in its last 2 s) ends by T0 + 70 s.
        clock, budget = _budget()
        clock.advance(configure_end)
        opened_at = clock.monotonic()
        content = budget.content_window()
        window, attempts, discovery = content.window, content.attempts, content.discovery

        assert (window.name, attempts.name, discovery.name) == ("content", "attempts", "discovery")
        assert window.expires_at <= START + NO_DELIVERY_BOUND_S
        assert window.expires_at <= budget.no_delivery_end
        assert window.expires_at <= opened_at + PHASE_BUDGETS_S[Phase.CONTENT]
        assert window.expires_at == pytest.approx(START + min(configure_end + 60.0, 70.0))
        assert attempts.expires_at == window.expires_at - PRESTAGE_RESERVE_S
        assert discovery.expires_at <= opened_at + DISCOVERY_S
        assert discovery.expires_at <= attempts.expires_at
        assert discovery.expires_at == min(opened_at + DISCOVERY_S, attempts.expires_at)

        # The window never touches the television reserve (§7.3).
        clock.advance_to(window.expires_at)
        assert budget.television_reserve_available()

    @pytest.mark.parametrize("configure_end", _half_seconds(40.0))
    def test_window_end_on_the_grid_is_exact(self, configure_end: float) -> None:
        clock, budget = _budget()
        clock.advance(configure_end)
        content = budget.content_window()
        assert content.window.expires_at == START + min(configure_end + 60.0, 70.0)

    def test_configure_finishing_early_does_not_extend_the_window(self) -> None:
        clock, budget = _budget()
        clock.advance(2.0)
        content = budget.content_window()
        assert content.window.expires_at == START + 62.0
        assert content.attempts.expires_at == START + 60.0
        assert content.discovery.expires_at == START + 32.0

    def test_configure_overrun_shortens_the_window(self) -> None:
        clock, budget = _budget()
        clock.advance(15.0)
        content = budget.content_window()
        assert content.window.expires_at == START + 70.0
        assert content.attempts.expires_at == START + 68.0
        assert content.discovery.expires_at == START + 45.0

    def test_late_configure_leaves_discovery_capped_by_the_attempts(self) -> None:
        clock, budget = _budget()
        clock.advance(40.0)
        content = budget.content_window()
        assert content.window.expires_at == START + 70.0
        assert content.attempts.expires_at == START + 68.0
        assert content.discovery.expires_at == START + 68.0

    def test_a_window_opened_too_late_is_expired_throughout(self) -> None:
        clock, budget = _budget()
        clock.advance(75.0)
        content = budget.content_window()
        assert content.window.expires_at == START + 75.0
        assert content.window.expired()
        assert content.attempts.expired()
        assert content.discovery.expired()
        with pytest.raises(DeadlineExceeded):
            content.download().clamp(DOWNLOAD_S)

    def test_open_derives_attempts_and_discovery_from_any_window(self) -> None:
        clock = FakeClock(START)
        budget = RunBudget(clock)
        window = budget.total.child(10.0, "short")
        content = ContentWindow.open(window)
        assert content.window is window
        assert content.attempts.expires_at == START + 8.0
        assert content.discovery.expires_at == START + 8.0

    @pytest.mark.parametrize("configure_end", [0.0, 2.0, 10.0, 15.0, 27.5, 40.0])
    def test_download_and_prepare_are_clamped_to_the_attempts(self, configure_end: float) -> None:
        clock, budget = _budget()
        clock.advance(configure_end)
        content = budget.content_window()
        attempts_end = content.attempts.expires_at
        assert attempts_end < content.window.expires_at
        while clock.monotonic() <= content.window.expires_at:
            now = clock.monotonic()
            download = content.download()
            prepare = content.prepare()
            assert (download.name, prepare.name) == ("download", "prepare")
            assert download.expires_at == min(attempts_end, now + DOWNLOAD_S)
            assert prepare.expires_at == min(attempts_end, now + PREPARE_S)
            assert download.expires_at <= attempts_end
            assert prepare.expires_at <= attempts_end
            assert download.expires_at <= budget.no_delivery_end - PRESTAGE_RESERVE_S
            clock.advance(0.5)

    def test_unused_discovery_time_passes_to_the_attempts(self) -> None:
        clock, budget = _budget()
        content = budget.content_window()
        assert content.discovery.expires_at == START + 30.0

        clock.advance(5.0)  # discovery ended early
        first_download = content.download()
        assert first_download.expires_at == START + 25.0
        clock.advance_to(first_download.expires_at)
        first_prepare = content.prepare()
        assert first_prepare.expires_at == START + 40.0
        clock.advance_to(first_prepare.expires_at)

        # A second attempt starts only if time remains, and is clamped.
        second_download = content.download()
        assert second_download.expires_at == START + 58.0
        assert second_download.clamp(DOWNLOAD_S) == 18.0
        clock.advance_to(second_download.expires_at)
        with pytest.raises(DeadlineExceeded) as caught:
            content.prepare().clamp(PREPARE_S)
        assert caught.value.deadline_name == "prepare"

        # The last 2 s stay for PRE-STAGE or a no-delivery FINISH.
        assert content.window.remaining() == PRESTAGE_RESERVE_S

    def test_full_discovery_leaves_the_rest_to_the_attempts(self) -> None:
        clock, budget = _budget()
        content = budget.content_window()
        clock.advance_to(content.discovery.expires_at)
        download = content.download()
        assert download.expires_at == START + 50.0
        clock.advance_to(download.expires_at)
        assert content.prepare().expires_at == START + 58.0


class TestClampingToPhaseAndTotal:
    def test_the_phase_binds_a_helper_read(self) -> None:
        clock, budget = _budget()
        configure = budget.phase(Phase.CONFIGURE)
        clock.advance(8.0)
        assert budget.total.clamp(HELPER_REQUEST_S) == 3.0
        assert configure.clamp(HELPER_REQUEST_S) == 2.0
        assert configure.child(HELPER_REQUEST_S, "helper").expires_at == START + 10.0

    def test_the_phase_binds_a_television_connect(self) -> None:
        clock, budget = _budget()
        clock.advance(100.0)
        deliver = budget.phase(Phase.DELIVER)
        clock.advance(7.0)
        assert budget.total.clamp(CONNECT_S) == 5.0
        assert deliver.clamp(CONNECT_S) == 3.0

    def test_the_total_binds_a_late_finish(self) -> None:
        # FINISH's own 10 s would reach T0 + 124 s; the total ends it at 120 s.
        clock, budget = _budget()
        clock.advance(114.0)
        finish = budget.phase(Phase.FINISH)
        assert finish.expires_at == budget.total.expires_at
        assert finish.clamp(METADATA_REQUEST_S) == 6.0
        assert finish.child(METADATA_REQUEST_S, "records").expires_at == START + 120.0
        clock.advance(6.0)
        with pytest.raises(DeadlineExceeded):
            finish.clamp(METADATA_REQUEST_S)

    def test_the_total_binds_a_request_derived_from_it(self) -> None:
        clock, budget = _budget()
        clock.advance(110.0)
        request = budget.total.child(DOWNLOAD_REQUEST_S, "request")
        assert request.expires_at == START + 120.0
        assert request.clamp(DOWNLOAD_REQUEST_S) == 10.0

    def test_four_helper_reads_fit_the_configure_phase(self) -> None:
        clock, budget = _budget()
        configure = budget.phase(Phase.CONFIGURE)
        granted: list[float] = []
        for _ in range(4):
            timeout = configure.clamp(HELPER_REQUEST_S)
            granted.append(timeout)
            clock.advance(timeout)  # each read uses its whole timeout
        assert granted == [3.0, 3.0, 3.0, 1.0]
        assert clock.elapsed == 10.0
        with pytest.raises(DeadlineExceeded):
            configure.clamp(HELPER_REQUEST_S)
        assert budget.content_window().window.expires_at == START + 70.0

    def test_nested_deadlines_never_outlive_the_phase_or_the_total(self) -> None:
        rng = SeededRandomSource(107)
        for _ in range(300):
            clock, budget = _budget()
            clock.advance(rng.random() * 130.0)
            for phase in Phase:
                deadline = budget.phase(phase)
                requested = 0.001 + rng.random() * 30.0
                child = deadline.child(requested, "request")
                assert child.expires_at <= deadline.expires_at <= budget.total.expires_at
                if deadline.remaining() > 0:
                    clamped = deadline.clamp(requested)
                    assert clamped <= requested
                    assert clamped <= deadline.remaining()
                    assert clamped <= budget.total.remaining()
                else:
                    with pytest.raises(DeadlineExceeded):
                        deadline.clamp(requested)


class _TickingClock(FakeClock):
    """A fake clock that moves on by ``tick`` after every reading, as real time does."""

    def __init__(self, tick: float) -> None:
        super().__init__(START)
        self.tick = tick

    def monotonic(self) -> float:
        now = super().monotonic()
        self.advance(self.tick)
        return now
