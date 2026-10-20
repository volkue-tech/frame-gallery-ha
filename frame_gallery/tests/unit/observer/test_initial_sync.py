"""Explicit initial-on gate regressions; synthetic cached Core states, no network."""

from __future__ import annotations

import pytest
from tests.unit.observer.test_events import ControllerRig, command

from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command
from frame_gallery.observer.service import serve
from frame_gallery.observer.wake import WakeEvent, WakeGate, WakeMonitor, WakeSample


@pytest.mark.parametrize("changed", [0.0, 50.0, 99.0, 100.0])
def test_first_on_can_be_old_but_cannot_repeat(changed: float) -> None:
    gate = WakeGate(100, initial_on=True)
    assert gate.feed(WakeSample("on", changed), 100) is WakeEvent.RESUME
    for now in (101, 105, 110):
        assert gate.feed(WakeSample("on", changed), now) is WakeEvent.NONE
    assert gate.feed(WakeSample("off", 111), 111) is WakeEvent.SLEEP
    assert gate.feed(WakeSample("on", 112), 112) is WakeEvent.RESUME


@pytest.mark.parametrize(
    "first",
    [
        None,
        WakeSample("off", 90),
        WakeSample("unknown", 90),
        WakeSample("unavailable", 90),
        WakeSample("on", 101),
        WakeSample("on", -0.5),
        WakeSample("on", float("nan")),
        WakeSample("on", float("inf")),
        WakeSample("playing", 90),
    ],
)
def test_first_error_or_non_on_consumes_startup_without_a_delayed_retry(
    first: WakeSample | None,
) -> None:
    gate = WakeGate(100, initial_on=True)
    assert gate.feed(first, 100) is (
        WakeEvent.SLEEP if first and first.state == "off" else WakeEvent.NONE
    )
    # The same old on would be allowed only by the now-spent startup opportunity.
    assert gate.feed(WakeSample("on", 95), 105) is WakeEvent.NONE
    assert gate.feed(WakeSample("on", 95), 110) is WakeEvent.NONE
    assert gate.feed(WakeSample("off", 111), 111) is WakeEvent.SLEEP
    assert gate.feed(WakeSample("on", 112), 112) is WakeEvent.RESUME


@pytest.mark.parametrize("now", [float("nan"), 99.0])
def test_invalid_wall_clock_also_spends_the_initial_opportunity(now: float) -> None:
    gate = WakeGate(100, initial_on=True)
    assert gate.feed(WakeSample("on", 90), now) is WakeEvent.NONE
    assert gate.feed(WakeSample("on", 90), 105) is WakeEvent.NONE


def test_initial_attempt_shares_six_attempt_cap_with_later_real_edges() -> None:
    gate = WakeGate(100, initial_on=True)
    assert gate.feed(WakeSample("on", 50), 100) is WakeEvent.RESUME
    for index in range(6):
        now = 101 + index * 2
        assert gate.feed(WakeSample("off", now), now) is WakeEvent.SLEEP
        assert gate.feed(WakeSample("on", now + 1), now + 1) is (
            WakeEvent.RESUME if index < 5 else WakeEvent.NONE
        )


def test_opted_out_gate_and_first_on_after_a_failed_read_stay_passive() -> None:
    for gate in (WakeGate(100), WakeGate(100, initial_on=False)):
        assert gate.feed(WakeSample("on", 99), 100) is WakeEvent.NONE
    gate = WakeGate(100, initial_on=True)
    assert gate.feed(None, 100) is WakeEvent.NONE
    assert gate.feed(WakeSample("on", 105), 105) is WakeEvent.NONE


def test_new_process_has_one_new_explicitly_opted_in_initial_attempt() -> None:
    sample = WakeSample("on", 50)
    for started in (100, 200):
        gate = WakeGate(started, initial_on=True)
        assert gate.feed(sample, started) is WakeEvent.RESUME
        assert gate.feed(sample, started + 1) is WakeEvent.NONE


def test_real_monitor_passes_initial_opt_in_but_keeps_ha_poll_cadence() -> None:
    now = 100.0
    reads: list[float] = []

    def read() -> WakeSample:
        reads.append(now)
        return WakeSample("on", 10)

    monitor = WakeMonitor(read, lambda: now, lambda: now, initial_on=True)
    assert monitor.poll() is WakeEvent.NONE
    now = 101
    assert monitor.poll() is WakeEvent.NONE
    now = 105
    assert monitor.poll() is WakeEvent.NONE
    now = 110
    assert monitor.poll() is WakeEvent.RESUME
    now = 115
    assert monitor.poll() is WakeEvent.NONE
    assert reads == [100, 105, 110, 115]


def test_queued_send_supersedes_initial_gate_before_a_read() -> None:
    rig = ControllerRig()
    monitor = WakeMonitor(lambda: WakeSample("on", 50), lambda: 100, lambda: 100, initial_on=True)
    controller = EventController(
        send=rig.send,
        source=rig.rig.backend,
        publish=rig.publish,
        claim=rig.claim,
        stopped=lambda: rig.stopped,
        prepare_resume=lambda: True,
        monitor_wake=monitor.poll,
        supersede_wake=monitor.supersede,
    )
    received = 0

    def receive(_timeout: float) -> Command | None:
        nonlocal received
        received += 1
        if received == 1:
            assert not rig.rig.session.starts
            return command(Action.NEW_ARTWORK)
        rig.stopped = True
        return None

    serve(controller, receive, lambda: rig.stopped)
    assert rig.sent == 1
    assert len(rig.rig.session.starts) == 1
