"""Tasks that tests run in real worker processes (the process executor).

Every task here installs the H2 network guard first (``tests/support/h2.py``),
so such a worker cannot reach the network even when it runs a production task
with the real libraries. The worker reaches this module through the test
launch's extra path (the project root); a worker that drops privileges
refuses such a path (D-163), so these tasks need a non-root parent.
"""

from __future__ import annotations

import errno
import functools
import json
import logging
import os
import resource
import struct
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from frame_gallery.isolation import worker_main
from frame_gallery.isolation.executor import EventSink, JsonObject
from tests.support import h2

type Task = Callable[..., JsonObject]

_log = logging.getLogger("tests.worker")


def guarded(function: Task) -> Task:
    @functools.wraps(function)
    def run(*args: Any) -> JsonObject:
        h2.install()
        return function(*args)

    return run


@guarded
def echo(payload: JsonObject) -> JsonObject:
    return {"echo": payload}


@guarded
def events(payload: JsonObject, emit: EventSink) -> JsonObject:
    """Sends ``payload["events"]`` (pausing ``gap`` seconds after the first),
    then sleeps ``payload["then_sleep"]``."""
    sent = payload.get("events", [])
    gap = payload.get("gap", 0)
    assert isinstance(sent, list)
    assert isinstance(gap, int | float)
    for index, event in enumerate(sent):
        assert isinstance(event, dict)
        emit(event)
        if index == 0:
            time.sleep(gap)
    pause = payload.get("then_sleep", 0)
    assert isinstance(pause, int | float)
    time.sleep(pause)
    return {"sent": len(sent)}


@guarded
def sleep(payload: JsonObject) -> JsonObject:
    seconds = payload.get("seconds", 60)
    assert isinstance(seconds, int | float)
    time.sleep(seconds)
    return {}


@guarded
def crash(payload: JsonObject) -> JsonObject:
    del payload
    msg = "a task failure"
    raise RuntimeError(msg)


@guarded
def memory(payload: JsonObject) -> JsonObject:
    del payload
    raise MemoryError


@guarded
def exit_now(payload: JsonObject) -> JsonObject:
    """Ends the worker without a result, as a fatal crash would."""
    code = payload.get("code", 1)
    assert isinstance(code, int)
    sys.stderr.write("dying on purpose\n")
    sys.stderr.flush()
    os._exit(code)


@guarded
def not_json(payload: JsonObject) -> JsonObject:
    del payload
    return {"value": {1, 2}}  # type: ignore[dict-item]


@guarded
def logs(payload: JsonObject) -> JsonObject:
    """``payload["count"]`` records, one of them long, then a secret."""
    count = payload.get("count", 1)
    assert isinstance(count, int)
    for index in range(count):
        _log.warning("record %d %s", index, "x" * (5000 if index == 3 else 1))
    _log.error("a critical-looking\nline")
    return {"logged": count}


@guarded
def raw(payload: JsonObject, emit: EventSink | None = None) -> JsonObject:
    """Writes ``payload["hex"]`` to the result pipe as it is, then sleeps;
    registered both with and without an event sink."""
    del emit
    data = payload.get("hex", "")
    assert isinstance(data, str)
    os.write(worker_main.result_fd(), bytes.fromhex(data))
    time.sleep(60)
    return {}


@guarded
def frame(payload: JsonObject, emit: EventSink | None = None) -> JsonObject:
    """Writes ``payload["message"]`` as one frame, then sleeps ``then_sleep``;
    registered both with and without an event sink."""
    del emit
    body = json.dumps(payload["message"]).encode()
    os.write(worker_main.result_fd(), struct.pack("!I", len(body)) + body)
    code = payload.get("then_exit")
    if isinstance(code, int):
        os._exit(code)
    pause = payload.get("then_sleep", 60)
    assert isinstance(pause, int | float)
    time.sleep(pause)
    return {"after": "frame"}


@guarded
def stderr_flood(payload: JsonObject) -> JsonObject:
    lines = payload.get("lines", 1000)
    assert isinstance(lines, int)
    for index in range(lines):
        sys.stderr.write(f"line {index}\x1b[31m\n")
    sys.stderr.flush()
    return {}


