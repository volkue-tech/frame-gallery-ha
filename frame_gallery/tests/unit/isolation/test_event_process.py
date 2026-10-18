from __future__ import annotations

import os
import threading
import time
from collections.abc import Sequence
from types import SimpleNamespace
from typing import Any, cast

import pytest

import frame_gallery.isolation.process as module
from frame_gallery.isolation.executor import (
    EventSink,
    IsolationFailure,
    JsonObject,
    StopCheck,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.isolation.process import ProcessExecutor, SessionProcess
from frame_gallery.observer.stream import MAX_EVENTS, SESSION_S, START_S
from tests.support.processes import require, worker_executor


class FakeExecutor(ProcessExecutor):
    def __init__(self) -> None:
        self.calls: list[JsonObject] = []
        self.error: Exception | None = None
        self.response: JsonObject = {"status": "paused"}
        self.kill_calls = 0
        self.is_idle = True

    @property
    def idle(self) -> bool:
        return self.is_idle

    def terminate_all(self) -> None:
        self.kill_calls += 1

    def try_terminate(self) -> bool:
        self.kill_calls += 1
        return True

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
        files: Sequence[int] = (),
    ) -> JsonObject:
        assert task == "observe_session"
        assert timeout == SESSION_S + START_S
        assert files
        assert payload["cancel_fd"] == files[0]
        assert on_event is not None
        assert should_stop is not None
        self.calls.append(payload)
        if self.error is not None:
            raise self.error
        on_event({"kind": "baseline", "observation": {}})
        return self.response


def test_start_result_and_fds_closed() -> None:
    executor = FakeExecutor()
    source = SessionProcess(executor, time.monotonic)
    source.start({"host": "192.168.1.20"})
    assert source._thread is not None
    source._thread.join(1)
    assert not source._thread.is_alive()
    first, second = source.poll(), source.poll()
    assert first is not None
    assert first[0]["kind"] == "baseline"
    assert second is not None
    assert second[0] == {"kind": "end", "status": "paused"}
    assert source.poll() is None
    fd = executor.calls[0]["cancel_fd"]
    assert isinstance(fd, int)
    with pytest.raises(OSError, match="Bad file descriptor"):
        os.fstat(fd)
    source.stop()
    source.stop()


@pytest.mark.parametrize(
    "error",
    [
        WorkerError(WorkerErrorKind.CRASH),
        IsolationFailure("bad"),
        OSError("bad"),
        ValueError("bad"),
    ],
)
def test_failure_does_not_leak_or_reconnect(error: Exception) -> None:
    executor = FakeExecutor()
    executor.error = error
    source = SessionProcess(executor, lambda: 0)
    r, w = os.pipe()
    try:
        source._run({"cancel_fd": r}, r)
        assert source.poll() == ({"kind": "end", "status": "unavailable"}, 0)
    finally:
        os.close(w)


@pytest.mark.parametrize("result", [{}, {"status": []}, {"status": "unexpected"}])
def test_bad_terminal_response(result: JsonObject) -> None:
    executor = FakeExecutor()
    executor.response = result
    source = SessionProcess(executor, lambda: 0)
    r, w = os.pipe()
    try:
        source._run({"cancel_fd": r}, r)
        item = source.poll()
        assert item is not None
        assert item[0]["kind"] == "baseline"
        assert source.poll() == ({"kind": "end", "status": "unavailable"}, 0)
    finally:
        os.close(w)


def test_bounded_queue_and_start_deadline() -> None:
    now = [0.0]
    source = SessionProcess(FakeExecutor(), lambda: now[0])
    assert not source._expired()
    now[0] = START_S
    assert source._expired()
    source._event({"kind": "baseline"})
    assert not source._expired()
    for _ in range(MAX_EVENTS - 1):
        source._event({"kind": "change"})
    with pytest.raises(ValueError, match="queue"):
        source._event({"kind": "change"})
    item = source.poll()
    assert item is not None
    assert item[0] == {"kind": "end", "status": "unavailable"}
    assert source.poll() is None
    source._force.set()
    assert source._expired()
    source.stop()


class Thread:
    def __init__(self, alive: list[bool]) -> None:
        self.alive = alive
        self.joins: list[float] = []

    def join(self, timeout: float) -> None:
        self.joins.append(timeout)

    def is_alive(self) -> bool:
        return self.alive.pop(0) if len(self.alive) > 1 else self.alive[0]


def test_stop_forces_then_refuses_to_replace_unreaped() -> None:
    executor = FakeExecutor()
    source = SessionProcess(executor, lambda: 0)
    thread = Thread([True, False])
    source._thread = cast(threading.Thread, thread)
    source.stop()
    assert executor.kill_calls == 1
    thread = Thread([True])
    source._thread = cast(threading.Thread, thread)
    with pytest.raises(IsolationFailure):
        source.stop()
    assert source._thread is not None
    thread.alive = [False]
    executor.is_idle = False
    with pytest.raises(IsolationFailure):
        source.stop()
    executor.is_idle = True
    source.stop()


@pytest.mark.parametrize("stage", ["blocking", "thread_start", "thread_create"])
def test_start_failure_closes_both_pipe_ends(stage: str, monkeypatch: pytest.MonkeyPatch) -> None:
    source = SessionProcess(FakeExecutor(), lambda: 0)
    r, w = os.pipe()
    monkeypatch.setattr(os, "pipe", lambda: (r, w))

    def fail(*_a: object, **_kw: object) -> None:
        raise OSError("synthetic")

    if stage == "blocking":
        monkeypatch.setattr(os, "set_blocking", fail)
    elif stage == "thread_create":
        monkeypatch.setattr(threading, "Thread", fail)
    else:
        monkeypatch.setattr(threading.Thread, "start", fail)
    with pytest.raises(OSError, match="synthetic"):
        source.start({})
    for fd in (r, w):
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(fd)


def test_executor_initial_idle() -> None:
    assert worker_executor().idle


def test_nonblocking_terminate_respects_reap_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    executor = worker_executor()
    assert executor.try_terminate()
    executor._lock.acquire()
    try:
        assert not executor.try_terminate()
    finally:
        executor._lock.release()
    sent: list[object] = []
    monkeypatch.setattr(module, "_signal", sent.append)
    worker: Any = SimpleNamespace(reaped=False)
    executor._active = worker
    assert executor.try_terminate()
    assert sent == [worker]
    worker.reaped = True
    assert executor.try_terminate()
    assert len(sent) == 1
    executor._active = None


def is_idle(executor: ProcessExecutor) -> bool:
    return executor.idle


def test_real_process_session_cancel_reap_and_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    require("unprivileged")
    monkeypatch.setenv("SUPERVISOR_TOKEN", "offline-synthetic-supervisor")
    executor = worker_executor()
    session = SessionProcess(executor, time.monotonic)
    session.start({})
    deadline = time.monotonic() + 4
    first = None
    try:
        while time.monotonic() < deadline:
            first = session.poll()
            if first is not None:
                break
            time.sleep(0.01)
        assert first is not None
        assert first[0] == {"kind": "baseline", "observation": {"synthetic": True}}
        assert not executor.idle
    finally:
        session.stop()
    assert is_idle(executor)
    assert session.poll() is None
