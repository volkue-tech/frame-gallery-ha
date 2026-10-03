"""The worker bootstrap (§11.3 steps 1-6, D-109, D-163).

These steps run first in every worker, before it reads its request, in the
order of §11.3:

1. **Privileges.** With an identity (the parent is root): ``setgroups([])``,
   then the group, then the user ID, all three of each (real, effective,
   saved); verified afterwards. Without one (development and tests), the
   worker must not be root.
2. **Parent death** (Linux; required there). ``PR_SET_DUMPABLE`` 0 and
   ``PR_SET_NO_NEW_PRIVS``, then ``PR_SET_PDEATHSIG(SIGKILL)``; each verified,
   and the capability sets must be empty. Then the parent must still be the
   expected one. Everywhere, a lifeline thread ends the worker as soon as its
   read of the parent's lifeline pipe returns, which happens when the parent
   is gone.
3. **umask** 027, verified.
4. **Resource limits**, each as soft = hard, so the worker cannot raise
   them again, and verified; the process limit (0) comes last, after the
   lifeline thread started.
5. **Environment**: exactly the one the parent passed.
6. **Logging**: records go to the parent over the channel, bounded and
   redacted; third-party loggers are capped at WARNING.

Every platform call goes through :class:`OsOps`, so each step and each
refusal is tested in-process with a fake; only the worker runs
:class:`RealOs`. A refusal raises :class:`Refused` with a short reason.
"""

from __future__ import annotations

import errno
import logging
import os
import re
import resource
import signal
import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final, Protocol

from frame_gallery.isolation.apparmor import ProfileError, confine
from frame_gallery.isolation.executor import JsonObject, JsonValue
from frame_gallery.isolation.launch import (
    PLATFORM_ENVIRONMENT,
    ExitCode,
    Limit,
    MessageType,
    WorkerConfig,
)
from frame_gallery.isolation.network_filter import install as install_network_filter
from frame_gallery.logs.redact import Redactor, set_active_redactor

PR_SET_PDEATHSIG: Final = 1
PR_GET_PDEATHSIG: Final = 2
PR_GET_DUMPABLE: Final = 3
PR_SET_DUMPABLE: Final = 4
PR_SET_NO_NEW_PRIVS: Final = 38
PR_GET_NO_NEW_PRIVS: Final = 39

CAPABILITY_SETS: Final = ("CapInh", "CapPrm", "CapEff", "CapAmb")
PROC_STATUS: Final = Path("/proc/self/status")
MAX_LOG_RECORDS: Final = 99
MAX_LOG_TEXT: Final = 900
THIRD_PARTY_LOGGERS: Final = ("PIL", "samsungtvws", "websocket", "urllib3", "requests")

_STATUS_LINE: Final = re.compile(r"^(\w+):\s*(\S+)", re.MULTILINE)


