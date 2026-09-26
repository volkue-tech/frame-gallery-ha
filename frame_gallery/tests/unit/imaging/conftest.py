"""Imaging test guards."""

from __future__ import annotations

import pytest
from PIL import Image


@pytest.fixture(autouse=True)
def _restore_pillow_pixel_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """``prepare_image`` sets Pillow's global limit; undo it after each test."""
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", Image.MAX_IMAGE_PIXELS)
