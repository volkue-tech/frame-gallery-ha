"""The process executor with real worker processes (isolation/process.py; §11.3, D-163).

Every worker here runs a task from tests/support/worker_tasks.py, which
installs the H2 network guard first. The launch is this host's production
launch plus the project root on the worker's path, which needs a non-root
parent (a root parent's workers refuse test paths); a root run skips this
module, and tests/unit/isolation/test_root_isolation.py holds the root-only
checks. The Linux-only checks call ``require("linux")``; see
tests/support/processes.py for ``FRAME_GALLERY_REQUIRE_ISOLATION`` (D-165).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import select
import signal
import struct
import subprocess
import sys
import textwrap
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any

import pytest

from frame_gallery.budget.clock import SystemClock
from frame_gallery.domain import BLACK, FitMode, Size
from frame_gallery.imaging.contract import ImageFormat, InspectRequest, PrepareRequest
from frame_gallery.isolation import process
from frame_gallery.isolation.executor import (
    IsolationFailure,
    JsonObject,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.isolation.framing import MAX_FRAME_BYTES, FrameBuffer, encode_frame
from frame_gallery.isolation.launch import (
    PRODUCTION_TASKS,
    WORKER_ENVIRONMENT,
    WORKER_ID,
    WORKER_UMASK,
    ExitCode,
    Limit,
    ordered_limits,
)
from frame_gallery.isolation.process import DRAIN_S, MAX_LOGS, ProcessExecutor
from frame_gallery.tv.contract import TvRequest
from tests.support.images import save_jpeg
from tests.support.processes import PROJECT_ROOT, require, worker_executor, worker_launch

TIMEOUT = 20.0


def run(task: str, payload: JsonObject | None = None, **options: Any) -> JsonObject:
    executor = options.pop("executor", None) or worker_executor()
    return executor.run(task, payload or {}, timeout=options.pop("timeout", TIMEOUT), **options)


def failure(task: str, payload: JsonObject | None = None, **options: Any) -> WorkerError:
    with pytest.raises(WorkerError) as caught:
        run(task, payload, **options)
    return caught.value


def open_fds() -> set[int]:
    found = set()
    for fd in range(256):
        try:
            os.fstat(fd)
        except OSError:
            continue
        found.add(fd)
    return found


@pytest.fixture(autouse=True)
def _needs_a_non_root_parent() -> None:
    require("unprivileged")


class OffsetClock(SystemClock):
    """The real clock, which a test can move forward to fire the kill timer
    at an exact point, whatever the worker's start-up time."""

    def __init__(self) -> None:
        self.offset = 0.0

    def monotonic(self) -> float:
        return super().monotonic() + self.offset


# ------------------------------------------------------------ conversations


def test_a_task_round_trip() -> None:
    executor = worker_executor()
    assert run("echo", {"n": [1, "x"]}, executor=executor) == {"echo": {"n": [1, "x"]}}
    assert executor.last_usage is not None
    assert isinstance(executor.last_usage["max_rss_bytes"], int)
    assert executor.last_usage["max_rss_bytes"] > 1_000_000


def test_events_arrive_in_order_before_the_result() -> None:
    seen: list[JsonObject] = []
    events: list[Any] = [{"marker": "connected"}, {"marker": "upload_started"}]
    assert run("events", {"events": events}, on_event=seen.append) == {"sent": 2}
    assert seen == events


def test_no_descriptor_of_the_parent_leaks() -> None:
    before = open_fds()
    report = run("report")
    assert open_fds() == before
    assert len(report["fds"]) == 6  # type: ignore[arg-type]  # 0, 1, 2, and the three pipes


def test_nothing_is_started_for_an_unknown_task_or_request() -> None:
    started: list[object] = []

    def popen(*args: object, **kwargs: Any) -> subprocess.Popen[bytes]:
        started.append(args)
        child: subprocess.Popen[bytes] = subprocess.Popen(*args, **kwargs)  # type: ignore[call-overload]  # noqa: S603
        return child

    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=popen)
    with pytest.raises(WorkerError) as caught:
        executor.run("teleport", {}, timeout=1)
    assert caught.value.kind is WorkerErrorKind.UNKNOWN_TASK
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {"x": {1}}, timeout=1)  # type: ignore[dict-item]
    assert caught.value.kind is WorkerErrorKind.PROTOCOL
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {}, timeout=1, should_stop=lambda: True)
    assert caught.value.kind is WorkerErrorKind.STOPPED
    with pytest.raises(ValueError, match="positive"):
        executor.run("echo", {}, timeout=0)
    assert started == []


# ----------------------------------------------------------- ends of a task


def test_the_kill_timer() -> None:
    started = time.monotonic()
    error = failure("sleep", {"seconds": 60}, timeout=0.5)
    elapsed = time.monotonic() - started
    assert error.kind is WorkerErrorKind.TIMEOUT
    assert 0.5 <= elapsed < 0.5 + DRAIN_S + 2.0


def test_a_stop_request_kills_and_still_relays_every_event_written() -> None:
    """The first event sets the stop request; the other two were written
    while the parent handled it, and arrive through the drain (D-141)."""
    seen: list[JsonObject] = []
    stop = threading.Event()

    def on_event(event: JsonObject) -> None:
        seen.append(event)
        if len(seen) == 1:
            stop.set()
            time.sleep(0.3)

    events: list[Any] = [{"n": 1}, {"n": 2}, {"n": 3}]
    started = time.monotonic()
    error = failure(
        "events",
        {"events": events, "gap": 0.05, "then_sleep": 60},
        on_event=on_event,
        should_stop=stop.is_set,
    )
    assert error.kind is WorkerErrorKind.STOPPED
    assert seen == events
    assert time.monotonic() - started < 10


def test_a_timeout_relays_the_events_still_in_the_pipe() -> None:
    """The kill timer runs out while the sink handles the first event; the
    second, written meanwhile, is still unread and arrives through the drain
    (D-163)."""
    clock = OffsetClock()
    seen: list[JsonObject] = []

    def on_event(event: JsonObject) -> None:
        seen.append(event)
        if len(seen) == 1:
            clock.offset = TIMEOUT + 1  # the deadline passes here
            time.sleep(0.5)  # the worker writes {"n": 2} 0.05 s after {"n": 1}

    events: list[Any] = [{"n": 1}, {"n": 2}]
    executor = ProcessExecutor(worker_launch(), clock)
    with pytest.raises(WorkerError) as caught:
        executor.run(
            "events",
            {"events": events, "gap": 0.05, "then_sleep": 60},
            timeout=TIMEOUT,
            on_event=on_event,
        )
    assert caught.value.kind is WorkerErrorKind.TIMEOUT
    assert seen == events


