"""The process executor (§4.3, §11.3, D-109, D-139, D-141, D-163).

Each task runs in a new worker process: ``python -I -B -c BOOT``, in its own
process group, with a fixed environment, ``/`` as its working directory, and
only four descriptors: the request pipe, the result pipe, a lifeline pipe
(its end in the parent closes when the parent dies), and stderr, a pipe whose
last 4 KiB the parent keeps. The worker's configuration is on its command
line; it holds no secret.

The conversation (frames of :mod:`frame_gallery.isolation.framing`):

1. The worker's bootstrap ends with ``ready`` and what it verified, which
   must match what the parent asked for. Until then, the worker has read
   nothing but its configuration: any end other than a kill is an
   :class:`IsolationFailure`, which the run reports as ``internal_error``.
2. The parent sends the request.
3. ``event`` messages go to ``on_event`` as they arrive; ``log`` messages
   are re-emitted under ``frame_gallery.worker.<task>``, capped at WARNING,
   sanitized, and bounded (excess ones are dropped, never fatal).
4. ``result``, or ``failure`` (``crash``, ``memory``, or ``protocol``).

The kill timer is the task's timeout. ``should_stop`` is polled at least
every 50 ms. On either, the worker's group and the worker itself get
``SIGKILL``; then the pipe is read to its end (bounded by 1 s and 1 MiB, not
by a message count), every complete event is still relayed, and the run
fails with ``timeout`` or ``stopped``. After every worker, on every path,
its group and the worker are killed, the worker is reaped, and the
descriptors are closed: :meth:`run` returns or raises only once the worker
is dead. :meth:`terminate_all` kills the active worker from any thread.
"""

from __future__ import annotations

