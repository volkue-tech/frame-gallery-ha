"""D-247 stop-only HA signals; no device I/O or physical no-wake claim."""

from __future__ import annotations

import pytest
from tests.unit.observer.test_events import SEEN, ControllerRig, command

from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Status
from frame_gallery.observer.wake import CachedStateStopMonitor, WakeEvent, WakeSample


class StopRig:
    def __init__(self, *, enabled: bool = True) -> None:
        self.now = 100.0
        self.wall = 1000.0
        self.sample: WakeSample | None = WakeSample("on", 10)
        self.reads = 0
        self.monitor = CachedStateStopMonitor(
            self.read, lambda: self.now, lambda: self.wall, enabled=enabled
        )

    def read(self) -> WakeSample | None:
        self.reads += 1
        return self.sample


def test_unconfigured_stop_monitor_does_not_even_read_core() -> None:
    r = StopRig(enabled=False)
    for _ in range(100):
        assert r.monitor.poll() is WakeEvent.NONE
        r.now += 60
    assert r.reads == 0


@pytest.mark.parametrize(
    "sample",
    [
        None,
        WakeSample("off", 50),
        WakeSample("unknown", 50),
        WakeSample("unavailable", 50),
        WakeSample("playing", 50),
        WakeSample("on", 1001),
        WakeSample("on", -1),
        WakeSample("on", float("nan")),
        WakeSample("on", float("inf")),
    ],
)
def test_missing_off_or_invalid_cached_state_only_stops(sample: WakeSample | None) -> None:
    r = StopRig()
    r.sample = sample
    assert r.monitor.poll() is WakeEvent.SLEEP
    r.now += 5
    r.sample = WakeSample("on", r.wall)
    assert r.monitor.poll() is WakeEvent.NONE  # NEVER resume from the following on


def test_valid_on_is_not_a_connection_grant_and_core_cadence_stays_bounded() -> None:
    r = StopRig()
    assert r.monitor.poll() is WakeEvent.NONE
    r.now += 1
    assert r.monitor.poll() is WakeEvent.NONE
    assert r.reads == 1
    r.now += 4
    assert r.monitor.poll() is WakeEvent.NONE
    assert r.reads == 2
    r.now += 16
    assert r.monitor.poll() is WakeEvent.SLEEP  # observation gap disarms
    r.now += 5
    assert r.monitor.poll() is WakeEvent.NONE


@pytest.mark.parametrize("now", [-1.0, float("nan"), float("inf"), 99.0])
def test_broken_or_backwards_monotonic_clock_fails_closed(now: float) -> None:
    r = StopRig()
    assert r.monitor.poll() is WakeEvent.NONE
    r.now = now
    assert r.monitor.poll() is WakeEvent.SLEEP
    assert r.reads == 1


@pytest.mark.parametrize("wall", [float("nan"), float("inf"), -1.0])
def test_invalid_wall_clock_cannot_keep_a_session_authorized(wall: float) -> None:
    r = StopRig()
    r.wall = wall
    assert r.monitor.poll() is WakeEvent.SLEEP


@pytest.mark.parametrize("state", [None, "off", "unknown", "unavailable"])
def test_after_explicit_send_failed_ha_evidence_closes_without_automatic_recovery(
    state: str | None,
) -> None:
    r, old = StopRig(), ControllerRig()
    controller = EventController(
        send=old.send,
        source=old.rig.backend,
        publish=old.publish,
        claim=old.claim,
        stopped=lambda: old.stopped,
        monitor_wake=r.monitor.poll,
    )
    controller.start()
    controller.command(command())
    assert old.sent == len(old.rig.session.starts) == 1
    old.rig.baseline()
    controller.tick()
    assert old.published[-1] == SEEN
    r.now += 5
    r.sample = None if state is None else WakeSample(state, r.wall)
    controller.tick()
    assert old.published[-1].status is Status.PAUSED
    assert not controller._active
    for index in range(24):
        r.now += 5
        r.sample = WakeSample("on", r.wall)
        controller.tick()
        controller.command(command(Action.REFRESH_CURRENT, f"safe_refresh_{index:03d}"))
    assert not controller.resume()
    assert old.sent == len(old.rig.session.starts) == 1
    assert old.published[-1].status is Status.PAUSED


def test_eight_virtual_hours_of_boot_on_and_sleep_wake_cycles_never_grant_resume() -> None:
    r = StopRig()
    outcomes = []
    for second in range(0, 8 * 3600, 5):
        r.now = 100.0 + second
        r.wall = 1000.0 + second
        state = "off" if second % 600 >= 500 else "on"
        r.sample = WakeSample(state, r.wall)
        outcomes.append(r.monitor.poll())
    assert set(outcomes) == {WakeEvent.NONE, WakeEvent.SLEEP}
    assert r.reads == 5760


def test_auth_revocation_in_a_passive_session_latches_even_an_injected_resume_hook() -> None:
    r = ControllerRig()
    controller = EventController(
        send=r.send,
        source=r.rig.backend,
        publish=r.publish,
        claim=r.claim,
        stopped=lambda: r.stopped,
        prepare_resume=lambda: pytest.fail("Authorization refusal must latch before preparation"),
    )
    controller.command(command())
    assert len(r.rig.session.starts) == 1
    r.rig.add({"kind": "end", "status": "not_authorized"})
    controller.tick()
    assert r.published[-1].status is Status.NOT_AUTHORIZED
    assert not controller._active
    assert not controller.resume()
    controller.command(command(Action.REFRESH_CURRENT, "auth_refresh_001"))
    assert r.sent == len(r.rig.session.starts) == 1
