"""The test-wide guards of tests/conftest.py (H2, §20.1; Pillow's global limit).

Every call below targets the loopback interface with numeric addresses, so it
would stay on this host even if a guard were missing.
"""

from __future__ import annotations

import _socket
import socket
import ssl
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest
from PIL import Image

from tests.support import h2

H2: Final = r"^network access is disabled in tests \(H2\)$"
LOOPBACK: Final = ("127.0.0.1", 9)
CONFTEST: Final = Path(__file__).resolve().parents[2] / "conftest.py"

RESOLVER_CALLS: Final[dict[str, tuple[object, ...]]] = {
    "getaddrinfo": (*LOOPBACK, 0, 0, 0, socket.AI_NUMERICHOST | socket.AI_NUMERICSERV),
    "gethostbyname": ("127.0.0.1",),
    "gethostbyname_ex": ("127.0.0.1",),
    "gethostbyaddr": ("127.0.0.1",),
    "getnameinfo": (LOOPBACK, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV),
}
"""Every blocked name-lookup function, with arguments that need no lookup."""

BLOCKED_ENTRY_POINTS: Final[tuple[tuple[object, str], ...]] = (
    *((socket.socket, name) for name in ("connect", "connect_ex", "sendto", "sendmsg")),
    (socket, "create_connection"),
    *((socket, name) for name in RESOLVER_CALLS),
    *((_socket, name) for name in RESOLVER_CALLS),
)

PILLOW_DEFAULT_MAX_IMAGE_PIXELS: Final = 1024 * 1024 * 1024 // 4 // 3
"""Pillow's own default for ``Image.MAX_IMAGE_PIXELS``."""


def _lookup_during_collection() -> str:
    try:
        socket.getaddrinfo(*LOOPBACK, flags=socket.AI_NUMERICHOST | socket.AI_NUMERICSERV)
    except RuntimeError as error:
        return str(error)
    return "not blocked"


AT_COLLECTION: Final = _lookup_during_collection()
"""Evaluated while pytest imports this module, i.e. during collection."""


def _session_conftest(config: pytest.Config) -> ModuleType:
    loaded = [
        plugin
        for plugin in config.pluginmanager.get_plugins()
        if isinstance(plugin, ModuleType) and Path(plugin.__file__ or "").resolve() == CONFTEST
    ]
    assert len(loaded) == 1, loaded
    return loaded[0]


# --- H2 ---------------------------------------------------------------------


def test_the_network_guard_covers_collection() -> None:
    assert AT_COLLECTION == "network access is disabled in tests (H2)"


@pytest.mark.parametrize("module", [socket, _socket], ids=["socket", "_socket"])
@pytest.mark.parametrize("name", sorted(RESOLVER_CALLS))
def test_every_name_lookup_is_blocked(module: ModuleType, name: str) -> None:
    resolver = getattr(module, name)
    with pytest.raises(RuntimeError, match=H2):
        resolver(*RESOLVER_CALLS[name])


def test_create_connection_is_blocked() -> None:
    with pytest.raises(RuntimeError, match=H2):
        socket.create_connection(LOOPBACK, timeout=0.01)


@pytest.mark.parametrize("kind", [socket.SOCK_STREAM, socket.SOCK_DGRAM], ids=["tcp", "udp"])
def test_every_socket_send_and_connect_is_blocked(kind: socket.SocketKind) -> None:
    with socket.socket(socket.AF_INET, kind) as sock:
        with pytest.raises(RuntimeError, match=H2):
            sock.connect(LOOPBACK)
        with pytest.raises(RuntimeError, match=H2):
            sock.connect_ex(LOOPBACK)
        with pytest.raises(RuntimeError, match=H2):
            sock.sendto(b"x", LOOPBACK)
        with pytest.raises(RuntimeError, match=H2):
            sock.sendmsg([b"x"], [], 0, LOOPBACK)


@pytest.mark.parametrize("method", ["connect", "connect_ex"])
def test_tls_sockets_inherit_the_guard(method: str) -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with (
        context.wrap_socket(socket.socket(), server_hostname="frame-gallery.invalid") as sock,
        pytest.raises(RuntimeError, match=H2),
    ):
        getattr(sock, method)(LOOPBACK)


def test_local_pipes_still_work() -> None:
    # The guard blocks outbound use only; socket pairs stay usable.
    left, right = socket.socketpair()
    with left, right:
        left.sendall(b"ping")
        assert right.recv(4) == b"ping"


def test_the_guard_restores_the_originals_at_the_end(pytestconfig: pytest.Config) -> None:
    # Remove the session guard as pytest_unconfigure does, then reinstall it.
    conftest = _session_conftest(pytestconfig)
    blocked = h2.blocked  # the guard's own replacement (tests/support/h2.py)
    assert set(h2.targets()) == set(BLOCKED_ENTRY_POINTS)
    assert all(getattr(owner, name) is blocked for owner, name in BLOCKED_ENTRY_POINTS)
    conftest.pytest_unconfigure(pytestconfig)
    try:
        restored = {(owner, name): getattr(owner, name) for owner, name in BLOCKED_ENTRY_POINTS}
        own_methods = set(vars(socket.socket))
    finally:
        conftest.pytest_configure(pytestconfig)

    assert all(value is not blocked for value in restored.values())
    # The methods are inherited from the C type again, not shadowed by a copy.
    assert own_methods.isdisjoint({"connect", "connect_ex", "sendto", "sendmsg"})
    assert all(getattr(owner, name) is blocked for owner, name in BLOCKED_ENTRY_POINTS)


# --- Pillow's process-global pixel limit --------------------------------------


def test_a_test_may_change_the_pillow_pixel_limit() -> None:
    Image.MAX_IMAGE_PIXELS = 1234  # restored by tests/conftest.py
    assert Image.MAX_IMAGE_PIXELS == 1234


def test_the_pillow_pixel_limit_is_restored_between_tests() -> None:
    # Runs after the test above and, in a full run, after the integration
    # tests, whose prepare_image sets the limit for its own purpose.
    assert Image.MAX_IMAGE_PIXELS == PILLOW_DEFAULT_MAX_IMAGE_PIXELS
