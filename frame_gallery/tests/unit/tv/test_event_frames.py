from __future__ import annotations

import socket
import struct
from types import SimpleNamespace
from typing import Any

import pytest
import websocket

from frame_gallery.observer.stream import MAX_EVENTS, MAX_FRAME, SESSION_S
from frame_gallery.tv.event_frames import FrameBounds, SessionClosed, SessionSockets


class Connection:
    def __init__(self) -> None:
        self.frame_buffer = SimpleNamespace(
            recv=lambda n: b"x" * n,
            recv_length=lambda: None,
            header=(1, 0, 0, 0, 1, 0, 1),
            length=1,
        )
        self.timeouts: list[float] = []
        self.closed = self.shutdowns = 0
        self.close_error = False

    def recv_frame(self) -> str:
        return "synthetic"

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)

    def close(self, *, timeout: float) -> None:
        assert timeout > 0
        self.closed += 1
        if self.close_error:
            raise OSError("synthetic")

    def shutdown(self) -> None:
        self.shutdowns += 1


def test_caps_read_restore_and_graceful_close() -> None:
    c = Connection()
    now = [0.0]
    b = FrameBounds(c, lambda: now[0], lambda: False, 0)
    assert b.read(2) == b"xx"
    assert b.read(1) == b"x"
    b.length()
    assert b.frame() == "synthetic"
    b.passive = True
    now[0] = 6
    b.check()
    assert b.frame() == "synthetic"
    b.close()
    assert c.closed == c.shutdowns == 1
    assert c.frame_buffer.recv(1) == b"x"
    assert c.recv_frame() == "synthetic"


@pytest.mark.parametrize(
    ("header", "size", "passive"),
    [
        (None, 1, False),
        ((1, 0, 0, 0, 1, 0, 1), None, False),
        ((1, 0, 0, 0, 1, 0, 1), -1, False),
        ((1, 0, 0, 0, 1, 0, 1), MAX_FRAME + 1, False),
        ((0, 0, 0, 0, 1, 0, 1), 1, False),
        ((1, 0, 0, 0, 0, 0, 1), 1, False),
        ((1, 0, 0, 0, 2, 0, 1), 1, True),
    ],
)
def test_reject_lengths_fragments_and_passive_binary(header: Any, size: Any, passive: bool) -> None:
    c = Connection()
    b = FrameBounds(c, lambda: 0, lambda: False, 0)
    c.frame_buffer.header, c.frame_buffer.length = header, size
    b.passive = passive
    with pytest.raises(ValueError, match="frame limit"):
        b.length()


def test_deadlines_idle_cancel_and_control_flood() -> None:
    now = [0.0]
    cancel = [False]
    c = Connection()
    b = FrameBounds(c, lambda: now[0], lambda: cancel[0], 0)
    now[0] = 5
    with pytest.raises(ValueError, match="deadline"):
        b.check()
    b.passive = True
    b.check()
    b.read(1)
    now[0] = 10
    with pytest.raises(ValueError, match="deadline"):
        b.check()
    b._partial = None
    for _ in range(MAX_EVENTS):
        b.frame()
    with pytest.raises(ValueError, match="rate"):
        b.frame()
    now[0] += 5
    b.frame()
    cancel[0] = True
    with pytest.raises(SessionClosed):
        b.check()
    cancel[0] = False
    now[0] = SESSION_S
    with pytest.raises(SessionClosed):
        b.check()
    b._closing = SESSION_S + 1
    b.check()
    b.read(1)
    now[0] += 1
    with pytest.raises(SessionClosed):
        b.check()


def test_empty_read_and_close_exception_restores_hooks() -> None:
    c = Connection()
    c.frame_buffer.recv = lambda _n: b""
    b = FrameBounds(c, lambda: 0, lambda: False, 0)
    assert b.read(1) == b""
    c.close_error = True
    with pytest.raises(OSError, match="synthetic"):
        b.close()
    assert c.shutdowns == 1


def test_factory_is_one_shot_and_always_restored() -> None:
    c = Connection()
    calls: list[object] = []

    def create(*a: Any, **kw: Any) -> Connection:
        calls.append((a, kw))
        return c

    module = SimpleNamespace(create_connection=create)
    factory = SessionSockets(module, lambda: 0, lambda: False)
    assert factory.create("synthetic") is c
    with pytest.raises(ValueError, match="reconnect"):
        factory.create("synthetic")
    assert len(calls) == 1
    c.close_error = True
    factory.close()
    assert module.create_connection is create
    assert c.shutdowns == 1
    empty = SessionSockets(module, lambda: 0, lambda: False)
    empty.close()
    broken = SimpleNamespace(shutdown=lambda: calls.append("shutdown"))
    module.create_connection = lambda: broken
    failed = SessionSockets(module, lambda: 0, lambda: False)
    with pytest.raises(AttributeError):
        failed.create()
    failed.close()
    assert calls[-1] == "shutdown"


@pytest.mark.parametrize("case", ["oversize", "partial", "partial-timeout", "binary", "fragment"])
def test_real_websocket_parser_bounds_before_payload(case: str) -> None:
    left, right = socket.socketpair()
    c = websocket.WebSocket()
    c.sock = left
    c.connected = True
    now = [0.0]
    bounds = FrameBounds(c, lambda: now[0], lambda: False, 0)
    bounds.passive = True
    try:
        if case == "oversize":
            right.sendall(struct.pack("!BBQ", 0x81, 127, 1 << 32))
            with pytest.raises(ValueError, match="frame limit"):
                c.recv()
        elif case in ("partial", "partial-timeout"):
            right.sendall(b"\x81")
            with pytest.raises(websocket.WebSocketTimeoutException):
                c.recv()
            if case == "partial":
                right.sendall(b"\x02{}")
                assert c.recv() == "{}"
            else:
                now[0] = 6
                with pytest.raises(ValueError, match="deadline"):
                    c.recv()
        else:
            right.sendall(bytes([0x82 if case == "binary" else 0x01, 0]))
            with pytest.raises(ValueError, match="frame limit"):
                c.recv()
    finally:
        left.close()
        right.close()
