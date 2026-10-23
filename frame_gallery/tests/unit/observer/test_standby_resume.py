"""D-250: injected cached HA only; no device/network transport."""

from __future__ import annotations

import pytest
from tests.unit.observer.test_events import ControllerRig, command

from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Observation, Status, StatusReason
from frame_gallery.observer.standby import StandbyResumeMonitor
from frame_gallery.observer.wake import WakeEvent, WakeSample


class Rig:
    def __init__(self, *, configured: bool = True) -> None:
        self.now, self.wall = 100.0, 1000.0
        self.sample: WakeSample | None = WakeSample("on", 900)
        self.reads, self.attempts = 0, 0
        self.denial: StatusReason | None = None
        self.monitor = StandbyResumeMonitor(
            self.read,
            lambda: self.now,
            lambda: self.wall,
            reserve=self.reserve,
            block_auth=lambda: None,
            clear_auth=lambda: True,
            configured=configured,
        )

    def read(self) -> WakeSample | None:
        self.reads += 1
        return self.sample

    def reserve(self, _wall: float) -> StatusReason | None:
        self.attempts += 1
        return self.denial

    def step(self, seconds: float = 5) -> WakeEvent:
        self.now += seconds
        self.wall += seconds
        return self.monitor.poll()

    def off(self) -> None:
        self.sample = WakeSample("off", self.wall)
        assert self.monitor.poll() is WakeEvent.SLEEP
        for _ in range(6):
            assert self.step() is WakeEvent.SLEEP

    def wake(self) -> None:
        self.now += 5
        self.wall += 5
        self.sample = WakeSample("on", self.wall)


def test_boot_on_and_unconfigured_never_connect() -> None:
    for configured in (False, True):
        r = Rig(configured=configured)
        for _ in range(100):
            assert r.step() is WakeEvent.NONE
        assert r.attempts == 0
        assert r.reads == (100 if configured else 0)


def test_one_settled_edge_is_consumed_no_retry_on_same_on() -> None:
    r = Rig()
    r.off()
    r.wake()
    assert r.monitor.poll() is WakeEvent.NONE
    assert r.monitor.take_status() is StatusReason.WAKE_SETTLING
    assert r.step() is WakeEvent.NONE
    assert r.step() is WakeEvent.RESUME
    assert r.attempts == 1
    for _ in range(100):
        assert r.step() is WakeEvent.NONE
    assert r.attempts == 1


@pytest.mark.parametrize("bad", [None, "unknown", "unavailable", "playing", "future", "old"])
def test_bad_sample_or_gap_cancels_old_edge(bad: str | None) -> None:
    r = Rig()
    r.off()
    r.sample = (
        None
        if bad is None
        else WakeSample(
            "on" if bad in {"future", "old"} else bad,
            r.wall + 50 if bad == "future" else (1 if bad == "old" else r.wall),
        )
    )
    assert r.step() is WakeEvent.SLEEP
    r.wake()
    for _ in range(4):
        assert r.step() is WakeEvent.NONE
    assert r.attempts == 0


def test_short_off_gap_and_superseded_edges_never_grant() -> None:
    for kind in ("short", "gap", "supersede"):
        r = Rig()
        if kind == "short":
            r.sample = WakeSample("off", r.wall)
            r.monitor.poll()
        else:
            r.off()
        if kind == "gap":
            assert r.step(16) is WakeEvent.SLEEP
        elif kind == "supersede":
            r.monitor.supersede()
        r.wake()
        for _ in range(5):
            assert r.step() is WakeEvent.NONE
        assert r.attempts == 0


@pytest.mark.parametrize(
    "denial",
    [StatusReason.RATE_LIMITED, StatusReason.BUDGET_UNAVAILABLE, StatusReason.TV_AUTHORIZATION],
)
def test_denied_reservation_consumes_edge(denial: StatusReason) -> None:
    r = Rig()
    r.denial = denial
    r.off()
    r.wake()
    for _ in range(10):
        assert r.step() is WakeEvent.NONE
    assert r.attempts == 1
    assert r.monitor.take_status() is denial


