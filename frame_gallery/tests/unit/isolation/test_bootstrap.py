"""The worker bootstrap, in-process over a fake OS (isolation/bootstrap.py; §11.3, D-163).

Every step and every refusal is reached here with :class:`FakeOs`, for root
on Linux as well as for a non-root development host. The real calls
(:class:`RealOs`) are covered with the harmful ones replaced; real workers
exercise them in test_process_executor.py.
"""

from __future__ import annotations

import errno
import logging
import os
import resource
import signal
import threading
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from frame_gallery.isolation import bootstrap
from frame_gallery.isolation.bootstrap import (
    MAX_LOG_RECORDS,
    MAX_LOG_TEXT,
    ChannelLogHandler,
    RealOs,
    Refused,
    check_environment,
    install_logging,
)
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.isolation.launch import (
    IMAGE_LIMITS,
    WORKER_ENVIRONMENT,
    WORKER_ID,
    WORKER_UMASK,
    Channels,
    ExitCode,
    Limit,
    WorkerConfig,
    ordered_limits,
)
from frame_gallery.logs.redact import Redactor, active_redactor

LINUX_STATUS = (
    "Name:\tpython\nCapInh:\t0000000000000000\nCapPrm:\t0000000000000000\n"
    "CapEff:\t0000000000000000\nCapBnd:\t000001ffffffffff\nCapAmb:\t0000000000000000\n"
)


def config(**changes: Any) -> WorkerConfig:
    fields: dict[str, Any] = {
        "task": "prepare",
        "module": "frame_gallery.imaging.worker_tasks",
        "function": "prepare_task",
        "events": False,
        "parent_pid": 100,
        "identity": (WORKER_ID, WORKER_ID),
        "require_pdeathsig": True,
        "umask": WORKER_UMASK,
        "limits": ordered_limits(IMAGE_LIMITS, skip=frozenset()),
        "environment": WORKER_ENVIRONMENT,
        "platform": "linux",
        "fds": Channels(3, 4, 5),
        "log_level": logging.INFO,
    }
    fields.update(changes)
    return WorkerConfig(**fields)


class FakeControls:
    def __init__(self) -> None:
        self.values = {"dumpable": 1, "no_new_privs": 0, "pdeathsig": 0}
        self.fail: str | None = None
        self.ignore: str | None = None

    def _set(self, name: str, value: int) -> None:
        if self.fail == name:
            raise OSError(errno.EPERM, "not permitted")
        if self.ignore != name:
            self.values[name] = value

    def set_dumpable(self, value: int) -> None:
        self._set("dumpable", value)

    def set_no_new_privs(self) -> None:
        self._set("no_new_privs", 1)

    def set_pdeathsig(self, signal_number: int) -> None:
        self._set("pdeathsig", signal_number)

    def get_dumpable(self) -> int:
        return self.values["dumpable"]

    def get_no_new_privs(self) -> int:
        return self.values["no_new_privs"]

    def get_pdeathsig(self) -> int:
        return self.values["pdeathsig"]


