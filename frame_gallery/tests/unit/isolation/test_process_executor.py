"""The process executor with real worker processes (isolation/process.py; §11.3, D-163).

Every worker here runs a task from tests/support/worker_tasks.py, which
installs the H2 network guard first. The launch is this host's production
launch plus the project root on the worker's path. Root-only and Linux-only
assertions of the bootstrap test are marked; ``FRAME_GALLERY_REQUIRE_ISOLATION=1``
turns their skips into failures (for the Phase 6 container).
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
from frame_gallery.isolation.framing import FrameBuffer, encode_frame
from frame_gallery.isolation.launch import (
    PRODUCTION_TASKS,
    WORKER_ENVIRONMENT,
    WORKER_UMASK,
    Limit,
    ordered_limits,
)
from frame_gallery.isolation.process import DRAIN_S, MAX_LOGS, Launch, ProcessExecutor
from frame_gallery.tv.contract import TvRequest
from tests.support.images import save_jpeg
from tests.support.processes import PROJECT_ROOT, worker_executor, worker_launch

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


def require_isolation(condition: bool, reason: str) -> None:
    if condition:
        return
    if os.environ.get("FRAME_GALLERY_REQUIRE_ISOLATION") == "1":
        pytest.fail(f"required here, but {reason}")
    pytest.skip(reason)


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


def test_a_timeout_also_relays_the_events_written() -> None:
    seen: list[JsonObject] = []
    error = failure(
        "events",
        {"events": [{"n": 1}, {"n": 2}], "then_sleep": 60},
        on_event=seen.append,
        timeout=1.0,
    )
    assert error.kind is WorkerErrorKind.TIMEOUT
    assert seen == [{"n": 1}, {"n": 2}]


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
    executor = worker_executor()
    timer = threading.Timer(0.5, executor.terminate_all)
    timer.start()
    started = time.monotonic()
    with pytest.raises(WorkerError) as caught:
        executor.run("sleep", {"seconds": 60}, timeout=TIMEOUT)
    timer.join()
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
    require_isolation(os.geteuid() != 0, "this test needs a non-root user")
    launch = worker_launch(
        tasks=PRODUCTION_TASKS, extra_paths=(), identity=(os.getuid() + 1, os.getgid())
    )
    executor = ProcessExecutor(launch, SystemClock())
    with pytest.raises(IsolationFailure, match=r"refused to run .*\(privileges:EPERM\)"):
        executor.run("prepare", {}, timeout=10)


def test_test_paths_are_refused_with_an_identity() -> None:
    executor = worker_executor(identity=(os.getuid(), os.getgid()))
    with pytest.raises(IsolationFailure, match=r"\(test_paths\)"):
        executor.run("echo", {}, timeout=10)


def test_a_worker_that_dies_before_ready_is_an_isolation_failure() -> None:
    executor = worker_executor(source_root="/nonexistent")
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
        return subprocess.Popen([argv[0], "-I", "-c", code, *argv[5:]], **kwargs)  # noqa: S603

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
    big: JsonObject = {"blob": "x" * 60_000}
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
    assert report["modules"] == []
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
    require_isolation(sys.platform.startswith("linux"), "RLIMIT_AS is enforced on Linux only")
    report = run("report")
    limits = report["limits"]
    assert isinstance(limits, dict)
    assert limits["RLIMIT_AS"] == [1024**3, 1024**3]
    television = run("report_tv")["limits"]
    assert isinstance(television, dict)
    assert television["RLIMIT_AS"] == [512 * 1024**2] * 2


def test_on_linux_the_worker_cannot_start_a_thread_either() -> None:
    require_isolation(sys.platform.startswith("linux"), "Linux counts threads against RLIMIT_NPROC")
    assert run("spawn")["thread"] == "RuntimeError"


def test_as_root_a_production_worker_drops_to_65534() -> None:
    """Root only (the Phase 6 container): the worker's ready report, which the
    parent checks, must show uid and gid 65534 and no groups; the task then
    fails on its empty request, as a crash, not as an isolation failure."""
    require_isolation(os.geteuid() == 0, "the privilege drop needs root")
    executor = ProcessExecutor(Launch.production(), SystemClock())
    with pytest.raises(WorkerError) as caught:
        executor.run("prepare", {}, timeout=10)
    assert caught.value.kind is WorkerErrorKind.CRASH


# ----------------------------------------------------------------- orphans


ORPHAN_PARENT = textwrap.dedent(
    """
    import sys
    sys.path[:0] = [sys.argv[1], sys.argv[2]]
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
    """The request is written in parts; the worker reads none of it and
    exits, so the rest of the write fails and the run is a crash."""
    ready = [{"type": "ready", "report": expected_report("echo")}]
    executor = ProcessExecutor(worker_launch(), SystemClock(), popen=scripted_boot(ready, 0.5))
    with pytest.raises(WorkerError) as caught:
        executor.run("echo", {"blob": "x" * 66_000}, timeout=10)
    assert caught.value.kind is WorkerErrorKind.CRASH


class TestInternals:
    """Paths that depend on timing, driven directly and deterministically."""

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
        assert seen == []  # the garbage ends the drain before anything is relayed
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


def test_as_root_the_worker_reads_in_and_writes_only_out(tmp_path: Path) -> None:
    """Root only (the Phase 6 container): with the workspace handed to group
    65534 (D-164), the dropped worker reads a source in ``in/``, creates its
    output in ``out/``, and cannot create a file in ``in/``."""
    require_isolation(os.geteuid() == 0, "the privilege drop needs root")
    from frame_gallery.isolation.launch import WORKER_ID  # noqa: PLC0415
    from frame_gallery.store.workspace import RunWorkspace  # noqa: PLC0415

    workspace = RunWorkspace(tmp_path, worker_gid=WORKER_ID)
    paths = workspace.create()
    source = save_jpeg_file(tmp_path)
    handed = paths.inbox / "source-0.bin"
    handed.write_bytes(source.read_bytes())
    handed.chmod(0o640)
    executor = ProcessExecutor(Launch.production(), SystemClock())

    def prepare(output: Path) -> JsonObject:
        request = PrepareRequest(
            source_path=str(handed),
            output_path=str(output),
            declared_format=ImageFormat.JPEG,
            fit_mode=FitMode.CONTAIN,
            background=BLACK,
            landscape_only=True,
            require_near_16_9=False,
            canvas=Size(384, 216),
        )
        return executor.run("prepare", request.to_json(), timeout=20)

    assert prepare(paths.outbox / "delivery-0.jpg")["status"] == "ok"
    assert (paths.outbox / "delivery-0.jpg").stat().st_uid == WORKER_ID
    refused = prepare(paths.inbox / "delivery-1.jpg")
    assert (refused["status"], refused["failure"]) == ("failed", "io")
    workspace.remove()