import logging
import os
import re
import select
import signal
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import frame_gallery
from frame_gallery.budget.clock import Clock
from frame_gallery.isolation.channel import ChannelError
from frame_gallery.isolation.executor import (
    EventSink,
    IsolationFailure,
    JsonObject,
    StopCheck,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.isolation.framing import FrameBuffer, encode_frame
from frame_gallery.isolation.launch import (
    PRODUCTION_TASKS,
    WORKER_ENVIRONMENT,
    WORKER_ID,
    WORKER_UMASK,
    Channels,
    ExitCode,
    Limit,
    MessageType,
    TaskEntry,
    WorkerConfig,
    ordered_limits,
)
from frame_gallery.logs.summary import sanitize_for_log

BOOT: Final = (
    "import sys;sys.path[:0]=sys.argv[2:];"
    "from frame_gallery.isolation.worker_main import main;main(sys.argv[1])"
)
"""The whole program the interpreter is given: no decision is made here."""

POLL_S: Final = 0.05
DRAIN_S: Final = 1.0
DRAIN_BYTES: Final = 1024 * 1024
REAP_S: Final = 2.0
READ_BYTES: Final = 64 * 1024
MAX_LOGS: Final = 100
MAX_LOG_TEXT: Final = 1000
STDERR_TAIL_BYTES: Final = 4096
STDERR_LINES: Final = 30

_LEVELS: Final = frozenset({10, 20, 30, 40, 50})
_LOGGER: Final = re.compile(r"[A-Za-z0-9_.]{1,64}")
_FAILURES: Final = {
    "crash": WorkerErrorKind.CRASH,
    "memory": WorkerErrorKind.MEMORY,
    "protocol": WorkerErrorKind.PROTOCOL,
}

_log = logging.getLogger("frame_gallery.isolation")


def _source_root() -> str:
    return str(Path(frame_gallery.__file__).resolve().parent.parent)


@dataclass(frozen=True, slots=True)
class Launch:
    """How workers are started. Production uses :meth:`production`; the
    fields after ``platform`` exist for tests only, and a worker that drops
    privileges refuses test paths (D-163)."""

    python: str
    source_root: str
    tasks: Mapping[str, TaskEntry]
    identity: tuple[int, int] | None
    require_pdeathsig: bool
    platform: str
    skip_limits: frozenset[Limit] = field(default=frozenset())
    extra_paths: tuple[str, ...] = ()
    extra_environment: Mapping[str, str] = field(default_factory=dict)
    """Added to the worker's environment but not to what it expects: lets a
    test prove that the worker refuses an environment it was not promised."""

    @classmethod
    def production(cls) -> Launch:
        """Root drops every worker to 65534; Linux requires the parent-death
        signal and enforces every limit. On a development host (not Linux,
        not root), the address-space limit, which the platform cannot set,
        is skipped and the worker keeps the developer's identity."""
        is_linux = sys.platform.startswith("linux")
        return cls(
            python=sys.executable,
            source_root=_source_root(),
            tasks=PRODUCTION_TASKS,
            identity=(WORKER_ID, WORKER_ID) if os.geteuid() == 0 else None,
            require_pdeathsig=is_linux,
            platform=sys.platform,
            skip_limits=frozenset() if is_linux else frozenset({Limit.ADDRESS_SPACE}),
        )

    @property
    def enforced(self) -> bool:
        """Whether every isolation step of §11.3 is in force."""
        return self.identity is not None and self.require_pdeathsig and not self.skip_limits


@dataclass
class _Worker:
    task: str
    entry: TaskEntry
    config: WorkerConfig
    process: subprocess.Popen[bytes]
    results: int
    stderr: int
    request: int | None
    lifeline: int
    reaped: bool = False
    stderr_tail: bytearray = field(default_factory=bytearray)
    stderr_cut: bool = False


@dataclass
class _Conversation:
    ready: bool = False
    pending: bytes = b""
    refused: str | None = None
    failure: tuple[WorkerErrorKind, str] | None = None
    logs: int = 0
    dropped_logs: int = 0


class _Abort(Exception):
    """End the conversation: kill the worker, then raise ``error``."""

    def __init__(self, error: Exception, *, drain: bool = False) -> None:
        super().__init__(str(error))
        self.error = error
        self.drain = drain


def _never() -> bool:
    return False


def _signal(worker: _Worker) -> None:
    """``SIGKILL`` to the worker's process group, then to the worker itself:
    it may have left its group (§14)."""
    for send in (os.killpg, os.kill):
        try:
            send(worker.process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            continue


class ProcessExecutor:
    """The ``Executor`` port over worker processes (Phase 5)."""

    def __init__(
        self,
        launch: Launch,
        clock: Clock,
        *,
        popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
        log_level: Callable[[], int] | None = None,
    ) -> None:
        self._launch = launch
        self._clock = clock
        self._popen = popen
        self._log_level = log_level or (
            lambda: logging.getLogger("frame_gallery").getEffectiveLevel()
        )
        self._lock = threading.Lock()
        self._active: _Worker | None = None
        self.last_usage: JsonObject | None = None
        """The last worker's own peak memory and CPU time (measurements)."""

    # ----------------------------------------------------------------- run

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
    ) -> JsonObject:
        """See :class:`~frame_gallery.isolation.executor.Executor`. Raises
        :class:`WorkerError` and :class:`IsolationFailure`."""
        if not timeout > 0:
            msg = f"timeout must be positive, got {timeout!r}"
            raise ValueError(msg)
        entry = self._launch.tasks.get(task)
        if entry is None:
            raise WorkerError(WorkerErrorKind.UNKNOWN_TASK, sanitize_for_log(task, max_length=40))
        try:
            request = encode_frame({"type": MessageType.REQUEST.value, "payload": payload})
        except ChannelError as error:
            raise WorkerError(WorkerErrorKind.PROTOCOL, f"request: {error}") from None
        stop = should_stop or _never
        if stop():
            raise WorkerError(WorkerErrorKind.STOPPED)
        deadline = self._clock.monotonic() + timeout
        worker = self._spawn(task, entry)
        try:
            return self._converse(worker, request, deadline, on_event, stop)
        finally:
            self._end(worker)

    # --------------------------------------------------------------- spawn

    def _spawn(self, task: str, entry: TaskEntry) -> _Worker:
        launch = self._launch
        request_r, request_w = os.pipe()
        results_r, results_w = os.pipe()
        stderr_r, stderr_w = os.pipe()
        lifeline_r, lifeline_w = os.pipe()
        config = WorkerConfig(
            task=task,
            module=entry.module,
            function=entry.function,
            events=entry.events,
            parent_pid=os.getpid(),
            identity=launch.identity,
            require_pdeathsig=launch.require_pdeathsig,
            umask=WORKER_UMASK,
            limits=ordered_limits(entry.limits, skip=launch.skip_limits),
            environment=WORKER_ENVIRONMENT,
            platform=launch.platform,
            fds=Channels(request_r, results_w, lifeline_r),
            log_level=self._log_level(),
            extra_paths=launch.extra_paths,
        )
        argv = [
            launch.python,
            "-I",
            "-B",
            "-c",
            BOOT,
            config.to_json(),
            launch.source_root,
            *launch.extra_paths,
        ]
        try:
            process = self._popen(
                argv,
                pass_fds=(request_r, results_w, lifeline_r),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=stderr_w,
                env={**WORKER_ENVIRONMENT, **launch.extra_environment},
                cwd="/",
                close_fds=True,
                process_group=0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            for fd in (request_w, results_r, stderr_r, lifeline_w):
                os.close(fd)
            msg = f"the worker could not be started ({type(exc).__name__})"
            raise IsolationFailure(msg) from None
        finally:
            for fd in (request_r, results_w, stderr_w, lifeline_r):
                os.close(fd)
        for fd in (request_w, results_r, stderr_r):
            os.set_blocking(fd, False)
        worker = _Worker(task, entry, config, process, results_r, stderr_r, request_w, lifeline_w)
        with self._lock:
            self._active = worker
        return worker

    # ------------------------------------------------------- conversation

    def _converse(
        self,
        worker: _Worker,
        request: bytes,
        deadline: float,
        on_event: EventSink | None,
        stop: StopCheck,
    ) -> JsonObject:
        state = _Conversation()
        frames = FrameBuffer()
        poller = select.poll()
        poller.register(worker.results, select.POLLIN)
        poller.register(worker.stderr, select.POLLIN)
        try:
            while True:
                left = deadline - self._clock.monotonic()
                if left <= 0:
                    raise _Abort(WorkerError(WorkerErrorKind.TIMEOUT), drain=True)
                if stop():
                    raise _Abort(WorkerError(WorkerErrorKind.STOPPED), drain=True)
                if state.pending and worker.request is not None:
                    poller.register(worker.request, select.POLLOUT)
                for fd, _ in poller.poll(min(POLL_S, left) * 1000):
                    if fd == worker.stderr:
                        self._read_stderr(worker, poller)
                    elif fd == worker.request:
                        self._write_request(worker, state, poller)
                    else:
                        done = self._read_results(worker, state, frames, request, on_event)
                        if done is not None:
                            return done
        except _Abort as abort:
            self._kill(worker)
            if abort.drain and state.ready:
                self._drain(worker, frames, on_event)
            raise abort.error from None

    def _read_results(
        self,
        worker: _Worker,
        state: _Conversation,
        frames: FrameBuffer,
        request: bytes,
        on_event: EventSink | None,
    ) -> JsonObject | None:
        chunk = os.read(worker.results, READ_BYTES)
        if not chunk:
            raise self._ended(worker, state)
        try:
            messages = frames.feed(chunk)
        except ChannelError as error:
            raise _Abort(self._violation(state, f"channel: {error}")) from None
        for message in messages:
            done = self._handle(worker, state, message, request, on_event)
            if done is not None:
                return done
        return None

    def _violation(self, state: _Conversation, detail: str) -> Exception:
        if not state.ready:
            return IsolationFailure(
                f"the worker broke the protocol during its bootstrap ({detail})"
            )
        return WorkerError(WorkerErrorKind.PROTOCOL, detail)

    def _handle(
        self,
        worker: _Worker,
        state: _Conversation,
        message: JsonObject,
        request: bytes,
        on_event: EventSink | None,
    ) -> JsonObject | None:
        kind = message.get("type")
        if kind == MessageType.LOG.value:
            self._relay_log(worker.task, state, message)
        elif not state.ready and kind == MessageType.READY.value:
            self._check_ready(worker.config, message)
            state.ready, state.pending = True, request
        elif not state.ready and kind == MessageType.REFUSED.value:
            reason = message.get("reason")
            state.refused = reason if isinstance(reason, str) else "unknown"
        elif state.ready and kind == MessageType.EVENT.value and set(message) == {"type", "event"}:
            event = message["event"]
            if not worker.entry.events or not isinstance(event, dict) or on_event is None:
                raise _Abort(WorkerError(WorkerErrorKind.PROTOCOL, "unexpected event"))
            try:
                on_event(event)
            except ValueError as error:
                raise _Abort(WorkerError(WorkerErrorKind.PROTOCOL, f"event: {error}")) from None
        elif state.ready and kind == MessageType.RESULT.value:
            return self._result(message)
        elif state.ready and kind == MessageType.FAILURE.value:
            state.failure = self._failure(message)
        else:
            what = sanitize_for_log(str(kind), max_length=20)
            raise _Abort(self._violation(state, f"unexpected message {what}"))
        return None

    def _check_ready(self, config: WorkerConfig, message: JsonObject) -> None:
        """The worker's own account of its bootstrap must match the request."""
        report = message.get("report")
        expected_limits = {limit.value: [value, value] for limit, value in config.limits}
        ok = (
            set(message) == {"type", "report"}
            and isinstance(report, dict)
            and report.get("umask") == config.umask
            and report.get("limits") == expected_limits
            and report.get("environment") == sorted(config.environment)
        )
        if ok and config.identity is not None and isinstance(report, dict):
            uid, gid = config.identity
            ok = (
                report.get("uid") == uid and report.get("gid") == gid and report.get("groups") == []
            )
        if not ok:
            msg = "the worker's bootstrap report does not match what was asked"
            raise _Abort(IsolationFailure(msg))

    def _result(self, message: JsonObject) -> JsonObject:
        result, usage = message.get("result"), message.get("usage")
        if set(message) != {"type", "result", "usage"} or not isinstance(result, dict):
            raise _Abort(WorkerError(WorkerErrorKind.PROTOCOL, "result: not a JSON object"))
        self.last_usage = usage if isinstance(usage, dict) else None
        return result

    def _failure(self, message: JsonObject) -> tuple[WorkerErrorKind, str]:
        kind, detail = message.get("kind"), message.get("detail")
        if (
            set(message) != {"type", "kind", "detail"}
            or not isinstance(kind, str)
            or kind not in _FAILURES
            or not isinstance(detail, str)
        ):
            raise _Abort(WorkerError(WorkerErrorKind.PROTOCOL, "failure: not understood"))
        return _FAILURES[kind], sanitize_for_log(detail, max_length=80)

    def _ended(self, worker: _Worker, state: _Conversation) -> _Abort:
        """The result pipe closed without a result."""
        code = self._reap(worker)
        if not state.ready:
            reason = sanitize_for_log(state.refused or f"exit status {code}", max_length=60)
            msg = f"the worker refused to run or died during its bootstrap ({reason})"
            return _Abort(IsolationFailure(msg))
        if state.failure is not None:
            return _Abort(WorkerError(*state.failure))
        if code == ExitCode.MEMORY:
            return _Abort(WorkerError(WorkerErrorKind.MEMORY, f"exit status {code}"))
        return _Abort(WorkerError(WorkerErrorKind.CRASH, f"exit status {code}"))

    def _write_request(self, worker: _Worker, state: _Conversation, poller: Any) -> None:
        assert worker.request is not None  # noqa: S101 - registered only while open
        try:
            written = os.write(worker.request, state.pending)
        except BlockingIOError:
            return
        except OSError:
            written = len(state.pending)  # the worker is gone; its end tells the rest
        state.pending = state.pending[written:]
        if not state.pending:
            poller.unregister(worker.request)
            os.close(worker.request)
            worker.request = None

    # ---------------------------------------------------------------- logs

    def _relay_log(self, task: str, state: _Conversation, message: JsonObject) -> None:
        level, name, text = message.get("level"), message.get("logger"), message.get("text")
        if (
            state.logs >= MAX_LOGS
            or set(message) != {"type", "level", "logger", "text"}
            or not isinstance(level, int)
            or level not in _LEVELS
            or not isinstance(name, str)
            or _LOGGER.fullmatch(name) is None
            or not isinstance(text, str)
            or len(text) > MAX_LOG_TEXT
        ):
            state.dropped_logs += 1
            return
        state.logs += 1
        text = sanitize_for_log(text, max_length=MAX_LOG_TEXT)
        logger = logging.getLogger(f"frame_gallery.worker.{task}")
        logger.log(min(level, logging.WARNING), "%s: %s", name, text)

    def _read_stderr(self, worker: _Worker, poller: Any) -> None:
        if self._take_stderr(worker) == 0:
            poller.unregister(worker.stderr)

    @staticmethod
    def _take_stderr(worker: _Worker) -> int:
        """Read what stderr holds now into the bounded tail. Returns the bytes
        read: 0 at its end, -1 when nothing is there yet."""
        try:
            chunk = os.read(worker.stderr, READ_BYTES)
        except BlockingIOError:
            return -1
        worker.stderr_tail += chunk
        if len(worker.stderr_tail) > STDERR_TAIL_BYTES:
            del worker.stderr_tail[: len(worker.stderr_tail) - STDERR_TAIL_BYTES]
            worker.stderr_cut = True
        return len(chunk)

    # ------------------------------------------------------------ the end

    def _drain(self, worker: _Worker, frames: FrameBuffer, on_event: EventSink | None) -> None:
        """After a kill: read the result pipe to its end (bounded by time and
        bytes) and relay every complete event it still held."""
        messages: list[JsonObject] = []
        end = self._clock.monotonic() + DRAIN_S
        total = 0
        os.set_blocking(worker.results, True)
        poller = select.poll()
        poller.register(worker.results, select.POLLIN)
        while total < DRAIN_BYTES:
            left = end - self._clock.monotonic()
            if left <= 0 or not poller.poll(left * 1000):
                break
            chunk = os.read(worker.results, READ_BYTES)
            if not chunk:
                break
            total += len(chunk)
            try:
                messages += frames.feed(chunk)
            except ChannelError:
                break
        if not worker.entry.events or on_event is None:
            return
        for message in messages:
            event = message.get("event")
            if message.get("type") != MessageType.EVENT.value or not isinstance(event, dict):
                continue
            try:
                on_event(event)
            except ValueError:
                return

    def _kill(self, worker: _Worker) -> None:
        with self._lock:
            if not worker.reaped:
                _signal(worker)

    def _reap(self, worker: _Worker) -> int | None:
        """Kill and reap under the lock, so :meth:`terminate_all` never
        signals an ID the kernel may already have reused."""
        with self._lock:
            _signal(worker)
            try:
                code = worker.process.wait(timeout=REAP_S)
            except subprocess.TimeoutExpired:
                _log.error("worker %s did not end after SIGKILL", worker.process.pid)
                return None
            worker.reaped = True
            if self._active is worker:
                self._active = None
        return code

    def _end(self, worker: _Worker) -> None:
        if not worker.reaped:
            self._reap(worker)
        for fd in (worker.results, worker.request, worker.lifeline):
            if fd is not None:
                os.close(fd)
        worker.request = None
        while self._take_stderr(worker) > 0:
            continue  # only what is there now: another holder cannot stall the end
        os.close(worker.stderr)
        self._log_stderr(worker)

    def _log_stderr(self, worker: _Worker) -> None:
        """The tail of the worker's stderr, at DEBUG only (§18.1)."""
        if not worker.stderr_tail:
            return
        lines = bytes(worker.stderr_tail).decode("utf-8", errors="replace").splitlines()
        if worker.stderr_cut:
            lines = lines[1:]
        logger = logging.getLogger(f"frame_gallery.worker.{worker.task}")
        for line in lines[-STDERR_LINES:]:
            logger.debug("stderr| %s", sanitize_for_log(line, max_length=300))

    def terminate_all(self) -> None:
        """Kill the active worker, if any (from any thread; idempotent)."""
        with self._lock:
            worker = self._active
        if worker is not None:
            self._kill(worker)