@pytest.mark.parametrize(
    ("task", "payload", "kind", "detail"),
    [
        ("crash", {}, WorkerErrorKind.CRASH, "RuntimeError"),
        ("memory", {}, WorkerErrorKind.MEMORY, "MemoryError"),
        ("exit_now", {"code": 3}, WorkerErrorKind.CRASH, "exit status 3"),
        ("exit_now", {"code": 75}, WorkerErrorKind.MEMORY, "exit status 75"),
        ("not_json", {}, WorkerErrorKind.PROTOCOL, "result"),
    ],
)
def test_task_failures(task: str, payload: JsonObject, kind: WorkerErrorKind, detail: str) -> None:
    error = failure(task, payload)
    assert (error.kind, error.detail) == (kind, detail)


def test_terminate_all_kills_the_running_worker() -> None:
    """From another thread, once the task is known to run (its first event)."""
    executor = worker_executor()
    running = threading.Event()

    def kill_when_running() -> None:
        running.wait(TIMEOUT)
        executor.terminate_all()

    killer = threading.Thread(target=kill_when_running)
    killer.start()
    started = time.monotonic()
    try:
        with pytest.raises(WorkerError) as caught:
            executor.run(
                "events",
                {"events": [{"n": 1}], "then_sleep": 60},
                timeout=TIMEOUT,
                on_event=lambda _event: running.set(),
            )
    finally:
        running.set()
        killer.join()
    assert caught.value.kind is WorkerErrorKind.CRASH
    assert caught.value.detail == f"exit status {-signal.SIGKILL}"
    assert time.monotonic() - started < 10
    executor.terminate_all()  # idle: nothing to kill


def test_an_unexpected_error_in_the_event_sink_propagates_after_the_kill() -> None:
    def broken(_event: JsonObject) -> None:
        raise KeyError("sink")

    with pytest.raises(KeyError):
        run("events", {"events": [{"n": 1}], "then_sleep": 60}, on_event=broken)


def test_an_event_the_sink_refuses_is_a_protocol_failure() -> None:
    def refuse(_event: JsonObject) -> None:
        raise ValueError("not a marker")

    error = failure("events", {"events": [{"n": 1}], "then_sleep": 60}, on_event=refuse)
    assert (error.kind, error.detail) == (WorkerErrorKind.PROTOCOL, "event: not a marker")


# ----------------------------------------------------------------- protocol


def frame_hex(message: object) -> str:
    body = json.dumps(message).encode()
    return (struct.pack("!I", len(body)) + body).hex()


@pytest.mark.parametrize(
    ("task", "payload", "detail"),
    [
        ("raw", {"hex": struct.pack("!I", 10_000_000).hex()}, "channel: frame of"),
        ("raw", {"hex": (struct.pack("!I", 3) + b"{x}").hex()}, "channel: message is not valid"),
        ("frame", {"message": {"type": "teleport"}}, "unexpected message teleport"),
        ("frame", {"message": {"type": "ready", "report": {}}}, "unexpected message ready"),
        ("frame", {"message": {"type": "event", "event": [1]}}, "unexpected event"),
        ("frame_plain", {"message": {"type": "event", "event": {"n": 1}}}, "unexpected event"),
        ("frame", {"message": {"type": "failure", "kind": "odd", "detail": ""}}, "failure: not"),
        (
            "frame",
            {"message": {"type": "result", "result": [1], "usage": {}}},
            "result: not a JSON object",
        ),
    ],
)
def test_protocol_violations_kill_the_worker(task: str, payload: JsonObject, detail: str) -> None:
    started = time.monotonic()
    error = failure(task, payload, on_event=lambda _event: None)
    assert error.kind is WorkerErrorKind.PROTOCOL
    assert error.detail.startswith(detail), error.detail
    assert time.monotonic() - started < 10


def test_an_event_without_a_sink_is_a_protocol_failure() -> None:
    error = failure("frame", {"message": {"type": "event", "event": {"n": 1}}})
    assert (error.kind, error.detail) == (WorkerErrorKind.PROTOCOL, "unexpected event")


def test_a_failure_message_decides_the_kind() -> None:
    message: JsonObject = {"type": "failure", "kind": "memory", "detail": "odd\nname"}
    payload: JsonObject = {"message": message, "then_exit": 0}
    error = failure("frame", payload, on_event=lambda _e: None)
    assert (error.kind, error.detail) == (WorkerErrorKind.MEMORY, "odd name")


def test_a_bad_log_message_is_dropped_not_fatal(caplog: pytest.LogCaptureFixture) -> None:
    message: JsonObject = {"type": "log", "level": 99, "logger": "x", "text": "y"}
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        result = run("frame", {"message": message, "then_sleep": 0}, on_event=lambda _e: None)
    assert result == {"after": "frame"}
    assert "y" not in [record.getMessage() for record in caplog.records]


