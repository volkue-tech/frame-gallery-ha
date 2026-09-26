"""``prepare`` rejections and failures (§11.1, D-121, Q-05; acceptance D7)."""

from __future__ import annotations

import errno
import json
import os
import tracemalloc
from pathlib import Path
from typing import Any

import pytest
from PIL import Image, ImageFile

from frame_gallery.domain import CANVAS, FitMode, Size
from frame_gallery.imaging import worker_tasks
from frame_gallery.imaging.contract import (
    JPEG_FALLBACK_QUALITY,
    JPEG_QUALITY,
    MAX_JPEG_PIXELS,
    MAX_SOURCE_BYTES,
    ImageFormat,
    PrepareFailure,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.imaging.worker_tasks import prepare_image, prepare_task
from frame_gallery.selection.geometry import Rejection
from tests.support import images
from tests.unit.imaging.prepare_helpers import (
    SMALL,
    assert_failed,
    assert_ok,
    assert_tv_jpeg,
    request,
)

# --- D7: limits before decoding -------------------------------------------------
# The crafted files carry a header and no decodable pixels: a limits result
# proves the check ran before any decoding was attempted.


@pytest.mark.parametrize(
    ("name", "data", "declared"),
    [
        ("wide.png", images.png_header_only(20_001, 100), ImageFormat.PNG),
        ("tall.png", images.png_header_only(100, 20_001), ImageFormat.PNG),
        ("png-pixels.png", images.png_header_only(7_000, 7_000), ImageFormat.PNG),
        ("png-bomb.png", images.png_header_only(50_000, 50_000), ImageFormat.PNG),
        ("wide.jpg", images.jpeg_header_only(20_001, 100), ImageFormat.JPEG),
        ("jpeg-pixels.jpg", images.jpeg_header_only(9_000, 9_000), ImageFormat.JPEG),
        ("jpeg-bomb.jpg", images.jpeg_header_only(12_000, 12_000), ImageFormat.JPEG),
    ],
)
def test_limits_are_enforced_before_decoding(
    tmp_path: Path, name: str, data: bytes, declared: ImageFormat
) -> None:
    source = images.write_bytes(tmp_path / name, data)
    req = request(tmp_path, source, declared=declared)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.LIMITS, tmp_path, Path(req.output_path))
    assert result.source_size is None


@pytest.mark.parametrize(
    ("name", "data", "declared"),
    [
        ("side.png", images.png_header_only(20_000, 100), ImageFormat.PNG),
        ("area.png", images.png_header_only(8_000, 5_000), ImageFormat.PNG),
        ("side.jpg", images.jpeg_header_only(100, 20_000), ImageFormat.JPEG),
        ("area.jpg", images.jpeg_header_only(8_000, 8_000), ImageFormat.JPEG),
    ],
)
def test_limits_accept_the_boundaries(
    tmp_path: Path, name: str, data: bytes, declared: ImageFormat
) -> None:
    # 20 000 px per side, 40 MP for PNG, and 64 MP for JPEG pass the limits;
    # the header-only files then stop at verification, before decoding.
    source = images.write_bytes(tmp_path / name, data)
    req = request(tmp_path, source, declared=declared, require_near_16_9=True)
    result = prepare_image(req)
    assert result.status is PrepareStatus.REJECTED, result
    assert result.rejection in (Rejection.NOT_LANDSCAPE, Rejection.NOT_NEAR_16_9)


def test_png_pixel_limit_is_lower_than_the_jpeg_limit(tmp_path: Path) -> None:
    source = images.write_bytes(tmp_path / "s.png", images.png_header_only(8_000, 8_000))
    result = prepare_image(request(tmp_path, source, declared=ImageFormat.PNG))
    assert result.failure is PrepareFailure.LIMITS
    assert result.detail == "8000x8000 exceeds 40000000 pixels for PNG"


def test_pillow_pixel_limit_is_set_by_the_task(tmp_path: Path) -> None:
    Image.MAX_IMAGE_PIXELS = None  # restored by the autouse fixture
    source = images.write_bytes(tmp_path / "s.jpg", images.jpeg_header_only(9_000, 9_000))
    result = prepare_image(request(tmp_path, source))
    assert result.failure is PrepareFailure.LIMITS
    assert Image.MAX_IMAGE_PIXELS == MAX_JPEG_PIXELS