@guarded
def report(payload: JsonObject) -> JsonObject:
    """What the bootstrap left in force, observed from inside the worker
    (the §11.3 bootstrap test)."""
    del payload
    mask = os.umask(0)
    os.umask(mask)
    names = ("RLIMIT_AS", "RLIMIT_CPU", "RLIMIT_FSIZE", "RLIMIT_NOFILE", "RLIMIT_CORE")
    limits = {
        name: list(resource.getrlimit(getattr(resource, name))) for name in (*names, "RLIMIT_NPROC")
    }
    raised = {}
    for name, (soft, hard) in limits.items():
        if hard == resource.RLIM_INFINITY:
            raised[name] = "unlimited"
            continue
        try:
            resource.setrlimit(getattr(resource, name), (soft, hard + 1))
        except (ValueError, OSError) as exc:
            raised[name] = type(exc).__name__
        else:
            raised[name] = "raised"
    observed: dict[str, Any] = {
        "uid": os.geteuid(),
        "gid": os.getegid(),
        "groups": sorted(os.getgroups()),
        "umask": mask,
        "limits": limits,
        "raise_limit": raised,
        "environment": dict(os.environ),
        "cwd": str(Path.cwd()),
        "ppid": os.getppid(),
        "fds": _open_fds(),
        "flags": {
            "isolated": sys.flags.isolated,
            "dont_write_bytecode": sys.flags.dont_write_bytecode,
        },
        "modules": sorted(
            {name.split(".")[0] for name in sys.modules}
            - set(sys.stdlib_module_names)
            - {"__main__"}
        ),
        "pid": os.getpid(),
        "pgrp": os.getpgrp(),
        "sid": os.getsid(0),
        "linux": _linux_controls(),
    }
    return observed


def _linux_controls() -> dict[str, object] | None:
    """On Linux, the parent-death signal, no-new-privileges, dumpability and
    capability sets, read here and not through the bootstrap's own code."""
    linux = sys.platform.startswith("linux")  # not a mypy platform check: both are typed
    if not linux:
        return None
    import ctypes  # noqa: PLC0415

    prctl = ctypes.CDLL(None, use_errno=True).prctl
    signal_number = ctypes.c_int(0)
    prctl(2, ctypes.byref(signal_number), 0, 0, 0)  # PR_GET_PDEATHSIG
    status = dict(
        line.split(":", 1)
        for line in Path("/proc/self/status").read_text().splitlines()
        if ":" in line
    )
    return {
        "pdeathsig": signal_number.value,
        "dumpable": prctl(3, 0, 0, 0, 0),  # PR_GET_DUMPABLE
        "no_new_privs": prctl(39, 0, 0, 0, 0),  # PR_GET_NO_NEW_PRIVS
        "capabilities": {
            name: int(status[name].strip(), 16) for name in ("CapInh", "CapPrm", "CapEff", "CapAmb")
        },
    }


EMULATORS: Final = ("/run/rosetta/rosetta",)
"""Emulators that keep descriptors in the process they run: Docker Desktop
runs amd64 containers under Rosetta, which holds itself and the emulated
binary open in every process."""


def _target(fd: int) -> str | None:
    try:
        return str(Path(f"/proc/self/fd/{fd}").readlink())
    except OSError:
        return None  # no /proc here (macOS), or the descriptor just closed


def _open_fds() -> list[int]:
    """The worker's open descriptors, without an emulator's own ones."""
    found = []
    for fd in range(64):
        try:
            os.fstat(fd)
        except OSError:
            continue
        found.append(fd)
    targets = {fd: _target(fd) for fd in found}
    if any(target in EMULATORS for target in targets.values()):
        own = {*EMULATORS, str(Path(sys.executable).resolve())}
        found = [fd for fd in found if targets[fd] not in own]
    return found


@guarded
def spawn(payload: JsonObject) -> JsonObject:
    """Tries to start a process and a thread (the process limit is 0)."""
    del payload
    outcome: dict[str, Any] = {}
    try:
        pid = os.fork()
    except OSError as exc:
        outcome["fork"] = errno.errorcode.get(exc.errno or 0, "error")
    else:
        if pid == 0:
            os._exit(0)
        os.waitpid(pid, 0)
        outcome["fork"] = "started"
    try:
        thread = threading.Thread(target=lambda: None)
        thread.start()
        thread.join()
    except RuntimeError as exc:
        outcome["thread"] = type(exc).__name__
    else:
        outcome["thread"] = "started"
    return outcome


@guarded
def orphan(payload: JsonObject) -> JsonObject:
    """Writes its pid to ``payload["pid_file"]`` and waits to be orphaned."""
    Path(str(payload["pid_file"])).write_text(str(os.getpid()))
    time.sleep(60)
    return {}


