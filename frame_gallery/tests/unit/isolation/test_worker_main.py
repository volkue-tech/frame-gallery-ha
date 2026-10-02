"""The worker's entry point, in-process over real pipes (isolation/worker_main.py; D-163).

``main`` runs in this process with a fake OS for the bootstrap and an exit
function that raises instead of ending the process.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NoReturn

import pytest

from frame_gallery.isolation import bootstrap, worker_main
from frame_gallery.isolation.executor import EventSink, JsonObject
from frame_gallery.isolation.framing import FrameBuffer, encode_frame
from frame_gallery.isolation.launch import Channels, ExitCode, WorkerConfig
from frame_gallery.isolation.worker_main import main, result_fd, usage
from tests.unit.isolation.test_bootstrap import FakeOs, config


class Exited(Exception):
    def __init__(self, code: int) -> None:
        super().__init__(code)
        self.code = code


def fake_exit(code: int) -> NoReturn:
    raise Exited(code)


class Worker:
    """The pipes of one worker, and a fake task module."""

    def __init__(self) -> None:
        self.request_r, self.request_w = os.pipe()
        self.results_r, self.results_w = os.pipe()
        self.module = types.ModuleType("frame_gallery.fake_worker_tasks")
        sys.modules[self.module.__name__] = self.module

    def config(self, function: str = "task", *, events: bool = False, **changes: Any) -> str:
        return config(
            module=self.module.__name__,
            function=function,
            events=events,
            fds=Channels(self.request_r, self.results_w, 99),
            **changes,
        ).to_json()

    def request(self, payload: JsonObject) -> None:
        os.write(self.request_w, encode_frame({"type": "request", "payload": payload}))

    def run(self, text: str, ops: FakeOs | None = None) -> int:
        with pytest.raises(Exited) as caught:
            main(text, ops=ops or FakeOs(), exit_=fake_exit)
        return caught.value.code

    def messages(self) -> list[JsonObject]:
        os.close(self.results_w)
        data = b""
        while chunk := os.read(self.results_r, 65536):
            data += chunk
        return FrameBuffer().feed(data)

    def close(self) -> None:
        del sys.modules[self.module.__name__]
        for fd in (self.request_r, self.request_w, self.results_r, self.results_w):
            with contextlib.suppress(OSError):
                os.close(fd)


@pytest.fixture
def worker() -> Iterator[Worker]:
    made = Worker()
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    try:
        yield made
    finally:
        made.close()
        for handler in list(root.handlers):
            root.removeHandler(handler)
        for handler in handlers:
            root.addHandler(handler)
        root.setLevel(level)
        worker_main._result_fd = None


def kinds(messages: list[JsonObject]) -> list[object]:
    return [message["type"] for message in messages]


def test_a_task_runs_after_ready_and_its_result_is_sent(worker: Worker) -> None:
    worker.module.task = lambda payload: {"doubled": payload["n"] * 2}  # type: ignore[attr-defined]
    worker.request({"n": 21})
    assert worker.run(worker.config()) == 0
    messages = worker.messages()
    assert kinds(messages) == ["ready", "result"]
    report = messages[0]["report"]
    assert isinstance(report, dict)
    assert report["uid"] == 65534
    assert messages[1]["result"] == {"doubled": 42}
    usage_data = messages[1]["usage"]
    assert isinstance(usage_data, dict)
    assert set(usage_data) == {"max_rss_bytes", "max_vm_bytes", "cpu_s"}
    assert result_fd() == worker.results_w


def test_an_event_task_gets_a_sink(worker: Worker) -> None:
    def task(payload: JsonObject, emit: EventSink) -> JsonObject:
        emit({"marker": "connected"})
        logging.getLogger("frame_gallery.tv.worker").warning("after the event")
        return {"ok": payload["x"]}

    worker.module.task = task  # type: ignore[attr-defined]
    worker.request({"x": True})
    assert worker.run(worker.config(events=True)) == 0
    messages = worker.messages()
    assert kinds(messages) == ["ready", "event", "log", "result"]
    assert messages[1] == {"type": "event", "event": {"marker": "connected"}}


def test_a_refusal_is_reported_before_exit(worker: Worker) -> None:
    ops = FakeOs()
    ops.ppid = 1
    assert worker.run(worker.config(), ops) == ExitCode.REFUSED
    assert worker.messages() == [{"type": "refused", "reason": "parent_gone"}]


def test_an_invalid_configuration_refuses_at_once(worker: Worker) -> None:
    assert worker.run("{}") == ExitCode.REFUSED
    assert worker.messages() == []


@pytest.mark.parametrize(
    "request_bytes",
    [
        b"",
        encode_frame({"type": "result", "payload": {}}),
        encode_frame({"type": "request", "payload": []}),
        encode_frame({"type": "request"}),
        b"\x00\x00\x00\x05{bad}",
    ],
)
def test_an_unreadable_request_ends_the_worker(worker: Worker, request_bytes: bytes) -> None:
    os.write(worker.request_w, request_bytes)
    os.close(worker.request_w)
    assert worker.run(worker.config()) == ExitCode.CHANNEL
    assert kinds(worker.messages()) == ["ready"]


@pytest.mark.parametrize(
    ("error", "code", "kind", "detail"),
    [
        (RuntimeError("x"), ExitCode.CRASH, "crash", "RuntimeError"),
        (SystemExit(3), ExitCode.CRASH, "crash", "SystemExit"),
        (MemoryError(), ExitCode.MEMORY, "memory", "MemoryError"),
    ],
)
def test_a_failing_task_names_only_its_exception_type(
    worker: Worker, error: BaseException, code: int, kind: str, detail: str
) -> None:
    def task(_payload: JsonObject) -> JsonObject:
        raise error

    worker.module.task = task  # type: ignore[attr-defined]
    worker.request({})
    assert worker.run(worker.config()) == code
    assert worker.messages()[-1] == {"type": "failure", "kind": kind, "detail": detail}


def test_a_missing_task_function_is_a_crash(worker: Worker) -> None:
    worker.request({})
    assert worker.run(worker.config("nowhere")) == ExitCode.CRASH
    assert worker.messages()[-1]["detail"] == "AttributeError"


def test_a_result_that_cannot_be_sent_is_a_protocol_failure(worker: Worker) -> None:
    worker.module.task = lambda _payload: {"x": {1, 2}}  # type: ignore[attr-defined]
    worker.request({})
    assert worker.run(worker.config()) == ExitCode.CHANNEL
    assert worker.messages()[-1] == {"type": "failure", "kind": "protocol", "detail": "result"}


def test_a_parent_that_is_gone_ends_the_worker(worker: Worker) -> None:
    """Nobody reads the result pipe: ``ready`` cannot be sent."""
    worker.module.task = lambda _payload: {}  # type: ignore[attr-defined]
    worker.request({})
    os.close(worker.results_r)
    assert worker.run(worker.config()) == ExitCode.CHANNEL


def test_a_result_pipe_that_breaks_after_the_task(
    worker: Worker, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[JsonObject] = []
    real = worker_main._Sender.__call__

    def breaking(self: worker_main._Sender, message: JsonObject) -> None:
        if message["type"] == "result":
            raise BrokenPipeError(32, "gone")
        sent.append(message)
        real(self, message)

    monkeypatch.setattr(worker_main._Sender, "__call__", breaking)
    worker.module.task = lambda _payload: {}  # type: ignore[attr-defined]
    worker.request({})
    assert worker.run(worker.config()) == ExitCode.CHANNEL
    assert kinds(sent) == ["ready"]


def test_result_fd_outside_a_worker() -> None:
    worker_main._result_fd = None
    with pytest.raises(RuntimeError, match="not inside a worker"):
        result_fd()


def test_usage_is_in_bytes_on_every_platform(tmp_path: Path) -> None:
    status = tmp_path / "status"
    status.write_text("Name:\tpython\nVmPeak:\t  812345 kB\nVmHWM:\t   23456 kB\n")
    darwin, linux = usage("darwin"), usage("linux", str(status))
    assert isinstance(darwin["max_rss_bytes"], int)
    assert darwin["max_vm_bytes"] is None
    assert linux["max_rss_bytes"] == 23456 * 1024
    assert linux["max_vm_bytes"] == 812345 * 1024
    unit = worker_main.MAXRSS_UNIT
    assert unit == {"darwin": 1}
    assert isinstance(darwin["cpu_s"], float)


@pytest.mark.parametrize(
    "content",
    [
        None,
        "VmPeak:\t812345 MB\nVmHWM:\tlots kB\nVmRSS\n",
        "Name:\tpython\n",
    ],
    ids=["unreadable", "malformed", "absent"],
)
def test_usage_without_the_status_peaks_reports_none_on_linux(
    tmp_path: Path, content: str | None
) -> None:
    """``ru_maxrss`` would count the parent's memory at the fork on Linux."""
    status = tmp_path / "status"
    if content is not None:
        status.write_text(content)
    report = usage("linux", str(status))
    assert report["max_rss_bytes"] is None
    assert report["max_vm_bytes"] is None