def test_worker_logs_are_bounded_capped_and_sanitized(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        run("logs", {"count": 150})
    records = [r for r in caplog.records if r.name == "frame_gallery.worker.logs"]
    assert len(records) == MAX_LOGS
    assert all(record.levelno <= logging.WARNING for record in records)
    texts = [record.getMessage() for record in records]
    assert texts[0] == "tests.worker: record 0 x"
    assert len(texts[3]) == len("tests.worker: ") + 900  # cut by the worker
    assert texts[-1] == "frame_gallery.isolation.bootstrap: further worker log records are dropped"


def test_the_error_record_is_capped_and_on_one_line(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        run("logs", {"count": 1})
    last = [r for r in caplog.records if r.name == "frame_gallery.worker.logs"][-1]
    assert (last.levelno, last.getMessage()) == (
        logging.WARNING,
        "tests.worker: a critical-looking line",
    )


def test_the_stderr_tail_is_logged_at_debug_only(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        run("stderr_flood", {"lines": 1000})
    lines = [
        r.getMessage() for r in caplog.records if r.name == "frame_gallery.worker.stderr_flood"
    ]
    assert len(lines) == 30
    assert lines[-1] == "stderr| line 999 [31m"
    assert all(r.levelno == logging.DEBUG for r in caplog.records if "stderr|" in r.getMessage())


def test_a_crash_leaves_its_stderr_at_debug(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        failure("exit_now", {"code": 4})
    assert "stderr| dying on purpose" in caplog.text


# ---------------------------------------------------------------- isolation


def test_a_worker_that_cannot_start_is_an_isolation_failure() -> None:
    before = open_fds()
    executor = ProcessExecutor(worker_launch(python="/nonexistent/python"), SystemClock())
    with pytest.raises(IsolationFailure, match=r"could not be started \(FileNotFoundError\)"):
        executor.run("echo", {}, timeout=5)
    assert open_fds() == before


def test_an_environment_it_was_not_promised_is_refused() -> None:
    executor = worker_executor(extra_environment={"HTTPS_PROXY": "http://proxy.invalid"})
    with pytest.raises(IsolationFailure, match=r"refused to run .*\(environment\)"):
        executor.run("echo", {}, timeout=10)


def test_a_privilege_drop_that_fails_is_refused() -> None:
    """As a non-root user, dropping to any identity fails: the worker refuses
    (production tasks only; a worker that drops privileges takes no test path)."""
    launch = worker_launch(
        tasks=PRODUCTION_TASKS, extra_paths=(), identity=(os.getuid() + 1, os.getgid())
    )
    executor = ProcessExecutor(launch, SystemClock())
    with pytest.raises(IsolationFailure, match=r"refused to run .*\(privileges:EPERM\)"):
        executor.run("prepare", {}, timeout=10)


def test_test_paths_are_refused_with_an_identity() -> None:
    """Refused before any privilege is touched, so this holds for any parent."""
    executor = worker_executor(identity=(WORKER_ID, WORKER_ID))
    with pytest.raises(IsolationFailure, match=r"\(test_paths\)"):
        executor.run("echo", {}, timeout=10)


def test_a_worker_that_dies_before_ready_is_an_isolation_failure() -> None:
    # Neither path holds the package (an image installs it in site-packages too).
    executor = worker_executor(source_root="/nonexistent", site_paths=())
    with pytest.raises(IsolationFailure, match=r"during its bootstrap \(exit status 1\)"):
        executor.run("echo", {}, timeout=10)


FAKE_BOOT = textwrap.dedent(
    """
    import json, os, struct, sys
    config = json.loads(sys.argv[1])
    out = config["fds"][1]
    for message in MESSAGES:
        data = message.encode() if isinstance(message, str) else json.dumps(message).encode()
        os.write(out, struct.pack("!I", len(data)) + data)
    import time; time.sleep(float(PAUSE))
    """
)


def scripted_boot(messages: Sequence[object], pause: float = 0.0) -> Callable[..., Any]:
    """A popen that runs a scripted worker instead of BOOT."""
    code = FAKE_BOOT.replace("MESSAGES", repr(messages)).replace("PAUSE", repr(pause))

    def popen(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        after_boot = argv[argv.index(process.BOOT) + 1 :]
        return subprocess.Popen([argv[0], "-I", "-c", code, *after_boot], **kwargs)  # noqa: S603

    return popen


def expected_report(task: str) -> dict[str, object]:
    launch = worker_launch()
    entry = launch.tasks[task]
    limits = ordered_limits(entry.limits, skip=launch.skip_limits)
    return {
        "uid": os.getuid(),
        "gid": os.getgid(),
        "groups": [],
        "umask": WORKER_UMASK,
        "limits": {limit.value: [value, value] for limit, value in limits},
        "environment": sorted(WORKER_ENVIRONMENT),
    }


@pytest.mark.parametrize(
    ("messages", "match"),
    [
        (["not json"], r"during its bootstrap \(channel: message is not valid JSON\)"),
        ([{"type": "event", "event": {}}], r"during its bootstrap \(unexpected message event\)"),
        ([{"type": "refused", "reason": 5}], r"\(unknown\)"),
        ([{"type": "ready", "report": {}}], "bootstrap report does not match"),
        ([{"type": "ready", "report": {}, "extra": 1}], "bootstrap report does not match"),
    ],
)
def test_a_broken_bootstrap_is_an_isolation_failure(messages: list[object], match: str) -> None:
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=scripted_boot(messages))
    with pytest.raises(IsolationFailure, match=match):
        executor.run("echo", {}, timeout=10)


def test_the_parent_checks_the_ready_report() -> None:
    good = expected_report("echo")
    ready = [{"type": "ready", "report": good}, {"type": "result", "result": {"ok": 1}, "usage": 1}]
    scripted = ProcessExecutor(worker_launch(), SystemClock(), popen=scripted_boot(ready, 1))
    assert scripted.run("echo", {}, timeout=10) == {"ok": 1}
    assert scripted.last_usage is None
    with_identity = worker_launch(identity=(4321, 4321))
    for report in (good, {**good, "uid": 4321, "gid": 4321, "groups": [1]}):
        bad = ProcessExecutor(
            with_identity, SystemClock(), popen=scripted_boot([{"type": "ready", "report": report}])
        )
        with pytest.raises(IsolationFailure, match="does not match"):
            bad.run("echo", {}, timeout=10)
    matching = {**good, "uid": 4321, "gid": 4321}
    ok = ProcessExecutor(
        with_identity,
        SystemClock(),
        popen=scripted_boot([{"type": "ready", "report": matching}, *ready[1:]], 1),
    )
    assert ok.run("echo", {}, timeout=10) == {"ok": 1}


def test_a_worker_that_exits_after_ready_without_reading_is_a_crash() -> None:
    good = expected_report("echo")
    scripted = ProcessExecutor(
        worker_launch(), SystemClock(), popen=scripted_boot([{"type": "ready", "report": good}])
    )
    big: JsonObject = {"blob": "x" * 60_000}  # under the message cap, near a pipe's size
    with pytest.raises(WorkerError) as caught:
        scripted.run("echo", big, timeout=10)
    assert caught.value.kind is WorkerErrorKind.CRASH


# ------------------------------------------------------- the bootstrap test


def test_the_bootstrap_as_seen_from_inside_the_worker() -> None:
    """§11.3: every value asserted from inside the child."""
    launch = worker_launch()
    report = run("report")
    assert report["cwd"] == "/"
    assert report["umask"] == WORKER_UMASK
    assert report["flags"] == {"isolated": 1, "dont_write_bytecode": 1}
    # Only this package and the test tasks: no .pth or sitecustomize ran (-S).
    assert set(report["modules"]) <= {"frame_gallery", "tests"}  # type: ignore[arg-type]
    # Its own process group, in the parent's session.
    assert report["pgrp"] == report["pid"]
    assert report["pgrp"] != os.getpgrp()
    assert report["sid"] == os.getsid(0)
    environment = dict(report["environment"])  # type: ignore[arg-type]
    if sys.platform == "darwin":
        environment.pop("__CF_USER_TEXT_ENCODING")
    assert environment == WORKER_ENVIRONMENT
    limits = report["limits"]
    assert isinstance(limits, dict)
    entry = launch.tasks["report"]
    for limit, value in entry.limits.items():
        if limit in launch.skip_limits:
            continue
        assert limits[limit.value] == [value, value], limit
        if value < 2**62:
            raised = report["raise_limit"]
            assert isinstance(raised, dict)
            assert raised[limit.value] == "ValueError"
    assert report["ppid"] == os.getpid()
    assert (report["uid"], report["gid"]) == (os.geteuid(), os.getegid())


def test_the_worker_can_start_no_process() -> None:
    assert run("spawn")["fork"] == "EAGAIN"


def test_the_address_space_limit_is_set_where_the_platform_allows_it() -> None:
    require("linux")
    report = run("report")
    limits = report["limits"]
    assert isinstance(limits, dict)
    assert limits["RLIMIT_AS"] == [1024**3, 1024**3]
    television = run("report_tv")["limits"]
    assert isinstance(television, dict)
    assert television["RLIMIT_AS"] == [512 * 1024**2] * 2


def test_on_linux_the_worker_cannot_start_a_thread_either() -> None:
    require("linux")
    assert run("spawn")["thread"] == "RuntimeError"


def test_on_linux_the_parent_death_signal_and_the_rest_hold_inside_the_worker() -> None:
    """Read by the task itself, not through the bootstrap's own code (§11.3)."""
    require("linux")
    assert run("report")["linux"] == {
        "pdeathsig": signal.SIGKILL,
        "dumpable": 0,
        "no_new_privs": 1,
        "capabilities": {"CapInh": 0, "CapPrm": 0, "CapEff": 0, "CapAmb": 0},
    }


# ----------------------------------------------------------------- orphans


ORPHAN_PARENT = textwrap.dedent(
    """
    import sys
    sys.path[:0] = [sys.argv[1], sys.argv[2]]
    from tests.support import h2
    h2.install()
    from tests.support.processes import worker_executor
    worker_executor().run("orphan", {"pid_file": sys.argv[3]}, timeout=60)
    """
)


def test_a_worker_dies_with_its_parent(tmp_path: Path) -> None:
    """The parent is SIGKILLed; the worker's lifeline read returns, and it
    exits (PR_SET_PDEATHSIG does the same on Linux)."""
    pid_file = tmp_path / "worker.pid"
    parent = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-c",
            ORPHAN_PARENT,
            str(PROJECT_ROOT / "src"),
            str(PROJECT_ROOT),
            str(pid_file),
        ],
        cwd=PROJECT_ROOT,
    )
    try:
        deadline = time.monotonic() + 20
        while not pid_file.exists() or not pid_file.read_text():
            assert time.monotonic() < deadline, "the worker never started"
            time.sleep(0.05)
        worker = int(pid_file.read_text())
        os.kill(parent.pid, signal.SIGKILL)
        parent.wait(timeout=10)
        deadline = time.monotonic() + 10
        while True:
            try:
                os.kill(worker, 0)
            except ProcessLookupError:
                break
            assert time.monotonic() < deadline, "the orphaned worker is still running"
            time.sleep(0.05)
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()


# --------------------------------------------------- production tasks, guarded


def test_prepare_in_a_worker(tmp_path: Path) -> None:
    source = save_jpeg_file(tmp_path)
    request = PrepareRequest(
        source_path=str(source),
        output_path=str(tmp_path / "delivery-0.jpg"),
        declared_format=ImageFormat.JPEG,
        fit_mode=FitMode.CONTAIN,
        background=BLACK,
        landscape_only=True,
        require_near_16_9=False,
        canvas=Size(384, 216),
    )
    result = run("prepare", request.to_json())
    assert result["status"] == "ok", result
    assert (tmp_path / "delivery-0.jpg").stat().st_size > 0


def test_inspect_in_a_worker(tmp_path: Path) -> None:
    source = save_jpeg_file(tmp_path)
    result = run("inspect", InspectRequest(str(source), ImageFormat.JPEG).to_json())
    assert result["status"] == "ok", result


def save_jpeg_file(tmp_path: Path) -> Path:
    from PIL import Image  # noqa: PLC0415

    return save_jpeg(Image.new("RGB", (768, 432), (200, 30, 30)), tmp_path / "source.jpg")


def tv_request(tmp_path: Path, seconds: float = 10.0) -> JsonObject:
    jpeg = tmp_path / "delivery-0.jpg"
    jpeg.write_bytes(b"\xff\xd8" + b"x" * 100 + b"\xff\xd9")
    return TvRequest(
        IPv4Address("192.0.2.20"),
        None,
        jpeg,
        hashlib.sha256(jpeg.read_bytes()).hexdigest(),
        time.monotonic() + seconds,
    ).to_json()


def test_the_delivery_logic_in_a_worker(tmp_path: Path) -> None:
    """The production delivery logic over the stand-in library, in a real
    worker: markers and the token arrive as events, then the result."""
    payload = tv_request(tmp_path, seconds=30.0)
    seen: list[JsonObject] = []
    result = run("deliver", payload, on_event=seen.append, timeout=30.0)
    assert result == {"status": "ok", "detail": "selected", "pairing": None}
    assert seen == [
        {"token": "12345678"},
        {"marker": "connected", "content_id": None},
        {"marker": "upload_started", "content_id": None},
        {"marker": "uploaded", "content_id": "MY_F0042"},
        {"marker": "selected", "content_id": None},
    ]
    calls = json.loads((tmp_path / "fake-tv-calls.json").read_text())
    assert calls[-1] == "shutdown"


def test_the_real_library_in_a_worker_meets_the_h2_guard(tmp_path: Path) -> None:
    """The production deliver task with the installed samsungtvws: the H2
    guard in the worker blocks its first connection attempt."""
    result = run("deliver_real", tv_request(tmp_path, seconds=30.0), on_event=lambda _e: None)
    assert result == {
        "status": "protocol",
        "detail": "the TV's device information was not readable (NetworkBlockedError)",
        "pairing": None,
    }


def test_a_skipped_limit_is_left_out() -> None:
    executor = worker_executor(skip_limits=frozenset({Limit.ADDRESS_SPACE, Limit.CPU}))
    limits = run("report", executor=executor)["limits"]
    assert isinstance(limits, dict)
    assert limits["RLIMIT_CPU"] != [30, 30]


def test_a_worker_that_closes_its_stderr_early(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        assert run("close_stderr") == {"closed": True}
    assert "stderr| last words" in caplog.text


def test_a_request_larger_than_the_pipe_to_a_worker_that_leaves() -> None:
    """The request may need several writes; the worker reads none of it and
    exits, so the result pipe closes while the rest may still be pending, and
    the run is a crash (a failed write itself: test_a_request_to_a_worker_that_is_gone)."""
    ready = [{"type": "ready", "report": expected_report("echo")}]
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=scripted_boot(ready, 0.5))
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {"blob": "x" * 60_000}, timeout=10)  # under the cap
    assert caught.value.kind is WorkerErrorKind.CRASH


class _ChildRig:
    """A sleeping child process in its own group, and a worker record with
    real pipes around it, for driving the executor's internals directly."""

    @pytest.fixture
    def child(self) -> Iterator[subprocess.Popen[bytes]]:
        started = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"], process_group=0
        )
        try:
            yield started
        finally:
            started.kill()
            started.wait()

    def worker(self, child: subprocess.Popen[bytes], *, events: bool = True) -> process._Worker:
        results_r, results_w = os.pipe()
        stderr_r, stderr_w = os.pipe()
        request_r, request_w = os.pipe()
        lifeline_r, lifeline_w = os.pipe()
        for fd in (stderr_r, request_w):
            os.set_blocking(fd, False)
        self.write_ends = [results_w, stderr_w, request_r, lifeline_r]
        entry = worker_launch().tasks["events" if events else "echo"]
        return process._Worker(
            "events",
            entry,
            None,  # type: ignore[arg-type]
            child,
            results_r,
            stderr_r,
            request_w,
            lifeline_w,
        )

    def close(self) -> None:
        for fd in self.write_ends:
            with contextlib.suppress(OSError):
                os.close(fd)