# Production tasks, behind the H2 guard.


@guarded
def guarded_prepare(payload: JsonObject) -> JsonObject:
    from frame_gallery.imaging.worker_tasks import prepare_task  # noqa: PLC0415

    return prepare_task(payload)


@guarded
def guarded_inspect(payload: JsonObject, emit: EventSink) -> JsonObject:
    from frame_gallery.imaging.worker_tasks import inspect_task  # noqa: PLC0415

    return inspect_task(payload, emit)


@guarded
def guarded_deliver(payload: JsonObject, emit: EventSink) -> JsonObject:
    """The production ``deliver`` task, with the real library: behind H2,
    its first connection attempt is blocked."""
    from frame_gallery.tv.samsung_task import deliver_task  # noqa: PLC0415

    return deliver_task(payload, emit)


@guarded
def fake_deliver(payload: JsonObject, emit: EventSink) -> JsonObject:
    """The production delivery logic over the stand-in library.

    The script is the nearest ``fake-tv.json`` at or above the delivery
    file's folder (a runner's workspace is created during the run, so a test
    puts it above); calls go to ``fake-tv-calls.json`` and the worker's pid to
    ``fake-tv-worker.pid`` next to it.
    """
    from frame_gallery.tv.contract import TvRequest  # noqa: PLC0415
    from frame_gallery.tv.samsung_task import quiet_library, run_delivery  # noqa: PLC0415
    from tests.support.fake_samsungtvws import Recorder, Script, make_library  # noqa: PLC0415

    request = TvRequest.from_json(payload)
    folder = next(
        (parent for parent in request.jpeg_path.parents if (parent / "fake-tv.json").is_file()),
        request.jpeg_path.parent,
    )
    (folder / "fake-tv-worker.pid").write_text(str(os.getpid()))
    quiet_library()
    script = Script.load(folder / "fake-tv.json")
    library = make_library(script, Recorder(folder / "fake-tv-calls.json"))
    return run_delivery(library, request, emit)


@guarded
def close_stderr(payload: JsonObject) -> JsonObject:
    """Closes stderr before it ends, so the parent sees that end first."""
    del payload
    sys.stderr.write("last words\n")
    sys.stderr.flush()
    os.close(2)
    time.sleep(0.3)
    return {"closed": True}


@guarded
def fork_and_sleep(payload: JsonObject, emit: EventSink) -> JsonObject:
    """Forks a child that stays in the worker's process group and sleeps;
    writes its pid to ``payload["pid_file"]``, sends one event, and sleeps."""
    pid = os.fork()
    if pid == 0:
        time.sleep(60)
        os._exit(0)
    Path(str(payload["pid_file"])).write_text(str(pid))
    emit({"child": pid})
    time.sleep(60)
    return {}


@guarded
def tick(payload: JsonObject, emit: EventSink) -> JsonObject:
    """Sends ``{"t": time.monotonic()}`` every 10 ms (the clock every process
    on the host shares), for up to ``payload["seconds"]``."""
    seconds = payload.get("seconds", 30)
    assert isinstance(seconds, int | float)
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        emit({"t": time.monotonic()})
        time.sleep(0.01)
    return {}


@guarded
def big_event(payload: JsonObject, emit: EventSink) -> JsonObject:
    """Sends one event of ``payload["size"]`` characters."""
    size = payload["size"]
    assert isinstance(size, int)
    emit({"x": "y" * size})
    return {}


@guarded
def big_result(payload: JsonObject) -> JsonObject:
    size = payload["size"]
    assert isinstance(size, int)
    return {"x": "y" * size}


@guarded
def stderr_line(payload: JsonObject) -> JsonObject:
    """Writes ``payload["text"]`` to stderr, as it is."""
    sys.stderr.write(str(payload["text"]))
    sys.stderr.flush()
    return {}


@guarded
def big_frame(payload: JsonObject, emit: EventSink | None = None) -> JsonObject:
    """Writes one valid frame whose body (an event or a result) holds
    ``payload["size"]`` characters: built here, so the request stays small."""
    del emit
    size = payload["size"]
    assert isinstance(size, int)
    body = {"x": "y" * size}
    message = (
        {"type": "event", "event": body}
        if payload["kind"] == "event"
        else {"type": "result", "result": body, "usage": {}}
    )
    data = json.dumps(message).encode()
    os.write(worker_main.result_fd(), struct.pack("!I", len(data)) + data)
    time.sleep(60)
    return {}
