"""What the parent tells a worker when it starts it (§11.3, D-163).

The parent builds one :class:`WorkerConfig` per worker and passes it, as
JSON, on the worker's command line: it holds no secret (the request, which
may carry the pairing token, follows over the request pipe only after the
worker's bootstrap has completed). The worker checks every field before it
acts on any.

Both sides also share the message types, the exit codes, the fixed worker
environment, and the resource-limit tables.
"""

from __future__ import annotations

import enum
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

GIB: Final = 1024 * 1024 * 1024
MIB: Final = 1024 * 1024

WORKER_ID: Final = 65534
"""The unprivileged user and group of every worker in production (§11.3)."""

WORKER_UMASK: Final = 0o027

WORKER_ENVIRONMENT: Final[Mapping[str, str]] = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "LC_ALL": "C.UTF-8",
    "TZ": "UTC",
}
"""The worker's exact environment. ``LC_ALL`` is always set, so the
interpreter never coerces the locale and adds ``LC_CTYPE`` (PEP 538)."""

PLATFORM_ENVIRONMENT: Final[Mapping[str, frozenset[str]]] = {
    "darwin": frozenset({"__CF_USER_TEXT_ENCODING"}),
}
"""Names an interpreter adds on its own on a development host: macOS's
CoreFoundation sets ``__CF_USER_TEXT_ENCODING`` in every process that links
it. None on Linux, where the check is exact."""


class Limit(enum.StrEnum):
    """Resource limits, by their ``resource`` module names."""

    ADDRESS_SPACE = "RLIMIT_AS"
    CPU = "RLIMIT_CPU"
    FILE_SIZE = "RLIMIT_FSIZE"
    OPEN_FILES = "RLIMIT_NOFILE"
    CORE = "RLIMIT_CORE"
    PROCESSES = "RLIMIT_NPROC"
    """Set to 0, and last: after it, the worker can start neither a process
    nor a thread, so nothing it runs can outlive it (D-163)."""


IMAGE_LIMITS: Final[Mapping[Limit, int]] = {
    Limit.ADDRESS_SPACE: 1 * GIB,
    Limit.CPU: 30,
    Limit.FILE_SIZE: 16 * MIB,
    Limit.OPEN_FILES: 32,
    Limit.CORE: 0,
    Limit.PROCESSES: 0,
}
"""The image worker (``prepare``, ``inspect``): 1 GiB of address space
(§11.3); a delivery file is at most 15 MiB."""

TELEVISION_LIMITS: Final[Mapping[Limit, int]] = {
    Limit.ADDRESS_SPACE: 512 * MIB,
    Limit.CPU: 30,
    Limit.FILE_SIZE: 1 * MIB,
    Limit.OPEN_FILES: 32,
    Limit.CORE: 0,
    Limit.PROCESSES: 0,
}
"""The television worker: 512 MiB of address space (§11.3); it writes no file."""


class ExitCode(enum.IntEnum):
    """How a worker ends when it cannot send a message saying so."""

    REFUSED = 70
    """The configuration was invalid or the bootstrap refused to run."""

    CRASH = 71
    PARENT_GONE = 72
    CHANNEL = 73
    """The request could not be read or the result not written."""

    MEMORY = 75


class MessageType(enum.StrEnum):
    READY = "ready"
    REFUSED = "refused"
    REQUEST = "request"
    EVENT = "event"
    LOG = "log"
    RESULT = "result"
    FAILURE = "failure"


@dataclass(frozen=True, slots=True)
class TaskEntry:
    module: str
    function: str
    events: bool
    """Whether the function also takes an event sink."""

    limits: Mapping[Limit, int]


PRODUCTION_TASKS: Final[Mapping[str, TaskEntry]] = {
    "prepare": TaskEntry(
        "frame_gallery.imaging.worker_tasks", "prepare_task", events=False, limits=IMAGE_LIMITS
    ),
    "inspect": TaskEntry(
        "frame_gallery.imaging.worker_tasks", "inspect_task", events=True, limits=IMAGE_LIMITS
    ),
    "deliver": TaskEntry(
        "frame_gallery.tv.samsung_task", "deliver_task", events=True, limits=TELEVISION_LIMITS
    ),
}
"""The only task table the production executor uses; a test asserts it."""

_NAME: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}")
_MODULE: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}(?:\.[A-Za-z_][A-Za-z0-9_]{0,63}){0,7}")
_FIELDS: Final = frozenset(
    {
        "task",
        "module",
        "function",
        "events",
        "parent_pid",
        "identity",
        "require_pdeathsig",
        "umask",
        "limits",
        "environment",
        "platform",
        "extra_paths",
        "fds",
        "log_level",
    }
)


