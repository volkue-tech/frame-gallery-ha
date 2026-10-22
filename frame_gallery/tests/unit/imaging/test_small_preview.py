from __future__ import annotations

import base64
import hashlib
import io
import json
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.imaging import worker_tasks
from frame_gallery.imaging.contract import PrepareResult
from frame_gallery.imaging.preview_codec import MAX_PREVIEW_BYTES, MAX_PREVIEW_TEXT, decode_preview
from tests.unit.imaging.prepare_helpers import SMALL, request
from tests.unit.imaging.test_contract import FAILED, OK
from tests.unit.imaging.test_delivery_reference import reference
from tests.unit.imaging.test_verify_thumbnail import jpeg
from tests.unit.store.test_current_preview import encoded


def test_real_prepare_derives_preview_from_exact_delivery_and_fits_ipc(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    source.write_bytes(jpeg((1200, 800)))
    result = worker_tasks.prepare_image(request(tmp_path, source, canvas=SMALL))
    assert result.preview_jpeg is not None
    assert len(decode_preview(result.preview_jpeg)) <= MAX_PREVIEW_BYTES
    assert (
        result.reference_sha256
        == hashlib.sha256((tmp_path / "delivery.jpg").read_bytes()).hexdigest()
    )
    assert PrepareResult.from_json(result.to_json()) == result

    assert len(json.dumps(result.to_json()).encode()) < 64 * 1024
    with Image.open(io.BytesIO(decode_preview(result.preview_jpeg))) as image:
        assert image.size == (SMALL.width, SMALL.height)


@pytest.mark.parametrize(
    "value", [None, 1, "", "!", "A" * (MAX_PREVIEW_TEXT + 1), "YWJj", encoded() + "="]
)
def test_invalid_small_preview_encoding_is_refused(value: object) -> None:
    with pytest.raises(ValueError, match="invalid small preview"):
        decode_preview(value)


@pytest.mark.parametrize("data", [jpeg((641, 360)), jpeg((640, 361)), jpeg((320, 180))[:-2]])
def test_small_preview_dimensions_and_terminator_are_bounded(data: bytes) -> None:
    with pytest.raises(ValueError, match="limits"):
        decode_preview(base64.b64encode(data).decode())


def test_preview_requires_success_and_matching_delivery_reference() -> None:
    with pytest.raises(ValueError, match="successful delivery reference"):
        replace(OK, preview_jpeg=encoded())
    with pytest.raises(ValueError, match="successful delivery reference"):
        replace(FAILED, preview_jpeg=encoded())
    good = replace(OK, preview_jpeg=encoded(), reference_rgb=reference(), reference_sha256="a" * 64)
    assert PrepareResult.from_json(good.to_json()) == good


def test_noisy_preview_has_bounded_lower_resolution_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(worker_tasks, "MAX_PREVIEW_BYTES", 20000)
    with Image.effect_noise((640, 360), 100).convert("RGB") as image:
        value = worker_tasks._small_preview(image)
    assert value is not None
    assert len(base64.b64decode(value)) <= 20000


def test_optional_encode_failure_and_exhaustion_do_not_reject_delivery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with Image.new("RGB", (16, 9)) as image:
        monkeypatch.setattr(worker_tasks, "MAX_PREVIEW_BYTES", 1)
        assert worker_tasks._small_preview(image) is None
        monkeypatch.setattr(
            Image.Image, "save", lambda *_a, **_kw: (_ for _ in ()).throw(OSError("encoder"))
        )
        assert worker_tasks._small_preview(image) is None