class TestInternals(_ChildRig):
    """Paths that depend on timing, driven directly and deterministically."""

    def test_a_full_request_pipe_waits(self, child: subprocess.Popen[bytes]) -> None:
        worker = self.worker(child)
        assert worker.request is not None
        with contextlib.suppress(BlockingIOError):
            while True:
                os.write(worker.request, b"x" * 65536)
        state = process._Conversation(ready=True, pending=b"more")
        worker_executor()._write_request(worker, state, select.poll())
        assert state.pending == b"more"
        worker_executor()._end(worker)
        self.close()

    def test_stderr_with_nothing_to_read(self, child: subprocess.Popen[bytes]) -> None:
        worker = self.worker(child)
        assert process.ProcessExecutor._take_stderr(worker) == -1
        os.write(self.write_ends[1], b"tail\n")
        executor = worker_executor()
        with self.caplog_at_debug() as records:
            executor._end(worker)  # reaps, then reads what stderr still held
        assert "stderr| tail" in [record.getMessage() for record in records]
        self.close()

    @contextlib.contextmanager
    def caplog_at_debug(self) -> Iterator[list[logging.LogRecord]]:
        records: list[logging.LogRecord] = []

        class Keep(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        logger = logging.getLogger("frame_gallery.worker")
        handler, level = Keep(), logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            yield records
        finally:
            logger.removeHandler(handler)
            logger.setLevel(level)

    def test_the_drain_is_bounded_by_time(self, child: subprocess.Popen[bytes]) -> None:
        """A write end still held open: the drain gives up after its time."""
        worker = self.worker(child)
        os.write(self.write_ends[0], encode_frame({"type": "event", "event": {"n": 1}}))
        seen: list[JsonObject] = []
        started = time.monotonic()
        worker_executor()._drain(worker, FrameBuffer(), seen.append)
        assert DRAIN_S <= time.monotonic() - started < DRAIN_S + 1
        assert seen == [{"n": 1}]
        worker_executor()._end(worker)
        self.close()

    def test_the_drain_skips_other_messages_and_stops_at_garbage(
        self, child: subprocess.Popen[bytes]
    ) -> None:
        worker = self.worker(child)
        data = (
            encode_frame({"type": "log", "level": 30, "logger": "x", "text": "y"})
            + encode_frame({"type": "event", "event": {"n": 1}})
            + struct.pack("!I", 3)
            + b"{x}"
        )
        os.write(self.write_ends[0], data)
        os.close(self.write_ends[0])
        seen: list[JsonObject] = []
        worker_executor()._drain(worker, FrameBuffer(), seen.append)
        assert seen == [{"n": 1}]  # relayed; the garbage after it ends the drain
        worker_executor()._end(worker)
        self.close()

    def test_the_drain_relays_events_until_one_is_refused(
        self, child: subprocess.Popen[bytes]
    ) -> None:
        worker = self.worker(child)
        messages: list[JsonObject] = [
            {"type": "log", "level": 30, "logger": "x", "text": "y"},
            {"type": "event", "event": {"n": 1}},
            {"type": "event", "event": {"n": 2}},
            {"type": "event", "event": {"n": 3}},
        ]
        data = b"".join(encode_frame(message) for message in messages)
        os.write(self.write_ends[0], data)
        os.close(self.write_ends[0])
        seen: list[JsonObject] = []

        def refuse_second(event: JsonObject) -> None:
            if event == {"n": 2}:
                raise ValueError("refused")
            seen.append(event)

        worker_executor()._drain(worker, FrameBuffer(), refuse_second)
        assert seen == [{"n": 1}]
        worker_executor()._end(worker)
        self.close()

    def test_the_drain_of_a_task_without_events_relays_nothing(
        self, child: subprocess.Popen[bytes]
    ) -> None:
        worker = self.worker(child, events=False)
        os.write(self.write_ends[0], encode_frame({"type": "event", "event": {"n": 1}}))
        os.close(self.write_ends[0])
        seen: list[JsonObject] = []
        worker_executor()._drain(worker, FrameBuffer(), seen.append)
        assert seen == []
        worker_executor()._end(worker)
        self.close()

    def test_a_worker_that_does_not_die(
        self, child: subprocess.Popen[bytes], caplog: pytest.LogCaptureFixture
    ) -> None:
        worker = self.worker(child)

        class Stuck:
            pid = child.pid

            def wait(self, timeout: float) -> int:
                raise subprocess.TimeoutExpired("worker", timeout)

        worker.process = Stuck()  # type: ignore[assignment]
        executor = worker_executor()
        with caplog.at_level(logging.ERROR, "frame_gallery.isolation"):
            assert executor._reap(worker) is None
        assert "did not end after SIGKILL" in caplog.text
        assert not worker.reaped
        executor._end(worker)  # closes the descriptors all the same
        self.close()

    def test_reaping_a_worker_that_is_not_the_active_one(
        self, child: subprocess.Popen[bytes]
    ) -> None:
        worker = self.worker(child)
        executor = worker_executor()
        assert executor._active is None
        assert executor._reap(worker) == -signal.SIGKILL
        executor._end(worker)
        self.close()

    def test_a_request_to_a_worker_that_is_gone(self, child: subprocess.Popen[bytes]) -> None:
        worker = self.worker(child)
        os.close(self.write_ends[2])  # the worker's end of the request pipe
        state = process._Conversation(ready=True, pending=b"request")
        poller = select.poll()
        request = worker.request
        assert request is not None
        poller.register(request, select.POLLOUT)
        worker_executor()._write_request(worker, state, poller)
        assert state.pending == b""
        assert worker.request is None
        worker_executor()._end(worker)
        self.close()

    def test_the_drain_is_bounded_by_bytes(
        self, child: subprocess.Popen[bytes], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(process, "DRAIN_BYTES", 8)
        worker = self.worker(child)
        frames = b"".join(encode_frame({"type": "event", "event": {"n": n}}) for n in range(3))
        os.write(self.write_ends[0], frames)
        seen: list[JsonObject] = []
        started = time.monotonic()
        worker_executor()._drain(worker, FrameBuffer(), seen.append)
        assert time.monotonic() - started < DRAIN_S
        assert seen == [{"n": 0}, {"n": 1}, {"n": 2}]  # one read held them all
        worker_executor()._end(worker)
        self.close()


# ------------------------------------------------ groups, stops, and drains


def test_the_kill_reaches_a_process_left_in_the_workers_group(tmp_path: Path) -> None:
    """With the process limit lifted, the task forks a child that stays in
    its group; the kill timer's group kill ends it too (§14)."""
    pid_file = tmp_path / "child.pid"
    executor = worker_executor(skip_limits=worker_launch().skip_limits | {Limit.PROCESSES})
    with pytest.raises(WorkerError) as caught:
        executor.run(
            "fork_and_sleep",
            {"pid_file": str(pid_file)},
            timeout=1.5,
            on_event=lambda _event: None,
        )
    assert caught.value.kind is WorkerErrorKind.TIMEOUT
    child = int(pid_file.read_text())
    deadline = time.monotonic() + 5
    try:
        while True:
            try:
                os.kill(child, 0)
            except ProcessLookupError:
                break
            if _zombie(child):
                break
            assert time.monotonic() < deadline, "the child in the worker's group survived"
            time.sleep(0.05)
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.kill(child, signal.SIGKILL)


def _zombie(pid: int) -> bool:
    """An orphan whose new parent has not reaped it yet is dead already."""
    state = subprocess.run(  # noqa: S603 - a fixed tool and our own child's pid
        ["/bin/ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return state.startswith("Z")


def test_the_worker_is_killed_before_the_pipe_is_drained() -> None:
    """A stop request 0.3 s after the first tick: no tick written later than
    the kill reaches the sink (D-163)."""
    ticks: list[float] = []
    stop_at: list[float] = []

    def on_event(event: JsonObject) -> None:
        value = event["t"]
        assert isinstance(value, float)
        ticks.append(value)
        if len(ticks) == 1:
            threading.Timer(0.3, lambda: stop_at.append(time.monotonic())).start()

    error = failure("tick", {"seconds": 30}, on_event=on_event, should_stop=lambda: bool(stop_at))
    assert error.kind is WorkerErrorKind.STOPPED
    assert max(ticks) - stop_at[0] < 0.3  # a drain before the kill would add a second


def test_a_stop_request_is_seen_within_the_poll_interval() -> None:
    """Set from another thread while the worker is silent (D-163: at least
    every 50 ms)."""
    stop_at: list[float] = []
    running = threading.Event()

    def stop_later() -> None:
        running.wait(TIMEOUT)
        time.sleep(0.5)
        stop_at.append(time.monotonic())

    stopper = threading.Thread(target=stop_later)
    stopper.start()
    try:
        error = failure(
            "events",
            {"events": [{"n": 1}], "then_sleep": 60},
            on_event=lambda _event: running.set(),
            should_stop=lambda: bool(stop_at),
        )
    finally:
        running.set()
        stopper.join()
    assert error.kind is WorkerErrorKind.STOPPED
    assert time.monotonic() - stop_at[0] < 0.5


def frames_hex(*messages: object, garbage: bytes = b"") -> str:
    data = b""
    for message in messages:
        body = json.dumps(message).encode()
        data += struct.pack("!I", len(body)) + body
    return (data + garbage).hex()


GARBAGE = struct.pack("!I", 3) + b"{x}"


def test_an_event_before_a_bad_frame_in_one_write_is_relayed() -> None:
    """Whatever the chunking (R1 of the Phase 5 review)."""
    seen: list[JsonObject] = []
    event = {"type": "event", "event": {"marker": "uploaded", "content_id": "MY_F1"}}
    error = failure("raw_events", {"hex": frames_hex(event, garbage=GARBAGE)}, on_event=seen.append)
    assert error.kind is WorkerErrorKind.PROTOCOL
    assert seen == [{"marker": "uploaded", "content_id": "MY_F1"}]


def test_a_result_before_a_bad_frame_in_one_write_stands() -> None:
    result = {"type": "result", "result": {"ok": 1}, "usage": {}}
    assert run("raw", {"hex": frames_hex(result, garbage=GARBAGE)}) == {"ok": 1}


@pytest.mark.parametrize("kind", ["event", "result"])
def test_a_body_over_the_message_cap_is_refused_by_the_parent(kind: str) -> None:
    """A frame may be 1 KiB larger than the cap for its envelope; its body
    may not (the in-process executor refuses the same sizes)."""
    size = 65_530  # the body is just over 64 KiB; its frame is under 65 KiB
    assert len(json.dumps({"x": "y" * size})) > 65_536
    assert len(json.dumps({"type": "result", "result": {"x": "y" * size}, "usage": {}})) < (
        MAX_FRAME_BYTES
    )
    error = failure("big_frame", {"kind": kind, "size": size}, on_event=lambda _event: None)
    assert (error.kind, error.detail) == (WorkerErrorKind.PROTOCOL, f"{kind}: over the message cap")


@pytest.mark.parametrize(
    ("task", "detail"),
    [("big_event", "event"), ("big_result", "result")],
)
def test_a_body_over_the_message_cap_is_a_protocol_failure_in_the_worker(
    task: str, detail: str
) -> None:
    error = failure(task, {"size": 65_530}, on_event=lambda _event: None)
    assert (error.kind, error.detail) == (WorkerErrorKind.PROTOCOL, detail)


def test_a_request_over_the_message_cap_starts_no_worker() -> None:
    started: list[object] = []

    def popen(*args: object, **kwargs: Any) -> subprocess.Popen[bytes]:
        started.append(args)
        raise AssertionError

    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=popen)
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {"x": "y" * 65_530}, timeout=5)
    assert caught.value.kind is WorkerErrorKind.PROTOCOL
    assert caught.value.detail.startswith("request: message exceeds")
    assert started == []


# ---------------------------------------------------------- the handshake


LISTENING_BOOT = textwrap.dedent(
    """
    import json, os, select, struct, sys, time
    config = json.loads(sys.argv[1])
    request, out = config["fds"][0], config["fds"][1]
    record, last, read_after = RECORD, LAST, READ_AFTER

    def send(message):
        data = json.dumps(message).encode()
        os.write(out, struct.pack("!I", len(data)) + data)

    def listen(milliseconds):
        poller = select.poll()
        poller.register(request, select.POLLIN)
        if not poller.poll(milliseconds):
            return b""
        os.set_blocking(request, False)
        try:
            return os.read(request, 65536)
        except BlockingIOError:
            return b""

    if read_after:
        send(last)
        open(record, "w").write(listen(5000).hex())
    else:
        open(record, "w").write(listen(300).hex())
        send(last)
        if last.get("type") == "refused":
            os._exit(70)
    time.sleep(1)
    """
)


def listening_boot(record: Path, last: object, *, read_after: bool = False) -> Callable[..., Any]:
    """A worker that records what arrives on its request pipe: before it
    sends ``last`` (so an early request would be seen), or after it."""
    code = (
        LISTENING_BOOT.replace("RECORD", repr(str(record)))
        .replace("LAST", repr(last))
        .replace("READ_AFTER", repr(read_after))
    )

    def popen(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        after_boot = argv[argv.index(process.BOOT) + 1 :]
        return subprocess.Popen([argv[0], "-I", "-c", code, *after_boot], **kwargs)  # noqa: S603

    return popen


@pytest.mark.parametrize(
    "last",
    [
        {"type": "refused", "reason": "environment"},
        {"type": "ready", "report": {}},
    ],
    ids=["refused", "mismatching-ready"],
)
def test_the_request_is_sent_only_after_a_verified_ready(tmp_path: Path, last: object) -> None:
    """The request may carry the pairing token (D-162): a worker that refuses,
    or reports values other than those asked for, never gets it (D-163)."""
    record = tmp_path / "read.hex"
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=listening_boot(record, last))
    with pytest.raises(IsolationFailure):
        executor.run("echo", {"token": "12345678"}, timeout=10)
    assert record.read_text() == ""


def test_the_listening_worker_sees_a_request_after_a_verified_ready(tmp_path: Path) -> None:
    """The control: the same probe does see the request once ready matched."""
    record = tmp_path / "read.hex"
    ready = {"type": "ready", "report": expected_report("echo")}
    popen = listening_boot(record, ready, read_after=True)
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=popen)
    with pytest.raises(WorkerError):
        executor.run("echo", {"token": "12345678"}, timeout=10)
    assert b"12345678".hex() in record.read_text()


@pytest.mark.parametrize("before_ready", [False, True], ids=["after-ready", "before-ready"])
def test_the_parent_caps_worker_log_records_itself(
    before_ready: bool, caplog: pytest.LogCaptureFixture
) -> None:
    """A worker that writes log frames past its own handler: the parent
    relays the first MAX_LOGS, drops the rest, and the run succeeds."""
    flood: list[object] = [
        {"type": "log", "level": 30, "logger": "x", "text": f"n{n}"} for n in range(MAX_LOGS + 50)
    ]
    ready: object = {"type": "ready", "report": expected_report("echo")}
    result: object = {"type": "result", "result": {"ok": 1}, "usage": {}}
    messages = [*flood, ready, result] if before_ready else [ready, *flood, result]
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=scripted_boot(messages, 1))
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        assert executor.run("echo", {}, timeout=10) == {"ok": 1}
    relayed = [r for r in caplog.records if r.name == "frame_gallery.worker.echo"]
    assert len(relayed) == MAX_LOGS