def test_clock_faults_and_auth_latch() -> None:
    r = Rig()
    r.off()
    r.now = float("nan")
    assert r.monitor.poll() is WakeEvent.SLEEP
    assert r.monitor.take_status() is StatusReason.HA_STATE_UNAVAILABLE
    r = Rig()
    r.monitor.observe(Observation(Status.NOT_AUTHORIZED))
    r.off()
    r.wake()
    for _ in range(5):
        assert r.step() is WakeEvent.NONE
    assert r.attempts == 0


def test_status_queue_is_changed_only_and_delivery_clears_auth_not_attempts() -> None:
    r = Rig()
    assert r.monitor.take_status() is StatusReason.WAITING_FOR_STANDBY
    assert r.monitor.take_status() is None
    r.monitor.observe(Observation(Status.NOT_AUTHORIZED))
    r.monitor.delivered()
    r.off()
    r.wake()
    assert r.monitor.poll() is WakeEvent.NONE
    assert r.step() is WakeEvent.NONE
    assert r.step() is WakeEvent.RESUME
    assert r.attempts == 1


@pytest.mark.parametrize("expiry", [0, 6, float("nan"), -1])
def test_grant_is_one_use_and_expires_before_worker_start(expiry: float) -> None:
    r = Rig()
    assert not r.monitor.claim()
    r.off()
    r.wake()
    r.monitor.poll()
    r.step()
    assert r.step() is WakeEvent.RESUME
    r.now = r.now + expiry if expiry != -1 else r.now - 1
    assert r.monitor.claim() is (expiry == 0)
    assert not r.monitor.claim()


@pytest.mark.parametrize("change", ["timestamp", "wall_jump", "wall_back", "old_on", "off_reset"])
def test_settling_rejects_hidden_changes_and_clock_discontinuity(change: str) -> None:
    r = Rig()
    r.off()
    if change == "off_reset":
        r.sample = WakeSample("off", r.wall + 5)
        r.step()
    r.wake()
    if change == "old_on":
        r.sample = WakeSample("on", r.wall - 25)
    r.monitor.poll()
    if change == "timestamp":
        r.sample = WakeSample("on", r.wall + 5)
    elif change == "wall_jump":
        r.wall += 3
    elif change == "wall_back":
        r.wall -= 10
    for _ in range(5):
        assert r.step() is not WakeEvent.RESUME
    assert r.attempts == 0


def test_core_cadence_and_failed_auth_clear_never_open_a_session() -> None:
    r = Rig()
    r.monitor.poll()
    assert r.step(1) is WakeEvent.NONE
    assert r.reads == 1
    r.monitor._clear_auth = lambda: False
    r.monitor.delivered()
    r.now += 5
    r.wall += 5
    r.off()
    r.wake()
    for _ in range(5):
        assert r.step() is WakeEvent.NONE
    assert r.attempts == 0


@pytest.mark.parametrize("success", [False, True])
def test_explicit_send_supersedes_pending_wake_without_double_initialization(success: bool) -> None:
    r, source = Rig(), ControllerRig()
    controller = EventController(
        send=source.send if success else lambda: 1,
        source=source.rig.backend,
        publish=source.publish,
        claim=source.claim,
        stopped=lambda: False,
        monitor_wake=r.monitor.poll,
        supersede_wake=r.monitor.supersede,
        prepare_resume=r.monitor.claim,
    )
    r.off()
    r.wake()
    r.monitor.poll()
    r.step()
    controller.command(command())
    for _ in range(5):
        r.now += 5
        r.wall += 5
        controller.tick()
    assert r.attempts == 0
    assert len(source.rig.session.starts) == int(success)


def test_shutdown_during_sleep_publication_prevents_any_further_processing() -> None:
    source = ControllerRig()
    stopping = False

    def publish(seen: Observation) -> None:
        nonlocal stopping
        stopping = seen.status is Status.PAUSED

    controller = EventController(
        send=source.send,
        source=source.rig.backend,
        publish=publish,
        claim=source.claim,
        stopped=lambda: stopping,
        monitor_wake=lambda: WakeEvent.SLEEP,
    )
    assert controller.command(command())
    assert stopping
    assert not controller._active
