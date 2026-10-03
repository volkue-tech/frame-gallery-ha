"""The bytes-only JSON channel (§11.3, D-109)."""

from __future__ import annotations

import enum
import json
import sys
from typing import cast

import pytest

from frame_gallery.isolation.channel import (
    MAX_MESSAGE_BYTES,
    MAX_NESTING_DEPTH,
    ChannelError,
    decode_message,
    encode_message,
)
from frame_gallery.isolation.executor import JsonObject


def _nested(depth: int) -> dict[str, object]:
    """An object whose containers nest ``depth`` levels deep (``{}`` is 1)."""
    message: dict[str, object] = {}
    for _ in range(depth - 1):
        message = {"a": message}
    return message


def _encode(message: object, max_bytes: int = MAX_MESSAGE_BYTES) -> bytes:
    """Encode a value the type checker would refuse (the seam sees such values)."""
    return encode_message(cast("JsonObject", message), max_bytes=max_bytes)


class _Colour(enum.StrEnum):
    RED = "red"


# --- encode ---------------------------------------------------------------


def test_encode_is_canonical_and_compact() -> None:
    data = encode_message({"b": 1, "a": [True, None, 1.5, "x", False, -3]})
    assert data == b'{"a":[true,null,1.5,"x",false,-3],"b":1}'


def test_encode_escapes_non_ascii() -> None:
    data = encode_message({"t": "caf" + chr(0xE9)})
    assert data.isascii()
    assert data == b'{"t":"caf' + b"\x5cu00e9" + b'"}'


def test_encode_round_trips_through_decode() -> None:
    message: JsonObject = {"n": 3, "f": 0.25, "s": "text", "l": [1, [2, {"k": None}]], "o": {}}
    assert decode_message(encode_message(message)) == message


def test_encode_accepts_str_and_int_subclasses_as_plain_values() -> None:
    data = _encode({"colour": _Colour.RED, "flag": True})
    assert decode_message(data) == {"colour": "red", "flag": True}


@pytest.mark.parametrize(
    "message",
    [[1, 2], "text", 3, None, (("a", 1),)],
    ids=["list", "str", "int", "none", "tuple"],
)
def test_encode_rejects_a_non_object(message: object) -> None:
    with pytest.raises(ChannelError, match="JSON object"):
        _encode(message)


@pytest.mark.parametrize("key", [1, 1.5, True, None, ("a",)])
def test_encode_rejects_non_string_keys(key: object) -> None:
    with pytest.raises(ChannelError, match="keys must be strings"):
        _encode({"outer": {key: "value"}})


@pytest.mark.parametrize(
    "value",
    [(1, 2), {1, 2}, b"bytes", object(), 1j, frozenset()],
    ids=["tuple", "set", "bytes", "object", "complex", "frozenset"],
)
def test_encode_rejects_non_json_types(value: object) -> None:
    with pytest.raises(ChannelError, match="not a JSON type"):
        _encode({"value": [value]})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_encode_rejects_non_finite_numbers(value: float) -> None:
    with pytest.raises(ChannelError, match="non-finite"):
        encode_message({"value": value})


def test_encode_accepts_the_maximum_nesting_depth() -> None:
    message = _nested(MAX_NESTING_DEPTH)
    assert decode_message(_encode(message)) == message


def test_encode_rejects_deeper_objects() -> None:
    with pytest.raises(ChannelError, match="nests deeper"):
        _encode(_nested(MAX_NESTING_DEPTH + 1))


def test_encode_rejects_deeper_arrays() -> None:
    value: object = []
    for _ in range(MAX_NESTING_DEPTH):
        value = [value]
    with pytest.raises(ChannelError, match="nests deeper"):
        _encode({"a": value})


def test_encode_rejects_cycles() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(ChannelError, match="nests deeper"):
        _encode({"a": cyclic})


def test_encode_bounds_the_walk_over_shared_structures() -> None:
    # 2**26 values if expanded; refused after max_bytes values instead.
    shared: list[object] = []
    for _ in range(25):
        shared = [shared, shared]
    with pytest.raises(ChannelError, match="exceeds 1024 bytes"):
        _encode({"a": shared}, max_bytes=1024)


def test_encode_rejects_integers_beyond_the_digit_limit() -> None:
    previous = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(640)
    try:
        with pytest.raises(ChannelError, match="not encodable"):
            encode_message({"n": 10**700})
    finally:
        sys.set_int_max_str_digits(previous)


def test_encode_size_limit_is_inclusive() -> None:
    message: JsonObject = {"s": "x" * 100}
    size = len(encode_message(message))
    assert len(encode_message(message, max_bytes=size)) == size
    with pytest.raises(ChannelError, match=f"exceeds {size - 1} bytes"):
        encode_message(message, max_bytes=size - 1)


def test_encode_rejects_oversize_by_default() -> None:
    with pytest.raises(ChannelError, match="exceeds"):
        encode_message({"s": "x" * MAX_MESSAGE_BYTES})


