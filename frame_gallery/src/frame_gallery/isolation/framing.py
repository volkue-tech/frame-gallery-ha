"""Frames on the worker's pipes (§11.3, D-163).

Each message is a 4-byte big-endian length followed by that many bytes of
canonical JSON (:mod:`frame_gallery.isolation.channel`). A frame may be at
most :data:`MAX_FRAME_BYTES`: the 64 KiB message cap plus a small envelope
(``{"type": "result", "result": …}``). The parent reads the worker's frames
through :class:`FrameBuffer`, which never trusts a length before checking it.
"""

from __future__ import annotations

import os
import struct
from typing import Final

from frame_gallery.isolation.channel import (
    MAX_MESSAGE_BYTES,
    ChannelError,
    decode_message,
    encode_message,
)
from frame_gallery.isolation.executor import JsonObject

ENVELOPE_BYTES: Final = 1024
MAX_FRAME_BYTES: Final = MAX_MESSAGE_BYTES + ENVELOPE_BYTES
_HEADER: Final = struct.Struct("!I")


def encode_frame(message: JsonObject) -> bytes:
    """Raises :class:`ChannelError` for a message that is not valid or too large."""
    body = encode_message(message, max_bytes=MAX_FRAME_BYTES)
    return _HEADER.pack(len(body)) + body


def write_frame(fd: int, message: JsonObject) -> None:
    """Write one frame completely. Raises ``OSError`` (``BrokenPipeError`` once
    the reader is gone) and :class:`ChannelError`."""
    view = memoryview(encode_frame(message))
    while view:
        written = os.write(fd, view)
        view = view[written:]


def read_frame(fd: int) -> JsonObject | None:
    """Read one frame, blocking; ``None`` at a clean end of the stream.
    Raises :class:`ChannelError` for a truncated or invalid frame."""
    header = _read_exactly(fd, _HEADER.size)
    if not header:
        return None
    (length,) = _HEADER.unpack(_complete(header, _HEADER.size))
    if length > MAX_FRAME_BYTES:
        msg = f"frame of {length} bytes exceeds {MAX_FRAME_BYTES}"
        raise ChannelError(msg)
    return decode_message(_complete(_read_exactly(fd, length), length), max_bytes=MAX_FRAME_BYTES)


def _read_exactly(fd: int, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = os.read(fd, size - len(data))
        if not chunk:
            break
        data += chunk
    return data


def _complete(data: bytes, size: int) -> bytes:
    if len(data) != size:
        msg = "the stream ended inside a frame"
        raise ChannelError(msg)
    return data


class FrameBuffer:
    """Collects bytes as they arrive and yields each complete message.

    A frame's length is checked as soon as its header is complete, so at most
    one frame of :data:`MAX_FRAME_BYTES`, plus the chunk being fed, is held.
    A malformed or oversize frame sets :attr:`error`; the messages decoded
    before it in the same chunk are still returned, and nothing after it is.
    """

    def __init__(self) -> None:
        self._data = bytearray()
        self.error: ChannelError | None = None

    def feed(self, chunk: bytes) -> list[JsonObject]:
        """Add ``chunk``; return the messages it completes, in order, up to
        the first bad frame (then :attr:`error` is set, and later chunks are
        ignored)."""
        if self.error is not None:
            return []
        self._data += chunk
        messages: list[JsonObject] = []
        while len(self._data) >= _HEADER.size:
            (length,) = _HEADER.unpack_from(self._data)
            if length > MAX_FRAME_BYTES:
                self.error = ChannelError(f"frame of {length} bytes exceeds {MAX_FRAME_BYTES}")
                break
            end = _HEADER.size + length
            if len(self._data) < end:
                break
            body = bytes(self._data[_HEADER.size : end])
            del self._data[:end]
            try:
                messages.append(decode_message(body, max_bytes=MAX_FRAME_BYTES))
            except ChannelError as error:
                self.error = error
                break
        if self.error is not None:
            self._data.clear()
        return messages

    @property
    def pending(self) -> int:
        """Bytes of an incomplete frame still held."""
        return len(self._data)
