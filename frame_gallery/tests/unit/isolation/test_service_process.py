from __future__ import annotations

import json
import os
import signal
import subprocess
from collections.abc import Iterator

import pytest

from frame_gallery.isolation.process import DeliveryProcess, ServiceInput
from frame_gallery.observer.model import Action, Command


@pytest.fixture
def pipe() -> Iterator[tuple[ServiceInput, int]]:
    read, write = os.pipe()
    try:
        yield ServiceInput(read), write
    finally:
        os.close(read)
        os.close(write)


def encoded() -> bytes:
    return (
        json.dumps(
            {"command": "new_artwork", "request_id": "request_123", "issued_at": 42}
        ).encode()
        + b"\n"
    )


def test_input_accepts_only_bounded_json(pipe: tuple[ServiceInput, int]) -> None:
    reader, write = pipe
    assert reader.receive(0) is None
    raw = encoded()
    os.write(write, raw[:20])
    assert reader.receive(0) is None
    os.write(write, raw[20:] + b"[]\n" + b"{bad\n")
    assert reader.receive(0) == Command(Action.NEW_ARTWORK, "request_123", 42)
    assert reader.receive(0) is None
    assert reader.receive(0) is None


def test_oversized_lines_are_discarded_not_executed(pipe: tuple[ServiceInput, int]) -> None:
    reader, write = pipe
    os.write(write, b"x" * 1025)
    assert reader.receive(0) is None
    os.write(write, b"still bad\n")
    assert reader.receive(0) is None
    os.write(write, b"x" * 1024 + b"\n")
    assert reader.receive(0) is None
    os.write(write, encoded())
    assert reader.receive(0) == Command(Action.NEW_ARTWORK, "request_123", 42)


def test_eof_stops_service() -> None:
    read, write = os.pipe()
    os.close(write)
    try:
        reader = ServiceInput(read)
        assert reader.receive(0) is None
        assert reader.closed
    finally:
        os.close(read)


def test_oversize_split_across_reads_is_rejected(pipe: tuple[ServiceInput, int]) -> None:
    reader, write = pipe
    os.write(write, b"x" * 1024)
    assert reader.receive(0) is None
    os.write(write, b"x\n")
    assert reader.receive(0) is None


class Child:
    pid = 998877

    def __init__(self, *, hangs: bool = False) -> None:
        self.code: int | None = None
        self.signals: list[signal.Signals] = []
        self.waits: list[float] = []
        self.hangs = hangs

    def poll(self) -> int | None:
        return self.code

    def send_signal(self, value: signal.Signals) -> None:
        self.signals.append(value)

    def wait(self, *, timeout: float) -> int:
        self.waits.append(timeout)
        if self.hangs and timeout == 10:
            raise subprocess.TimeoutExpired("fixed command", timeout)
        self.code = -15 if self.signals else 0
        return self.code


@pytest.mark.parametrize(("stopped", "hangs"), [(False, False), (True, False), (True, True)])
def test_child_is_fixed_reaped_and_bounded(
    monkeypatch: pytest.MonkeyPatch, stopped: bool, hangs: bool
) -> None:
    child = Child(hangs=hangs)
    calls: list[tuple[object, dict[str, object]]] = []
    killed: list[tuple[int, signal.Signals]] = []

    def start(args: object, **kwargs: object) -> Child:
        calls.append((args, kwargs))
        return child

    monkeypatch.setattr(subprocess, "Popen", start)
    monkeypatch.setattr(os, "killpg", lambda pid, value: killed.append((pid, value)))

    def pause(_seconds: float) -> None:
        child.code = 0

    checks = 0

    def stopping() -> bool:
        nonlocal checks
        checks += 1
        return stopped and checks > 1

    result = DeliveryProcess({"PATH": "/usr/bin"}, stopping, pause=pause).run()
    args, kwargs = calls[0]
    assert isinstance(args, list)
    assert args[1:4] == ["-I", "-B", "-c"]
    assert "delivery_main" in str(args[4])
    assert kwargs["stdin"] == subprocess.DEVNULL
    assert kwargs["start_new_session"] is True
    assert killed == ([(child.pid, signal.SIGKILL)] if hangs else [])
    assert child.waits[-1] == 2
    assert result == (70 if hangs else -15 if stopped else 0)


def test_stopped_delivery_never_starts_a_process(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("stopped command must not spawn")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert DeliveryProcess({}, lambda: True).run() == 130


def test_child_deadline_sends_term_and_handles_already_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    child = Child(hangs=True)
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: child)

    def gone(_pid: int, _value: signal.Signals) -> None:
        raise ProcessLookupError

    monkeypatch.setattr(os, "killpg", gone)
    times = iter([0.0, 136.0])
    assert DeliveryProcess({}, lambda: False, monotonic=lambda: next(times)).run() == 70
    assert child.signals == [signal.SIGTERM]
