"""Bytes-only JSON messages for the executor seam (§11.3, D-109).

Requests and results cross the seam as size-capped UTF-8 JSON objects. The
encoder is canonical (sorted keys, ASCII only, no whitespace) and the decoder
treats its input as hostile: the size is checked before parsing, and nothing
is ever unpickled or evaluated.
"""

from __future__ import annotations

import json
import math
from typing import Final, NoReturn

from frame_gallery.errors import FrameGalleryError
from frame_gallery.isolation.executor import JsonObject

MAX_MESSAGE_BYTES: Final = 64 * 1024
"""The message cap (§11.3), in both executors. The process executor carries
each message in a frame that may be ``framing.ENVELOPE_BYTES`` larger for its
envelope; the body is still held to this cap (D-163)."""

MAX_NESTING_DEPTH: Final = 32
"""Containers (objects and arrays) nested deeper than this are refused."""


class ChannelError(FrameGalleryError):
    """A message is not a valid, size-capped JSON object."""


def _check_max_bytes(max_bytes: int) -> None:
    if max_bytes <= 0:
        msg = f"max_bytes must be positive, got {max_bytes!r}"
        raise ValueError(msg)


def _validate_tree(message: object, max_nodes: int) -> None:
    """Refuse anything ``json.dumps`` would encode loosely or not at all.

    Non-string keys, tuples, and other types are refused rather than coerced,
    so a message decodes to exactly what was encoded. Every value encodes to
    at least one byte, so more than ``max_nodes`` values means oversize; this
    also bounds the walk over shared or cyclic structures.
    """
    if not isinstance(message, dict):
        msg = "a message must be a JSON object"
        raise ChannelError(msg)
    stack: list[tuple[object, int]] = [(message, 1)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            msg = f"message exceeds {max_nodes} bytes"
            raise ChannelError(msg)
        if isinstance(value, dict):
            if depth > MAX_NESTING_DEPTH:
                msg = f"message nests deeper than {MAX_NESTING_DEPTH} levels"
                raise ChannelError(msg)
            for key, item in value.items():
                if not isinstance(key, str):
                    msg = f"object keys must be strings, not {type(key).__name__}"
                    raise ChannelError(msg)
                stack.append((item, depth + 1))
        elif isinstance(value, list):
            if depth > MAX_NESTING_DEPTH:
                msg = f"message nests deeper than {MAX_NESTING_DEPTH} levels"
                raise ChannelError(msg)
            stack.extend((item, depth + 1) for item in value)
        elif isinstance(value, float):
            if not math.isfinite(value):
                msg = "non-finite numbers are not valid JSON"
                raise ChannelError(msg)
        elif value is not None and not isinstance(value, str | int):
            msg = f"{type(value).__name__} is not a JSON type"
            raise ChannelError(msg)


def encode_message(message: JsonObject, *, max_bytes: int = MAX_MESSAGE_BYTES) -> bytes:
    """Encode a JSON object canonically. Raises :class:`ChannelError`."""
    _check_max_bytes(max_bytes)
    _validate_tree(message, max_bytes)
    try:
        text = json.dumps(
            message, ensure_ascii=True, allow_nan=False, separators=(",", ":"), sort_keys=True
        )
    except (TypeError, ValueError):
        # Reached only for integers beyond the interpreter's digit limit.
        msg = "message is not encodable as JSON"
        raise ChannelError(msg) from None
    data = text.encode("ascii")
    if len(data) > max_bytes:
        msg = f"message exceeds {max_bytes} bytes"
        raise ChannelError(msg)
    return data


def _reject_constant(name: str) -> NoReturn:
    msg = f"{name} is not valid JSON"
    raise ValueError(msg)


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        msg = "number out of range"
        raise ValueError(msg)
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    obj = dict(pairs)
    if len(obj) != len(pairs):
        msg = "duplicate object key"
        raise ValueError(msg)
    return obj


def _check_depth(value: object) -> None:
    stack: list[tuple[object, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if isinstance(item, dict):
            children: list[object] = list(item.values())
        elif isinstance(item, list):
            children = item
        else:
            continue
        if depth > MAX_NESTING_DEPTH:
            msg = f"message nests deeper than {MAX_NESTING_DEPTH} levels"
            raise ChannelError(msg)
        stack.extend((child, depth + 1) for child in children)


def decode_message(data: bytes, *, max_bytes: int = MAX_MESSAGE_BYTES) -> JsonObject:
    """Decode an untrusted message into a JSON object. Raises :class:`ChannelError`.

    Refuses oversize input (before parsing), invalid UTF-8, invalid JSON,
    ``NaN`` and infinities (including overflowing literals such as ``1e999``),
    duplicate keys, a top level that is not an object, and nesting deeper
    than :data:`MAX_NESTING_DEPTH`.
    """
    _check_max_bytes(max_bytes)
    if len(data) > max_bytes:
        msg = f"message exceeds {max_bytes} bytes"
        raise ChannelError(msg)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        msg = "message is not valid UTF-8"
        raise ChannelError(msg) from None
    try:
        value: object = json.loads(
            text,
            parse_constant=_reject_constant,
            parse_float=_finite_float,
            object_pairs_hook=_unique_object,
        )
    except (ValueError, RecursionError):
        msg = "message is not valid JSON"
        raise ChannelError(msg) from None
    if not isinstance(value, dict):
        msg = "a message must be a JSON object"
        raise ChannelError(msg)
    _check_depth(value)
    result: JsonObject = value
    return result
