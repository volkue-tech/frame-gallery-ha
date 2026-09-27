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

The test session installs it in ``pytest_configure`` (``tests/conftest.py``);
every task a test runs in a worker process installs it first
(``tests/support/worker_tasks.py``), so no process a test starts can reach
the network. Socket creation, ``socketpair``, pipes and subprocesses are
unaffected. It needs nothing but the standard library.
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
