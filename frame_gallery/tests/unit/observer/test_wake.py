"""Authored offline sleep/wake cases; not proof of physical no-wake behaviour."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from tests.unit.observer.test_events import SEEN, ControllerRig

from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Observation, Status
from frame_gallery.observer.wake import WakeEvent, WakeGate, WakeMonitor, WakeSample

ENTITY = "media_player.samsung_frame"


def sample(state: str, changed: float) -> WakeSample:
    return WakeSample(state, changed)


def test_valid_core_state_timestamp_is_preserved_not_refreshed() -> None:
    raw = {"entity_id": ENTITY, "state": "on", "last_changed": "2026-10-18T21:00:00+00:00"}
    value = WakeSample.from_json(raw, ENTITY)
    assert value == WakeSample("on", datetime(2026, 10, 18, 21, tzinfo=UTC).timestamp())


@pytest.mark.parametrize(
    "changes",
    [
        {"entity_id": "media_player.other"},
        {"state": None},
        {"state": []},
        {"state": 1},
        {"state": "playing"},
        {"state": "ON"},
        {"last_changed": None},
        {"last_changed": 1},
        {"last_changed": ""},
        {"last_changed": "x" * 65},
        {"last_changed": "2026-10-18T21:00:00"},
        {"last_changed": "not-a-date"},
        {"last_changed": "0001-01-01T00:00:00+00:00"},
    ],
)
def test_invalid_core_objects_cannot_authorize_an_edge(changes: dict[str, object]) -> None:
    raw = {"entity_id": ENTITY, "state": "on", "last_changed": "2026-10-18T21:00:00Z"}
    with pytest.raises(ValueError, match=r"wake|isoformat"):
        WakeSample.from_json({**raw, **changes}, ENTITY)
    with pytest.raises(ValueError, match="wake"):
        WakeSample.from_json([], ENTITY)


def test_boot_on_never_connects_and_fresh_off_on_is_consumed_once() -> None:
    gate = WakeGate(100)
    assert gate.feed(sample("on", 99), 100) is WakeEvent.NONE
    assert gate.feed(sample("on", 99), 105) is WakeEvent.NONE
    assert gate.feed(sample("off", 106), 106) is WakeEvent.SLEEP
    assert gate.feed(sample("on", 110), 111) is WakeEvent.RESUME
    for now in (111, 112, 115, 120, 125):
        assert gate.feed(sample("on", 110), now) is WakeEvent.NONE
    assert gate.feed(sample("off", 126), 126) is WakeEvent.SLEEP
    assert gate.feed(sample("on", 127), 128) is WakeEvent.RESUME


@pytest.mark.parametrize("interrupt", [None, sample("unknown", 102), sample("unavailable", 102)])
def test_missing_unknown_or_unavailable_clears_the_old_off(interrupt: WakeSample | None) -> None:
    gate = WakeGate(100)
    assert gate.feed(sample("off", 100), 100) is WakeEvent.SLEEP
    assert gate.feed(interrupt, 102) is WakeEvent.NONE
    assert gate.feed(sample("on", 103), 104) is WakeEvent.NONE


@pytest.mark.parametrize(
    ("initial", "following", "received"),
    [
        (sample("off", 100), sample("on", 99), 105),  # reordered
        (sample("off", 100), sample("on", 100), 105),  # conflicting same timestamp
        (sample("off", 100), sample("on", 106), 105),  # future
        (sample("off", 100), sample("on", 101), 132),  # stale and reader gap
        (sample("off", 99), sample("on", 99.5), 105),  # restored pre-boot on
        (sample("off", 100), sample("on", 104), 116),  # >15-second observation gap
        (sample("off", 100), sample("on", 99), 99),  # wall-clock rollback
        (sample("off", 100), sample("playing", 104), 105),
        (sample("off", 100), sample("on", float("nan")), 105),
        (sample("off", 100), sample("on", 104), float("nan")),
    ],
)
def test_invalid_stale_reordered_or_gapped_edge_never_resumes(
    initial: WakeSample, following: WakeSample, received: float
) -> None:
    gate = WakeGate(100)
    gate.feed(initial, 100)
    assert gate.feed(following, received) is WakeEvent.NONE


def test_stale_on_cannot_retry_later_or_replay_a_spent_off() -> None:
    gate = WakeGate(0)
    gate.feed(sample("off", 0), 100)
    gate.feed(sample("off", 0), 110)
    assert gate.feed(sample("on", 1), 111) is WakeEvent.NONE
    assert gate.feed(sample("on", 1), 112) is WakeEvent.NONE
    assert gate.feed(sample("off", 0), 113) is WakeEvent.NONE
    assert gate.feed(sample("on", 1), 114) is WakeEvent.NONE


def test_restarting_does_not_replay_a_previous_wake() -> None:
    old = WakeGate(90)
    old.feed(sample("off", 100), 100)
    assert old.feed(sample("on", 101), 102) is WakeEvent.RESUME
    restarted = WakeGate(103)
    assert restarted.feed(sample("on", 101), 103) is WakeEvent.NONE
    assert restarted.feed(sample("off", 100), 104) is WakeEvent.NONE
    assert restarted.feed(sample("on", 101), 105) is WakeEvent.NONE


def test_six_per_hour_limit_is_consumed_even_without_success() -> None:
    gate = WakeGate(100)
    for n in range(7):
        now = 100 + n * 2
        assert gate.feed(sample("off", now), now) is WakeEvent.SLEEP
        assert gate.feed(sample("on", now + 1), now + 1) is (
            WakeEvent.RESUME if n < 6 else WakeEvent.NONE
        )
    gate.feed(sample("off", 3700), 3700)
    assert gate.feed(sample("on", 3701), 3701) is WakeEvent.RESUME


def test_monitor_reads_only_at_its_bounded_ha_cadence() -> None:
    now = 100.0
    reads: list[float] = []

    def read() -> WakeSample:
        reads.append(now)
        return sample("off" if now == 100 else "on", now)

    monitor = WakeMonitor(read, lambda: now, lambda: now)
    assert monitor.poll() is WakeEvent.SLEEP
    now = 101
    assert monitor.poll() is WakeEvent.NONE
    now = 105
    assert monitor.poll() is WakeEvent.RESUME
    assert reads == [100, 105]


def test_controller_two_sleep_wake_cycles_never_call_sender_or_reuse_old_proof() -> None:
    rig = ControllerRig()
    edges = iter((WakeEvent.RESUME, WakeEvent.SLEEP, WakeEvent.NONE, WakeEvent.RESUME))
    rig.controller = EventController(
        send=rig.send,
        source=rig.rig.backend,
        publish=rig.publish,
        claim=rig.claim,
        stopped=lambda: rig.stopped,
        prepare_resume=lambda: True,
        monitor_wake=lambda: next(edges, WakeEvent.NONE),
    )
    c = rig.controller
    c.start()
    rig.rig.baseline()
    c.tick()
    assert rig.published[-1] == SEEN
    c.tick()
    assert rig.published[-1] == Observation(Status.PAUSED)
    c.tick()
    assert len(rig.rig.session.starts) == 1
    rig.rig.baseline()
    c.tick()
    assert rig.published[-1] == SEEN
    assert len(rig.rig.session.starts) == 2
    assert rig.sent == 0
    c.sleep()
    c.sleep()  # idempotent, no new socket


@pytest.mark.parametrize("problem", ["prepare", "prepare_stop", "publish_stop", "stopped", "start"])
def test_resume_failure_and_cancel_never_send_or_retry(problem: str) -> None:
    rig = ControllerRig()

    def prepare() -> bool:
        if problem == "prepare_stop":
            rig.stopped = True
        return problem != "prepare"

    def publish(seen: Observation) -> None:
        rig.publish(seen)
        if problem == "publish_stop":
            rig.stopped = True

    rig.stopped = problem == "stopped"
    if problem == "start":
        rig.rig.host.request = Observation(Status.NOT_AUTHORIZED)
    c = EventController(
        send=rig.send,
        source=rig.rig.backend,
        publish=publish,
        claim=rig.claim,
        stopped=lambda: rig.stopped,
        prepare_resume=prepare,
    )
    assert not c.resume()
    for _ in range(3):
        c.tick()
    assert len(rig.rig.session.starts) == 0
    assert rig.sent == 0


def test_already_active_or_stop_during_ha_read_prevents_parallel_resume() -> None:
    rig = ControllerRig()
    c = EventController(
        send=rig.send,
        source=rig.rig.backend,
        publish=rig.publish,
        claim=rig.claim,
        stopped=lambda: rig.stopped,
        prepare_resume=lambda: True,
    )
    assert c.resume()
    assert not c.resume()
    assert len(rig.rig.session.starts) == 1

    def read_and_stop() -> WakeEvent:
        rig.stopped = True
        return WakeEvent.RESUME

    c._monitor_wake = read_and_stop
    c.tick()
    assert len(rig.rig.session.starts) == 1
    assert rig.sent == 0