@dataclass(frozen=True, slots=True)
class Channels:
    request: int
    result: int
    lifeline: int


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    task: str
    module: str
    function: str
    events: bool
    parent_pid: int
    identity: tuple[int, int] | None
    """The user and group to drop to, or ``None`` when the parent is not root
    (development and tests: the worker then must not be root either)."""

    require_pdeathsig: bool
    """True on Linux: the parent-death signal, no-new-privileges, and a
    non-dumpable worker are then required, not optional."""

    umask: int
    limits: tuple[tuple[Limit, int], ...]
    """Applied in order; the process limit comes last."""

    environment: Mapping[str, str]
    platform: str
    fds: Channels
    log_level: int
    extra_paths: tuple[str, ...] = field(default=())
    """Absolute directories put on ``sys.path`` after the source root; only
    tests set them, and a worker that drops privileges refuses them."""

    def to_json(self) -> str:
        return json.dumps(
            {
                "task": self.task,
                "module": self.module,
                "function": self.function,
                "events": self.events,
                "parent_pid": self.parent_pid,
                "identity": None if self.identity is None else list(self.identity),
                "require_pdeathsig": self.require_pdeathsig,
                "umask": self.umask,
                "limits": [[limit.value, value] for limit, value in self.limits],
                "environment": dict(self.environment),
                "platform": self.platform,
                "extra_paths": list(self.extra_paths),
                "fds": [self.fds.request, self.fds.result, self.fds.lifeline],
                "log_level": self.log_level,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, text: str) -> WorkerConfig:
        """Raises ``ValueError`` for anything unexpected."""
        data = json.loads(text)
        if not isinstance(data, dict) or set(data) != _FIELDS:
            msg = "invalid worker configuration"
            raise ValueError(msg)
        identity = data["identity"]
        return cls(
            task=_name(data["task"]),
            module=_module(data["module"]),
            function=_name(data["function"]),
            events=_boolean(data["events"]),
            parent_pid=_count(data["parent_pid"], minimum=1),
            identity=None if identity is None else _identity(identity),
            require_pdeathsig=_boolean(data["require_pdeathsig"]),
            umask=_count(data["umask"], maximum=0o777),
            limits=_limits(data["limits"]),
            environment=_environment(data["environment"]),
            platform=_name(data["platform"]),
            extra_paths=_paths(data["extra_paths"]),
            fds=_channels(data["fds"]),
            log_level=_count(data["log_level"], maximum=50),
        )


def _invalid(what: str) -> ValueError:
    return ValueError(f"invalid worker configuration: {what}")


def _name(value: object) -> str:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise _invalid("name")
    return value


def _module(value: object) -> str:
    if not isinstance(value, str) or _MODULE.fullmatch(value) is None:
        raise _invalid("module")
    return value


def _boolean(value: object) -> bool:
    if not isinstance(value, bool):
        raise _invalid("flag")
    return value


def _count(value: object, *, minimum: int = 0, maximum: int = 2**62) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise _invalid("number")
    return value


def _identity(value: object) -> tuple[int, int]:
    if not isinstance(value, list) or len(value) != 2:
        raise _invalid("identity")
    return _count(value[0], minimum=1), _count(value[1], minimum=1)


def _limits(value: object) -> tuple[tuple[Limit, int], ...]:
    if not isinstance(value, list):
        raise _invalid("limits")
    limits: list[tuple[Limit, int]] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], str):
            raise _invalid("limits")
        try:
            limit = Limit(item[0])
        except ValueError:
            raise _invalid("limits") from None
        limits.append((limit, _count(item[1])))
    if len({limit for limit, _ in limits}) != len(limits):
        raise _invalid("limits")
    return tuple(limits)


def _environment(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) for key, item in value.items()
    ):
        raise _invalid("environment")
    return dict(value)


def _paths(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.startswith("/") for item in value
    ):
        raise _invalid("paths")
    return tuple(value)


def _channels(value: object) -> Channels:
    if not isinstance(value, list) or len(value) != 3:
        raise _invalid("channels")
    request, result, lifeline = (_count(item, minimum=3, maximum=4096) for item in value)
    if len({request, result, lifeline}) != 3:
        raise _invalid("channels")
    return Channels(request, result, lifeline)


def ordered_limits(
    limits: Mapping[Limit, int], *, skip: frozenset[Limit]
) -> tuple[tuple[Limit, int], ...]:
    """``limits`` without ``skip``, with the process limit last."""
    kept = [(limit, value) for limit, value in limits.items() if limit not in skip]
    kept.sort(key=lambda item: item[0] is Limit.PROCESSES)
    return tuple(kept)
