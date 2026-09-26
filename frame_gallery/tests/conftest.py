"""Test-wide guards.

H2 (acceptance item; ARCHITECTURE.md §20.1): outbound networking is disabled
for the whole pytest session, collection included. ``pytest_configure``
replaces the entry points below and ``pytest_unconfigure`` restores the
originals. Each replacement raises :class:`NetworkBlockedError` (a
``RuntimeError``) with the message ``network access is disabled in tests (H2)``:

* the ``socket.socket`` methods ``connect``, ``connect_ex``, ``sendto`` and
  ``sendmsg``, and so the same methods of its subclasses (``ssl.SSLSocket``);
* the ``socket`` functions ``create_connection``, ``getaddrinfo``,
  ``gethostbyname``, ``gethostbyname_ex``, ``gethostbyaddr`` and
  ``getnameinfo``;
* the same five resolver functions of the C module ``_socket``.

The attributes are replaced, so a call through the module or the class is
blocked; a reference bound before the session started is not. The methods of
the C type ``_socket.socket`` cannot be replaced; the source may not import
``_socket`` at all (tests/unit/test_architecture_boundaries.py). Socket
creation, ``socketpair``, pipes and subprocesses are unaffected.

Every test also restores Pillow's process-global ``Image.MAX_IMAGE_PIXELS``,
which ``prepare_image`` sets (worker_tasks.py), to the value it started with.
"""

from __future__ import annotations

import _socket
import socket
from collections.abc import Iterator
from typing import Final, NoReturn

import pytest
from PIL import Image

from frame_gallery.logs.redact import active_redactor, set_active_redactor

H2_MESSAGE: Final = "network access is disabled in tests (H2)"

_SOCKET_METHODS: Final = ("connect", "connect_ex", "sendto", "sendmsg")
_RESOLVERS: Final = (
    "getaddrinfo",
    "gethostbyname",
    "gethostbyname_ex",
    "gethostbyaddr",
    "getnameinfo",
)

_GUARD: Final = pytest.StashKey[pytest.MonkeyPatch]()


class NetworkBlockedError(RuntimeError):
    """A test tried to use the network."""


def _blocked(*_args: object, **_kwargs: object) -> NoReturn:
    raise NetworkBlockedError(H2_MESSAGE)


def pytest_configure(config: pytest.Config) -> None:
    """Install the H2 guard before collection starts."""
    guard = pytest.MonkeyPatch()
    for method in _SOCKET_METHODS:
        guard.setattr(socket.socket, method, _blocked)
    guard.setattr(socket, "create_connection", _blocked)
    for resolver in _RESOLVERS:
        guard.setattr(socket, resolver, _blocked)
        guard.setattr(_socket, resolver, _blocked)
    config.stash[_GUARD] = guard


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore every replaced entry point (inherited methods are deleted again)."""
    guard = config.stash.get(_GUARD, None)
    if guard is not None:
        del config.stash[_GUARD]
        guard.undo()


@pytest.fixture(autouse=True)
def _restore_pillow_global_pixel_limit() -> Iterator[None]:
    """``prepare_image`` sets Pillow's global pixel limit; restore it after each test."""
    saved = Image.MAX_IMAGE_PIXELS
    yield
    Image.MAX_IMAGE_PIXELS = saved


@pytest.fixture(autouse=True)
def _restore_active_redactor() -> Iterator[None]:
    """A test that configures logging cannot leave its redactor active for the
    tests that follow (the redactor is process-wide, §19)."""
    previous = active_redactor()
    try:
        yield
    finally:
        set_active_redactor(previous)