class Refused(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Controls(Protocol):
    """Linux ``prctl`` operations; each setter raises ``OSError`` on failure."""

    def set_dumpable(self, value: int) -> None: ...
    def set_no_new_privs(self) -> None: ...
    def set_pdeathsig(self, signal_number: int) -> None: ...
    def get_dumpable(self) -> int: ...
    def get_no_new_privs(self) -> int: ...
    def get_pdeathsig(self) -> int: ...


class OsOps(Protocol):
    def setgroups(self, groups: list[int]) -> None: ...
    def setresgid(self, gid: int) -> None: ...
    def setresuid(self, uid: int) -> None: ...
    def getresuid(self) -> tuple[int, int, int]: ...
    def getresgid(self) -> tuple[int, int, int]: ...
    def getgroups(self) -> list[int]: ...
    def geteuid(self) -> int: ...
    def getppid(self) -> int: ...
    def umask(self, mask: int) -> int: ...
    def setrlimit(self, limit: Limit, value: int) -> None: ...
    def getrlimit(self, limit: Limit) -> tuple[int, int]: ...
    def environ(self) -> Mapping[str, str]: ...
    def controls(self) -> Controls | None: ...
    def proc_status(self) -> str: ...
    def start_lifeline(self, fd: int) -> None: ...


def run(config: WorkerConfig, ops: OsOps, send: Callable[[JsonObject], None]) -> JsonObject:
    """Steps 1-6; returns the report the worker sends as ``ready``.
    Raises :class:`Refused`."""
    check_configuration(config)
    try:
        profile = confine(config.apparmor_profile, config.task)
    except ProfileError as exc:
        raise Refused(f"apparmor:{exc}") from None
    drop_privileges(config, ops)
    guard_parent(config, ops)
    set_umask(config, ops)
    apply_limits(config, ops)
    check_environment(dict(ops.environ()), config.environment, config.platform)
    install_logging(send, config.log_level)
    uid, _, _ = ops.getresuid()
    gid, _, _ = ops.getresgid()
    groups: list[JsonValue] = [*sorted(ops.getgroups())]
    environment: list[JsonValue] = [*sorted(config.environment)]
    limits: dict[str, JsonValue] = {
        limit.value: [*ops.getrlimit(limit)] for limit, _ in config.limits
    }
    report: JsonObject = {
        "uid": uid,
        "gid": gid,
        "groups": groups,
        "umask": config.umask,
        "limits": limits,
        "environment": environment,
    }
    if profile is not None:
        report["apparmor_profile"] = profile
        report["network_filter"] = config.task
    return report


def check_configuration(config: WorkerConfig) -> None:
    """Only production's own task modules run without test paths; a worker
    that drops privileges accepts no test path at all (D-163)."""
    if config.identity is not None and config.extra_paths:
        raise Refused("test_paths")
    if not config.extra_paths and not config.module.startswith("frame_gallery."):
        raise Refused("module")


def drop_privileges(config: WorkerConfig, ops: OsOps) -> None:
    if config.identity is None:
        if ops.geteuid() == 0:
            raise Refused("root_without_identity")
        return
    uid, gid = config.identity
    try:
        ops.setgroups([])
        ops.setresgid(gid)
        ops.setresuid(uid)
    except OSError as exc:
        raise Refused(f"privileges:{_errno(exc)}") from None
    if ops.getresuid() != (uid, uid, uid) or ops.getresgid() != (gid, gid, gid):
        raise Refused("privileges:ids")
    if ops.getgroups():
        raise Refused("privileges:groups")


def guard_parent(config: WorkerConfig, ops: OsOps) -> None:
    if config.require_pdeathsig:
        controls = ops.controls()
        if controls is None:
            raise Refused("prctl:missing")
        try:
            controls.set_dumpable(0)
            controls.set_no_new_privs()
            controls.set_pdeathsig(signal.SIGKILL)
        except OSError as exc:
            raise Refused(f"prctl:{_errno(exc)}") from None
        if (
            controls.get_dumpable() != 0
            or controls.get_no_new_privs() != 1
            or controls.get_pdeathsig() != signal.SIGKILL
        ):
            raise Refused("prctl:values")
        if not _no_capabilities(ops.proc_status()):
            raise Refused("capabilities")
    if ops.getppid() != config.parent_pid:
        raise Refused("parent_gone")
    if config.apparmor_profile is not None:
        try:
            install_network_filter(config.task)
        except (OSError, ValueError):
            raise Refused("network_filter") from None
    ops.start_lifeline(config.fds.lifeline)


def _no_capabilities(status_text: str) -> bool:
    """Whether every capability set in ``/proc/self/status`` is empty; a
    missing or unreadable line counts as not empty."""
    status = dict(_STATUS_LINE.findall(status_text))
    try:
        return all(int(status.get(name, "1"), 16) == 0 for name in CAPABILITY_SETS)
    except ValueError:
        return False


def set_umask(config: WorkerConfig, ops: OsOps) -> None:
    ops.umask(config.umask)
    if ops.umask(config.umask) != config.umask:
        raise Refused("umask")


def apply_limits(config: WorkerConfig, ops: OsOps) -> None:
    for limit, value in config.limits:
        try:
            ops.setrlimit(limit, value)
        except (OSError, ValueError):
            raise Refused(f"limit:{limit.value}") from None
        if ops.getrlimit(limit) != (value, value):
            raise Refused(f"limit:{limit.value}")


def check_environment(actual: dict[str, str], expected: Mapping[str, str], platform: str) -> None:
    """Exactly ``expected``; only the names ``platform``'s interpreter adds by
    itself are ignored (none on Linux)."""
    for name in PLATFORM_ENVIRONMENT.get(platform, frozenset()):
        actual.pop(name, None)
    if actual != dict(expected):
        raise Refused("environment")


class ChannelLogHandler(logging.Handler):
    """Sends each record to the parent: redacted, at most
    :data:`MAX_LOG_TEXT` characters, and at most :data:`MAX_LOG_RECORDS`
    records, then one note that the rest were dropped. It never raises: a
    lost log line never ends a task."""

    def __init__(self, send: Callable[[JsonObject], None], redactor: Redactor) -> None:
        super().__init__()
        self._send = send
        self._redactor = redactor
        self._sent = 0
        self._noted = False

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self._sent < MAX_LOG_RECORDS:
                self._sent += 1
                text, level, name = self.format(record), record.levelno, record.name
            elif not self._noted:
                self._noted = True
                text, level, name = "further worker log records are dropped", 30, __name__
            else:
                return
            self._send(
                {
                    "type": MessageType.LOG.value,
                    "level": level,
                    "logger": name[:64],
                    "text": self._redactor.redact(text)[:MAX_LOG_TEXT],
                }
            )
        except Exception:  # noqa: BLE001, S110 - a lost log line never ends a task
            pass

    def handleError(self, record: logging.LogRecord) -> None:  # noqa: N802 - logging API
        """Nothing is printed: the worker's stderr is only a crash tail."""
        del record


def install_logging(send: Callable[[JsonObject], None], level: int) -> Redactor:
    """Route every record to the parent (§4 step 6, §18.1). The redactor is
    also the process's active one, so a task can register its secrets."""
    redactor = Redactor()
    set_active_redactor(redactor)
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    handler = ChannelLogHandler(send, redactor)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(level)
    for name in THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(max(level, logging.WARNING))
    return redactor


def _errno(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "error")


class RealOs:
    """The worker's own process (never used in the test process)."""

    def setgroups(self, groups: list[int]) -> None:
        os.setgroups(groups)

    def setresgid(self, gid: int) -> None:
        getattr(os, "setresgid")(gid, gid, gid)  # noqa: B009 - Linux only

    def setresuid(self, uid: int) -> None:
        getattr(os, "setresuid")(uid, uid, uid)  # noqa: B009 - Linux only

    def getresuid(self) -> tuple[int, int, int]:
        getter = getattr(os, "getresuid", None)
        if getter is None:
            uid = os.geteuid()
            return os.getuid(), uid, uid
        result: tuple[int, int, int] = getter()
        return result

    def getresgid(self) -> tuple[int, int, int]:
        getter = getattr(os, "getresgid", None)
        if getter is None:
            gid = os.getegid()
            return os.getgid(), gid, gid
        result: tuple[int, int, int] = getter()
        return result

    def getgroups(self) -> list[int]:
        return os.getgroups()

    def geteuid(self) -> int:
        return os.geteuid()

    def getppid(self) -> int:
        return os.getppid()

    def umask(self, mask: int) -> int:
        return os.umask(mask)

    def setrlimit(self, limit: Limit, value: int) -> None:
        resource.setrlimit(getattr(resource, limit.value), (value, value))

    def getrlimit(self, limit: Limit) -> tuple[int, int]:
        return resource.getrlimit(getattr(resource, limit.value))

    def environ(self) -> Mapping[str, str]:
        return dict(os.environ)

    def controls(self) -> Controls | None:
        import ctypes  # noqa: PLC0415 - the only use of ctypes (D-163)

        libc = ctypes.CDLL(None, use_errno=True)
        function = getattr(libc, "prctl", None)
        if function is None:
            return None
        function.argtypes = [ctypes.c_int, *[ctypes.c_ulong] * 4]
        function.restype = ctypes.c_int
        return _LibcControls(function, ctypes)

    def proc_status(self) -> str:
        return PROC_STATUS.read_text(encoding="ascii", errors="replace")

    def start_lifeline(self, fd: int) -> None:
        def watch() -> None:
            try:
                os.read(fd, 1)
            finally:
                os._exit(ExitCode.PARENT_GONE)

        threading.Thread(target=watch, name="lifeline", daemon=True).start()


class _LibcControls:
    def __init__(self, function: Callable[..., int], ctypes: Any) -> None:
        self._prctl = function
        self._ctypes = ctypes

    def _call(self, option: int, argument: int = 0) -> int:
        result = self._prctl(option, argument, 0, 0, 0)
        if result == -1:
            code = self._ctypes.get_errno()
            raise OSError(code, os.strerror(code))
        return result

    def set_dumpable(self, value: int) -> None:
        self._call(PR_SET_DUMPABLE, value)

    def set_no_new_privs(self) -> None:
        self._call(PR_SET_NO_NEW_PRIVS, 1)

    def set_pdeathsig(self, signal_number: int) -> None:
        self._call(PR_SET_PDEATHSIG, signal_number)

    def get_dumpable(self) -> int:
        return self._call(PR_GET_DUMPABLE)

    def get_no_new_privs(self) -> int:
        return self._call(PR_GET_NO_NEW_PRIVS)

    def get_pdeathsig(self) -> int:
        value = self._ctypes.c_int(0)
        self._call(PR_GET_PDEATHSIG, self._ctypes.addressof(value))
        result: int = value.value
        return result