def test_the_real_os_is_the_default(monkeypatch: pytest.MonkeyPatch, worker: Worker) -> None:
    used: list[object] = []

    def fake_run(config: WorkerConfig, ops: object, send: object) -> JsonObject:
        used.append(ops)
        raise bootstrap.Refused("stop here")

    monkeypatch.setattr(worker_main, "run_bootstrap", fake_run)
    with pytest.raises(Exited):
        main(worker.config(), exit_=fake_exit)
    assert isinstance(used[0], bootstrap.RealOs)


def test_a_refusal_that_cannot_be_sent_still_refuses(worker: Worker) -> None:
    ops = FakeOs()
    ops.ppid = 1
    os.close(worker.results_r)
    assert worker.run(worker.config(), ops) == ExitCode.REFUSED


def test_an_event_over_the_message_cap_is_a_protocol_failure(worker: Worker) -> None:
    def task(_payload: JsonObject, emit: EventSink) -> JsonObject:
        emit({"x": "y" * 65_530})
        return {}

    worker.module.task = task  # type: ignore[attr-defined]
    worker.request({})
    assert worker.run(worker.config(events=True)) == ExitCode.CHANNEL
    assert worker.messages()[-1] == {"type": "failure", "kind": "protocol", "detail": "event"}


def test_a_result_over_the_message_cap_is_a_protocol_failure(worker: Worker) -> None:
    worker.module.task = lambda _payload: {"x": "y" * 65_530}  # type: ignore[attr-defined]
    worker.request({})
    assert worker.run(worker.config()) == ExitCode.CHANNEL
    assert worker.messages()[-1] == {"type": "failure", "kind": "protocol", "detail": "result"}
