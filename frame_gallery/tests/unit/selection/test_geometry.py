"""Shape and quality classification (§8.1, D-116) on the 3840 x 2160 canvas."""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from frame_gallery.domain import CANVAS, FitMode, Size
from frame_gallery.selection.geometry import (
    MAX_UPSCALE,
    SQUARE_LOWER,
    SQUARE_UPPER,
    STRICT_TOLERANCE,
    TV_RATIO,
    Rejection,
    Shape,
    check_rendition,
    classify,
    is_near_16_9,
    is_too_small,
    log_distance_to_16_9,
    ratio,
    scale_factor,
)

STRICT_LOWER = Fraction(1600, 909)
"""``(16/9) / 1.01`` as an exact fraction."""

STRICT_UPPER = Fraction(404, 225)
"""``(16/9) * 1.01`` as an exact fraction."""


def _near_by_integers(width: int, height: int) -> bool:
    """``1600/909 <= w/h <= 1616/900`` by cross-multiplication (independent oracle)."""
    return 1600 * height <= 909 * width and 900 * width <= 1616 * height


def _band_edges(height: int) -> tuple[int, int] | None:
    """The narrowest and widest near-16:9 widths at ``height``, found by search.

    ``None`` if the band is empty or not contiguous at this height.
    """
    widths = [
        width
        for width in range(int(height * 1.7), int(height * 1.85) + 1)
        if is_near_16_9(Size(width, height))
    ]
    if not widths or widths != list(range(widths[0], widths[-1] + 1)):
        return None
    return widths[0], widths[-1]


def test_canvas_is_3840_by_2160() -> None:
    assert Size(3840, 2160) == CANVAS
    assert ratio(CANVAS) == TV_RATIO == Fraction(16, 9)


def test_threshold_constants_are_exact() -> None:
    assert Fraction(19, 20) == SQUARE_LOWER
    assert Fraction(20, 19) == SQUARE_UPPER
    assert Fraction(101, 100) == STRICT_TOLERANCE
    assert TV_RATIO / STRICT_TOLERANCE == STRICT_LOWER
    assert TV_RATIO * STRICT_TOLERANCE == STRICT_UPPER
    assert Fraction(5, 2) == MAX_UPSCALE


def test_ratio_is_an_exact_fraction() -> None:
    assert ratio(Size(3000, 1500)) == Fraction(2)
    assert ratio(Size(20, 19)) == SQUARE_UPPER


@pytest.mark.parametrize(
    ("width", "height", "shape"),
    [
        (94, 100, Shape.PORTRAIT),
        (949, 1000, Shape.PORTRAIT),
        (95, 100, Shape.SQUARE),
        (950, 1000, Shape.SQUARE),
        (100, 100, Shape.SQUARE),
        (20, 19, Shape.SQUARE),
        (100, 95, Shape.SQUARE),
        (1999, 1900, Shape.SQUARE),
        (2001, 1900, Shape.LANDSCAPE),
        (21, 19, Shape.LANDSCAPE),
        (16, 9, Shape.LANDSCAPE),
        (9, 16, Shape.PORTRAIT),
    ],
)
def test_classify_boundaries(width: int, height: int, shape: Shape) -> None:
    assert classify(Size(width, height)) is shape


@pytest.mark.parametrize(
    ("width", "height", "near"),
    [
        (3840, 2160, True),
        (16, 9, True),
        (1600, 909, True),
        (3200, 1818, True),
        (1599, 909, False),
        (1616, 900, True),
        (404, 225, True),
        (1617, 900, False),
        (405, 225, False),
        (3000, 1500, False),
        (2160, 3840, False),
    ],
)
def test_is_near_16_9_exact_boundaries(width: int, height: int, near: bool) -> None:
    assert is_near_16_9(Size(width, height)) is near


def test_is_near_16_9_band_edges_match_the_integer_oracle() -> None:
    wrong: list[int] = []
    for height in range(100, 1200):
        edges = _band_edges(height)
        if edges is None:
            wrong.append(height)
            continue
        lowest, highest = edges
        # The search's edges are exactly where the integer oracle flips.
        if not (
            _near_by_integers(lowest, height)
            and not _near_by_integers(lowest - 1, height)
            and _near_by_integers(highest, height)
            and not _near_by_integers(highest + 1, height)
        ):
            wrong.append(height)
    assert wrong == []


def test_is_near_16_9_edges_at_2160() -> None:
    assert _band_edges(2160) == (3802, 3878)
    assert not is_near_16_9(Size(3801, 2160))
    assert not is_near_16_9(Size(3879, 2160))


def test_is_near_16_9_agrees_with_the_logarithmic_formula() -> None:
    threshold = math.log(1.01)
    target = 16 / 9
    mismatches: list[tuple[int, int]] = []
    on_threshold: list[tuple[int, int]] = []
    near_count = 0
    for width in range(1000, 2001):
        for height in range(560, 1131):
            distance = abs(math.log((width / height) / target))
            if abs(distance - threshold) < 1e-12:
                on_threshold.append((width, height))
                continue
            near = is_near_16_9(Size(width, height))
            near_count += near
            if near is not (distance <= threshold):
                mismatches.append((width, height))
    assert mismatches == []
    assert near_count > 1000
    # Only exact boundary ratios are too close to the threshold for floats.
    assert on_threshold
    assert all(
        1600 * height == 909 * width or 900 * width == 1616 * height
        for width, height in on_threshold
    )
    assert all(is_near_16_9(Size(width, height)) for width, height in on_threshold)


