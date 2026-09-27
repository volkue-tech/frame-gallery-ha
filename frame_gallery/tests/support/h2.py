"""The H2 network guard (acceptance item H2; ARCHITECTURE.md §20.1).

``install()`` replaces the entry points below in the calling process; each
replacement raises :class:`NetworkBlockedError` (a ``RuntimeError``) with
the message :data:`H2_MESSAGE`:

* the ``socket.socket`` methods ``connect``, ``connect_ex``, ``sendto`` and
  ``sendmsg``, and so the same methods of its subclasses (``ssl.SSLSocket``);
* the ``socket`` functions ``create_connection``, ``getaddrinfo``,
  ``gethostbyname``, ``gethostbyname_ex``, ``gethostbyaddr`` and
  ``getnameinfo``;
* the same five resolver functions of the C module ``_socket``.

The test session installs it in ``pytest_configure`` (``tests/conftest.py``).
Every task in ``tests/support/worker_tasks.py`` installs it first in its
worker, and so do the child processes that run the runner or an executor
(the E9 children and the orphan test's parent). Not guarded: the root-only
workers, which load no test code by design and run only production tasks
that open no socket (``tests/unit/isolation/test_root_isolation.py``), and
helper interpreters that run only the standard library or fakes (scripted
workers, sleeping children, and the import checks, which must not load
``socket`` at all). Socket creation, ``socketpair``, pipes and subprocesses
are unaffected. It needs nothing but the standard library.
"""

from __future__ import annotations

import _socket
import socket
from collections.abc import Callable
from typing import Final, NoReturn

H2_MESSAGE: Final = "network access is disabled in tests (H2)"

SOCKET_METHODS: Final = ("connect", "connect_ex", "sendto", "sendmsg")
RESOLVERS: Final = (
    "getaddrinfo",
    "gethostbyname",
    "gethostbyname_ex",
    "gethostbyaddr",
    "getnameinfo",
)


class NetworkBlockedError(RuntimeError):
    """A test tried to use the network."""


def blocked(*_args: object, **_kwargs: object) -> NoReturn:
    raise NetworkBlockedError(H2_MESSAGE)


def targets() -> list[tuple[object, str]]:
    """Every (owner, attribute) the guard replaces."""
    found: list[tuple[object, str]] = [(socket.socket, name) for name in SOCKET_METHODS]
    found.append((socket, "create_connection"))
    for resolver in RESOLVERS:
        found += [(socket, resolver), (_socket, resolver)]
    return found


def install(replace: Callable[[object, str, object], None] | None = None) -> None:
    """Install the guard; ``replace(owner, name, value)`` defaults to ``setattr``
    (the test session passes a ``MonkeyPatch`` so it can undo it)."""
    for owner, name in targets():
        if replace is None:
            setattr(owner, name, blocked)
        else:
            replace(owner, name, blocked)
