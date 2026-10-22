"""Bounded standard-library validation of optional, worker-derived small JPEGs."""

from __future__ import annotations

import base64
from typing import Final

from frame_gallery.imaging.jpeg_header import APP1, APP2, COM, JpegHeaderError, parse_jpeg

MAX_PREVIEW_BYTES: Final = 32 * 1024
MAX_PREVIEW_TEXT: Final = 4 * ((MAX_PREVIEW_BYTES + 2) // 3)


def decode_preview(value: object) -> bytes:
    if not isinstance(value, str) or not 0 < len(value) <= MAX_PREVIEW_TEXT:
        raise ValueError("invalid small preview encoding")
    try:
        data = base64.b64decode(value, validate=True)
        info = parse_jpeg(data)
    except (ValueError, JpegHeaderError) as exc:
        raise ValueError("invalid small preview JPEG") from exc
    if (
        not 0 < len(data) <= MAX_PREVIEW_BYTES
        or base64.b64encode(data).decode("ascii") != value
        or not data.endswith(b"\xff\xd9")
        or not info.is_baseline
        or info.precision != 8
        or info.components != 3
        or not (0 < info.width <= 640 and 0 < info.height <= 360)
        or any(marker in info.markers for marker in (APP1, APP2, COM))
    ):
        raise ValueError("invalid small preview limits")
    return data
