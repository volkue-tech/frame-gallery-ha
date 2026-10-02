"""The worker's entry point (§11.3, D-163).

The process executor starts ``python -I -S -B -c BOOT <configuration>
<paths>``; ``BOOT`` puts the paths on ``sys.path`` and calls :func:`main`.
Without ``site``, and with this module importing only the standard library
and the isolation and logging packages, nothing third-party is loaded before
the bootstrap has run.

The conversation, over the pipes the parent passed:

1. the bootstrap (:mod:`frame_gallery.isolation.bootstrap`); on a refusal,
   a ``refused`` message and exit code 70;
2. ``ready``, with what the bootstrap verified;
3. the ``request`` from the parent;
4. the task, which may send ``event`` and ``log`` messages;
5. its ``result`` (with the worker's own peak memory and CPU time), or a
   ``failure`` naming only the exception type; then ``os._exit``, so no
   finalizer or library clean-up can follow.

An event or a result over the 64 KiB message cap is a ``protocol`` failure,
as in the in-process executor.
"""

from __future__ import annotations

import importlib
import os
import resource
import threading
from collections.abc import Callable
from typing import Final, NoReturn

from frame_gallery.isolation.bootstrap import OsOps, RealOs, Refused
from frame_gallery.isolation.bootstrap import run as run_bootstrap
from frame_gallery.isolation.channel import ChannelError, encode_message
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.isolation.framing import read_frame, write_frame
from frame_gallery.isolation.launch import ExitCode, MessageType, WorkerConfig

type Exit = Callable[[int], NoReturn]

_result_fd: int | None = None


def result_fd() -> int:
    """The worker's result pipe, for test tasks that must write raw frames."""
    if _result_fd is None:
        msg = "not inside a worker"
        raise RuntimeError(msg)
    return _result_fd


class _Sender:
    """Writes whole frames to the result pipe, one at a time."""

    def __init__(self, fd: int) -> None:
        self._fd = fd
        self._lock = threading.Lock()

    def __call__(self, message: JsonObject) -> None:
        with self._lock:
            write_frame(self._fd, message)

    def attempt(self, message: JsonObject) -> None:
        """Best effort, for the last message before an exit."""
        try:
            self(message)
        except (OSError, ChannelError):
            return


def main(config_text: str, *, ops: OsOps | None = None, exit_: Exit = os._exit) -> NoReturn:
    global _result_fd  # noqa: PLW0603 - the one accessor for test tasks
    try:
        config = WorkerConfig.from_json(config_text)
    except ValueError:
        exit_(ExitCode.REFUSED)
    _result_fd = config.fds.result
    send = _Sender(config.fds.result)
    try:
        report = run_bootstrap(config, ops or RealOs(), send)
    except Refused as refused:
        send.attempt({"type": MessageType.REFUSED.value, "reason": refused.reason})
        exit_(ExitCode.REFUSED)
    try:
        send({"type": MessageType.READY.value, "report": report})
        payload = _payload(read_frame(config.fds.request))
    except (OSError, ChannelError, ValueError):
        exit_(ExitCode.CHANNEL)
    exit_(_run(config, payload, send))


def _payload(message: JsonObject | None) -> JsonObject:
    if (
        message is None
        or set(message) != {"type", "payload"}
        or message["type"] != MessageType.REQUEST.value
        or not isinstance(message["payload"], dict)
    ):
        msg = "not a request"
        raise ValueError(msg)
    return message["payload"]


class _EventOverCap(Exception):
    """An event over the message cap: the task ends as a protocol failure."""


def _run(config: WorkerConfig, payload: JsonObject, send: _Sender) -> int:
    def emit(event: JsonObject) -> None:
        try:
            encode_message(event)
        except ChannelError:
            raise _EventOverCap from None
        send({"type": MessageType.EVENT.value, "event": event})

    try:
        function = getattr(importlib.import_module(config.module), config.function)
        result = function(payload, emit) if config.events else function(payload)
    except _EventOverCap:
        send.attempt(_failure("protocol", "event"))
        return ExitCode.CHANNEL
    except MemoryError:
        send.attempt(_failure("memory", "MemoryError"))
        return ExitCode.MEMORY
    except BaseException as exc:  # noqa: BLE001 - every task failure is reported
        send.attempt(_failure("crash", type(exc).__name__))
        return ExitCode.CRASH
    try:
        encode_message(result)
        send({"type": MessageType.RESULT.value, "result": result, "usage": usage(config.platform)})
    except ChannelError:
        send.attempt(_failure("protocol", "result"))
        return ExitCode.CHANNEL
    except OSError:
        return ExitCode.CHANNEL
    return 0


def _failure(kind: str, detail: str) -> JsonObject:
    return {"type": MessageType.FAILURE.value, "kind": kind, "detail": detail[:80]}


MAXRSS_UNIT: Final = {"darwin": 1}
"""``ru_maxrss`` is in bytes on macOS and in KiB elsewhere (Linux)."""

STATUS_FILE: Final = "/proc/self/status"
MAX_STATUS_BYTES: Final = 16 * 1024
_PEAKS: Final = {"VmHWM": "max_rss_bytes", "VmPeak": "max_vm_bytes"}


def usage(platform: str, status_file: str = STATUS_FILE) -> JsonObject:
    """The worker's own peak memory and CPU time so far.

    On Linux the peaks come from ``status_file``: ``VmHWM`` (resident) and
    ``VmPeak`` (address space, which ``RLIMIT_AS`` limits). Linux carries a
    process's ``ru_maxrss`` over ``exec``, so there it would also count the
    parent's resident memory at the fork. Elsewhere ``ru_maxrss`` is used and
    the address-space peak is unknown (``None``); so is any peak that the
    file does not give.
    """
    own = resource.getrusage(resource.RUSAGE_SELF)
    report: JsonObject = {
        "max_rss_bytes": own.ru_maxrss * MAXRSS_UNIT.get(platform, 1024),
        "max_vm_bytes": None,
        "cpu_s": round(own.ru_utime + own.ru_stime, 3),
    }
    if platform.startswith("linux"):
        report["max_rss_bytes"] = None
        report.update(_status_peaks(status_file))
    return report


def _status_peaks(status_file: str) -> dict[str, int]:
    """The ``VmHWM`` and ``VmPeak`` lines of ``status_file`` in bytes; the
    ones it lacks, or a file that cannot be read, give nothing."""
    try:
        fd = os.open(status_file, os.O_RDONLY | os.O_CLOEXEC)
        try:
            text = os.read(fd, MAX_STATUS_BYTES).decode("ascii", "replace")
        finally:
            os.close(fd)
    except OSError:
        return {}
    peaks: dict[str, int] = {}
    for line in text.splitlines():
        name, _, value = line.partition(":")
        fields = value.split()
        if name in _PEAKS and len(fields) == 2 and fields[0].isdigit() and fields[1] == "kB":
            peaks[_PEAKS[name]] = int(fields[0]) * 1024
    return peaks
