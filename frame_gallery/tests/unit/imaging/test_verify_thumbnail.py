from __future__ import annotations

import base64
import hashlib
import io
import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from frame_gallery.imaging.worker_tasks import verify_thumbnail_task
from frame_gallery.isolation.executor import JsonObject


def jpeg(size: tuple[int, int], colour: str = "blue") -> bytes:
    with Image.new("RGB", size, colour) as image:
        if colour == "blue":
            draw = ImageDraw.Draw(image)
            draw.rectangle(
                (0, 0, max(0, size[0] // 2 - 1), max(0, size[1] // 2 - 1)), fill="yellow"
            )
        result = io.BytesIO()
        image.save(result, format="JPEG")
        return result.getvalue()


def run(tmp_path: Path, content: bytes, thumbnail: bytes, **changes: object) -> JsonObject:
    file = tmp_path / "preview.jpg"
    file.write_bytes(content)
    fd = os.open(file, os.O_RDONLY)
    try:
        payload: JsonObject = {
            "fd": fd,
            "sha256": hashlib.sha256(content).hexdigest(),
            "thumbnail": base64.b64encode(thumbnail).decode(),
        }
        return verify_thumbnail_task(dict(payload, **changes))
    finally:
        os.close(fd)


def test_same_artwork_matches_and_different_image_does_not(tmp_path: Path) -> None:
    content = jpeg((3840, 2160))
    assert run(tmp_path, content, jpeg((320, 180))) == {"matched": True}
    assert run(tmp_path, content, jpeg((320, 180), "red")) == {"matched": False}
    assert run(tmp_path, content, jpeg((320, 180)), sha256="f" * 64) == {"matched": False}


def test_featureless_images_are_too_ambiguous_to_attribute(tmp_path: Path) -> None:
    assert run(tmp_path, jpeg((3840, 2160), "red"), jpeg((320, 180), "red")) == {"matched": False}


@pytest.mark.parametrize(("size", "thumb"), [((100, 100), (320, 180)), ((3840, 2160), (2048, 1))])
def test_wrong_shape_or_excessive_thumbnail(
    tmp_path: Path, size: tuple[int, int], thumb: tuple[int, int]
) -> None:
    assert run(tmp_path, jpeg(size), jpeg(thumb)) == {"matched": False}


@pytest.mark.parametrize("thumbnail", [b"", b"bad JPEG", b"x" * (40 * 1024 + 1)])
def test_bad_thumbnail_is_not_an_association(tmp_path: Path, thumbnail: bytes) -> None:
    assert run(tmp_path, b"trusted content", thumbnail) == {"matched": False}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"fd": True, "sha256": "f" * 64, "thumbnail": ""},
        {"fd": 2, "sha256": "f" * 64, "thumbnail": ""},
        {"fd": 3, "sha256": "bad", "thumbnail": ""},
        {"fd": 3, "sha256": "f" * 64, "thumbnail": "x" * (56 * 1024 + 1)},
    ],
)
def test_invalid_requests_fail_before_decoding(payload: JsonObject) -> None:
    with pytest.raises(ValueError, match="invalid thumbnail verification request"):
        verify_thumbnail_task(payload)