def test_oversized_source_file_is_refused(tmp_path: Path) -> None:
    source = tmp_path / "huge.jpg"
    with source.open("wb") as file:
        file.write(images.encoded_jpeg(Image.new("RGB", (8, 8))))
        file.truncate(MAX_SOURCE_BYTES + 1)  # sparse: nothing is allocated
    req = request(tmp_path, source)
    assert_failed(prepare_image(req), PrepareFailure.LIMITS, tmp_path, Path(req.output_path))


# --- header floods (L4-01): refused before Pillow parses the header ---------------
# Each flood is small and decodable once its extra segments or chunks are
# removed, and passes every dimension and pixel limit.

FLOOD = 2_000
"""Well over the 1 024 segments or chunks the pre-scan allows."""

FLOOD_SIZE = (320, 180)
"""Scaled by 1.2 onto the small canvas: acceptable apart from the flood."""


def _flood_request(tmp_path: Path, name: str, data: bytes) -> PrepareResult:
    declared = ImageFormat.PNG if name.endswith(".png") else ImageFormat.JPEG
    source = images.write_bytes(tmp_path / name, data)
    req = request(tmp_path, source, declared=declared, canvas=SMALL)
    result = prepare_image(req)
    if result.status is PrepareStatus.FAILED:
        assert not Path(req.output_path).exists()
    return result


def test_jpeg_segment_flood_is_refused(tmp_path: Path) -> None:
    base = images.encoded_jpeg(Image.new("RGB", FLOOD_SIZE, (200, 120, 40)))
    flood = images.jpeg_segment(0xEF, b"") * FLOOD
    result = _flood_request(tmp_path, "flood.jpg", images.with_segments(base, flood))
    assert_failed(result, PrepareFailure.LIMITS, tmp_path)
    assert result.detail == "more than 1024 segments before the start of scan"
    assert result.source_size is None  # Pillow never parsed the header


@pytest.mark.parametrize("where", ["before", "after"])
def test_png_chunk_flood_is_refused(tmp_path: Path, where: str) -> None:
    # Pillow parses the chunks after the image data while decoding, so a
    # flood there is refused as well.
    flood = images.png_chunk(b"prVt", b"") * FLOOD
    data = images.flat_png(
        FLOOD_SIZE,
        (200, 120, 40),
        before=flood if where == "before" else b"",
        after=flood if where == "after" else b"",
    )
    result = _flood_request(tmp_path, f"flood-{where}.png", data)
    assert_failed(result, PrepareFailure.LIMITS, tmp_path)
    assert result.detail == "more than 1024 PNG chunks besides the image data"
    assert result.source_size is None


def test_unknown_critical_png_chunk_is_a_decode_failure(tmp_path: Path) -> None:
    data = images.flat_png(FLOOD_SIZE, (200, 120, 40), before=images.png_chunk(b"ZZZZ", b"x"))
    result = _flood_request(tmp_path, "critical.png", data)
    assert_failed(result, PrepareFailure.DECODE, tmp_path)
    assert result.detail == "unknown critical PNG chunk ZZZZ"


def test_many_jpeg_segments_within_the_limits_are_accepted(tmp_path: Path) -> None:
    # EXIF, an ICC profile, and 1 000 comment segments: under the limits.
    exif = Image.Exif()
    exif[0x0112] = 1
    base = images.encoded_jpeg(
        Image.new("RGB", FLOOD_SIZE, (200, 120, 40)),
        exif=exif.tobytes(),
        icc_profile=images.srgb_icc(),
    )
    comments = images.jpeg_segment(0xFE, b"note") * 1_000
    result = _flood_request(tmp_path, "many.jpg", images.with_segments(base, comments))
    assert result.status is PrepareStatus.OK, result


def test_many_png_chunks_within_the_limits_are_accepted(tmp_path: Path) -> None:
    text = images.png_chunk(b"tEXt", b"Comment\x00note")
    data = images.flat_png(FLOOD_SIZE, (200, 120, 40), before=text * 500, after=text * 500)
    result = _flood_request(tmp_path, "many.png", data)
    assert result.status is PrepareStatus.OK, result