@pytest.mark.parametrize(
    "change",
    [
        {"umask": 0o022},
        {"limits": "one"},
        {"environment": ["PATH"]},
        {"extra_key": True},
    ],
    ids=["umask", "limit", "environment", "key"],
)
def test_each_field_of_the_ready_report_is_checked(change: dict[str, object]) -> None:
    report = dict(expected_report("echo"))
    if change.get("limits") == "one":
        limits = dict(report["limits"])  # type: ignore[call-overload]
        first = next(iter(limits))
        limits[first] = [limits[first][0], limits[first][0] + 1]
        report["limits"] = limits
    elif "extra_key" in change:
        report = {**report}
    else:
        report.update(change)
    message: dict[str, object] = {"type": "ready", "report": report}
    if "extra_key" in change:
        message["extra"] = True
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=scripted_boot([message]))
    with pytest.raises(IsolationFailure, match="does not match"):
        executor.run("echo", {}, timeout=10)


@pytest.mark.parametrize(
    "change",
    [{"uid": 4321}, {"gid": 4321}, {"groups": [7]}],
    ids=["uid", "gid", "groups"],
)
def test_each_identity_field_of_the_ready_report_is_checked(change: dict[str, object]) -> None:
    good = {**expected_report("echo"), "uid": 4322, "gid": 4323}
    launch = worker_launch(identity=(4322, 4323))
    bad = ProcessExecutor(
        launch,
        SystemClock(),
        popen=scripted_boot([{"type": "ready", "report": {**good, **change}}]),
    )
    with pytest.raises(IsolationFailure, match="does not match"):
        bad.run("echo", {}, timeout=10)
    ready = [{"type": "ready", "report": good}, {"type": "result", "result": {}, "usage": {}}]
    ok = ProcessExecutor(launch, SystemClock(), popen=scripted_boot(ready, 1))
    assert ok.run("echo", {}, timeout=10) == {}


