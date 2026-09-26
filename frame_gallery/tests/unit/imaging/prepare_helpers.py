"""Shared helpers for the ``prepare`` tests."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageStat

from frame_gallery.domain import BLACK, CANVAS, FitMode, Rgb, Size
from frame_gallery.imaging.contract import (
    ImageFormat,
    PrepareFailure,
    PrepareRequest,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.imaging.jpeg_header import APP0, SOF_BASELINE, parse_jpeg

SMALL = Size(384, 216)
"""A small canvas: the pipeline is the same, and the tests stay fast."""

ALLOWED_MARKERS = frozenset({APP0, SOF_BASELINE, 0xDB, 0xC4})
"""APP0 (JFIF), DQT, SOF0, and DHT: no EXIF, ICC, comment, or other APPn."""

Colour = tuple[int, int, int]


def request(
    tmp_path: Path,
    source: Path,
    *,
    declared: ImageFormat = ImageFormat.JPEG,
    fit_mode: FitMode = FitMode.CONTAIN,
    background: Rgb = BLACK,
    landscape_only: bool = True,
    require_near_16_9: bool = False,
    canvas: Size = CANVAS,
    output: str = "delivery.jpg",
) -> PrepareRequest:
    return PrepareRequest(
        source_path=str(source),
        output_path=str(tmp_path / output),
        declared_format=declared,
        fit_mode=fit_mode,
        background=background,
        landscape_only=landscape_only,
        require_near_16_9=require_near_16_9,
        canvas=canvas,
    )


def assert_tv_jpeg(path: Path, canvas: Size) -> None:
    """A baseline, 8-bit, three-component JPEG of exactly ``canvas`` with no
    metadata segments (D1, D6)."""
    info = parse_jpeg(path.read_bytes())
    assert info.is_baseline
    assert info.precision == 8
    assert info.components == 3
    assert info.size == canvas
    assert set(info.markers) <= ALLOWED_MARKERS, [hex(m) for m in info.markers]
    with Image.open(path) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"
        assert image.size == (canvas.width, canvas.height)
        assert "exif" not in image.info
        assert "icc_profile" not in image.info


def assert_ok(result: PrepareResult, path: Path) -> None:
    assert result.status is PrepareStatus.OK, result
    assert result.output_bytes == path.stat().st_size


def assert_failed(
    result: PrepareResult, failure: PrepareFailure, tmp_path: Path, output: Path | None = None
) -> None:
    """A ``failed`` result with a short, log-safe detail and no output file."""
    assert result.status is PrepareStatus.FAILED, result
    assert result.failure is failure, result
    assert result.detail
    assert len(result.detail) <= 130
    assert str(tmp_path) not in result.detail
    if output is not None:
        assert not output.exists()


def mean(image: Image.Image, centre: tuple[int, int], radius: int = 4) -> Colour:
    """The mean colour of a small square around ``centre``."""
    x, y = centre
    box = (x - radius, y - radius, x + radius + 1, y + radius + 1)
    red, green, blue = ImageStat.Stat(image.crop(box)).mean[:3]
    return round(red), round(green), round(blue)


def near(actual: Colour, expected: Colour, tolerance: int = 12) -> bool:
    return all(abs(a - e) <= tolerance for a, e in zip(actual, expected, strict=True))


def output_image(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.copy()


def extrema_max(image: Image.Image, box: tuple[int, int, int, int]) -> int:
    """The largest channel value inside ``box``."""
    bands = image.crop(box).getextrema()
    return max(high for _, high in bands)  # type: ignore[misc]