# --- metadata TIFF bombs (P1): refused before Pillow parses the metadata ----------
# Each bomb is under 1 MiB, and its image decodable. Pillow would copy or
# decode the shared value once per entry: 50 to 200 MiB. A limits result
# without a source size shows that Pillow never opened the file.

MIB = 1024 * 1024
METADATA_ALLOCATION_BOUND = 8 * MIB
VALUES_OVER = "metadata values exceed 1048576 bytes"


def _metadata_bomb(name: str) -> bytes:
    colour = (200, 120, 40)
    jpeg = images.encoded_jpeg(Image.new("RGB", FLOOD_SIZE, colour))
    shared = images.tiff_bomb(200, 960 * 1024, filler=960 * 1024 + 1)
    if name == "exif.jpg":
        return images.with_segments(jpeg, images.exif_segments(shared))
    if name == "mpf.jpg":
        return images.with_segments(jpeg, images.mpf_segment(images.mpf_value_bomb(300)))
    if name == "exif.png":
        return images.flat_png(FLOOD_SIZE, colour, before=images.png_chunk(b"eXIf", shared))
    quarter = images.tiff_bomb(200, MIB // 4, filler=MIB // 4 + 1)
    chunk = images.raw_profile_chunk(b"zTXt", images.raw_profile_text(quarter))
    return images.flat_png(FLOOD_SIZE, colour, before=chunk)


@pytest.mark.parametrize("name", ["exif.jpg", "mpf.jpg", "exif.png", "raw-profile.png"])
def test_metadata_bombs_are_refused_before_pillow_parses_them(tmp_path: Path, name: str) -> None:
    data = _metadata_bomb(name)
    tracemalloc.start()
    try:
        result = _flood_request(tmp_path, name, data)
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert_failed(result, PrepareFailure.LIMITS, tmp_path)
    assert result.detail == VALUES_OVER
    assert result.source_size is None
    assert peak < METADATA_ALLOCATION_BOUND, peak


def test_bigtiff_metadata_is_a_decode_failure(tmp_path: Path) -> None:
    before = images.png_chunk(b"eXIf", b"II+\x00" + bytes(12))
    data = images.flat_png(FLOOD_SIZE, (200, 120, 40), before=before)
    result = _flood_request(tmp_path, "bigtiff.png", data)
    assert_failed(result, PrepareFailure.DECODE, tmp_path)
    assert result.detail == "BigTIFF metadata is not supported"


def test_source_read_errors_are_decode_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_scan(file: object) -> None:
        raise OSError(errno.EIO, "Input/output error")

    monkeypatch.setattr(worker_tasks, "scan_source", failing_scan)
    req = request(tmp_path, images.save_jpeg(images.marked(FLOOD_SIZE), tmp_path / "s.jpg"))
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.DECODE, tmp_path, Path(req.output_path))
    assert result.detail == "OSError: [Errno 5] Input/output error"


# --- verification of the choice (before decoding) --------------------------------


def test_portrait_is_rejected_when_landscape_only(tmp_path: Path) -> None:
    # Header only: verification must not need the pixels.
    source = images.write_bytes(tmp_path / "p.jpg", images.jpeg_header_only(1200, 2000))
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert result.status is PrepareStatus.REJECTED
    assert result.rejection is Rejection.NOT_LANDSCAPE
    assert result.source_size == Size(1200, 2000)
    assert result.oriented_size == Size(1200, 2000)
    assert result.orientation == 1
    assert not Path(req.output_path).exists()


def test_png_is_verified_without_decoding(tmp_path: Path) -> None:
    # PNG's own EXIF reader would decode the (empty) image data first.
    source = images.write_bytes(tmp_path / "p.png", images.png_header_only(1200, 2000))
    result = prepare_image(request(tmp_path, source, declared=ImageFormat.PNG))
    assert result.status is PrepareStatus.REJECTED
    assert result.rejection is Rejection.NOT_LANDSCAPE
    assert result.orientation == 1


