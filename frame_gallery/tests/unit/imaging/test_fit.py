"""Fit geometry tables (§11.2, D-005; acceptance D1, D2, D4, B6)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from frame_gallery.domain import CANVAS, Size
from frame_gallery.imaging.fit import contain_layout, cover_crop, scaled_source

SMALL = Size(16, 9)

CONTAIN_TABLE = [
    # (source, canvas, scaled, offset)
    (Size(3840, 2160), CANVAS, Size(3840, 2160), (0, 0)),
    (Size(1920, 1080), CANVAS, Size(3840, 2160), (0, 0)),
    (Size(7680, 4320), CANVAS, Size(3840, 2160), (0, 0)),
    (Size(1600, 1000), CANVAS, Size(3456, 2160), (192, 0)),
    (Size(4000, 1000), CANVAS, Size(3840, 960), (0, 600)),
    (Size(1000, 1000), CANVAS, Size(2160, 2160), (840, 0)),
    (Size(1000, 1600), CANVAS, Size(1350, 2160), (1245, 0)),
    # Round half up on the non-binding axis: 4001 / 2 = 2000.5 and 3001 / 2 = 1500.5.
    (Size(7680, 4001), CANVAS, Size(3840, 2001), (0, 79)),
    (Size(3001, 4320), CANVAS, Size(1501, 2160), (1169, 0)),
    # Extreme panoramas keep at least one pixel.
    (Size(100_000, 1), CANVAS, Size(3840, 1), (0, 1079)),
    (Size(1, 100_000), CANVAS, Size(1, 2160), (1919, 0)),
    (Size(1, 1), SMALL, Size(9, 9), (3, 0)),
    (Size(2, 1), SMALL, Size(16, 8), (0, 0)),
]

COVER_TABLE = [
    # (source, canvas, box)
    (Size(3840, 2160), CANVAS, (0, 0, 3840, 2160)),
    (Size(1920, 1080), CANVAS, (0, 0, 1920, 1080)),
    (Size(1600, 1000), CANVAS, (0, 50, 1600, 950)),
    (Size(4000, 1000), CANVAS, (1111, 0, 2889, 1000)),
    # 2160 * 1000 / 3840 = 562.5 rounds half up to 563.
    (Size(1000, 1600), CANVAS, (0, 518, 1000, 1081)),
    (Size(1, 100_000), CANVAS, (0, 49_999, 1, 50_000)),
    (Size(100_000, 1), CANVAS, (49_999, 0, 50_001, 1)),
    (Size(1, 1), SMALL, (0, 0, 1, 1)),
]


@pytest.mark.parametrize(("source", "canvas", "scaled", "offset"), CONTAIN_TABLE)
def test_contain_layout_table(
    source: Size, canvas: Size, scaled: Size, offset: tuple[int, int]
) -> None:
    layout = contain_layout(source, canvas)
    assert layout.scaled == scaled
    assert layout.offset == offset
    assert layout.scale == min(
        Fraction(canvas.width, source.width), Fraction(canvas.height, source.height)
    )


@pytest.mark.parametrize(("source", "canvas", "scaled", "offset"), CONTAIN_TABLE)
def test_contain_keeps_every_pixel_without_stretching(
    source: Size, canvas: Size, scaled: Size, offset: tuple[int, int]
) -> None:
    layout = contain_layout(source, canvas)
    width, height = layout.scaled.width, layout.scaled.height
    # D1/D2: the whole image fits, and it fills the canvas along one axis.
    assert width <= canvas.width
    assert height <= canvas.height
    assert width == canvas.width or height == canvas.height
    # Uniform scale: each side is the source side times s, rounded (or 1 px).
    for side, source_side in ((width, source.width), (height, source.height)):
        exact = source_side * layout.scale
        assert abs(side - exact) <= Fraction(1, 2) or side == 1
    # Centred: the margins differ by at most one pixel.
    x, y = layout.offset
    assert canvas.width - width - 2 * x in (0, 1)
    assert canvas.height - height - 2 * y in (0, 1)


@pytest.mark.parametrize(("source", "canvas", "box"), COVER_TABLE)
def test_cover_crop_table(source: Size, canvas: Size, box: tuple[int, int, int, int]) -> None:
    crop = cover_crop(source, canvas)
    assert crop.box == box
    assert crop.scale == max(
        Fraction(canvas.width, source.width), Fraction(canvas.height, source.height)
    )


@pytest.mark.parametrize(("source", "canvas", "box"), COVER_TABLE)
def test_cover_crops_only_the_overflowing_axis_centred(
    source: Size, canvas: Size, box: tuple[int, int, int, int]
) -> None:
    crop = cover_crop(source, canvas)
    left, top, right, bottom = crop.box
    kept_w, kept_h = right - left, bottom - top
    assert 0 <= left < right <= source.width
    assert 0 <= top < bottom <= source.height
    # D4: one axis is kept whole; the other is cropped symmetrically.
    width_whole = (left, right) == (0, source.width)
    height_whole = (top, bottom) == (0, source.height)
    assert width_whole or height_whole
    assert left == (source.width - kept_w) // 2
    assert top == (source.height - kept_h) // 2
    # The kept region scales onto the canvas uniformly (within rounding).
    assert abs(kept_w * crop.scale - canvas.width) <= crop.scale / 2 or kept_w == 1
    assert abs(kept_h * crop.scale - canvas.height) <= crop.scale / 2 or kept_h == 1


def test_cover_does_not_crop_an_exact_match() -> None:
    assert cover_crop(Size(1920, 1080), CANVAS).box == (0, 0, 1920, 1080)
    assert contain_layout(Size(1920, 1080), CANVAS).offset == (0, 0)


@pytest.mark.parametrize(
    ("source", "scale", "expected"),
    [
        (Size(1600, 1000), Fraction(12, 5), Size(3840, 2400)),
        (Size(1000, 1600), Fraction(96, 25), Size(3840, 6144)),
        (Size(3, 3), Fraction(1, 2), Size(2, 2)),
        (Size(4000, 1000), Fraction(54, 25), Size(8640, 2160)),
        (Size(10, 10), Fraction(1, 1000), Size(1, 1)),
    ],
)
def test_scaled_source_rounds_up(source: Size, scale: Fraction, expected: Size) -> None:
    assert scaled_source(source, scale) == expected