class FakeOs:
    """A root process on Linux, until a test changes it."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.uid = (0, 0, 0)
        self.gid = (0, 0, 0)
        self.groups = [0, 1]
        self.ppid = 100
        self.mask = 0o022
        self.limits: dict[Limit, tuple[int, int]] = {}
        self.env: dict[str, str] = dict(WORKER_ENVIRONMENT)
        self.prctl: FakeControls | None = FakeControls()
        self.status = LINUX_STATUS
        self.fail: str | None = None
        self.sticky_ids = False
        self.umask_drift = False
        self.limit_drift: Limit | None = None
        self.lifeline: int | None = None

    def _check(self, name: str) -> None:
        self.calls.append(name)
        if self.fail == name:
            raise OSError(errno.EPERM, "not permitted")

    def setgroups(self, groups: list[int]) -> None:
        self._check("setgroups")
        if not self.sticky_ids:
            self.groups = groups

    def setresgid(self, gid: int) -> None:
        self._check("setresgid")
        if not self.sticky_ids:
            self.gid = (gid, gid, gid)

    def setresuid(self, uid: int) -> None:
        self._check("setresuid")
        if not self.sticky_ids:
            self.uid = (uid, uid, uid)

    def getresuid(self) -> tuple[int, int, int]:
        return self.uid

    def getresgid(self) -> tuple[int, int, int]:
        return self.gid

    def getgroups(self) -> list[int]:
        return list(self.groups)

    def geteuid(self) -> int:
        return self.uid[1]

    def getppid(self) -> int:
        return self.ppid

    def umask(self, mask: int) -> int:
        self.calls.append(f"umask:{mask:o}")
        previous, self.mask = self.mask, (mask if not self.umask_drift else 0o022)
        return previous

    def setrlimit(self, limit: Limit, value: int) -> None:
        self.calls.append(f"setrlimit:{limit.value}")
        if self.fail == limit.value:
            raise ValueError("not allowed")
        self.limits[limit] = (value, value) if self.limit_drift is not limit else (value, value + 1)

    def getrlimit(self, limit: Limit) -> tuple[int, int]:
        return self.limits.get(limit, (-1, -1))

    def environ(self) -> Mapping[str, str]:
        return self.env

    def controls(self) -> FakeControls | None:
        return self.prctl

    def proc_status(self) -> str:
        return self.status

    def start_lifeline(self, fd: int) -> None:
        self.calls.append("lifeline")
        self.lifeline = fd


class Sent(list[JsonObject]):
    def __call__(self, message: JsonObject) -> None:
        self.append(message)


@pytest.fixture(autouse=True)
def _restore_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    levels = {name: logging.getLogger(name).level for name in bootstrap.THIRD_PARTY_LOGGERS}
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)
    for name, value in levels.items():
        logging.getLogger(name).setLevel(value)


def run(ops: FakeOs, **changes: Any) -> tuple[JsonObject, Sent]:
    sent = Sent()
    return bootstrap.run(config(**changes), ops, sent), sent


def refusal(ops: FakeOs, **changes: Any) -> str:
    with pytest.raises(Refused) as caught:
        run(ops, **changes)
    return caught.value.reason


# ------------------------------------------------------------------ the whole


def test_root_on_linux_passes_every_step_in_order() -> None:
    ops = FakeOs()
    report, _ = run(ops)
    assert ops.calls[:3] == ["setgroups", "setresgid", "setresuid"]
    assert ops.calls[3:6] == ["lifeline", "umask:27", "umask:27"]
    assert ops.calls[6:] == [f"setrlimit:{limit.value}" for limit, _ in config().limits]
    assert ops.calls[-1] == "setrlimit:RLIMIT_NPROC"
    assert ops.prctl is not None
    assert ops.prctl.values == {"dumpable": 0, "no_new_privs": 1, "pdeathsig": signal.SIGKILL}
    assert ops.lifeline == 5
    assert report == {
        "uid": WORKER_ID,
        "gid": WORKER_ID,
        "groups": [],
        "umask": WORKER_UMASK,
        "limits": {limit.value: [value, value] for limit, value in config().limits},
        "environment": ["LC_ALL", "PATH", "TZ"],
    }


def test_a_development_host_keeps_its_identity() -> None:
    ops = FakeOs()
    ops.uid, ops.gid, ops.groups = (501, 501, 501), (20, 20, 20), [12, 20]
    ops.env["__CF_USER_TEXT_ENCODING"] = "0x1F5:0x0:0x3"
    report, _ = run(ops, identity=None, require_pdeathsig=False, platform="darwin")
    assert "setgroups" not in ops.calls
    assert (report["uid"], report["gid"], report["groups"]) == (501, 20, [12, 20])
    assert ops.prctl is not None
    assert ops.prctl.values["pdeathsig"] == 0
    assert "lifeline" in ops.calls


# ----------------------------------------------------------------- refusals


@pytest.mark.parametrize("step", ["setgroups", "setresgid", "setresuid"])
def test_a_failed_privilege_drop_refuses(step: str) -> None:
    ops = FakeOs()
    ops.fail = step
    assert refusal(ops) == "privileges:EPERM"


def test_ids_that_did_not_change_refuse() -> None:
    ops = FakeOs()
    ops.sticky_ids = True
    assert refusal(ops) == "privileges:ids"


def test_remaining_groups_refuse() -> None:
    ops = FakeOs()
    ops.sticky_ids = True
    ops.uid = ops.gid = (WORKER_ID,) * 3
    assert refusal(ops) == "privileges:groups"


def test_root_without_an_identity_refuses() -> None:
    assert refusal(FakeOs(), identity=None) == "root_without_identity"


def test_test_paths_are_refused_when_privileges_are_dropped() -> None:
    assert refusal(FakeOs(), extra_paths=("/project",)) == "test_paths"


def test_a_module_outside_the_package_needs_a_test_path() -> None:
    ops = FakeOs()
    assert refusal(ops, identity=None, module="tests.support.worker_tasks") == "module"
    ops.uid = (501, 501, 501)
    run(ops, identity=None, module="tests.support.worker_tasks", extra_paths=("/project",))


def test_missing_prctl_refuses_on_linux() -> None:
    ops = FakeOs()
    ops.prctl = None
    assert refusal(ops) == "prctl:missing"


@pytest.mark.parametrize("control", ["dumpable", "no_new_privs", "pdeathsig"])
def test_a_failing_prctl_refuses(control: str) -> None:
    ops = FakeOs()
    assert ops.prctl is not None
    ops.prctl.fail = control
    assert refusal(ops) == "prctl:EPERM"


@pytest.mark.parametrize("control", ["dumpable", "no_new_privs", "pdeathsig"])
def test_a_prctl_that_did_not_take_refuses(control: str) -> None:
    ops = FakeOs()
    assert ops.prctl is not None
    ops.prctl.ignore = control
    assert refusal(ops) == "prctl:values"


@pytest.mark.parametrize(
    "status",
    [
        LINUX_STATUS.replace("CapEff:\t0000000000000000", "CapEff:\t0000000000000400"),
        LINUX_STATUS.replace("CapAmb:\t0000000000000000\n", ""),
        LINUX_STATUS.replace("CapPrm:\t0000000000000000", "CapPrm:\tzz"),
        "",
    ],
)
def test_capabilities_refuse(status: str) -> None:
    ops = FakeOs()
    ops.status = status
    assert refusal(ops) == "capabilities"


def test_a_different_parent_refuses() -> None:
    ops = FakeOs()
    ops.ppid = 1
    assert refusal(ops) == "parent_gone"
    assert "lifeline" not in ops.calls


def test_an_umask_that_did_not_take_refuses() -> None:
    ops = FakeOs()
    ops.umask_drift = True
    assert refusal(ops) == "umask"


def test_a_limit_that_cannot_be_set_refuses() -> None:
    ops = FakeOs()
    ops.fail = "RLIMIT_AS"
    assert refusal(ops) == "limit:RLIMIT_AS"


def test_a_limit_whose_hard_value_differs_refuses() -> None:
    ops = FakeOs()
    ops.limit_drift = Limit.OPEN_FILES
    assert refusal(ops) == "limit:RLIMIT_NOFILE"


class TestEnvironment:
    def test_exactly_the_promised_environment(self) -> None:
        check_environment(dict(WORKER_ENVIRONMENT), WORKER_ENVIRONMENT, "linux")

    @pytest.mark.parametrize(
        "change",
        [
            {"SUPERVISOR_TOKEN": "x"},
            {"LC_CTYPE": "C.UTF-8"},
            {"PATH": "/usr/sbin"},
            {"__CF_USER_TEXT_ENCODING": "0x0"},
        ],
    )
    def test_anything_else_refuses_on_linux(self, change: dict[str, str]) -> None:
        with pytest.raises(Refused, match="environment"):
            check_environment({**WORKER_ENVIRONMENT, **change}, WORKER_ENVIRONMENT, "linux")

    def test_a_missing_name_refuses(self) -> None:
        actual = dict(WORKER_ENVIRONMENT)
        del actual["TZ"]
        with pytest.raises(Refused, match="environment"):
            check_environment(actual, WORKER_ENVIRONMENT, "linux")

    def test_macos_adds_only_its_own_name(self) -> None:
        actual = {**WORKER_ENVIRONMENT, "__CF_USER_TEXT_ENCODING": "0x1F5:0x0:0x3"}
        check_environment(actual, WORKER_ENVIRONMENT, "darwin")
        with pytest.raises(Refused, match="environment"):
            check_environment({**actual, "LC_CTYPE": "C"}, WORKER_ENVIRONMENT, "darwin")

    def test_the_bootstrap_refuses_an_extra_variable(self) -> None:
        ops = FakeOs()
        ops.env["HTTPS_PROXY"] = "http://proxy"
        assert refusal(ops) == "environment"


# ------------------------------------------------------------------ logging


class TestLogging:
    def test_records_go_to_the_parent_redacted(self) -> None:
        sent = Sent()
        redactor = install_logging(sent, logging.INFO)
        assert active_redactor() is redactor
        redactor.add_secret("s3cr3t-token")
        logging.getLogger("frame_gallery.tv.worker").warning("token %s", "s3cr3t-token")
        logging.getLogger("frame_gallery.tv.worker").debug("not sent")
        assert sent == [
            {
                "type": "log",
                "level": logging.WARNING,
                "logger": "frame_gallery.tv.worker",
                "text": "token [REDACTED]",
            }
        ]

    def test_third_party_loggers_are_capped_at_warning(self) -> None:
        sent = Sent()
        install_logging(sent, logging.DEBUG)
        logging.getLogger("samsungtvws").info("New token 12345678")
        logging.getLogger("PIL").warning("kept")
        assert [message["text"] for message in sent] == ["kept"]
        assert logging.getLogger("samsungtvws").level == logging.WARNING

    def test_earlier_handlers_are_removed(self) -> None:
        root = logging.getLogger()
        stray = logging.StreamHandler()
        root.addHandler(stray)
        install_logging(Sent(), logging.INFO)
        assert stray not in root.handlers
        assert [type(handler) for handler in root.handlers] == [ChannelLogHandler]

    def test_records_are_bounded(self) -> None:
        sent = Sent()
        handler = ChannelLogHandler(sent, Redactor())
        logger = logging.getLogger("bounded")
        for index in range(MAX_LOG_RECORDS + 5):
            handler.emit(logger.makeRecord("bounded", logging.INFO, "f", 1, "r%d", (index,), None))
        assert len(sent) == MAX_LOG_RECORDS + 1
        assert sent[-1]["text"] == "further worker log records are dropped"
        assert sent[-1]["level"] == logging.WARNING
        long = logger.makeRecord("x" * 80, logging.INFO, "f", 1, "y" * 5000, (), None)
        fresh = Sent()
        ChannelLogHandler(fresh, Redactor()).emit(long)
        assert len(str(fresh[0]["text"])) == MAX_LOG_TEXT
        assert fresh[0]["logger"] == "x" * 64

    def test_a_failing_channel_never_raises(self) -> None:
        def broken(_message: JsonObject) -> None:
            raise BrokenPipeError(32, "gone")

        handler = ChannelLogHandler(broken, Redactor())
        handler.emit(logging.makeLogRecord({"msg": "lost"}))
        handler.handleError(logging.makeLogRecord({"msg": "lost"}))


# ------------------------------------------------------------ the real calls


class TestRealOs:
    """The real platform calls, with the ones that would change this test
    process replaced by recorders."""

    def test_privilege_calls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[str, tuple[int, ...]]] = []
        monkeypatch.setattr(os, "setgroups", lambda groups: calls.append(("groups", tuple(groups))))
        for name in ("setresgid", "setresuid"):
            monkeypatch.setattr(
                os, name, lambda *ids, name=name: calls.append((name, ids)), raising=False
            )
        ops = RealOs()
        ops.setgroups([])
        ops.setresgid(7)
        ops.setresuid(8)
        assert calls == [("groups", ()), ("setresgid", (7, 7, 7)), ("setresuid", (8, 8, 8))]

    def test_ids_with_and_without_getres(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ops = RealOs()
        monkeypatch.delattr(os, "getresuid", raising=False)
        monkeypatch.delattr(os, "getresgid", raising=False)
        assert ops.getresuid() == (os.getuid(), os.geteuid(), os.geteuid())
        assert ops.getresgid() == (os.getgid(), os.getegid(), os.getegid())
        monkeypatch.setattr(os, "getresuid", lambda: (1, 2, 3), raising=False)
        monkeypatch.setattr(os, "getresgid", lambda: (4, 5, 6), raising=False)
        assert (ops.getresuid(), ops.getresgid()) == ((1, 2, 3), (4, 5, 6))

    def test_plain_queries(self) -> None:
        ops = RealOs()
        assert ops.getgroups() == os.getgroups()
        assert ops.geteuid() == os.geteuid()
        assert ops.getppid() == os.getppid()
        assert ops.environ() == dict(os.environ)
        assert ops.getrlimit(Limit.CPU) == resource.getrlimit(resource.RLIMIT_CPU)

    def test_umask_is_set_and_restored(self) -> None:
        ops = RealOs()
        previous = ops.umask(0o027)
        try:
            assert ops.umask(0o027) == 0o027
        finally:
            os.umask(previous)

    def test_setrlimit_sets_soft_and_hard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[int, tuple[int, int]]] = []
        monkeypatch.setattr(resource, "setrlimit", lambda res, values: calls.append((res, values)))
        RealOs().setrlimit(Limit.CORE, 0)
        assert calls == [(resource.RLIMIT_CORE, (0, 0))]

    def test_proc_status(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        (tmp_path / "status").write_text(LINUX_STATUS)
        monkeypatch.setattr(bootstrap, "PROC_STATUS", tmp_path / "status")
        assert RealOs().proc_status() == LINUX_STATUS

    def test_the_lifeline_ends_the_worker_when_the_parent_is_gone(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ended = threading.Event()
        codes: list[int] = []

        def fake_exit(code: int) -> None:
            codes.append(code)
            ended.set()

        monkeypatch.setattr(os, "_exit", fake_exit)
        read, write = os.pipe()
        try:
            RealOs().start_lifeline(read)
            assert not ended.wait(0.1)
            os.close(write)  # the parent is gone
            assert ended.wait(5)
        finally:
            os.close(read)
        assert codes == [ExitCode.PARENT_GONE]

    def test_controls_without_prctl(self) -> None:
        """macOS has no prctl: the controls are missing, and Linux refuses that."""
        if hasattr(__import__("ctypes").CDLL(None), "prctl"):
            pytest.skip("this libc has prctl")
        assert RealOs().controls() is None


class FakeCtypes:
    """Enough of ctypes for the prctl wrapper."""

    class c_int:  # noqa: N801 - the ctypes name
        def __init__(self, value: int) -> None:
            self.value = value

    def __init__(self) -> None:
        self.errno = 0
        self.cells: dict[int, FakeCtypes.c_int] = {}

    def get_errno(self) -> int:
        return self.errno

    def addressof(self, cell: FakeCtypes.c_int) -> int:
        self.cells[id(cell)] = cell
        return id(cell)


def test_the_libc_controls() -> None:
    ctypes = FakeCtypes()
    calls: list[tuple[int, ...]] = []

    def prctl(option: int, a2: int, a3: int, a4: int, a5: int) -> int:
        calls.append((option, a2, a3, a4, a5))
        if option == bootstrap.PR_GET_PDEATHSIG:
            ctypes.cells[a2].value = signal.SIGKILL
            return 0
        if option == bootstrap.PR_GET_DUMPABLE:
            return 0
        if option == bootstrap.PR_GET_NO_NEW_PRIVS:
            return 1
        return 0

    controls = bootstrap._LibcControls(prctl, ctypes)
    controls.set_dumpable(0)
    controls.set_no_new_privs()
    controls.set_pdeathsig(signal.SIGKILL)
    assert (controls.get_dumpable(), controls.get_no_new_privs()) == (0, 1)
    assert controls.get_pdeathsig() == signal.SIGKILL
    assert calls[:3] == [
        (bootstrap.PR_SET_DUMPABLE, 0, 0, 0, 0),
        (bootstrap.PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0),
        (bootstrap.PR_SET_PDEATHSIG, signal.SIGKILL, 0, 0, 0),
    ]


def test_a_failing_libc_call_raises_its_errno() -> None:
    ctypes = FakeCtypes()
    ctypes.errno = errno.EINVAL
    controls = bootstrap._LibcControls(lambda *_args: -1, ctypes)
    with pytest.raises(OSError, match="Invalid argument") as caught:
        controls.set_dumpable(0)
    assert caught.value.errno == errno.EINVAL


def test_the_real_controls_bind_prctl_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    import ctypes  # noqa: PLC0415

    class Function:
        def __init__(self) -> None:
            self.argtypes: list[object] = []
            self.restype: object = None

        def __call__(self, *args: int) -> int:
            return 0

    class Library:
        prctl = Function()

    monkeypatch.setattr(ctypes, "CDLL", lambda name, use_errno: Library())
    controls = RealOs().controls()
    assert controls is not None
    assert Library.prctl.restype is ctypes.c_int
    assert len(Library.prctl.argtypes) == 5