def test_orientation_can_turn_a_landscape_file_into_a_portrait(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1600, 1000)), tmp_path / "s.jpg", orientation=6)
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert result.status is PrepareStatus.REJECTED
    assert result.rejection is Rejection.NOT_LANDSCAPE
    assert result.source_size == Size(1600, 1000)
    assert result.oriented_size == Size(1000, 1600)
    assert result.orientation == 6


def test_portrait_is_accepted_when_landscape_only_is_off(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1000, 1600)), tmp_path / "p.jpg")
    req = request(tmp_path, source, landscape_only=False)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert_tv_jpeg(Path(req.output_path), CANVAS)


def test_not_near_16_9_is_rejected_when_strict(tmp_path: Path) -> None:
    source = images.write_bytes(tmp_path / "s.jpg", images.jpeg_header_only(1600, 1200))
    result = prepare_image(request(tmp_path, source, require_near_16_9=True))
    assert result.status is PrepareStatus.REJECTED
    assert result.rejection is Rejection.NOT_NEAR_16_9


def test_too_small_is_rejected(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((320, 180)), tmp_path / "s.jpg")
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert result.status is PrepareStatus.REJECTED
    assert result.rejection is Rejection.TOO_SMALL
    assert result.detail == "oriented size 320x180"
    assert not Path(req.output_path).exists()


def test_too_small_depends_on_the_fit_mode(tmp_path: Path) -> None:
    # 4000 x 800: contain scales by 0.96, cover by 2.7 (> 2.5).
    source = images.write_bytes(tmp_path / "s.jpg", images.jpeg_header_only(4000, 800))
    result = prepare_image(request(tmp_path, source, fit_mode=FitMode.COVER))
    assert result.rejection is Rejection.TOO_SMALL


# --- format ---------------------------------------------------------------------


def test_png_declared_as_jpeg_is_a_mismatch(tmp_path: Path) -> None:
    source = images.save_png(images.marked((320, 180)), tmp_path / "fake.jpg")
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.FORMAT_MISMATCH, tmp_path, Path(req.output_path))
    assert result.detail == "declared JPEG, found PNG"


def test_jpeg_declared_as_png_is_a_mismatch(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((320, 180)), tmp_path / "fake.png")
    req = request(tmp_path, source, declared=ImageFormat.PNG, canvas=SMALL)
    assert_failed(prepare_image(req), PrepareFailure.FORMAT_MISMATCH, tmp_path)


@pytest.mark.parametrize(
    "data",
    [b"", b"not an image at all", b"GIF89a\x01\x00\x01\x00\x00\x00\x00;"],
)
def test_unidentifiable_files_are_a_mismatch(tmp_path: Path, data: bytes) -> None:
    source = images.write_bytes(tmp_path / "s.jpg", data)
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.FORMAT_MISMATCH, tmp_path, Path(req.output_path))
    assert result.detail == "not a readable JPEG file"


def test_truncated_jpeg_header_is_a_decode_failure(tmp_path: Path) -> None:
    # The JPEG magic bytes and nothing else: a truncated header, which the
    # module's mapping reports as ``decode`` (the pre-scan finds it before
    # Pillow, whose own reader turned it into "unidentified").
    source = images.write_bytes(tmp_path / "s.jpg", b"\xff\xd8\xff")
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.DECODE, tmp_path, Path(req.output_path))
    assert result.detail == "truncated inside a marker"


def test_gif_is_never_opened(tmp_path: Path) -> None:
    source = tmp_path / "s.gif"
    Image.new("P", (32, 18)).save(source, "GIF")
    result = prepare_image(request(tmp_path, source, declared=ImageFormat.PNG))
    assert result.failure is PrepareFailure.FORMAT_MISMATCH


# --- decode ---------------------------------------------------------------------


def test_truncated_jpeg_fails_to_decode(tmp_path: Path) -> None:
    data = images.encoded_jpeg(images.marked((320, 180)), quality=95)
    source = images.write_bytes(tmp_path / "s.jpg", data[: len(data) // 2])
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.DECODE, tmp_path, Path(req.output_path))
    assert result.detail is not None
    assert result.detail.startswith("OSError: ")
    # What was learned from the header is reported with the failure.
    assert result.source_size == Size(320, 180)
    assert result.oriented_size == Size(320, 180)
    assert result.orientation == 1


def test_truncated_png_chunk_fails_while_opening(tmp_path: Path) -> None:
    source = images.write_bytes(tmp_path / "s.png", images.png_truncated_chunk())
    req = request(tmp_path, source, declared=ImageFormat.PNG)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.DECODE, tmp_path, Path(req.output_path))
    assert result.source_size is None