# ------------------------------------------------------------ the stderr tail


def test_a_cut_stderr_tail_without_a_newline_is_still_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """From its first whole word: a cut may split a secret (R4)."""
    text = "secretpart" * 500 + " visible end"
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        run("stderr_line", {"text": text})
    lines = [r.getMessage() for r in caplog.records if r.name == "frame_gallery.worker.stderr_line"]
    assert lines == ["stderr| …visible end"]


def test_a_cut_stderr_tail_of_one_word_is_only_counted(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, "frame_gallery.worker"):
        run("stderr_line", {"text": "x" * 5000})
    lines = [r.getMessage() for r in caplog.records if r.name == "frame_gallery.worker.stderr_line"]
    assert lines == ["stderr| … (4096 characters)"]


# ------------------------------------------------------- starts that break


class Interrupted(BaseException):
    """Stands for a stop request (Cancelled) raised at an unlucky moment."""


def test_a_start_interrupted_after_the_fork_leaks_nothing() -> None:
    """Popen forks, then raises: the worker is not known, but closing our
    ends of its pipes makes it end by itself."""
    before = open_fds()
    started: list[subprocess.Popen[bytes]] = []

    def popen(*args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        started.append(subprocess.Popen(*args, **kwargs))  # noqa: S603
        raise Interrupted

    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=popen)
    with pytest.raises(Interrupted):
        executor.run("echo", {}, timeout=10)
    assert open_fds() == before
    assert started[0].wait(timeout=10) in (ExitCode.CHANNEL, ExitCode.PARENT_GONE)


