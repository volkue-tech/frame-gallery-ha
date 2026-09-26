"""The watchdog (§4.3, D-106, D-133). No test waits for real beyond ~10 ms."""

from __future__ import annotations

import inspect
import os
import threading
from collections.abc import Callable, Sequence

import pytest

from frame_gallery.budget.clock import SystemClock
from frame_gallery.budget.watchdog import WATCHDOG_EXIT_CODE, WATCHDOG_OUTCOME, Watchdog
from tests.support.clock import FakeClock

JOIN_S = 5.0
"""Upper bound for joining a thread; passing tests finish far sooner."""


class Recorder:
    """Records the watchdog's actions in order, from any thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.events: list[str] = []
        self.lines: list[str] = []
        self.exit_codes: list[int] = []
        self.exited = threading.Event()

    def _record(self, event: str) -> None:
        with self._lock:
            self.events.append(event)

    def callback(self, name: str) -> Callable[[], None]:
        return lambda: self._record(name)

    def emit_line(self, line: str) -> None:
        self._record("line")
        with self._lock:
            self.lines.append(line)

    def exit_process(self, code: int) -> None:
        self._record("exit")
        with self._lock:
            self.exit_codes.append(code)
        self.exited.set()


def _watchdog(
    recorder: Recorder,
    clock: FakeClock | SystemClock,
    fire_at: float,
    *,
    on_fire: Sequence[Callable[[], None]] | None = None,
    wait: Callable[[float], bool] | None = None,
    started_at: float | None = None,
) -> Watchdog:
    return Watchdog(
        clock=clock,
        fire_at=fire_at,
        on_fire=on_fire
        if on_fire is not None
        else [recorder.callback("kill_worker_group"), recorder.callback("remove_workspace")],
        emit_line=recorder.emit_line,
        exit_process=recorder.exit_process,
        wait=wait,
        started_at=started_at,
    )


def _thread(watchdog: Watchdog) -> threading.Thread | None:
    """Read afresh (mypy would keep an earlier narrowing of the property)."""
    return watchdog.thread


def _join(watchdog: Watchdog) -> None:
    thread = _thread(watchdog)
    assert thread is not None
    thread.join(JOIN_S)
    assert not thread.is_alive()


def test_constants() -> None:
    assert WATCHDOG_EXIT_CODE == 71
    assert WATCHDOG_OUTCOME == "watchdog_termination"


def test_the_default_exit_is_os_exit() -> None:
    assert inspect.signature(Watchdog).parameters["exit_process"].default is os._exit


def test_fires_when_the_time_has_already_passed() -> None:
    clock = FakeClock()
    recorder = Recorder()
    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 130.0)
    clock.advance(130.0)
    watchdog.arm()
    _join(watchdog)
    assert recorder.events == ["kill_worker_group", "remove_workspace", "line", "exit"]
    assert recorder.lines == ["outcome=watchdog_termination exit=71 elapsed=130.0"]
    assert recorder.exit_codes == [WATCHDOG_EXIT_CODE]
    assert watchdog.fired


def test_waits_for_the_remaining_time_then_fires() -> None:
    clock = FakeClock()
    recorder = Recorder()
    waits: list[float] = []

    def wait(seconds: float) -> bool:
        waits.append(seconds)
        clock.advance(seconds)
        return False

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 130.0, wait=wait)
    watchdog.arm()
    _join(watchdog)
    assert waits == [130.0]
    assert recorder.exit_codes == [71]
    assert recorder.lines == ["outcome=watchdog_termination exit=71 elapsed=130.0"]


def test_an_early_wakeup_waits_again_for_the_rest() -> None:
    clock = FakeClock()
    recorder = Recorder()
    waits: list[float] = []

    def wait(seconds: float) -> bool:
        waits.append(seconds)
        clock.advance(min(seconds, 100.0))
        return False

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 130.0, wait=wait)
    watchdog.arm()
    _join(watchdog)
    assert waits == [130.0, 30.0]
    assert recorder.exit_codes == [71]


def test_disarm_before_firing_prevents_it() -> None:
    clock = FakeClock()
    recorder = Recorder()
    waits: list[float] = []
    watchdog: Watchdog

    def wait(seconds: float) -> bool:
        waits.append(seconds)
        if len(waits) == 3:
            watchdog.disarm()
        return False

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 1e9, wait=wait)
    watchdog.arm()
    _join(watchdog)
    assert waits == [1e9, 1e9, 1e9]
    assert recorder.events == []
    assert not watchdog.fired


def test_disarm_from_another_thread_while_waiting() -> None:
    clock = FakeClock()
    recorder = Recorder()
    waiting = threading.Event()
    release = threading.Event()

    def wait(seconds: float) -> bool:
        waiting.set()
        return release.wait(JOIN_S)

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 1.0, wait=wait)
    watchdog.arm()
    assert waiting.wait(JOIN_S)
    watchdog.disarm()
    clock.advance(10.0)  # the deadline passes, but the watchdog is disarmed
    release.set()
    _join(watchdog)
    assert recorder.events == []


def test_disarm_does_not_stop_a_claimed_firing() -> None:
    # The contract the Phase 6 entry point relies on: after disarm(), a true
    # `fired` means the watchdog line and exit 71 are still coming, so the
    # entry point must wait instead of emitting its own summary line.
    clock = FakeClock()
    recorder = Recorder()
    firing = threading.Event()
    release = threading.Event()

    def kill_worker_group() -> None:
        firing.set()
        release.wait(JOIN_S)

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic(), on_fire=[kill_worker_group])
    watchdog.arm()
    assert firing.wait(JOIN_S)
    watchdog.disarm()  # returns while the claimed firing is still running
    assert watchdog.fired
    assert recorder.exit_codes == []
    release.set()
    _join(watchdog)
    assert recorder.lines == ["outcome=watchdog_termination exit=71 elapsed=0.0"]
    assert recorder.exit_codes == [WATCHDOG_EXIT_CODE]
    assert watchdog.fired


def test_disarm_in_time_leaves_fired_false_for_good() -> None:
    clock = FakeClock()
    recorder = Recorder()
    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 1.0)
    watchdog.arm()
    watchdog.disarm()
    assert not watchdog.fired
    clock.advance(10.0)
    _join(watchdog)
    assert not watchdog.fired
    assert recorder.events == []


def test_the_contract_is_documented() -> None:
    disarm_doc = inspect.getdoc(Watchdog.disarm) or ""
    fired_doc = inspect.getdoc(Watchdog.fired) or ""
    assert "never fires" not in disarm_doc
    assert "fired" in disarm_doc
    assert "summary line must not be emitted" in fired_doc


def test_the_default_wait_wakes_on_disarm() -> None:
    clock = FakeClock()
    recorder = Recorder()
    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 3600.0)
    watchdog.arm()
    watchdog.disarm()
    _join(watchdog)
    assert recorder.events == []


def test_fires_with_the_real_clock_and_default_wait() -> None:
    clock = SystemClock()
    recorder = Recorder()
    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 0.01)
    watchdog.arm()
    assert recorder.exited.wait(JOIN_S)
    _join(watchdog)
    assert recorder.exit_codes == [71]
    assert len(recorder.lines) == 1
    assert recorder.lines[0].startswith("outcome=watchdog_termination exit=71 elapsed=0.")


def test_disarm_is_idempotent() -> None:
    clock = FakeClock()
    recorder = Recorder()
    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic())
    watchdog.disarm()
    watchdog.disarm()
    watchdog.arm()
    assert watchdog.thread is None
    assert recorder.events == []


def test_arm_starts_one_daemon_thread() -> None:
    clock = FakeClock()
    recorder = Recorder()
    release = threading.Event()

    def wait(seconds: float) -> bool:
        return release.wait(JOIN_S)

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 60.0, wait=wait)
    assert _thread(watchdog) is None
    watchdog.arm()
    thread = _thread(watchdog)
    assert thread is not None
    assert thread.daemon
    assert thread.name == "frame-gallery-watchdog"
    watchdog.arm()
    assert _thread(watchdog) is thread
    watchdog.disarm()
    release.set()
    _join(watchdog)
    assert recorder.events == []


def test_a_failing_callback_does_not_stop_the_next() -> None:
    clock = FakeClock()
    recorder = Recorder()

    def failing() -> None:
        msg = "cannot kill the worker group"
        raise ProcessLookupError(msg)

    watchdog = _watchdog(
        recorder,
        clock,
        fire_at=clock.monotonic(),
        on_fire=[failing, recorder.callback("remove_workspace"), failing],
    )
    watchdog.arm()
    _join(watchdog)
    assert recorder.events == ["remove_workspace", "line", "exit"]
    assert recorder.exit_codes == [71]


def test_a_failing_emit_still_exits() -> None:
    clock = FakeClock()
    recorder = Recorder()

    def broken_emit(line: str) -> None:
        msg = "stderr closed"
        raise OSError(msg)

    watchdog = Watchdog(
        clock=clock,
        fire_at=clock.monotonic(),
        on_fire=[],
        emit_line=broken_emit,
        exit_process=recorder.exit_process,
    )
    watchdog.fire()
    assert recorder.exit_codes == [71]


def test_exit_happens_even_if_a_callback_raises_a_base_exception() -> None:
    clock = FakeClock()
    recorder = Recorder()

    def interrupted() -> None:
        raise KeyboardInterrupt

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic(), on_fire=[interrupted])
    with pytest.raises(KeyboardInterrupt):
        watchdog.fire()
    assert recorder.exit_codes == [71]
    assert recorder.lines == []


def test_fire_runs_at_most_once() -> None:
    clock = FakeClock()
    recorder = Recorder()
    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 1e9)
    watchdog.fire()
    watchdog.fire()
    assert recorder.events == ["kill_worker_group", "remove_workspace", "line", "exit"]
    assert recorder.exit_codes == [71]


def test_a_direct_fire_stops_the_waiting_thread() -> None:
    clock = FakeClock()
    recorder = Recorder()
    waiting = threading.Event()
    release = threading.Event()

    def wait(seconds: float) -> bool:
        waiting.set()
        return release.wait(JOIN_S)

    watchdog = _watchdog(recorder, clock, fire_at=clock.monotonic() + 1.0, wait=wait)
    watchdog.arm()
    assert waiting.wait(JOIN_S)
    watchdog.fire()
    clock.advance(10.0)
    release.set()
    _join(watchdog)
    assert recorder.exit_codes == [71]
    assert len(recorder.lines) == 1


def test_elapsed_is_measured_from_the_given_start() -> None:
    clock = FakeClock()
    recorder = Recorder()
    watchdog = _watchdog(
        recorder, clock, fire_at=clock.monotonic(), started_at=clock.monotonic() - 12.34
    )
    watchdog.fire()
    assert recorder.lines == ["outcome=watchdog_termination exit=71 elapsed=12.3"]