@pytest.mark.parametrize("max_bytes", [0, -1])
def test_encode_requires_a_positive_cap(max_bytes: int) -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        encode_message({}, max_bytes=max_bytes)


# --- decode ---------------------------------------------------------------


def test_decode_returns_the_object() -> None:
    assert decode_message(b'{"a":[1,2.5,"x",true,null],"b":{"c":{}}}') == {
        "a": [1, 2.5, "x", True, None],
        "b": {"c": {}},
    }


def test_decode_accepts_utf8_and_whitespace() -> None:
    text = '{ "t" : "caf' + chr(0xE9) + '" }'
    assert decode_message(text.encode("utf-8")) == {"t": "caf" + chr(0xE9)}


def test_decode_checks_the_size_before_parsing() -> None:
    # Not JSON at all: the size check must answer first.
    with pytest.raises(ChannelError, match="exceeds 10 bytes"):
        decode_message(b"\xff" * 11, max_bytes=10)


def test_decode_size_limit_is_inclusive() -> None:
    data = b'{"a":1}'
    assert decode_message(data, max_bytes=len(data)) == {"a": 1}
    with pytest.raises(ChannelError, match="exceeds"):
        decode_message(data, max_bytes=len(data) - 1)


def test_decode_rejects_invalid_utf8() -> None:
    with pytest.raises(ChannelError, match="UTF-8"):
        decode_message(b'{"a":"\xff"}')


@pytest.mark.parametrize(
    "data",
    [b"", b"{", b'{"a":}', b"{} {}", b"{'a':1}", b'{"a":1,}', b"\xef\xbb\xbf{}", b"\x80\x05K\x01."],
    ids=["empty", "open", "missing", "trailing", "quotes", "comma", "bom", "pickle"],
)
def test_decode_rejects_invalid_json(data: bytes) -> None:
    with pytest.raises(ChannelError):
        decode_message(data)


@pytest.mark.parametrize(
    "literal", [b"NaN", b"Infinity", b"-Infinity", b"1e999", b"-1e999", b"[1e400]"]
)
def test_decode_rejects_non_finite_numbers(literal: bytes) -> None:
    with pytest.raises(ChannelError, match="not valid JSON"):
        decode_message(b'{"a":' + literal + b"}")


def test_decode_keeps_finite_floats() -> None:
    assert decode_message(b'{"a":1.5e3,"b":-0.25}') == {"a": 1500.0, "b": -0.25}


@pytest.mark.parametrize("data", [b'{"a":1,"a":2}', b'{"o":{"k":1,"k":1}}'])
def test_decode_rejects_duplicate_keys(data: bytes) -> None:
    with pytest.raises(ChannelError, match="not valid JSON"):
        decode_message(data)


@pytest.mark.parametrize("data", [b"[]", b'"text"', b"1", b"null", b"true"])
def test_decode_rejects_a_non_object_top_level(data: bytes) -> None:
    with pytest.raises(ChannelError, match="JSON object"):
        decode_message(data)


def test_decode_accepts_the_maximum_nesting_depth() -> None:
    data = json.dumps(_nested(MAX_NESTING_DEPTH)).encode()
    assert decode_message(data) == _nested(MAX_NESTING_DEPTH)


def test_decode_rejects_deeper_objects() -> None:
    data = json.dumps(_nested(MAX_NESTING_DEPTH + 1)).encode()
    with pytest.raises(ChannelError, match="nests deeper"):
        decode_message(data)


def test_decode_rejects_deeper_arrays() -> None:
    depth = MAX_NESTING_DEPTH  # plus the top-level object
    data = b'{"a":' + b"[" * depth + b"]" * depth + b"}"
    with pytest.raises(ChannelError, match="nests deeper"):
        decode_message(data)


def test_decode_rejects_extreme_nesting_before_the_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected_parser(*args: object, **kwargs: object) -> object:
        pytest.fail("oversized nesting must be refused before the JSON parser")

    monkeypatch.setattr("frame_gallery.isolation.channel.json.loads", unexpected_parser)
    depth = 100_000
    data = b'{"a":' + b"[" * depth + b"]" * depth + b"}"
    with pytest.raises(ChannelError, match="nests deeper"):
        decode_message(data, max_bytes=len(data))


def test_decode_retains_a_defensive_depth_check_on_the_decoded_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_tree(*args: object, **kwargs: object) -> object:
        return _nested(MAX_NESTING_DEPTH + 1)

    monkeypatch.setattr("frame_gallery.isolation.channel.json.loads", unexpected_tree)
    with pytest.raises(ChannelError, match="nests deeper"):
        decode_message(b"{}")


@pytest.mark.parametrize("max_bytes", [0, -5])
def test_decode_requires_a_positive_cap(max_bytes: int) -> None:
    with pytest.raises(ValueError, match="max_bytes"):
        decode_message(b"{}", max_bytes=max_bytes)