def test_a_start_interrupted_after_popen_returned_kills_and_reaps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = open_fds()
    started: list[subprocess.Popen[bytes]] = []

    def popen(*args: Any, **kwargs: Any) -> subprocess.Popen[bytes]:
        child = subprocess.Popen(*args, **kwargs)  # noqa: S603
        started.append(child)
        return child

    real = os.set_blocking

    def interrupt(fd: int, blocking: bool) -> None:
        monkeypatch.setattr(os, "set_blocking", real)
        raise Interrupted

    monkeypatch.setattr(os, "set_blocking", interrupt)
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=popen)
    with pytest.raises(Interrupted):
        executor.run("echo", {}, timeout=10)
    assert open_fds() == before
    assert started[0].returncode is not None  # reaped
    assert executor._active is None


def test_a_failing_pipe_is_an_isolation_failure_without_a_leak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = open_fds()
    real = os.pipe
    calls: list[int] = []

    def pipe() -> tuple[int, int]:
        calls.append(1)
        if len(calls) == 3:
            raise OSError(24, "Too many open files")
        return real()

    monkeypatch.setattr(os, "pipe", pipe)
    with pytest.raises(IsolationFailure, match=r"could not be started \(OSError\)"):
        worker_executor().run("echo", {}, timeout=10)
    monkeypatch.undo()
    assert open_fds() == before


