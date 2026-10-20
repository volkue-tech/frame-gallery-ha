"""Offline startup/send arbitration; fake clock and I/O, session H2 guard active."""

from __future__ import annotations

import pytest
from tests.support.clock import FakeClock

from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command, Observation, Status
from frame_gallery.observer.service import serve
from frame_gallery.observer.wake import WakeEvent, WakeGate, WakeMonitor, WakeSample


class StartupRig:
    def __init__(self, *, initial_on: bool = True) -> None:
        self.clock = FakeClock(start=0)
        self.stopped = False
        self.claimed: set[str] = set()
        self.trace: list[tuple[str, float]] = []
        self.published: list[Observation] = []
        self.code = 0
        self.start_status = Status.CHECKING
        self.stop_error = False
        self.sample: WakeSample | None = WakeSample("on", self.wall() - 3600)
        self.reads = 0
        self.monitor = WakeMonitor(
            self.read, self.clock.monotonic, self.wall, initial_on=initial_on
        )
        self.controller = EventController(
            send=self.send,
            source=self,
            publish=self.published.append,
            claim=self.claim,
            stopped=lambda: self.stopped,
            prepare_resume=lambda: True,
            monitor_wake=self.monitor.poll,
            supersede_wake=self.monitor.supersede,
        )

    def wall(self) -> float:
        return self.clock.utc_now().timestamp()

    def read(self) -> WakeSample | None:
        self.reads += 1
        return self.sample

    def start(self) -> Observation:
        self.trace.append(("read", self.clock.elapsed))
        return Observation(self.start_status)

    def update(self) -> None:
        return None

    def stop(self) -> None:
        self.trace.append(("reap", self.clock.elapsed))
        if self.stop_error:
            raise RuntimeError("synthetic unreaped worker")

    def send(self) -> int:
        self.trace.append(("send", self.clock.elapsed))
        # A real send lasts longer than the startup grace; a failed send must
        # not accidentally re-arm the initial read when it eventually returns.
        self.clock.advance(20)
        return self.code

    def claim(self, command: Command) -> bool:
        if command.request_id in self.claimed:
            return False
        self.claimed.add(command.request_id)
        return True

    def request(self, action: Action = Action.NEW_ARTWORK, key: str = "startup_001") -> Command:
        return Command(action, key, self.wall())

    def run(self, at: float | None, action: Action = Action.NEW_ARTWORK) -> None:
        issued = False

        def receive(timeout: float) -> Command | None:
            nonlocal issued
            self.clock.advance(timeout)
            if at is not None and not issued and self.clock.elapsed >= at:
                issued = True
                return self.request(action)
            if self.clock.elapsed >= 40:
                self.stopped = True
            return None

        serve(self.controller, receive, lambda: self.stopped)


@pytest.mark.parametrize("initial_on", [False, True])
@pytest.mark.parametrize("at", [0, 2, 5, 9.5, 10])
@pytest.mark.parametrize("code", [0, 1])
def test_startup_dashboard_send_has_no_read_before_delivery_or_failed_send_retry(
    initial_on: bool, at: float, code: int
) -> None:
    r = StartupRig(initial_on=initial_on)
    r.code = code
    r.run(at)
    assert [event for event, _ in r.trace if event != "reap"] == (
        ["send", "read"] if code == 0 else ["send"]
    )
    assert r.published[-1].status is Status.PAUSED


@pytest.mark.parametrize("status", [Status.UNAVAILABLE, Status.NOT_AUTHORIZED])
def test_failed_post_send_read_does_not_fall_back_to_startup_read(status: Status) -> None:
    r = StartupRig()
    r.start_status = status
    r.run(2)
    assert [event for event, _ in r.trace if event != "reap"] == ["send", "read"]


@pytest.mark.parametrize("at", [None, 2])
def test_standalone_start_or_refresh_keeps_one_delayed_initial_read(at: float | None) -> None:
    r = StartupRig()
    r.run(at, Action.REFRESH_CURRENT)
    assert [event for event, _ in r.trace if event != "reap"] == ["read"]
    assert next(when for event, when in r.trace if event == "read") >= 10
    assert r.reads <= 8  # the old five-second Core cadence, never TV polling


def test_duplicate_command_does_not_create_or_postpone_startup_attempt() -> None:
    r = StartupRig()
    r.claimed.add("startup_001")
    r.run(2)
    assert [event for event, _ in r.trace if event != "reap"] == ["read"]
    assert next(when for event, when in r.trace if event == "read") >= 10


