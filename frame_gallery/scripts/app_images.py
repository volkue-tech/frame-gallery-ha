"""Export the approved Frame Gallery mark without changing its pixels.

The independent, AI-assisted design and its provenance are committed under
assets/brand. Both Supervisor PNGs use the same transparent square mark.
Home Assistant recommends smaller sizes, but only requires a square PNG icon;
preserving the approved master avoids redrawing or regenerating the design.

    .venv/bin/python scripts/app_images.py   # copies icon.png and logo.png
"""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile
from typing import Final

from PIL import Image

PROJECT: Final = Path(__file__).resolve().parents[1]
MASTER: Final = PROJECT / "assets" / "brand" / "frame-gallery-mark.png"
ICON: Final = PROJECT / "icon.png"
LOGO: Final = PROJECT / "logo.png"


def icon() -> Image.Image:
    """Read a detached copy of the approved square icon, including its alpha."""
    with Image.open(MASTER) as image:
        return image.copy()


def logo() -> Image.Image:
    """The app detail page uses the identical approved brand mark."""
    return icon()


def main() -> int:
    copyfile(MASTER, ICON)
    copyfile(MASTER, LOGO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
