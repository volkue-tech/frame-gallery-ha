"""Bound the pinned websocket parser before it allocates a payload.

No networking or library imports. This adapter is used only inside the TV
worker. The package stays unmodified; all instance hooks/factory are restored.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

from frame_gallery.observer.stream import IDLE_S, MAX_EVENTS, MAX_FRAME, QUERY_S, SESSION_S, START_S


class SessionClosed(Exception):
    """Cancellation/finite lifetime, not permission to reconnect."""


class FrameBounds:
    def __init__(
        self,
        connection: Any,
        now: Callable[[], float],
        cancelled: Callable[[], bool],
        started: float,
    ) -> None:
        self.connection, self._now, self._cancelled = connection, now, cancelled
        self._started = started
        self._partial: float | None = None
        self._window, self._frames = started, 0
        self.passive = False
        self._closing: float | None = None
        self._query_until: float | None = None
        buffer = connection.frame_buffer
        self._read, self._length, self._frame = (
            buffer.recv,
            buffer.recv_length,
            connection.recv_frame,
        )
        buffer.recv, buffer.recv_length, connection.recv_frame = self.read, self.length, self.frame

    def check(self) -> None:
        now = self._now()
        if self._closing is not None:
            if now >= self._closing:
                raise SessionClosed
            return
        if self._cancelled() or now - self._started >= SESSION_S:
            raise SessionClosed
        if self._query_until is not None and now >= self._query_until:
            raise ValueError("event query deadline")
        if (not self.passive and now - self._started >= START_S) or (
            self._partial is not None and now - self._partial >= START_S
        ):
            raise ValueError("event frame deadline")

    def read(self, count: int) -> bytes:
        self.check()
        timeout = IDLE_S if self.passive else min(2.0, START_S - (self._now() - self._started))
        if self._query_until is not None:
            timeout = min(timeout, max(0.001, self._query_until - self._now()))
        if self._closing is not None:
            timeout = min(timeout, max(0.001, self._closing - self._now()))
        self.connection.settimeout(max(0.001, timeout))
        data: bytes = self._read(count)
        if data and self._partial is None:
            self._partial = self._now()
        return data

    def length(self) -> None:
        self.check()
        self._length()  # only the 0/2/8 length bytes, not the payload
        buffer = self.connection.frame_buffer
        header, size = buffer.header, buffer.length
        if (
            not isinstance(size, int)
            or not 0 <= size <= MAX_FRAME
            or header is None
            or header[0] != 1
            or header[4] not in {1, 2, 8, 9, 10}
            or (self.passive and header[4] == 2)
        ):
            raise ValueError("event frame limit or type")

    def frame(self) -> Any:
        self.check()
        if self._now() - self._window >= START_S:
            self._window, self._frames = self._now(), 0
        self._frames += 1
        if self._frames > MAX_EVENTS:
            raise ValueError("event frame rate")
        result = self._frame()
        self._partial = None
        return result

    def begin_query(self) -> None:
        self.check()
        if not self.passive or self._query_until is not None:
            raise ValueError("event query must be once on an established session")
        self._query_until = self._now() + QUERY_S
        self.connection.settimeout(IDLE_S)

    def close(self) -> None:
        self._closing = self._now() + IDLE_S
        try:
            self.connection.close(timeout=IDLE_S)
        finally:
            try:
                self.connection.shutdown()
            finally:
                buffer = self.connection.frame_buffer
                buffer.recv, buffer.recv_length = self._read, self._length
                self.connection.recv_frame = self._frame


class SessionSockets:
    def __init__(
        self, module: Any, now: Callable[[], float], cancelled: Callable[[], bool]
    ) -> None:
        self._module, self._now, self._cancelled = module, now, cancelled
        self._real = module.create_connection
        self._started = now()
        self.bound: FrameBounds | None = None
        module.create_connection = self.create

    def create(self, *args: Any, **kwargs: Any) -> Any:
        if self.bound is not None:
            raise ValueError("event session cannot reconnect")
        connection = self._real(*args, **kwargs)
        try:
            self.bound = FrameBounds(connection, self._now, self._cancelled, self._started)
        except BaseException:
            connection.shutdown()
            raise
        return connection

    def close(self) -> None:
        self._module.create_connection = self._real
        if self.bound is not None:
            with contextlib.suppress(Exception):
                self.bound.close()
