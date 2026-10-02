"""Draw the app's icon and logo (ARCHITECTURE.md §17.4; Phase 6).

Both images are original and purely geometric: a gilded picture frame
around a small landscape with a sun and two hills. They use no font, no
trademark, and nothing from another project. A test redraws them and
compares the pixels with the committed files.

    .venv/bin/python scripts/app_images.py   # writes icon.png and logo.png
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from PIL import Image, ImageDraw

PROJECT: Final = Path(__file__).resolve().parents[1]
ICON: Final = PROJECT / "icon.png"
LOGO: Final = PROJECT / "logo.png"

WALL: Final = (31, 41, 51)
FRAME: Final = (200, 162, 74)
FRAME_SHADE: Final = (150, 118, 48)
SKY: Final = (127, 179, 213)
SUN: Final = (244, 211, 94)
FAR_HILL: Final = (110, 160, 112)
NEAR_HILL: Final = (78, 143, 90)

type Box = tuple[int, int, int, int]


def _framed_landscape(draw: ImageDraw.ImageDraw, box: Box, border: int) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, fill=FRAME_SHADE)
    draw.rectangle((left + 2, top + 2, right - 2, bottom - 2), fill=FRAME)
    inner = (left + border, top + border, right - border, bottom - border)
    draw.rectangle(inner, fill=SKY)
    x0, y0, x1, y1 = inner
    width, height = x1 - x0, y1 - y0
    radius = max(2, height // 7)
    sun_x, sun_y = x0 + width * 7 // 10, y0 + height * 3 // 10
    draw.ellipse((sun_x - radius, sun_y - radius, sun_x + radius, sun_y + radius), fill=SUN)
    draw.polygon(
        [
            (x0, y1),
            (x0, y0 + height * 6 // 10),
            (x0 + width * 4 // 10, y0 + height * 4 // 10),
            (x0 + width * 8 // 10, y1),
        ],
        fill=FAR_HILL,
    )
    draw.polygon(
        [
            (x0 + width * 3 // 10, y1),
            (x0 + width * 7 // 10, y0 + height * 55 // 100),
            (x1, y0 + height * 7 // 10),
            (x1, y1),
        ],
        fill=NEAR_HILL,
    )


def icon() -> Image.Image:
    """128 x 128, as the app store asks."""
    image = Image.new("RGB", (128, 128), WALL)
    _framed_landscape(ImageDraw.Draw(image), (14, 26, 113, 101), 10)
    return image


def logo() -> Image.Image:
    """250 x 100: a large frame and two small ones, as on a gallery wall."""
    image = Image.new("RGB", (250, 100), WALL)
    draw = ImageDraw.Draw(image)
    _framed_landscape(draw, (10, 12, 132, 88), 9)
    _framed_landscape(draw, (146, 12, 236, 46), 6)
    _framed_landscape(draw, (146, 54, 236, 88), 6)
    return image


def main() -> int:
    icon().save(ICON, "PNG", optimize=True)
    logo().save(LOGO, "PNG", optimize=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