def test_the_shield_wraps_the_start() -> None:
    entered: list[str] = []

    @contextlib.contextmanager
    def shield() -> Iterator[None]:
        entered.append("enter")
        yield
        entered.append("exit")

    executor = ProcessExecutor(worker_launch(), SystemClock(), shield=shield)
    assert executor.run("echo", {"n": 1}, timeout=TIMEOUT) == {"echo": {"n": 1}}
    assert entered == ["enter", "exit"]


def test_a_reap_interrupted_by_a_stop_request_runs_again() -> None:
    executor = worker_executor()
    real_reap = executor._reap
    calls: list[int] = []

    def reap_once_interrupted(worker: process._Worker) -> int | None:
        calls.append(1)
        if len(calls) == 1:
            process._signal(worker)
            raise Interrupted
        return real_reap(worker)

    executor._reap = reap_once_interrupted  # type: ignore[method-assign]
    before = open_fds()
    with pytest.raises(Interrupted):
        executor.run("echo", {}, timeout=TIMEOUT)
    assert len(calls) == 2
    assert open_fds() == before


class TestMoreInternals(_ChildRig):
    """More deterministic paths (the fixtures of TestInternals)."""

    def test_a_request_written_in_parts(self, child: subprocess.Popen[bytes]) -> None:
        worker = self.worker(child)
        request = worker.request
        assert request is not None
        with contextlib.suppress(BlockingIOError):
            while True:
                os.write(request, b"x" * 65536)
        os.read(self.write_ends[2], 4096)  # the worker reads a little
        state = process._Conversation(ready=True, pending=b"y" * 60_000)
        poller = select.poll()
        poller.register(request, select.POLLOUT)
        worker_executor()._write_request(worker, state, poller)
        assert 0 < len(state.pending) < 60_000
        assert worker.request == request  # still open for the rest
        worker_executor()._end(worker)
        self.close()

    def test_the_drain_stops_at_a_result(self, child: subprocess.Popen[bytes]) -> None:
        worker = self.worker(child)
        messages: list[JsonObject] = [
            {"type": "event", "event": {"n": 1}},
            {"type": "result", "result": {}, "usage": {}},
            {"type": "event", "event": {"n": 2}},
        ]
        os.write(self.write_ends[0], b"".join(encode_frame(message) for message in messages))
        os.close(self.write_ends[0])
        seen: list[JsonObject] = []
        worker_executor()._drain(worker, FrameBuffer(), seen.append)
        assert seen == [{"n": 1}]
        worker_executor()._end(worker)
        self.close()
