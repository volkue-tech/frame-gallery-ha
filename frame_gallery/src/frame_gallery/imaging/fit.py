"""Fit geometry (§11.2, D-005): pure and standard library only.

Both fits scale uniformly, so an artwork is never stretched. All arithmetic is
exact: scale factors are fractions and every rounding is round-half-up on
integers, so a boundary case never depends on floating-point behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from frame_gallery.domain import Size


def _round_half_up(numerator: int, denominator: int) -> int:
    """``numerator / denominator`` rounded half up (both positive)."""
    return (2 * numerator + denominator) // (2 * denominator)


def _clamp(value: int, upper: int) -> int:
    return max(1, min(value, upper))


@dataclass(frozen=True, slots=True)
class ContainLayout:
    """Where a ``contain``-fitted image sits on the canvas."""

    scaled: Size
    """The scaled image: it fits the canvas and fills it along one axis."""

    offset: tuple[int, int]
    """The ``(x, y)`` of the scaled image's top-left corner on the canvas."""

    scale: Fraction


@dataclass(frozen=True, slots=True)
class CoverCrop:
    """The source region that a ``cover`` fit keeps."""

    box: tuple[int, int, int, int]
    """``(left, top, right, bottom)`` in source coordinates."""

    scale: Fraction


def contain_layout(source: Size, canvas: Size) -> ContainLayout:
    """Scale by ``s = min(W/w, H/h)`` and centre the result (default fit).

    Nothing is cropped: every source pixel is present in the scaled image,
    which matches the canvas exactly along the binding axis and fits within
    it along the other. The margins show the background colour (D-005).
    """
    if canvas.width * source.height <= canvas.height * source.width:
        # The width binds (W/w <= H/h): the image spans the canvas width.
        scale = Fraction(canvas.width, source.width)
        width = canvas.width
        height = _clamp(_round_half_up(source.height * canvas.width, source.width), canvas.height)
    else:
        scale = Fraction(canvas.height, source.height)
        height = canvas.height
        width = _clamp(_round_half_up(source.width * canvas.height, source.height), canvas.width)
    offset = ((canvas.width - width) // 2, (canvas.height - height) // 2)
    return ContainLayout(scaled=Size(width, height), offset=offset, scale=scale)


def cover_crop(source: Size, canvas: Size) -> CoverCrop:
    """Scale by ``s = max(W/w, H/h)`` and keep the centred region that fills
    the canvas (opt-in fit).

    Only the overflowing axis is cropped, and only by the overflow; the other
    axis is kept whole. The kept region has the canvas's aspect ratio within
    rounding (``canvas / s``, rounded) and never exceeds the source.
    """
    if canvas.width * source.height >= canvas.height * source.width:
        # The width binds (W/w >= H/h): the height overflows and is cropped.
        scale = Fraction(canvas.width, source.width)
        kept = _clamp(_round_half_up(canvas.height * source.width, canvas.width), source.height)
        top = (source.height - kept) // 2
        box = (0, top, source.width, top + kept)
    else:
        scale = Fraction(canvas.height, source.height)
        kept = _clamp(_round_half_up(canvas.width * source.height, canvas.height), source.width)
        left = (source.width - kept) // 2
        box = (left, 0, left + kept, source.height)
    return CoverCrop(box=box, scale=scale)


def scaled_source(source: Size, scale: Fraction) -> Size:
    """The whole ``source`` scaled by ``scale``, rounded up (at least 1 px).

    Used to request a JPEG draft reduction that never falls below what the
    fit needs (§11.1 step 3).
    """
    width = -((-source.width * scale.numerator) // scale.denominator)
    height = -((-source.height * scale.numerator) // scale.denominator)
    return Size(max(1, width), max(1, height))
