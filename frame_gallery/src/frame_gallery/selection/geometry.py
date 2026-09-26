"""Shape and quality classification (§8.1, D-116, accepted).

All tests use exact integer arithmetic, so boundary cases never depend on
floating-point rounding. Each rule states its equivalent closed form.

- portrait: ``r < 0.95``; square: ``0.95 <= r <= 1/0.95``; landscape: ``r > 1/0.95``
- near-16:9 (strict): ``abs(ln(r / (16/9))) <= ln(1.01)``, about 1.760-1.796
- too small: the fit mode's scale factor ``s`` onto the canvas exceeds 2.5

``r`` is width divided by height after EXIF orientation, measured on the
rendition that will be delivered.
"""

from __future__ import annotations

import enum
import math
from fractions import Fraction
from typing import Final

from frame_gallery.domain import CANVAS, FitMode, Size

SQUARE_LOWER: Final = Fraction(95, 100)
"""``0.95``: below this ratio a work is portrait."""

SQUARE_UPPER: Final = 1 / SQUARE_LOWER
"""``1/0.95``: above this ratio a work is landscape."""

TV_RATIO: Final = Fraction(16, 9)
STRICT_TOLERANCE: Final = Fraction(101, 100)
"""The strict band is ``[TV_RATIO / 1.01, TV_RATIO * 1.01]``, i.e. ``ln(1.01)``."""

MAX_UPSCALE: Final = Fraction(5, 2)
"""A work whose scale factor exceeds 2.5 is too small (quality rule)."""


class Shape(enum.StrEnum):
    PORTRAIT = "portrait"
    SQUARE = "square"
    LANDSCAPE = "landscape"


class Rejection(enum.StrEnum):
    """Why a rendition does not qualify."""

    TOO_SMALL = "too_small"
    NOT_LANDSCAPE = "not_landscape"
    NOT_NEAR_16_9 = "not_near_16_9"


def ratio(size: Size) -> Fraction:
    """The exact aspect ratio ``width / height``."""
    return Fraction(size.width, size.height)


def classify(size: Size) -> Shape:
    """Portrait, square, or landscape (square band 0.95 to 1/0.95 inclusive)."""
    r = ratio(size)
    if r < SQUARE_LOWER:
        return Shape.PORTRAIT
    if r > SQUARE_UPPER:
        return Shape.LANDSCAPE
    return Shape.SQUARE


def is_near_16_9(size: Size) -> bool:
    """``abs(ln(r / (16/9))) <= ln(1.01)``, evaluated exactly."""
    r = ratio(size)
    return TV_RATIO / STRICT_TOLERANCE <= r <= TV_RATIO * STRICT_TOLERANCE


def log_distance_to_16_9(size: Size) -> float:
    """``abs(ln(r / (16/9)))``: the fallback ranking key (smaller is better)."""
    return abs(math.log(ratio(size) / TV_RATIO))


def scale_factor(size: Size, fit_mode: FitMode, canvas: Size = CANVAS) -> Fraction:
    """The uniform scale factor that fits ``size`` onto ``canvas``.

    ``contain``: ``min(W/w, H/h)``; ``cover``: ``max(W/w, H/h)`` (§11.2).
    """
    horizontal = Fraction(canvas.width, size.width)
    vertical = Fraction(canvas.height, size.height)
    if fit_mode is FitMode.CONTAIN:
        return min(horizontal, vertical)
    return max(horizontal, vertical)


def is_too_small(size: Size, fit_mode: FitMode, canvas: Size = CANVAS) -> bool:
    """Whether the upscale factor exceeds :data:`MAX_UPSCALE`."""
    return scale_factor(size, fit_mode, canvas) > MAX_UPSCALE


def check_rendition(
    size: Size,
    *,
    fit_mode: FitMode,
    landscape_only: bool,
    require_near_16_9: bool,
    canvas: Size = CANVAS,
) -> Rejection | None:
    """The first rule ``size`` violates, or ``None`` if it qualifies.

    Selection uses this to evaluate candidates, and the prepare task uses it
    again on the real dimensions to verify the reason a candidate was chosen.
    """
    if is_too_small(size, fit_mode, canvas):
        return Rejection.TOO_SMALL
    if landscape_only and classify(size) is not Shape.LANDSCAPE:
        return Rejection.NOT_LANDSCAPE
    if require_near_16_9 and not is_near_16_9(size):
        return Rejection.NOT_NEAR_16_9
    return None
