"""Frames on the worker pipes (isolation/framing.py; §11.3, D-163)."""

from __future__ import annotations

import contextlib
import os
import struct
from collections.abc import Iterator

import pytest

from frame_gallery.isolation.channel import MAX_MESSAGE_BYTES, ChannelError
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.isolation.framing import (
    MAX_FRAME_BYTES,
    FrameBuffer,
    encode_frame,
    read_frame,
    write_frame,
)


@pytest.fixture
def pipe() -> Iterator[tuple[int, int]]:
    read, write = os.pipe()
    try:
        yield read, write
    finally:
        for fd in (read, write):
            with contextlib.suppress(OSError):
                os.close(fd)


def header(length: int) -> bytes:
    return struct.pack("!I", length)


def test_a_frame_is_its_length_then_canonical_json() -> None:
    assert encode_frame({"b": 1, "a": [True, None]}) == header(23) + b'{"a":[true,null],"b":1}'


def test_the_frame_cap_leaves_room_for_the_envelope() -> None:
    assert MAX_FRAME_BYTES == MAX_MESSAGE_BYTES + 1024
    encode_frame({"result": {"x": "y" * (MAX_MESSAGE_BYTES - 20)}})
    with pytest.raises(ChannelError, match="exceeds"):
        encode_frame({"x": "y" * MAX_FRAME_BYTES})


def test_write_and_read_round_trip(pipe: tuple[int, int]) -> None:
    read, write = pipe
    write_frame(write, {"type": "ready"})
    write_frame(write, {"n": 2})
    os.close(write)
    assert read_frame(read) == {"type": "ready"}
    assert read_frame(read) == {"n": 2}
    assert read_frame(read) is None


def test_a_large_frame_is_written_completely(pipe: tuple[int, int]) -> None:
    """More than a pipe buffer at once: written in parts by one call."""
    read, write = pipe
    message: JsonObject = {"data": "z" * (MAX_MESSAGE_BYTES - 20)}
    received: list[object] = []
    import threading  # noqa: PLC0415

    reader = threading.Thread(target=lambda: received.append(read_frame(read)))
    reader.start()
    write_frame(write, message)
    reader.join(timeout=10)
    assert received == [message]


@pytest.mark.parametrize(
    ("data", "match"),
    [
        (header(10)[:2], "ended inside a frame"),
        (header(10) + b"{}", "ended inside a frame"),
        (header(MAX_FRAME_BYTES + 1), "exceeds"),
        (header(4) + b"[1] ", "JSON object"),
        (header(3) + b"{x}", "not valid JSON"),
    ],
)
def test_a_bad_frame_is_refused(pipe: tuple[int, int], data: bytes, match: str) -> None:
    read, write = pipe
    os.write(write, data)
    os.close(write)
    with pytest.raises(ChannelError, match=match):
        read_frame(read)


class TestFrameBuffer:
    def test_messages_across_chunks(self) -> None:
        frames = FrameBuffer()
        data = encode_frame({"a": 1}) + encode_frame({"b": 2})
        assert frames.feed(data[:3]) == []
        assert frames.pending == 3
        assert frames.feed(data[3:10]) == []
        assert frames.feed(data[10:]) == [{"a": 1}, {"b": 2}]
        assert frames.pending == 0

    def test_an_oversize_length_is_refused_before_the_body(self) -> None:
        with pytest.raises(ChannelError, match="exceeds"):
            FrameBuffer().feed(header(MAX_FRAME_BYTES + 1))

    def test_an_invalid_body_is_refused(self) -> None:
        with pytest.raises(ChannelError, match="not valid JSON"):
            FrameBuffer().feed(header(2) + b"{]")

    def test_the_largest_frame_is_accepted(self) -> None:
        body = b'{"x":"' + b"y" * (MAX_FRAME_BYTES - 8) + b'"}'
        assert len(body) == MAX_FRAME_BYTES
        assert FrameBuffer().feed(header(len(body)) + body) == [{"x": "y" * (MAX_FRAME_BYTES - 8)}]
