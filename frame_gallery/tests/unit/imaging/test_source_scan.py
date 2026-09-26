"""The worker's bounded pre-scan of a source header (§11.1 step 2, §18.1; L4-01)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.imaging import source_scan
from frame_gallery.imaging.source_scan import (
    MAX_FILL_BYTES,
    MAX_HEADER_SEGMENTS,
    SourceLimitError,
    SourceScanError,
    SourceStructureError,
    scan_source,
)
from tests.support import images

COLOUR = (90, 140, 200)
SOI = b"\xff\xd8"
COM = images.jpeg_segment(0xFE, b"")
PRIVATE = images.png_chunk(b"prVt", b"")


def _scan(data: bytes) -> None:
    """Scan ``data`` from an arbitrary position; the file is rewound after."""
    file = io.BytesIO(data)
    file.seek(len(data) // 2)
    scan_source(file)
    assert file.tell() == 0


def _refused(data: bytes, error: type[SourceScanError], message: str) -> None:
    with pytest.raises(error, match=message) as caught:
        _scan(data)
    assert len(str(caught.value)) <= 120


def _jpeg(mode: str = "RGB", **options: object) -> bytes:
    return images.encoded_jpeg(Image.new(mode, (32, 18)), **options)


def _png(image: Image.Image, **options: object) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, "PNG", **options)
    return buffer.getvalue()


# --- ordinary files ----------------------------------------------------------------


@pytest.mark.parametrize(
    "data",
    [
        _jpeg(),
        _jpeg(progressive=True),
        _jpeg("L"),
        _jpeg("CMYK"),
        _jpeg(icc_profile=images.srgb_icc(), exif=b"Exif\x00\x00II*\x00\x08\x00\x00\x00"),
        _png(Image.new("RGB", (32, 18), COLOUR)),
        _png(Image.new("RGB", (32, 18), COLOUR), icc_profile=images.srgb_icc()),
        _png(images.palette((32, 18), COLOUR, transparent_left=True), transparency=1),
        _png(Image.new("I;16", (32, 18), 1000)),
        images.flat_png((8, 4), COLOUR, before=images.png_chunk(b"tEXt", b"a\x00b")),
        images.flat_png((8, 4), COLOUR, after=images.png_chunk(b"tEXt", b"a\x00b")),
    ],
    ids=[
        "jpeg",
        "jpeg-progressive",
        "jpeg-grey",
        "jpeg-cmyk",
        "jpeg-icc-exif",
        "png",
        "png-icc",
        "png-palette",
        "png-16-bit",
        "png-text-before",
        "png-text-after",
    ],
)
def test_ordinary_files_pass(data: bytes) -> None:
    _scan(data)


def test_multi_frame_files_pass(tmp_path: Path) -> None:
    frames = [Image.new("RGB", (32, 18), COLOUR), Image.new("RGB", (16, 9), (0, 0, 0))]
    _scan(images.save_mpo(frames, tmp_path / "s.jpg").read_bytes())
    _scan(images.save_apng(frames[:1] * 2, tmp_path / "s.png").read_bytes())


@pytest.mark.parametrize(
    "data", [b"", b"GIF89a\x01\x00\x01\x00\x00\x00\x00;", b"not an image", b"\xff\xd8"]
)
def test_other_content_is_left_to_pillow(data: bytes) -> None:
    _scan(data)


# --- JPEG ----------------------------------------------------------------------------


def test_jpeg_segment_limit_is_inclusive() -> None:
    # The frame header and SOS count too: 1 022 comments make 1 024 markers.
    header = images.jpeg_header_only(32, 18)
    _scan(images.with_segments(header, COM * (MAX_HEADER_SEGMENTS - 2)))
    _refused(
        images.with_segments(header, COM * (MAX_HEADER_SEGMENTS - 1)),
        SourceLimitError,
        "more than 1024 segments before the start of scan",
    )


def test_jpeg_segment_flood_stops_early() -> None:
    flood = images.jpeg_segment(0xEF, b"") * 2_000_000  # 8 MB, like the finding
    _refused(images.with_segments(_jpeg(), flood), SourceLimitError, "more than 1024 segments")


def test_jpeg_fill_limit_is_inclusive() -> None:
    _scan(images.with_segments(_jpeg(), b"\xff" * MAX_FILL_BYTES))
    _refused(
        images.with_segments(_jpeg(), b"\xff" * (MAX_FILL_BYTES + 1)),
        SourceLimitError,
        "more than 4096 fill bytes before the start of scan",
    )


def test_jpeg_fill_flood_to_the_end_is_a_limit() -> None:
    # No marker ever follows: the fill limit is reported before truncation.
    _refused(SOI + b"\xff" * 100_000, SourceLimitError, "fill bytes")


def test_jpeg_header_larger_than_the_first_window_passes() -> None:
    # Three 60 000-byte APP segments: the window grows until SOS is found.
    metadata = images.jpeg_segment(0xE9, bytes(60_000)) * 3
    _scan(images.with_segments(_jpeg(), metadata))


def test_jpeg_header_byte_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = images.jpeg_segment(0xE9, bytes(60_000)) * 3
    monkeypatch.setattr(source_scan, "MAX_HEADER_BYTES", 100_000)
    _refused(
        images.with_segments(_jpeg(), metadata),
        SourceLimitError,
        "the JPEG header exceeds 100000 bytes",
    )


def test_jpeg_header_byte_limit_below_the_first_window(monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = images.jpeg_segment(0xE9, bytes(2_000))
    monkeypatch.setattr(source_scan, "MAX_HEADER_BYTES", 1_000)
    _refused(images.with_segments(_jpeg(), metadata), SourceLimitError, "exceeds 1000 bytes")


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (SOI + b"\xff", "truncated inside a marker"),
        (SOI + images.jpeg_segment(0xC0, images.sof_payload(32, 18)), "truncated before the start"),
        # A maximal segment cut by one byte: longer than the first window.
        (SOI + images.jpeg_segment(0xE9, bytes(65_533))[:-1], "truncated segment"),
        # Junk between segments (Pillow would skip it byte by byte).
        (SOI + COM + b"\x00" + _jpeg()[2:], "expected a marker"),
        (SOI + b"\xff\xd9" + _jpeg()[2:], "unexpected marker 0xD9"),
    ],
    ids=["cut-marker", "no-scan", "cut-segment", "junk", "end-of-image"],
)
def test_malformed_jpeg_headers_are_structural(data: bytes, message: str) -> None:
    _refused(data, SourceStructureError, message)


@pytest.mark.parametrize("marker", [0xC8, 0xF0, 0xF7, 0xFD])
def test_markers_pillow_reads_without_a_length_are_refused(marker: int) -> None:
    # Pillow would step over the length and parse the payload as markers.
    segment = images.jpeg_segment(marker, COM * 10)
    _refused(
        images.with_segments(_jpeg(), segment),
        SourceStructureError,
        f"unexpected marker 0x{marker:02X} before the start of scan",
    )


@pytest.mark.parametrize("marker", [0xE0, 0xEF, 0xFE])
def test_application_and_comment_segments_pass(marker: int) -> None:
    _scan(images.with_segments(_jpeg(), images.jpeg_segment(marker, b"payload")))


# --- PNG -------------------------------------------------------------------------------


def _png_file(*chunks: bytes) -> bytes:
    return images.png_file(images.png_ihdr(8, 4), *chunks)


IDAT = images.png_idat([bytes(COLOUR) * 8] * 4)


def test_png_chunk_limit_is_inclusive() -> None:
    # IHDR counts: with 1 023 private chunks there are 1 024 besides the data.
    _scan(_png_file(PRIVATE * (MAX_HEADER_SEGMENTS - 1), IDAT, images.PNG_IEND))
    _refused(
        _png_file(PRIVATE * MAX_HEADER_SEGMENTS, IDAT, images.PNG_IEND),
        SourceLimitError,
        "more than 1024 PNG chunks besides the image data",
    )


@pytest.mark.parametrize("where", ["before", "after"])
def test_png_chunk_flood_stops_early(where: str) -> None:
    flood = PRIVATE * 1_000_000  # 12 MB
    data = images.flat_png(
        (8, 4),
        COLOUR,
        before=flood if where == "before" else b"",
        after=flood if where == "after" else b"",
    )
    _refused(data, SourceLimitError, "more than 1024 PNG chunks")


def test_png_metadata_byte_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    text = images.png_chunk(b"tEXt", b"key\x00" + bytes(2_000))
    monkeypatch.setattr(source_scan, "MAX_HEADER_BYTES", 2_000)
    _refused(
        _png_file(IDAT, text, images.PNG_IEND),
        SourceLimitError,
        "PNG metadata exceeds 2000 bytes",
    )


def test_png_image_data_chunk_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = images.png_chunk(b"IDAT", b"")
    monkeypatch.setattr(source_scan, "MAX_PNG_DATA_CHUNKS", 10)
    _scan(_png_file(empty * 10, images.PNG_IEND))
    _refused(
        _png_file(empty * 11, images.PNG_IEND),
        SourceLimitError,
        "more than 10 PNG image data chunks",
    )


def test_animation_frames_count_as_image_data() -> None:
    # 600 frames (fcTL and fdAT each) are more chunks than the metadata limit.
    frame = images.png_chunk(b"fcTL", bytes(26)) + images.png_chunk(b"fdAT", bytes(4))
    actl = images.png_chunk(b"acTL", bytes(8))
    _scan(_png_file(actl, images.png_chunk(b"fcTL", bytes(26)), IDAT, frame * 600))


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (_png_file(images.png_chunk(b"ZZZZ", b"x"), IDAT), "unknown critical PNG chunk ZZZZ"),
        (_png_file(IDAT, images.png_chunk(b"CgBI", b"")), "unknown critical PNG chunk CgBI"),
        (_png_file(images.png_chunk(b"ab1d", b"")), "invalid PNG chunk type"),
        (_png_file(IDAT, images.png_chunk(b"te_t", b"")), "invalid PNG chunk type"),
        (images.png_truncated_chunk(), "a PNG chunk runs past the end of the file"),
        (_png_file(IDAT)[:-5], "a PNG chunk runs past the end of the file"),
        (images.PNG_SIGNATURE, "the PNG ends before its image data"),
        (_png_file(b"\x00\x00\x00"), "the PNG ends before its image data"),
        # A frame control chunk alone is not image data.
        (_png_file(images.png_chunk(b"fcTL", bytes(26))), "the PNG ends before its image data"),
    ],
    ids=[
        "critical-before-data",
        "critical-after-data",
        "digit-in-type",
        "underscore-in-type",
        "chunk-past-end",
        "data-past-end",
        "signature-only",
        "cut-header",
        "frame-control-only",
    ],
)
def test_malformed_png_structure(data: bytes, message: str) -> None:
    _refused(data, SourceStructureError, message)


@pytest.mark.parametrize(
    "data",
    [
        # Pillow stops reading at the end of the file after the image data.
        _png_file(IDAT),
        _png_file(IDAT, b"\x00\x00\x00"),
        # The walk ends at IEND, like Pillow's reader.
        _png_file(IDAT, images.PNG_IEND, PRIVATE * 2_000, b"trailing garbage"),
    ],
    ids=["no-iend", "partial-header-after-data", "after-iend"],
)
def test_png_ends_after_the_image_data(data: bytes) -> None:
    _scan(data)
