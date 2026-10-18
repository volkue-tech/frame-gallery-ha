"""Bounded archive references use the existing isolated JPEG verifier only."""

from __future__ import annotations

import base64
import io
from dataclasses import replace

import pytest
from PIL import Image

from frame_gallery.imaging.contract import PrepareResult
from frame_gallery.imaging.worker_tasks import verify_thumbnail_task
from frame_gallery.isolation.executor import JsonObject
from tests.unit.imaging.test_contract import FAILED, OK
from tests.unit.imaging.test_verify_thumbnail import jpeg


def reference() -> str:
    with Image.open(io.BytesIO(jpeg((320, 180)))) as image:
        return base64.b64encode(
            image.convert("RGB").resize((64, 36), Image.Resampling.LANCZOS).tobytes()
        ).decode()


def test_real_archived_reference_matches_without_full_image_or_file_descriptor() -> None:
    payload: JsonObject = {
        "reference_rgb": reference(),
        "thumbnail": base64.b64encode(jpeg((320, 180))).decode(),
    }
    assert verify_thumbnail_task(payload) == {"matched": True}
    payload["thumbnail"] = base64.b64encode(jpeg((320, 180), "red")).decode()
    assert verify_thumbnail_task(payload) == {"matched": False}


@pytest.mark.parametrize("thumbnail", [b"", b"bad JPEG", b"x" * (40 * 1024 + 1), jpeg((2048, 1))])
def test_bad_or_oversized_thumbnail_cannot_verify_reference(thumbnail: bytes) -> None:
    assert verify_thumbnail_task(
        {"reference_rgb": reference(), "thumbnail": base64.b64encode(thumbnail).decode()}
    ) == {"matched": False}


@pytest.mark.parametrize(
    "changes", [{"reference_rgb": "bad"}, {"thumbnail": 1}, {"thumbnail": "x" * (56 * 1024 + 1)}]
)
def test_invalid_payload_rejected_before_decoder(changes: JsonObject) -> None:
    with pytest.raises(ValueError, match="invalid stored-reference"):
        verify_thumbnail_task({"reference_rgb": reference(), "thumbnail": "", **changes})


def test_reference_roundtrips_only_with_a_matching_contract_sha() -> None:
    result = replace(OK, reference_rgb=reference(), reference_sha256="a" * 64)
    assert PrepareResult.from_json(result.to_json()) == result


@pytest.mark.parametrize(
    "changes",
    [
        {"reference_rgb": "bad"},
        {"reference_rgb": reference()},
        {"reference_sha256": "a" * 64},
        {"reference_rgb": reference(), "reference_sha256": "invalid"},
    ],
)
def test_reference_requires_success_and_both_valid_fields(changes: JsonObject) -> None:
    with pytest.raises(ValueError, match="invalid delivery pixel"):
        replace(OK, **changes)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid delivery pixel"):
        replace(FAILED, reference_rgb=reference(), reference_sha256="a" * 64)
