"""The bounded JPEG header parser (§11.3, §18.2)."""

from __future__ import annotations

import pytest
from PIL import Image

from frame_gallery.domain import Size
from frame_gallery.imaging.jpeg_header import (
    APP0,
    COM,
    MAX_SEGMENTS,
    SOF_BASELINE,
    SOF_MARKERS,
    SOF_PROGRESSIVE,
    SOS,
    TEM,
    JpegHeaderError,
    JpegLimitError,
    JpegTruncatedError,
    parse_jpeg,
)
from tests.support.images import (
    encoded_jpeg,
    jpeg_header_only,
    jpeg_segment,
    sof_payload,
    sos_payload,
)

SOI = b"\xff\xd8"
SOF0 = jpeg_segment(0xC0, sof_payload(64, 36))
SCAN = jpeg_segment(SOS, sos_payload())


def test_pillow_baseline_jpeg() -> None:
    data = encoded_jpeg(Image.new("RGB", (64, 36), (200, 10, 10)), quality=90)
    info = parse_jpeg(data)
    assert (info.width, info.height) == (64, 36)
    assert info.size == Size(64, 36)
    assert info.precision == 8
    assert info.components == 3
    assert info.sof_marker == SOF_BASELINE
    assert info.is_baseline
    assert info.markers[0] == APP0
    assert SOF_BASELINE in info.markers
    assert SOS not in info.markers


def test_pillow_progressive_and_greyscale_jpeg() -> None:
    progressive = parse_jpeg(encoded_jpeg(Image.new("RGB", (32, 16)), progressive=True))
    assert progressive.sof_marker == SOF_PROGRESSIVE
    assert not progressive.is_baseline
    grey = parse_jpeg(encoded_jpeg(Image.new("L", (32, 16))))
    assert grey.components == 1


def test_markers_are_listed_in_order() -> None:
    comment = jpeg_segment(COM, b"hello")
    info = parse_jpeg(SOI + comment + SOF0 + SCAN)
    assert info.markers == (COM, 0xC0)


def test_segments_locate_each_payload() -> None:
    # Standalone markers and SOS have no entry; fill bytes do not shift one.
    comment = jpeg_segment(COM, b"hello")
    data = SOI + comment + bytes([0xFF, TEM]) + b"\xff\xff" + SOF0 + SCAN
    info = parse_jpeg(data)
    assert [(s.marker, data[s.start : s.end]) for s in info.segments] == [
        (COM, b"hello"),
        (0xC0, sof_payload(64, 36)),
    ]


def test_fill_bytes_before_a_marker_are_skipped() -> None:
    data = SOI + b"\xff\xff\xff" + SOF0 + b"\xff\xff" + SCAN
    assert parse_jpeg(data).size == Size(64, 36)


def test_standalone_markers_have_no_length() -> None:
    data = SOI + bytes([0xFF, TEM]) + SOF0 + b"\xff\xd0\xff\xd7" + SCAN
    assert parse_jpeg(data).markers == (TEM, 0xC0, 0xD0, 0xD7)


@pytest.mark.parametrize("marker", sorted(SOF_MARKERS))
def test_every_sof_marker_is_a_frame_header(marker: int) -> None:
    info = parse_jpeg(SOI + jpeg_segment(marker, sof_payload(5, 7)) + SCAN)
    assert info.sof_marker == marker
    assert info.is_baseline is (marker == SOF_BASELINE)


@pytest.mark.parametrize("marker", [0xC4, 0xC8, 0xCC])
def test_dht_jpg_and_dac_are_not_frame_headers(marker: int) -> None:
    with pytest.raises(JpegHeaderError, match="without a frame header"):
        parse_jpeg(SOI + jpeg_segment(marker, sof_payload(5, 7)) + SCAN)


def test_the_segment_limit_is_inclusive() -> None:
    fillers = jpeg_segment(COM, b"") * (MAX_SEGMENTS - 2)
    assert parse_jpeg(SOI + fillers + SOF0 + SCAN).size == Size(64, 36)
    with pytest.raises(JpegHeaderError, match="more than 512 segments"):
        parse_jpeg(SOI + fillers + jpeg_segment(COM, b"") + SOF0 + SCAN)