def test_zero_dimension_is_a_decode_failure() -> None:
    with pytest.raises(worker_tasks._Failed) as caught:
        worker_tasks._check_limits(Image.new("RGB", (0, 5)), ImageFormat.PNG)
    assert caught.value.failure is PrepareFailure.DECODE


# --- source and output files -----------------------------------------------------


def test_missing_source(tmp_path: Path) -> None:
    req = request(tmp_path, tmp_path / "missing.jpg")
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.IO, tmp_path, Path(req.output_path))
    assert result.detail == "cannot open the source (ENOENT)"


def test_source_symlink_is_not_followed(tmp_path: Path) -> None:
    target = images.save_jpeg(images.marked((1600, 1000)), tmp_path / "real.jpg")
    link = tmp_path / "link.jpg"
    link.symlink_to(target)
    req = request(tmp_path, link)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.IO, tmp_path, Path(req.output_path))
    assert result.detail == "cannot open the source (ELOOP)"


def test_source_must_be_a_regular_file(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    for source in (fifo, tmp_path):
        req = request(tmp_path, source)
        result = prepare_image(req)
        assert_failed(result, PrepareFailure.IO, tmp_path, Path(req.output_path))
        assert result.detail == "the source is not a regular file"


def _small_source(tmp_path: Path) -> Path:
    return images.save_jpeg(images.marked((320, 180)), tmp_path / "source.jpg")


def test_existing_output_is_never_overwritten(tmp_path: Path) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    output = Path(req.output_path)
    output.write_bytes(b"precious")
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.IO, tmp_path)
    assert result.detail == "cannot create the output (EEXIST)"
    assert output.read_bytes() == b"precious"


def test_output_symlink_is_never_followed(tmp_path: Path) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    target = tmp_path / "target.jpg"
    Path(req.output_path).symlink_to(target)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.IO, tmp_path)
    assert not target.exists()


def test_output_directory_must_exist(tmp_path: Path) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL, output="missing/delivery.jpg")
    assert_failed(prepare_image(req), PrepareFailure.IO, tmp_path)


def test_output_permissions(tmp_path: Path) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    previous = os.umask(0)
    try:
        assert_ok(prepare_image(req), Path(req.output_path))
    finally:
        os.umask(previous)
    assert Path(req.output_path).stat().st_mode & 0o777 == 0o640


def test_failed_write_removes_the_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    original_fdopen = os.fdopen

    class _FullDisk:
        def __init__(self, fd: int) -> None:
            self._file = original_fdopen(fd, "wb")

        def __enter__(self) -> _FullDisk:
            return self

        def __exit__(self, *exc: object) -> None:
            self._file.close()

        def write(self, data: bytes) -> int:
            self._file.write(data[:10])
            raise OSError(errno.ENOSPC, "No space left on device")

    def fdopen(fd: int, mode: str = "r", *args: object, **kwargs: object) -> object:
        if mode == "wb":
            return _FullDisk(fd)
        return original_fdopen(fd, mode, *args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(os, "fdopen", fdopen)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.IO, tmp_path, Path(req.output_path))
    assert result.detail == "cannot write the output (ENOSPC)"


# --- render and encode failures ---------------------------------------------------


def test_resize_errors_are_render_failures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_resize(self: Image.Image, *args: object, **kwargs: object) -> Image.Image:
        raise ValueError("resize failed")

    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    monkeypatch.setattr(Image.Image, "resize", broken_resize)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.RENDER, tmp_path, Path(req.output_path))
    assert result.detail == "ValueError: resize failed"