@pytest.mark.parametrize(
    "sample", [None, WakeSample("off", 0), WakeSample("unknown", 0), WakeSample("on", float("inf"))]
)
def test_changed_or_invalid_core_state_cancels_deferred_start(sample: WakeSample | None) -> None:
    r = StartupRig()
    assert r.monitor.poll() is WakeEvent.NONE
    r.clock.advance(5)
    if sample and sample.changed == 0:
        sample = WakeSample(sample.state, r.wall())
    r.sample = sample
    assert r.monitor.poll() is (
        WakeEvent.SLEEP if sample and sample.state == "off" else WakeEvent.NONE
    )
    r.clock.advance(5)
    r.sample = WakeSample("on", r.wall() - 3600)
    assert r.monitor.poll() is WakeEvent.NONE


def test_pending_initial_is_discarded_after_observation_gap() -> None:
    r = StartupRig()
    assert r.monitor.poll() is WakeEvent.NONE
    r.clock.advance(16)
    assert r.monitor.poll() is WakeEvent.NONE
    r.clock.advance(5)
    assert r.monitor.poll() is WakeEvent.NONE


def test_explicit_send_supersedes_initial_and_old_off_but_not_a_later_real_wake() -> None:
    r = StartupRig()
    r.sample = WakeSample("off", r.wall())
    r.controller.tick()
    r.code = 1
    r.controller.command(r.request())
    r.sample = WakeSample("on", r.wall())
    r.controller.tick()
    assert [event for event, _ in r.trace if event != "reap"] == ["send"]
    r.clock.advance(5)
    r.sample = WakeSample("off", r.wall())
    r.controller.tick()
    r.clock.advance(5)
    r.sample = WakeSample("on", r.wall())
    r.controller.tick()
    assert [event for event, _ in r.trace if event != "reap"] == ["send", "read"]


def test_supersession_does_not_clear_attempt_budget() -> None:
    gate = WakeGate(100, initial_on=True)
    assert gate.feed(WakeSample("on", 90), 100) is WakeEvent.RESUME
    for index in range(6):
        gate.supersede()
        now = 101 + index * 2
        assert gate.feed(WakeSample("off", now), now) is WakeEvent.SLEEP
        assert gate.feed(WakeSample("on", now + 1), now + 1) is (
            WakeEvent.RESUME if index < 5 else WakeEvent.NONE
        )


def test_unreaped_source_still_blocks_delivery_after_consuming_startup() -> None:
    r = StartupRig()
    r.stop_error = True
    with pytest.raises(RuntimeError, match="unreaped"):
        r.controller.command(r.request())
    r.stop_error = False
    r.clock.advance(20)
    r.controller.tick()
    assert not any(event in {"send", "read"} for event, _ in r.trace)


def test_shutdown_during_startup_wait_never_reads_or_sends() -> None:
    r = StartupRig()

    def receive(timeout: float) -> Command | None:
        r.clock.advance(timeout)
        r.stopped = True
        return r.request()

    serve(r.controller, receive, lambda: r.stopped)
    assert r.trace == [("reap", 0.5)]


def test_queued_command_wins_even_if_grace_elapsed_before_receiving() -> None:
    r = StartupRig()
    r.clock.advance(11)
    r.run(0)
    assert [event for event, _ in r.trace if event != "reap"] == ["send", "read"]


def test_refresh_flood_cannot_extend_grace_or_reopen_an_initial_failure() -> None:
    r = StartupRig()
    r.start_status = Status.UNAVAILABLE

    def receive(timeout: float) -> Command | None:
        r.clock.advance(timeout)
        if r.clock.elapsed >= 40:
            r.stopped = True
        return r.request(Action.REFRESH_CURRENT, f"refresh_{int(r.clock.elapsed * 2):04d}")

    serve(r.controller, receive, lambda: r.stopped)
    assert [event for event, _ in r.trace if event != "reap"] == ["read"]
    assert next(when for event, when in r.trace if event == "read") <= 11


def test_later_send_reaps_an_already_established_receiver_before_sending() -> None:
    r = StartupRig()
    r.run(20)
    lifecycle = [event for event, _ in r.trace]
    assert lifecycle == ["read", "reap", "send", "read", "reap"]
    # This is a later user action, not an indefinitely postponed initial read.
    assert next(when for event, when in r.trace if event == "read") < 20


def test_missing_first_core_state_is_not_retried_at_end_of_grace() -> None:
    r = StartupRig()
    r.sample = None
    assert r.monitor.poll() is WakeEvent.NONE
    for _ in range(4):
        r.clock.advance(5)
        r.sample = WakeSample("on", r.wall() - 3600)
        assert r.monitor.poll() is WakeEvent.NONE