def test_log_distance_to_16_9() -> None:
    assert log_distance_to_16_9(Size(3840, 2160)) == 0.0
    assert log_distance_to_16_9(Size(32, 9)) == pytest.approx(math.log(2))
    assert log_distance_to_16_9(Size(8, 9)) == pytest.approx(math.log(2))
    assert log_distance_to_16_9(Size(2400, 1500)) < log_distance_to_16_9(Size(3000, 1500))


@pytest.mark.parametrize(
    ("width", "height", "contain", "cover"),
    [
        (3840, 2160, Fraction(1), Fraction(1)),
        (1920, 1080, Fraction(2), Fraction(2)),
        (7680, 4320, Fraction(1, 2), Fraction(1, 2)),
        (1536, 500, Fraction(5, 2), Fraction(108, 25)),
        (1000, 1000, Fraction(54, 25), Fraction(96, 25)),
        (800, 864, Fraction(5, 2), Fraction(24, 5)),
    ],
)
def test_scale_factor_contain_and_cover(
    width: int, height: int, contain: Fraction, cover: Fraction
) -> None:
    size = Size(width, height)
    assert scale_factor(size, FitMode.CONTAIN) == contain
    assert scale_factor(size, FitMode.COVER) == cover


def test_scale_factor_uses_the_given_canvas() -> None:
    assert scale_factor(Size(960, 540), FitMode.CONTAIN, Size(1920, 1080)) == 2
    assert scale_factor(Size(960, 270), FitMode.COVER, Size(1920, 1080)) == 4


@pytest.mark.parametrize(
    ("width", "height", "fit_mode", "too_small"),
    [
        # A wide work limited by its width: exactly 2.5 is still acceptable.
        (1536, 500, FitMode.CONTAIN, False),
        (1535, 500, FitMode.CONTAIN, True),
        # A narrow work limited by its height.
        (800, 864, FitMode.CONTAIN, False),
        (800, 863, FitMode.CONTAIN, True),
        # Cover uses the larger factor, so the same wide work is too small.
        (1536, 500, FitMode.COVER, True),
        (4000, 864, FitMode.COVER, False),
        (4000, 863, FitMode.COVER, True),
        # The Art Institute's 1686 px rendition at 16:9 is upscaled about 2.28x.
        (1686, 948, FitMode.CONTAIN, False),
        (1686, 948, FitMode.COVER, False),
        (640, 360, FitMode.CONTAIN, True),
    ],
)
def test_is_too_small_at_the_2_5_boundary(
    width: int, height: int, fit_mode: FitMode, too_small: bool
) -> None:
    assert is_too_small(Size(width, height), fit_mode) is too_small


def test_is_too_small_uses_the_given_canvas() -> None:
    assert is_too_small(Size(640, 360), FitMode.CONTAIN)
    assert not is_too_small(Size(640, 360), FitMode.CONTAIN, Size(1280, 720))


@pytest.mark.parametrize(
    ("width", "height", "landscape_only", "require_near", "expected"),
    [
        # Too small is checked first, even for a portrait, non-16:9 work.
        (100, 200, True, True, Rejection.TOO_SMALL),
        (640, 360, False, False, Rejection.TOO_SMALL),
        # Then the shape, before the strict band.
        (2000, 4000, True, True, Rejection.NOT_LANDSCAPE),
        (3000, 3000, True, True, Rejection.NOT_LANDSCAPE),
        (3000, 3000, True, False, Rejection.NOT_LANDSCAPE),
        (2000, 4000, False, True, Rejection.NOT_NEAR_16_9),
        (3000, 1500, True, True, Rejection.NOT_NEAR_16_9),
        # Qualifying renditions.
        (2000, 4000, False, False, None),
        (3000, 1500, True, False, None),
        (3840, 2160, True, True, None),
        (1616, 900, True, True, None),
    ],
)
def test_check_rendition_order_of_rejections(
    width: int,
    height: int,
    landscape_only: bool,
    require_near: bool,
    expected: Rejection | None,
) -> None:
    rejection = check_rendition(
        Size(width, height),
        fit_mode=FitMode.CONTAIN,
        landscape_only=landscape_only,
        require_near_16_9=require_near,
    )
    assert rejection is expected


def _check(size: Size, fit_mode: FitMode, canvas: Size = CANVAS) -> Rejection | None:
    return check_rendition(
        size, fit_mode=fit_mode, landscape_only=True, require_near_16_9=False, canvas=canvas
    )


def test_check_rendition_respects_fit_mode_and_canvas() -> None:
    wide = Size(1600, 500)
    assert _check(wide, FitMode.CONTAIN) is None
    assert _check(wide, FitMode.COVER) is Rejection.TOO_SMALL
    small = Size(640, 360)
    assert _check(small, FitMode.CONTAIN) is Rejection.TOO_SMALL
    assert _check(small, FitMode.CONTAIN, Size(1280, 720)) is None