def test_compose_errors_are_render_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_paste(self: Image.Image, *args: object, **kwargs: object) -> None:
        raise OSError("paste\nfailed " + "x" * 300)

    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    monkeypatch.setattr(Image.Image, "paste", broken_paste)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.RENDER, tmp_path, Path(req.output_path))
    assert result.detail is not None
    assert "\n" not in result.detail
    assert len(result.detail) == 120


def test_orientation_errors_are_render_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_transpose(self: Image.Image, method: Image.Transpose) -> Image.Image:
        raise ValueError("transpose failed")

    source = images.oriented_jpeg(tmp_path, 6, (320, 180))
    req = request(tmp_path, source, canvas=SMALL)
    monkeypatch.setattr(Image.Image, "transpose", broken_transpose)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.RENDER, tmp_path, Path(req.output_path))
    assert result.orientation == 6


def test_encoder_errors_are_encode_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_save(self: Image.Image, *args: object, **kwargs: object) -> None:
        raise OSError("encoder error -2")

    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    monkeypatch.setattr(Image.Image, "save", broken_save)
    result = prepare_image(req)
    assert_failed(result, PrepareFailure.ENCODE, tmp_path, Path(req.output_path))


def test_the_decoded_source_is_released_before_encoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    events: list[str] = []
    original_close = ImageFile.ImageFile.close
    original_save = Image.Image.save

    def close(self: ImageFile.ImageFile) -> None:
        events.append("close")
        original_close(self)

    def save(self: Image.Image, *args: Any, **kwargs: Any) -> None:
        events.append("save")
        original_save(self, *args, **kwargs)

    monkeypatch.setattr(ImageFile.ImageFile, "close", close)
    monkeypatch.setattr(Image.Image, "save", save)
    assert_ok(prepare_image(req), Path(req.output_path))
    assert events == ["close", "save"]


# --- Q-05: the single re-encode at quality 85 --------------------------------------


def test_encode_fallback_and_output_too_large(tmp_path: Path) -> None:
    source = _small_source(tmp_path)

    def run(name: str, limit: int) -> PrepareResult:
        return prepare_image(
            request(tmp_path, source, canvas=SMALL, output=name), max_output_bytes=limit
        )

    first = run("q90.jpg", 10**9)
    assert first.jpeg_quality == JPEG_QUALITY
    assert first.output_bytes is not None
    at_90 = first.output_bytes

    exact = run("q90-exact.jpg", at_90)
    assert exact.jpeg_quality == JPEG_QUALITY  # the limit is inclusive

    fallback = run("q85.jpg", at_90 - 1)
    assert_ok(fallback, tmp_path / "q85.jpg")
    assert fallback.jpeg_quality == JPEG_FALLBACK_QUALITY
    assert fallback.output_bytes is not None
    at_85 = fallback.output_bytes
    assert at_85 < at_90
    assert_tv_jpeg(tmp_path / "q85.jpg", SMALL)

    exact_85 = run("q85-exact.jpg", at_85)
    assert exact_85.jpeg_quality == JPEG_FALLBACK_QUALITY

    too_large = run("none.jpg", at_85 - 1)
    assert_failed(too_large, PrepareFailure.OUTPUT_TOO_LARGE, tmp_path, tmp_path / "none.jpg")
    assert too_large.source_size == Size(320, 180)


# --- the task at the executor seam --------------------------------------------------


def test_prepare_task_speaks_json(tmp_path: Path) -> None:
    req = request(tmp_path, _small_source(tmp_path), canvas=SMALL)
    payload = json.loads(json.dumps(req.to_json()))
    raw = prepare_task(payload)
    result = PrepareResult.from_json(json.loads(json.dumps(raw)))
    assert result.status is PrepareStatus.OK
    assert result.output_bytes == Path(req.output_path).stat().st_size


def test_prepare_task_reports_failures_as_results(tmp_path: Path) -> None:
    req = request(tmp_path, tmp_path / "missing.jpg")
    result = PrepareResult.from_json(prepare_task(req.to_json()))
    assert result.failure is PrepareFailure.IO


def test_prepare_task_rejects_an_invalid_request(tmp_path: Path) -> None:
    payload = request(tmp_path, _small_source(tmp_path)).to_json()
    del payload["fit_mode"]
    with pytest.raises(ValueError, match="fit_mode"):
        prepare_task(payload)
