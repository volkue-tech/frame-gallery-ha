"""A bounded JPEG header parser (§11.3, §18.2): standard library only.

It walks the marker segments from SOI up to the first SOS and never looks at
entropy-coded data. Every malformed or unexpected structure raises
:class:`JpegHeaderError`; the input is untrusted. The parent validates
``delivery.jpg`` with the default rules; the worker's pre-scan of a source
(``source_scan``) passes stricter ones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from frame_gallery.domain import Size
from frame_gallery.errors import FrameGalleryError

MAX_SEGMENTS: Final = 512
"""Markers scanned after SOI, including SOS: the scan is bounded even for
hostile input."""

SOI: Final = 0xD8
EOI: Final = 0xD9
SOS: Final = 0xDA
TEM: Final = 0x01
APP0: Final = 0xE0
APP1: Final = 0xE1
APP2: Final = 0xE2
COM: Final = 0xFE
SOF_BASELINE: Final = 0xC0
SOF_PROGRESSIVE: Final = 0xC2

SOF_MARKERS: Final = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)
"""Start-of-frame markers; 0xC4 (DHT), 0xC8 (JPG), and 0xCC (DAC) are not."""

RST_MARKERS: Final = frozenset(range(0xD0, 0xD8))
_STANDALONE: Final = RST_MARKERS | {TEM}
"""Markers without a length field that may appear between segments."""

_FILL: Final = 0xFF
_NOT_FILL: Final = re.compile(rb"[^\xff]")
_NO_MARKERS: Final[frozenset[int]] = frozenset()


class JpegHeaderError(FrameGalleryError):
    """The data is not a well-formed JPEG header. The message is log-safe."""


class JpegTruncatedError(JpegHeaderError):
    """The data ends before the start of scan."""


class JpegLimitError(JpegHeaderError):
    """The header has more markers or fill bytes than the rules allow."""


@dataclass(frozen=True, slots=True)
class JpegSegment:
    """A marker segment with a length field: where its payload lies in the
    parsed data (``data[start:end]``)."""

    marker: int
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class JpegInfo:
    """What the header declares."""

    width: int
    height: int
    precision: int
    """Sample precision in bits (8 for baseline)."""

    components: int
    sof_marker: int
    markers: tuple[int, ...]
    """Every marker after SOI and before SOS, in order (the second byte)."""

    segments: tuple[JpegSegment, ...]
    """Every segment with a length field after SOI and before SOS, in order."""

    @property
    def size(self) -> Size:
        return Size(self.width, self.height)

    @property
    def is_baseline(self) -> bool:
        """Baseline sequential DCT (SOF0)."""
        return self.sof_marker == SOF_BASELINE


@dataclass(frozen=True, slots=True)
class _Frame:
    width: int
    height: int
    precision: int
    components: int
    marker: int


def _parse_frame(marker: int, segment: bytes) -> _Frame:
    if len(segment) < 6:
        msg = "frame header too short"
        raise JpegHeaderError(msg)
    precision = segment[0]
    height = int.from_bytes(segment[1:3], "big")
    width = int.from_bytes(segment[3:5], "big")
    components = segment[5]
    if components == 0 or len(segment) != 6 + 3 * components:
        msg = "frame header length does not match its components"
        raise JpegHeaderError(msg)
    if width == 0 or height == 0:
        msg = "frame header declares a zero dimension"
        raise JpegHeaderError(msg)
    return _Frame(width, height, precision, components, marker)


def _next_marker(data: bytes, pos: int, fill: int, max_fill: int) -> tuple[int, int, int]:
    """The marker at ``pos`` after any fill bytes, the position after it, and
    the fill bytes counted so far (``fill`` plus those skipped here)."""
    end = len(data)
    if pos >= end:
        msg = "truncated before the start of scan"
        raise JpegTruncatedError(msg)
    if data[pos] != _FILL:
        msg = "expected a marker"
        raise JpegHeaderError(msg)
    # The last 0xFF before the marker byte belongs to the marker itself.
    match = _NOT_FILL.search(data, pos)
    marker_pos = end if match is None else match.start()
    fill += marker_pos - pos - 1
    if fill > max_fill:
        msg = f"more than {max_fill} fill bytes before the start of scan"
        raise JpegLimitError(msg)
    if marker_pos >= end:
        msg = "truncated inside a marker"
        raise JpegTruncatedError(msg)
    return data[marker_pos], marker_pos + 1, fill


def _segment_end(data: bytes, pos: int) -> int:
    """The position after the segment whose length field is at ``pos``; its
    payload starts at ``pos + 2``. The payload is not copied."""
    end = len(data)
    if pos + 2 > end:
        msg = "truncated segment length"
        raise JpegTruncatedError(msg)
    length = int.from_bytes(data[pos : pos + 2], "big")
    if length < 2:
        msg = "bad segment length"
        raise JpegHeaderError(msg)
    if pos + length > end:
        msg = "truncated segment"
        raise JpegTruncatedError(msg)
    return pos + length


def parse_jpeg(
    data: bytes,
    *,
    max_segments: int = MAX_SEGMENTS,
    max_fill_bytes: int | None = None,
    refused_markers: frozenset[int] = _NO_MARKERS,
) -> JpegInfo:
    """Parse the header of ``data`` up to the first SOS.

    Fill bytes (``0xFF`` padding before a marker) are skipped, and the
    standalone markers TEM and RST0-RST7 are accepted between segments.
    Raises :class:`JpegHeaderError` for a missing SOI, a bad length, a
    second SOF, SOS without a preceding SOF, a zero dimension, or a marker
    in ``refused_markers``; :class:`JpegTruncatedError` when the data ends
    first; and :class:`JpegLimitError` for more than ``max_segments``
    markers or ``max_fill_bytes`` fill bytes in total (unlimited when
    ``None``).
    """
    if data[:2] != b"\xff\xd8":
        msg = "missing start-of-image marker"
        raise JpegHeaderError(msg)
    pos = 2
    frame: _Frame | None = None
    markers: list[int] = []
    segments: list[JpegSegment] = []
    fill = 0
    max_fill = len(data) if max_fill_bytes is None else max_fill_bytes
    for _ in range(max_segments):
        marker, pos, fill = _next_marker(data, pos, fill, max_fill)
        if marker in _STANDALONE:
            markers.append(marker)
            continue
        if marker in (0x00, SOI, EOI) or marker in refused_markers:
            msg = f"unexpected marker 0x{marker:02X} before the start of scan"
            raise JpegHeaderError(msg)
        start = pos + 2
        pos = _segment_end(data, pos)
        if marker == SOS:
            if frame is None:
                msg = "start of scan without a frame header"
                raise JpegHeaderError(msg)
            return JpegInfo(
                width=frame.width,
                height=frame.height,
                precision=frame.precision,
                components=frame.components,
                sof_marker=frame.marker,
                markers=tuple(markers),
                segments=tuple(segments),
            )
        markers.append(marker)
        segments.append(JpegSegment(marker, start, pos))
        if marker in SOF_MARKERS:
            if frame is not None:
                msg = "more than one frame header"
                raise JpegHeaderError(msg)
            frame = _parse_frame(marker, data[start:pos])
    msg = f"more than {max_segments} segments before the start of scan"
    raise JpegLimitError(msg)