def test_standalone_markers_count_towards_the_segment_limit() -> None:
    with pytest.raises(JpegHeaderError, match="more than 512 segments"):
        parse_jpeg(SOI + b"\xff\xd0" * MAX_SEGMENTS + SOF0 + SCAN)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "missing start-of-image"),
        (b"\xff", "missing start-of-image"),
        (b"\x89PNG\r\n\x1a\n", "missing start-of-image"),
        (SOI, "truncated before the start of scan"),
        (SOI + SOF0, "truncated before the start of scan"),
        (SOI + b"\x00\xff\xc0", "expected a marker"),
        (SOI + b"\xff\xff\xff", "truncated inside a marker"),
        (SOI + b"\xff\x00", "unexpected marker 0x00"),
        (SOI + b"\xff\xd8", "unexpected marker 0xD8"),
        (SOI + SOF0 + b"\xff\xd9", "unexpected marker 0xD9"),
        (SOI + b"\xff\xe0", "truncated segment length"),
        (SOI + b"\xff\xe0\x00", "truncated segment length"),
        (SOI + b"\xff\xe0\x00\x01", "bad segment length"),
        (SOI + b"\xff\xe0\x00\x10abc", "truncated segment"),
        (SOI + SOF0 + SOF0 + SCAN, "more than one frame header"),
        (SOI + jpeg_segment(0xC2, sof_payload(1, 1)) + SOF0 + SCAN, "more than one frame"),
        (SOI + SCAN, "without a frame header"),
        (SOI + jpeg_segment(0xC0, sof_payload(0, 36)) + SCAN, "zero dimension"),
        (SOI + jpeg_segment(0xC0, sof_payload(64, 0)) + SCAN, "zero dimension"),
        (SOI + jpeg_segment(0xC0, sof_payload(64, 36, components=0)) + SCAN, "components"),
        (SOI + jpeg_segment(0xC0, sof_payload(64, 36)[:-1]) + SCAN, "components"),
        (SOI + jpeg_segment(0xC0, sof_payload(64, 36) + b"\0") + SCAN, "components"),
        (SOI + jpeg_segment(0xC0, b"\x08\x00\x10") + SCAN, "too short"),
        (SOI + SOF0 + b"\xff\xda\x00", "truncated segment length"),
        (SOI + SOF0 + b"\xff\xda\x00\x0cab", "truncated segment"),
    ],
)
def test_malformed_headers_are_rejected(data: bytes, message: str) -> None:
    with pytest.raises(JpegHeaderError, match=message):
        parse_jpeg(data)


@pytest.mark.parametrize(
    "data",
    [
        SOI,
        SOI + SOF0,
        SOI + b"\xff\xff\xff",
        SOI + b"\xff\xe0",
        SOI + b"\xff\xe0\x00\x10abc",
    ],
)
def test_truncation_has_its_own_error(data: bytes) -> None:
    # The worker's pre-scan reads more of the file when its window ends.
    with pytest.raises(JpegTruncatedError):
        parse_jpeg(data)


def test_limits_have_their_own_error() -> None:
    with pytest.raises(JpegLimitError):
        parse_jpeg(SOI + jpeg_segment(COM, b"") * MAX_SEGMENTS + SOF0 + SCAN)


def test_segment_limit_is_configurable() -> None:
    data = SOI + jpeg_segment(COM, b"") * 3 + SOF0 + SCAN
    assert parse_jpeg(data, max_segments=5).size == Size(64, 36)
    with pytest.raises(JpegLimitError, match="more than 4 segments"):
        parse_jpeg(data, max_segments=4)


def test_fill_bytes_are_unlimited_by_default() -> None:
    assert parse_jpeg(SOI + b"\xff" * 100_000 + SOF0 + SCAN).size == Size(64, 36)


def test_fill_limit_counts_every_marker() -> None:
    # Two fill bytes before SOF and one before SOS.
    data = SOI + b"\xff\xff" + SOF0 + b"\xff" + SCAN
    assert parse_jpeg(data, max_fill_bytes=3).size == Size(64, 36)
    with pytest.raises(JpegLimitError, match="more than 2 fill bytes before the start of scan"):
        parse_jpeg(data, max_fill_bytes=2)


def test_refused_markers() -> None:
    data = SOI + jpeg_segment(0xF0, b"x") + SOF0 + SCAN
    assert parse_jpeg(data).markers == (0xF0, 0xC0)
    with pytest.raises(JpegHeaderError, match="unexpected marker 0xF0") as caught:
        parse_jpeg(data, refused_markers=frozenset({0xF0}))
    assert not isinstance(caught.value, JpegTruncatedError | JpegLimitError)


def test_header_only_file_parses() -> None:
    info = parse_jpeg(jpeg_header_only(20_000, 3, components=1, sof=0xC2, precision=12))
    assert info.size == Size(20_000, 3)
    assert (info.components, info.precision, info.sof_marker) == (1, 12, 0xC2)
    assert info.markers == (0xC2,)
